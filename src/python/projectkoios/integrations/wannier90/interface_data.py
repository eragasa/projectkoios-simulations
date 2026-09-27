"""Typed adaptation of Wannier90 eigenvalue, projection, and overlap files."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from physkit.units.quantities import (
    ComplexMatrixQuantity,
    MatrixQuantity,
    ModelSystemUnit,
    Unitless,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90EigenvalueData:
    """Retain the complete native band-by-k-point eigenvalue table."""

    eigenvalues: MatrixQuantity

    def __post_init__(self) -> None:
        """Validate a nonempty finite two-dimensional energy table."""
        if type(self.eigenvalues) is not MatrixQuantity:
            raise TypeError("eigenvalues must be MatrixQuantity")
        if 0 in self.eigenvalues.magnitude.shape:
            raise ValueError("eigenvalues must be nonempty")

    @property
    def kpoint_count(self) -> int:
        """Return the native reciprocal-point count."""
        return int(self.eigenvalues.magnitude.shape[0])

    @property
    def band_count(self) -> int:
        """Return the native band count."""
        return int(self.eigenvalues.magnitude.shape[1])


class Wannier90EigenvalueParser:
    """Parse one UTF-8 Wannier90 ``.eig`` payload."""

    __slots__ = ()

    def execute(
        self, payload: bytes, energy_unit: ModelSystemUnit
    ) -> Wannier90EigenvalueData:
        """Decode one-based band and k-point indices into a complete matrix."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        lines = self._decode_nonempty_lines(payload, "eigenvalue")
        records: list[tuple[int, int, float]] = []
        for line in lines:
            fields = line.split()
            if len(fields) != 3:
                raise ValueError("eigenvalue entry must contain three fields")
            try:
                records.append((int(fields[0]), int(fields[1]), float(fields[2])))
            except ValueError as error:
                raise ValueError(
                    "eigenvalue entry contains an invalid number"
                ) from error
        if not records:
            raise ValueError("eigenvalue payload must be nonempty")
        band_count = max(record[0] for record in records)
        kpoint_count = max(record[1] for record in records)
        if band_count <= 0 or kpoint_count <= 0:
            raise ValueError("eigenvalue indices must be one-based and positive")
        values = np.empty((kpoint_count, band_count), dtype=np.float64)
        occupied: set[tuple[int, int]] = set()
        for band_index, kpoint_index, value in records:
            key = (kpoint_index - 1, band_index - 1)
            if key[0] < 0 or key[1] < 0:
                raise ValueError("eigenvalue indices must be one-based and positive")
            if key in occupied:
                raise ValueError("eigenvalue payload contains a duplicate index")
            occupied.add(key)
            values[key] = value
        if len(occupied) != kpoint_count * band_count:
            raise ValueError("eigenvalue payload does not contain a complete table")
        return Wannier90EigenvalueData(MatrixQuantity(values, energy_unit))

    @staticmethod
    def _decode_nonempty_lines(payload: bytes, label: str) -> tuple[str, ...]:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"{label} payload must be valid UTF-8") from error
        return tuple(line for line in text.splitlines() if line.strip())


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90ProjectionData:
    """Retain native band-by-Wannier projection matrices at ordered k points."""

    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        """Validate nonempty homogeneous unitless projection matrices."""
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
        """Return the native reciprocal-point count."""
        return len(self.matrices)

    @property
    def band_count(self) -> int:
        """Return the outer band count."""
        return int(self.matrices[0].magnitude.shape[0])

    @property
    def wannier_count(self) -> int:
        """Return the projection count."""
        return int(self.matrices[0].magnitude.shape[1])


