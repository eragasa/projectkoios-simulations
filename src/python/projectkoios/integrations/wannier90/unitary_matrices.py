"""Typed adaptation of Wannier90 ``_u.mat`` matrix files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from physkit.units.quantities import ComplexMatrixQuantity, MatrixQuantity, Unitless


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90UnitaryMatrixData:
    """Retain ordered fractional k points and native gauge matrices.

    Matrix rows follow the native outer subspace and columns follow the Wannier
    subspace. Square matrices are expected when no disentanglement is present, but the
    adapter preserves rectangular native matrices.
    """

    fractional_kpoints: MatrixQuantity
    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        """Validate unitless three-coordinate points and homogeneous matrix shapes."""
        if type(self.fractional_kpoints) is not MatrixQuantity:
            raise TypeError("fractional_kpoints must be MatrixQuantity")
        if not isinstance(self.fractional_kpoints.unit, Unitless):
            raise ValueError("fractional_kpoints must be unitless")
        if (
            self.fractional_kpoints.magnitude.ndim != 2
            or self.fractional_kpoints.magnitude.shape[1] != 3
        ):
            raise ValueError("fractional_kpoints must have shape (count, 3)")
        if not isinstance(self.matrices, tuple) or not self.matrices:
            raise TypeError("matrices must be a nonempty tuple")
        if len(self.matrices) != self.fractional_kpoints.magnitude.shape[0]:
            raise ValueError("matrix count must equal k-point count")
        if type(self.matrices[0]) is not ComplexMatrixQuantity:
            raise TypeError("every matrix must be ComplexMatrixQuantity")
        first_shape = self.matrices[0].magnitude.shape
        if first_shape[0] == 0 or first_shape[1] == 0:
            raise ValueError("native gauge matrices must have nonzero dimensions")
        for matrix in self.matrices:
            if type(matrix) is not ComplexMatrixQuantity:
                raise TypeError("every matrix must be ComplexMatrixQuantity")
            if not isinstance(matrix.unit, Unitless):
                raise ValueError("native gauge matrices must be unitless")
            if matrix.magnitude.shape != first_shape:
                raise ValueError("all native gauge matrices must have equal shape")

    @property
    def kpoint_count(self) -> int:
        """Return the native reciprocal-point count."""
        return len(self.matrices)

    @property
    def outer_dimension(self) -> int:
        """Return the native gauge-matrix row count."""
        return int(self.matrices[0].magnitude.shape[0])

    @property
    def wannier_count(self) -> int:
        """Return the native gauge-matrix column count."""
        return int(self.matrices[0].magnitude.shape[1])


class Wannier90UnitaryMatrixParser:
    """Parse one UTF-8 Wannier90 ``_u.mat`` payload without filesystem access."""

    __slots__ = ()

    def execute(self, payload: bytes) -> Wannier90UnitaryMatrixData:
        """Return ordered k points and column-major native matrix entries."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("u-matrix payload must be valid UTF-8") from error
        if len(lines) < 2:
            raise ValueError("u-matrix payload lacks its dimension header")
        dimension_fields = lines[1].split()
        if len(dimension_fields) != 3:
            raise ValueError("u-matrix dimension header must contain three integers")
        try:
            kpoint_count, row_count, column_count = (
                int(field) for field in dimension_fields
            )
        except ValueError as error:
            raise ValueError("u-matrix dimensions must be integers") from error
        if kpoint_count <= 0 or row_count <= 0 or column_count <= 0:
            raise ValueError("u-matrix dimensions must be positive")
        kpoints = np.empty((kpoint_count, 3), dtype=np.float64)
        matrices: list[ComplexMatrixQuantity] = []
        line_index = 2
        for kpoint_index in range(kpoint_count):
            while line_index < len(lines) and not lines[line_index].strip():
                line_index += 1
            if line_index >= len(lines):
                raise ValueError("u-matrix payload ends before all k points")
            coordinate_fields = lines[line_index].split()
            if len(coordinate_fields) < 3:
                raise ValueError("u-matrix k-point line must contain three coordinates")
            try:
                kpoints[kpoint_index] = [
                    float(coordinate_fields[0]),
                    float(coordinate_fields[1]),
                    float(coordinate_fields[2]),
                ]
            except ValueError as error:
                raise ValueError("u-matrix k-point coordinates must be real") from error
            line_index += 1
            matrix = np.empty((row_count, column_count), dtype=np.complex128)
            for column in range(column_count):
                for row in range(row_count):
                    if line_index >= len(lines):
                        raise ValueError("u-matrix payload ends within a matrix")
                    fields = lines[line_index].split()
                    if len(fields) != 2:
                        raise ValueError(
                            "u-matrix entry must contain real and imaginary parts"
                        )
                    try:
                        matrix[row, column] = complex(
                            float(fields[0]), float(fields[1])
                        )
                    except ValueError as error:
                        raise ValueError(
                            "u-matrix entries must contain real numbers"
                        ) from error
                    line_index += 1
            matrices.append(ComplexMatrixQuantity(matrix, Unitless()))
        if any(line.strip() for line in lines[line_index:]):
            raise ValueError("u-matrix payload contains trailing nonempty lines")
        return Wannier90UnitaryMatrixData(
            MatrixQuantity(kpoints, Unitless()), tuple(matrices)
        )
