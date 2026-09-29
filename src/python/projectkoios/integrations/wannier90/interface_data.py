"""Typed adaptation of Wannier90 eigenvalue, projection, and overlap files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from projectkoios.physkit.units.quantities import (
    ComplexMatrixQuantity,
    MatrixQuantity,
    ModelSystemUnit,
    Unitless,
)

from ._parsing import (
    BoundedParser,
    checked_product,
    decode_text,
    parse_fortran_real,
    positive_dimension,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90EigenvalueData:
    """Retain the complete native k-point-by-band eigenvalue table."""

    eigenvalues: MatrixQuantity

    def __post_init__(self) -> None:
        if type(self.eigenvalues) is not MatrixQuantity:
            raise TypeError("eigenvalues must be MatrixQuantity")
        if 0 in self.eigenvalues.magnitude.shape:
            raise ValueError("eigenvalues must be nonempty")

    @property
    def kpoint_count(self) -> int:
        return int(self.eigenvalues.magnitude.shape[0])

    @property
    def band_count(self) -> int:
        return int(self.eigenvalues.magnitude.shape[1])


class Wannier90EigenvalueParser(BoundedParser):
    """Parse one bounded UTF-8 Wannier90 ``.eig`` payload."""

    def execute(
        self, payload: bytes, energy_unit: ModelSystemUnit
    ) -> Wannier90EigenvalueData:
        """Decode a complete table in mandatory native k-point-major order."""
        text = decode_text(payload, "eigenvalue", self.limits)
        lines = tuple(line for line in text.splitlines() if line.strip())
        if not lines:
            raise ValueError("eigenvalue payload must be nonempty")
        if len(lines) > self.limits.maximum_records:
            raise ValueError("eigenvalue record count exceeds maximum_records")
        records: list[tuple[int, int, float]] = []
        for line in lines:
            fields = line.split()
            if len(fields) != 3:
                raise ValueError("eigenvalue entry must contain three fields")
            try:
                band = int(fields[0])
                kpoint = int(fields[1])
            except ValueError as error:
                raise ValueError("eigenvalue indices must be integers") from error
            value = parse_fortran_real(fields[2], "eigenvalue")
            records.append((band, kpoint, value))
        band_count = positive_dimension(
            max(record[0] for record in records), "band_count", self.limits
        )
        kpoint_count = positive_dimension(
            max(record[1] for record in records), "kpoint_count", self.limits
        )
        expected_count = checked_product(
            (kpoint_count, band_count), "eigenvalue", self.limits
        )
        if len(records) != expected_count:
            raise ValueError("eigenvalue payload does not contain a complete table")
        expected_order = tuple(
            (band, kpoint)
            for kpoint in range(1, kpoint_count + 1)
            for band in range(1, band_count + 1)
        )
        actual_order = tuple((band, kpoint) for band, kpoint, _ in records)
        if actual_order != expected_order:
            raise ValueError("eigenvalue records are not in native band/k-point order")
        values: npt.NDArray[np.float64] = np.asarray(
            [record[2] for record in records], dtype=np.float64
        ).reshape((kpoint_count, band_count))
        return Wannier90EigenvalueData(MatrixQuantity(values, energy_unit))


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90ProjectionData:
    """Retain native band-by-projection AMN matrices at ordered k points."""

    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.matrices, tuple) or not self.matrices:
            raise TypeError("matrices must be a nonempty tuple")
        if type(self.matrices[0]) is not ComplexMatrixQuantity:
            raise TypeError("every matrix must be ComplexMatrixQuantity")
        shape = self.matrices[0].magnitude.shape
        if shape[0] == 0 or shape[1] == 0:
            raise ValueError("projection matrices must have nonzero dimensions")
        for matrix in self.matrices:
            if type(matrix) is not ComplexMatrixQuantity:
                raise TypeError("every matrix must be ComplexMatrixQuantity")
            if matrix.magnitude.shape != shape:
                raise ValueError("all projection matrices must have equal shape")
            if not isinstance(matrix.unit, Unitless):
                raise ValueError("projection matrices must be unitless")

    @property
    def kpoint_count(self) -> int:
        return len(self.matrices)

    @property
    def band_count(self) -> int:
        return int(self.matrices[0].magnitude.shape[0])

    @property
    def projection_count(self) -> int:
        """Return the AMN projection count, not an inferred Wannier count."""
        return int(self.matrices[0].magnitude.shape[1])


class Wannier90ProjectionParser(BoundedParser):
    """Parse one bounded UTF-8 Wannier90 ``.amn`` payload."""

    def execute(self, payload: bytes) -> Wannier90ProjectionData:
        text = decode_text(payload, "projection", self.limits)
        lines = text.splitlines()
        if len(lines) < 2:
            raise ValueError("projection payload lacks its dimension header")
        dimensions = lines[1].split()
        if len(dimensions) != 3:
            raise ValueError("projection dimension header must contain three integers")
        try:
            raw_dimensions = tuple(int(field) for field in dimensions)
        except ValueError as error:
            raise ValueError("projection dimensions must be integers") from error
        band_count = positive_dimension(raw_dimensions[0], "band_count", self.limits)
        kpoint_count = positive_dimension(
            raw_dimensions[1], "kpoint_count", self.limits
        )
        projection_count = positive_dimension(
            raw_dimensions[2], "projection_count", self.limits
        )
        expected_count = checked_product(
            (kpoint_count, band_count, projection_count), "projection", self.limits
        )
        entries = tuple(line for line in lines[2:] if line.strip())
        if len(entries) != expected_count:
            raise ValueError("projection payload does not contain a complete table")
        parsed: list[tuple[int, int, int, complex]] = []
        occupied: set[tuple[int, int, int]] = set()
        for line in entries:
            fields = line.split()
            if len(fields) != 5:
                raise ValueError("projection entry must contain five fields")
            try:
                band = int(fields[0]) - 1
                projection = int(fields[1]) - 1
                kpoint = int(fields[2]) - 1
            except ValueError as error:
                raise ValueError("projection indices must be integers") from error
            value = complex(
                parse_fortran_real(fields[3], "projection real part"),
                parse_fortran_real(fields[4], "projection imaginary part"),
            )
            key = (kpoint, band, projection)
            if not (
                0 <= kpoint < kpoint_count
                and 0 <= band < band_count
                and 0 <= projection < projection_count
            ):
                raise ValueError("projection entry index lies outside dimensions")
            if key in occupied:
                raise ValueError("projection payload contains a duplicate index")
            occupied.add(key)
            parsed.append((kpoint, band, projection, value))
        matrices: npt.NDArray[np.complex128] = np.empty(
            (kpoint_count, band_count, projection_count), dtype=np.complex128
        )
        for kpoint, band, projection, value in parsed:
            matrices[kpoint, band, projection] = value
        return Wannier90ProjectionData(
            tuple(ComplexMatrixQuantity(matrix, Unitless()) for matrix in matrices)
        )


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90NeighborOverlapData:
    """Retain ordered native neighbor records and square band-overlap matrices."""

    kpoint_count: int
    neighbor_count: int
    first_kpoint_indices: tuple[int, ...]
    second_kpoint_indices: tuple[int, ...]
    reciprocal_shifts: tuple[tuple[int, int, int], ...]
    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        if type(self.kpoint_count) is not int or type(self.neighbor_count) is not int:
            raise TypeError("kpoint_count and neighbor_count must be built-in integers")
        if self.kpoint_count <= 0 or self.neighbor_count <= 0:
            raise ValueError("kpoint_count and neighbor_count must be positive")
        record_count = self.kpoint_count * self.neighbor_count
        inventories = (
            self.first_kpoint_indices,
            self.second_kpoint_indices,
            self.reciprocal_shifts,
            self.matrices,
        )
        if any(not isinstance(values, tuple) for values in inventories):
            raise TypeError("neighbor inventories must be tuples")
        if any(len(values) != record_count for values in inventories):
            raise ValueError("neighbor inventories have an inconsistent record count")
        expected_sources = tuple(
            source
            for source in range(self.kpoint_count)
            for _ in range(self.neighbor_count)
        )
        if self.first_kpoint_indices != expected_sources:
            raise ValueError(
                "each first k point must own neighbor_count records "
                "in normalized native order"
            )
        for first, second in zip(
            self.first_kpoint_indices, self.second_kpoint_indices, strict=True
        ):
            if type(first) is not int or type(second) is not int:
                raise TypeError("k-point indices must be built-in integers")
            if not (0 <= first < self.kpoint_count and 0 <= second < self.kpoint_count):
                raise ValueError("k-point index lies outside declared count")
        for shift in self.reciprocal_shifts:
            if (
                not isinstance(shift, tuple)
                or len(shift) != 3
                or any(type(value) is not int for value in shift)
            ):
                raise TypeError("reciprocal shifts must be integer triples")
        normalized = tuple(
            (first, second, *shift)
            for first, second, shift in zip(
                self.first_kpoint_indices,
                self.second_kpoint_indices,
                self.reciprocal_shifts,
                strict=True,
            )
        )
        if len(set(normalized)) != len(normalized):
            raise ValueError("neighbor inventory contains a duplicate record")
        if type(self.matrices[0]) is not ComplexMatrixQuantity:
            raise TypeError("every matrix must be ComplexMatrixQuantity")
        shape = self.matrices[0].magnitude.shape
        if shape[0] == 0 or shape[0] != shape[1]:
            raise ValueError("neighbor-overlap matrices must be nonempty and square")
        for matrix in self.matrices:
            if type(matrix) is not ComplexMatrixQuantity:
                raise TypeError("every matrix must be ComplexMatrixQuantity")
            if matrix.magnitude.shape != shape:
                raise ValueError("all overlap matrices must have equal shape")
            if not isinstance(matrix.unit, Unitless):
                raise ValueError("overlap matrices must be unitless")

    @property
    def band_count(self) -> int:
        return int(self.matrices[0].magnitude.shape[0])

    @property
    def normalized_records(self) -> tuple[tuple[int, int, int, int, int], ...]:
        """Return one-based source/target indices and shifts in native order."""
        return tuple(
            (first + 1, second + 1, *shift)
            for first, second, shift in zip(
                self.first_kpoint_indices,
                self.second_kpoint_indices,
                self.reciprocal_shifts,
                strict=True,
            )
        )


class Wannier90NeighborOverlapParser(BoundedParser):
    """Parse one bounded UTF-8 Wannier90 ``.mmn`` payload."""

    def execute(self, payload: bytes) -> Wannier90NeighborOverlapData:
        text = decode_text(payload, "neighbor-overlap", self.limits)
        lines = text.splitlines()
        if len(lines) < 2:
            raise ValueError("neighbor-overlap payload lacks its dimension header")
        dimensions = lines[1].split()
        if len(dimensions) != 3:
            raise ValueError("overlap dimension header must contain three integers")
        try:
            raw_dimensions = tuple(int(field) for field in dimensions)
        except ValueError as error:
            raise ValueError("overlap dimensions must be integers") from error
        band_count = positive_dimension(raw_dimensions[0], "band_count", self.limits)
        kpoint_count = positive_dimension(
            raw_dimensions[1], "kpoint_count", self.limits
        )
        neighbor_count = positive_dimension(
            raw_dimensions[2], "neighbor_count", self.limits
        )
        block_count = checked_product(
            (kpoint_count, neighbor_count), "neighbor", self.limits
        )
        matrix_entry_count = checked_product(
            (block_count, band_count, band_count), "overlap", self.limits
        )
        content = tuple(line for line in lines[2:] if line.strip())
        expected_line_count = block_count + matrix_entry_count
        if len(content) < expected_line_count:
            raise ValueError("neighbor-overlap payload ends within a matrix")
        if len(content) > expected_line_count:
            raise ValueError("neighbor-overlap payload contains trailing records")
        first_indices: list[int] = []
        second_indices: list[int] = []
        shifts: list[tuple[int, int, int]] = []
        matrices: list[ComplexMatrixQuantity] = []
        line_index = 0
        for _ in range(block_count):
            header = content[line_index].split()
            line_index += 1
            if len(header) != 5:
                raise ValueError("neighbor header must contain five integers")
            try:
                first = int(header[0]) - 1
                second = int(header[1]) - 1
                shift = (int(header[2]), int(header[3]), int(header[4]))
            except ValueError as error:
                raise ValueError("neighbor header must contain integers") from error
            values: list[complex] = []
            for _ in range(band_count * band_count):
                fields = content[line_index].split()
                line_index += 1
                if len(fields) != 2:
                    raise ValueError("overlap entry must contain two fields")
                values.append(
                    complex(
                        parse_fortran_real(fields[0], "overlap real part"),
                        parse_fortran_real(fields[1], "overlap imaginary part"),
                    )
                )
            matrix: npt.NDArray[np.complex128] = np.asarray(
                values, dtype=np.complex128
            ).reshape((band_count, band_count), order="F")
            first_indices.append(first)
            second_indices.append(second)
            shifts.append(shift)
            matrices.append(ComplexMatrixQuantity(matrix, Unitless()))
        return Wannier90NeighborOverlapData(
            kpoint_count,
            neighbor_count,
            tuple(first_indices),
            tuple(second_indices),
            tuple(shifts),
            tuple(matrices),
        )
