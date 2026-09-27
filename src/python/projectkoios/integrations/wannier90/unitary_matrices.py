"""Typed adaptation of native Wannier90 ``_u.mat`` matrix files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from physkit.units.quantities import ComplexMatrixQuantity, MatrixQuantity, Unitless

from ._parsing import (
    BoundedParser,
    checked_product,
    decode_text,
    parse_fortran_real,
    positive_dimension,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90UnitaryMatrixData:
    """Retain ordered fractional k points and square Wannier gauge matrices."""

    fractional_kpoints: MatrixQuantity
    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
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
        first = self.matrices[0]
        if type(first) is not ComplexMatrixQuantity:
            raise TypeError("every matrix must be ComplexMatrixQuantity")
        dimension = first.magnitude.shape[0]
        if dimension == 0 or first.magnitude.shape != (dimension, dimension):
            raise ValueError("_u.mat gauge matrices must be nonempty and square")
        for matrix in self.matrices:
            if type(matrix) is not ComplexMatrixQuantity:
                raise TypeError("every matrix must be ComplexMatrixQuantity")
            if not isinstance(matrix.unit, Unitless):
                raise ValueError("native gauge matrices must be unitless")
            if matrix.magnitude.shape != (dimension, dimension):
                raise ValueError(
                    "all native gauge matrices must have equal square shape"
                )

    @property
    def kpoint_count(self) -> int:
        return len(self.matrices)

    @property
    def wannier_count(self) -> int:
        return int(self.matrices[0].magnitude.shape[0])


class Wannier90UnitaryMatrixParser(BoundedParser):
    """Parse bounded square native ``_u.mat`` payloads.

    Rectangular ``_u_dis.mat`` data have different native semantics and are
    deliberately unsupported rather than being interpreted as ``_u.mat``.
    """

    def execute(self, payload: bytes) -> Wannier90UnitaryMatrixData:
        text = decode_text(payload, "u-matrix", self.limits)
        lines = text.splitlines()
        if len(lines) < 2:
            raise ValueError("u-matrix payload lacks its dimension header")
        dimension_fields = lines[1].split()
        if len(dimension_fields) != 3:
            raise ValueError("u-matrix dimension header must contain three integers")
        try:
            raw_dimensions = tuple(int(field) for field in dimension_fields)
        except ValueError as error:
            raise ValueError("u-matrix dimensions must be integers") from error
        kpoint_count = positive_dimension(
            raw_dimensions[0], "kpoint_count", self.limits
        )
        row_count = positive_dimension(raw_dimensions[1], "row_count", self.limits)
        column_count = positive_dimension(
            raw_dimensions[2], "column_count", self.limits
        )
        if row_count != column_count:
            raise ValueError(
                "_u.mat dimensions must be square; rectangular "
                "_u_dis.mat is unsupported"
            )
        matrix_entry_count = checked_product(
            (kpoint_count, row_count, column_count), "u-matrix", self.limits
        )
        content = tuple(line for line in lines[2:] if line.strip())
        expected_line_count = kpoint_count + matrix_entry_count
        if len(content) < expected_line_count:
            raise ValueError("u-matrix payload ends within a matrix")
        if len(content) > expected_line_count:
            raise ValueError("u-matrix payload contains trailing records")
        kpoint_values: list[tuple[float, float, float]] = []
        matrices: list[ComplexMatrixQuantity] = []
        line_index = 0
        for _ in range(kpoint_count):
            coordinate_fields = content[line_index].split()
            line_index += 1
            if len(coordinate_fields) != 3:
                raise ValueError("u-matrix k-point line must contain three coordinates")
            kpoint_values.append(
                (
                    parse_fortran_real(coordinate_fields[0], "k-point coordinate"),
                    parse_fortran_real(coordinate_fields[1], "k-point coordinate"),
                    parse_fortran_real(coordinate_fields[2], "k-point coordinate"),
                )
            )
            values: list[complex] = []
            for _ in range(row_count * column_count):
                fields = content[line_index].split()
                line_index += 1
                if len(fields) != 2:
                    raise ValueError(
                        "u-matrix entry must contain real and imaginary parts"
                    )
                values.append(
                    complex(
                        parse_fortran_real(fields[0], "u-matrix real part"),
                        parse_fortran_real(fields[1], "u-matrix imaginary part"),
                    )
                )
            matrix: npt.NDArray[np.complex128] = np.asarray(
                values, dtype=np.complex128
            ).reshape((row_count, column_count), order="F")
            matrices.append(ComplexMatrixQuantity(matrix, Unitless()))
        kpoints: npt.NDArray[np.float64] = np.asarray(kpoint_values, dtype=np.float64)
        return Wannier90UnitaryMatrixData(
            MatrixQuantity(kpoints, Unitless()), tuple(matrices)
        )