class Wannier90ProjectionParser:
    """Parse one UTF-8 Wannier90 ``.amn`` payload."""

    __slots__ = ()

    def execute(self, payload: bytes) -> Wannier90ProjectionData:
        """Decode one-based band, projection, and k-point indices."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("projection payload must be valid UTF-8") from error
        if len(lines) < 2:
            raise ValueError("projection payload lacks its dimension header")
        dimensions = lines[1].split()
        if len(dimensions) != 3:
            raise ValueError("projection dimension header must contain three integers")
        try:
            band_count, kpoint_count, wannier_count = (
                int(field) for field in dimensions
            )
        except ValueError as error:
            raise ValueError("projection dimensions must be integers") from error
        if min(band_count, kpoint_count, wannier_count) <= 0:
            raise ValueError("projection dimensions must be positive")
        matrices = np.empty(
            (kpoint_count, band_count, wannier_count), dtype=np.complex128
        )
        occupied: set[tuple[int, int, int]] = set()
        for line in lines[2:]:
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) != 5:
                raise ValueError("projection entry must contain five fields")
            try:
                band = int(fields[0]) - 1
                projection = int(fields[1]) - 1
                kpoint = int(fields[2]) - 1
                value = complex(float(fields[3]), float(fields[4]))
            except ValueError as error:
                raise ValueError(
                    "projection entry contains an invalid number"
                ) from error
            key = (kpoint, band, projection)
            if not (
                0 <= kpoint < kpoint_count
                and 0 <= band < band_count
                and 0 <= projection < wannier_count
            ):
                raise ValueError("projection entry index lies outside dimensions")
            if key in occupied:
                raise ValueError("projection payload contains a duplicate index")
            occupied.add(key)
            matrices[key] = value
        if len(occupied) != kpoint_count * band_count * wannier_count:
            raise ValueError("projection payload does not contain a complete table")
        return Wannier90ProjectionData(
            tuple(ComplexMatrixQuantity(matrix, Unitless()) for matrix in matrices)
        )


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90NeighborOverlapData:
    """Retain ordered native neighbor records and band-overlap matrices."""

    kpoint_count: int
    neighbor_count: int
    first_kpoint_indices: tuple[int, ...]
    second_kpoint_indices: tuple[int, ...]
    reciprocal_shifts: tuple[tuple[int, int, int], ...]
    matrices: tuple[ComplexMatrixQuantity, ...]

    def __post_init__(self) -> None:
        """Validate complete zero-based neighbor inventories and matrix dimensions."""
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
            raise ValueError(
                "neighbor inventories must contain "
                "kpoint_count * neighbor_count records"
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
        counts = np.bincount(
            np.asarray(self.first_kpoint_indices, dtype=np.int64),
            minlength=self.kpoint_count,
        )
        if not np.all(counts == self.neighbor_count):
            raise ValueError("each first k point must have neighbor_count records")

    @property
    def band_count(self) -> int:
        """Return the represented band count."""
        return int(self.matrices[0].magnitude.shape[0])


class Wannier90NeighborOverlapParser:
    """Parse one UTF-8 Wannier90 ``.mmn`` payload."""

    __slots__ = ()

    def execute(self, payload: bytes) -> Wannier90NeighborOverlapData:
        """Decode ordered neighbor headers and column-major overlap matrices."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("neighbor-overlap payload must be valid UTF-8") from error
        if len(lines) < 2:
            raise ValueError("neighbor-overlap payload lacks its dimension header")
        dimensions = lines[1].split()
        if len(dimensions) != 3:
            raise ValueError("overlap dimension header must contain three integers")
        try:
            band_count, kpoint_count, neighbor_count = (
                int(field) for field in dimensions
            )
        except ValueError as error:
            raise ValueError("overlap dimensions must be integers") from error
        if min(band_count, kpoint_count, neighbor_count) <= 0:
            raise ValueError("overlap dimensions must be positive")
        first_indices: list[int] = []
        second_indices: list[int] = []
        shifts: list[tuple[int, int, int]] = []
        matrices: list[ComplexMatrixQuantity] = []
        line_index = 2
        for _ in range(kpoint_count * neighbor_count):
            if line_index >= len(lines):
                raise ValueError("overlap payload ends before a neighbor header")
            header = lines[line_index].split()
            line_index += 1
            if len(header) != 5:
                raise ValueError("neighbor header must contain five integers")
            try:
                first = int(header[0]) - 1
                second = int(header[1]) - 1
                shift = (int(header[2]), int(header[3]), int(header[4]))
            except ValueError as error:
                raise ValueError("neighbor header must contain integers") from error
            matrix = np.empty((band_count, band_count), dtype=np.complex128)
            for column in range(band_count):
                for row in range(band_count):
                    if line_index >= len(lines):
                        raise ValueError("overlap payload ends within a matrix")
                    fields = lines[line_index].split()
                    line_index += 1
                    if len(fields) != 2:
                        raise ValueError("overlap entry must contain two fields")
                    try:
                        matrix[row, column] = complex(
                            float(fields[0]), float(fields[1])
                        )
                    except ValueError as error:
                        raise ValueError(
                            "overlap entry contains an invalid number"
                        ) from error
            first_indices.append(first)
            second_indices.append(second)
            shifts.append(shift)
            matrices.append(ComplexMatrixQuantity(matrix, Unitless()))
        if any(line.strip() for line in lines[line_index:]):
            raise ValueError("neighbor-overlap payload contains trailing lines")
        return Wannier90NeighborOverlapData(
            kpoint_count,
            neighbor_count,
            tuple(first_indices),
            tuple(second_indices),
            tuple(shifts),
            tuple(matrices),
        )
