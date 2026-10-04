"""Typed adaptation of native rectangular Wannier90 ``_u_dis.mat`` files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from projectkoios.physkit.units.quantities import (
    ComplexMatrixQuantity,
    MatrixQuantity,
    Unitless,
)

from ._matrix_conventions import Wannier90MatrixStorageOrder
from ._parsing import (
    BoundedParser,
    checked_product,
    decode_text,
    parse_fortran_real,
    positive_dimension,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90DisentanglementMatrixData:
    """Retain logical native matrices with shape ``(band, wannier)``."""

    fractional_kpoints: MatrixQuantity
    matrices: tuple[ComplexMatrixQuantity, ...]
    band_count: int
    wannier_count: int
    storage_order: Wannier90MatrixStorageOrder

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
        for label, value in (
            ("band_count", self.band_count),
            ("wannier_count", self.wannier_count),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")
        if self.wannier_count > self.band_count:
            raise ValueError("wannier_count must not exceed band_count")
        if type(self.storage_order) is not Wannier90MatrixStorageOrder:
            raise TypeError("storage_order must be a Wannier90MatrixStorageOrder")
        if type(self.matrices) is not tuple or not self.matrices:
            raise TypeError("matrices must be a nonempty tuple")
        if len(self.matrices) != self.fractional_kpoints.magnitude.shape[0]:
            raise ValueError("matrix count must equal k-point count")
        expected_shape = (self.band_count, self.wannier_count)
        for matrix in self.matrices:
            if type(matrix) is not ComplexMatrixQuantity:
                raise TypeError("every matrix must be ComplexMatrixQuantity")
            if not isinstance(matrix.unit, Unitless):
                raise ValueError("native disentanglement matrices must be unitless")
            if matrix.magnitude.shape != expected_shape:
                raise ValueError(
                    "native disentanglement matrix must have (band, wannier) shape"
                )

    @property
    def kpoint_count(self) -> int:
        """Return the number of native k-point blocks."""
        return len(self.matrices)


class Wannier90DisentanglementMatrixParser(BoundedParser):
    """Parse bounded rectangular native ``_u_dis.mat`` payloads.

    The native header is ``(kpoints, wannier, bands)`` while each matrix is
    returned with logical orientation ``(bands, wannier)``. Fortran-native
    records vary the band (first) index fastest.
    """

    def execute(self, payload: bytes) -> Wannier90DisentanglementMatrixData:
        text = decode_text(payload, "u-dis-matrix", self.limits)
        lines = text.splitlines()
        if len(lines) < 2:
            raise ValueError("u-dis-matrix payload lacks its dimension header")
        dimension_fields = lines[1].split()
        if len(dimension_fields) != 3:
            raise ValueError(
                "u-dis-matrix dimension header must contain three integers"
            )
        try:
            raw_dimensions = tuple(int(field) for field in dimension_fields)
        except ValueError as error:
            raise ValueError("u-dis-matrix dimensions must be integers") from error
        kpoint_count = positive_dimension(
            raw_dimensions[0], "kpoint_count", self.limits
        )
        wannier_count = positive_dimension(
            raw_dimensions[1], "wannier_count", self.limits
        )
        band_count = positive_dimension(raw_dimensions[2], "band_count", self.limits)
        if wannier_count > band_count:
            raise ValueError("u_dis Wannier count must not exceed band count")
        matrix_entry_count = checked_product(
            (kpoint_count, band_count, wannier_count),
            "u-dis-matrix",
            self.limits,
        )
        content = tuple(line for line in lines[2:] if line.strip())
        expected_line_count = kpoint_count + matrix_entry_count
        if len(content) < expected_line_count:
            raise ValueError("u-dis-matrix payload ends within a matrix")
        if len(content) > expected_line_count:
            raise ValueError("u-dis-matrix payload contains trailing records")
        kpoint_values: list[tuple[float, float, float]] = []
        matrices: list[ComplexMatrixQuantity] = []
        line_index = 0
        for _ in range(kpoint_count):
            coordinate_fields = content[line_index].split()
            line_index += 1
            if len(coordinate_fields) != 3:
                raise ValueError(
                    "u-dis-matrix k-point line must contain three coordinates"
                )
            kpoint_values.append(
                (
                    parse_fortran_real(coordinate_fields[0], "k-point coordinate"),
                    parse_fortran_real(coordinate_fields[1], "k-point coordinate"),
                    parse_fortran_real(coordinate_fields[2], "k-point coordinate"),
                )
            )
            values: list[complex] = []
            for _ in range(band_count * wannier_count):
                fields = content[line_index].split()
                line_index += 1
                if len(fields) != 2:
                    raise ValueError(
                        "u-dis-matrix entry must contain real and imaginary parts"
                    )
                values.append(
                    complex(
                        parse_fortran_real(fields[0], "u-dis-matrix real part"),
                        parse_fortran_real(fields[1], "u-dis-matrix imaginary part"),
                    )
                )
            matrix: npt.NDArray[np.complex128] = np.asarray(
                values, dtype=np.complex128
            ).reshape((band_count, wannier_count), order="F")
            matrices.append(ComplexMatrixQuantity(matrix, Unitless()))
        kpoints: npt.NDArray[np.float64] = np.asarray(kpoint_values, dtype=np.float64)
        return Wannier90DisentanglementMatrixData(
            fractional_kpoints=MatrixQuantity(kpoints, Unitless()),
            matrices=tuple(matrices),
            band_count=band_count,
            wannier_count=wannier_count,
            storage_order=Wannier90MatrixStorageOrder.first_index_fastest,
        )


__all__ = [
    "Wannier90DisentanglementMatrixData",
    "Wannier90DisentanglementMatrixParser",
    "Wannier90MatrixStorageOrder",
]
