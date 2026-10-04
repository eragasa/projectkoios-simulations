"""Fail-closed typed adaptation of generated Wannier90 ``.nnkp`` files."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from ._parsing import (
    BoundedParser,
    checked_product,
    decode_text,
    parse_fortran_real,
    positive_dimension,
)

type Vector3 = tuple[float, float, float]
type Matrix3 = tuple[Vector3, Vector3, Vector3]


class Wannier90NnkpCoordinateConvention(StrEnum):
    """Native coordinate conventions established by the generated interface file."""

    real_lattice_angstrom = "real-lattice-cartesian-angstrom"
    reciprocal_lattice_per_angstrom = (
        "reciprocal-lattice-cartesian-per-angstrom-including-2pi"
    )
    kpoints_reciprocal_fractional = "kpoints-reciprocal-fractional"


@dataclass(frozen=True, slots=True)
class Wannier90NnkpProjection:
    """One two-record native projection declaration in source order."""

    center_fractional: Vector3
    angular_momentum: int
    magnetic_index: int
    radial_index: int
    z_axis: Vector3
    x_axis: Vector3
    radial_scale: float

    def __post_init__(self) -> None:
        _validate_vector(self.center_fractional, "projection center")
        _validate_vector(self.z_axis, "projection z axis")
        _validate_vector(self.x_axis, "projection x axis")
        for label, value in (
            ("angular_momentum", self.angular_momentum),
            ("magnetic_index", self.magnetic_index),
            ("radial_index", self.radial_index),
        ):
            if type(value) is not int:
                raise TypeError(f"{label} must be a built-in integer")
        if type(self.radial_scale) is not float or not math.isfinite(self.radial_scale):
            raise ValueError("radial_scale must be a finite built-in float")
        if self.radial_scale <= 0.0:
            raise ValueError("radial_scale must be positive")


@dataclass(frozen=True, slots=True)
class Wannier90NnkpNeighbor:
    """One ordered one-based k-point neighbor and reciprocal-cell shift."""

    source_kpoint_index: int
    target_kpoint_index: int
    reciprocal_cell_shift: tuple[int, int, int]

    def __post_init__(self) -> None:
        for label, value in (
            ("source_kpoint_index", self.source_kpoint_index),
            ("target_kpoint_index", self.target_kpoint_index),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")
        if (
            type(self.reciprocal_cell_shift) is not tuple
            or len(self.reciprocal_cell_shift) != 3
            or any(type(value) is not int for value in self.reciprocal_cell_shift)
        ):
            raise TypeError("reciprocal_cell_shift must contain three integers")


@dataclass(frozen=True, slots=True)
class Wannier90NnkpData:
    """Complete supported generated interface-coordinate and neighbor contract."""

    real_lattice: Matrix3
    reciprocal_lattice: Matrix3
    kpoints: tuple[Vector3, ...]
    projections: tuple[Wannier90NnkpProjection, ...]
    neighbor_count: int
    neighbors: tuple[Wannier90NnkpNeighbor, ...]
    excluded_bands: tuple[int, ...]
    real_lattice_convention: Wannier90NnkpCoordinateConvention
    reciprocal_lattice_convention: Wannier90NnkpCoordinateConvention
    kpoint_convention: Wannier90NnkpCoordinateConvention

    def __post_init__(self) -> None:
        _validate_matrix(self.real_lattice, "real_lattice")
        _validate_matrix(self.reciprocal_lattice, "reciprocal_lattice")
        if type(self.kpoints) is not tuple or not self.kpoints:
            raise ValueError("kpoints must be a nonempty tuple")
        for kpoint in self.kpoints:
            _validate_vector(kpoint, "kpoint")
        if type(self.projections) is not tuple:
            raise TypeError("projections must be a tuple")
        if any(type(item) is not Wannier90NnkpProjection for item in self.projections):
            raise TypeError("projections contain the wrong record type")
        if type(self.neighbor_count) is not int or self.neighbor_count <= 0:
            raise ValueError("neighbor_count must be positive")
        expected_neighbor_count = len(self.kpoints) * self.neighbor_count
        if (
            type(self.neighbors) is not tuple
            or len(self.neighbors) != expected_neighbor_count
        ):
            raise ValueError("neighbor inventory has the wrong record count")
        expected_sources = tuple(
            source
            for source in range(1, len(self.kpoints) + 1)
            for _ in range(self.neighbor_count)
        )
        if (
            tuple(item.source_kpoint_index for item in self.neighbors)
            != expected_sources
        ):
            raise ValueError("neighbors do not retain k-point-major native order")
        for neighbor in self.neighbors:
            if type(neighbor) is not Wannier90NnkpNeighbor:
                raise TypeError("neighbors contain the wrong record type")
            if neighbor.target_kpoint_index > len(self.kpoints):
                raise ValueError("neighbor target lies outside the k-point inventory")
        normalized = tuple(
            (
                item.source_kpoint_index,
                item.target_kpoint_index,
                *item.reciprocal_cell_shift,
            )
            for item in self.neighbors
        )
        if len(normalized) != len(set(normalized)):
            raise ValueError("neighbor inventory contains a duplicate record")
        if type(self.excluded_bands) is not tuple or any(
            type(value) is not int or value <= 0 for value in self.excluded_bands
        ):
            raise ValueError("excluded_bands must contain positive built-in integers")
        if len(self.excluded_bands) != len(set(self.excluded_bands)):
            raise ValueError("excluded_bands contains duplicates")
        expected_conventions = (
            (
                self.real_lattice_convention,
                Wannier90NnkpCoordinateConvention.real_lattice_angstrom,
            ),
            (
                self.reciprocal_lattice_convention,
                Wannier90NnkpCoordinateConvention.reciprocal_lattice_per_angstrom,
            ),
            (
                self.kpoint_convention,
                Wannier90NnkpCoordinateConvention.kpoints_reciprocal_fractional,
            ),
        )
        if any(observed is not expected for observed, expected in expected_conventions):
            raise ValueError("NNKP coordinate convention declaration is inconsistent")

    @property
    def kpoint_count(self) -> int:
        """Return the ordered native k-point count."""
        return len(self.kpoints)


class Wannier90NnkpParser(BoundedParser):
    """Parse the bounded generated NNKP schema used by the production provider."""

    _SECTIONS = (
        "real_lattice",
        "recip_lattice",
        "kpoints",
        "projections",
        "nnkpts",
        "exclude_bands",
    )

    def execute(self, payload: bytes) -> Wannier90NnkpData:
        """Decode every required block and reject unknown or duplicate blocks."""
        text = decode_text(payload, "nnkp", self.limits)
        lines = tuple(line.strip() for line in text.splitlines())
        sections = self._sections(lines)
        real_lattice = self._matrix(sections["real_lattice"], "real_lattice")
        reciprocal_lattice = self._matrix(sections["recip_lattice"], "recip_lattice")
        kpoints = self._counted_vectors(sections["kpoints"], "kpoints")
        projections = self._projections(sections["projections"])
        neighbor_count, neighbors = self._neighbors(sections["nnkpts"], len(kpoints))
        excluded_bands = self._excluded_bands(sections["exclude_bands"])
        return Wannier90NnkpData(
            real_lattice=real_lattice,
            reciprocal_lattice=reciprocal_lattice,
            kpoints=kpoints,
            projections=projections,
            neighbor_count=neighbor_count,
            neighbors=neighbors,
            excluded_bands=excluded_bands,
            real_lattice_convention=(
                Wannier90NnkpCoordinateConvention.real_lattice_angstrom
            ),
            reciprocal_lattice_convention=(
                Wannier90NnkpCoordinateConvention.reciprocal_lattice_per_angstrom
            ),
            kpoint_convention=(
                Wannier90NnkpCoordinateConvention.kpoints_reciprocal_fractional
            ),
        )

    def _sections(self, lines: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        sections: dict[str, tuple[str, ...]] = {}
        observed_order: list[str] = []
        cursor = 0
        while cursor < len(lines):
            line = lines[cursor]
            if line.startswith("end "):
                raise ValueError(f"unmatched NNKP section terminator: {line}")
            if not line.startswith("begin "):
                cursor += 1
                continue
            name = line.removeprefix("begin ")
            if name not in self._SECTIONS:
                raise ValueError(f"unsupported NNKP section: {name}")
            if name in sections:
                raise ValueError(f"duplicated NNKP section: {name}")
            end_line = f"end {name}"
            try:
                end = lines.index(end_line, cursor + 1)
            except ValueError as error:
                raise ValueError(f"unterminated NNKP section: {name}") from error
            if any(
                item.startswith(("begin ", "end ")) for item in lines[cursor + 1 : end]
            ):
                raise ValueError("nested or mismatched NNKP sections are unsupported")
            sections[name] = tuple(item for item in lines[cursor + 1 : end] if item)
            observed_order.append(name)
            cursor = end + 1
        if tuple(observed_order) != self._SECTIONS:
            raise ValueError("NNKP required sections are missing or out of order")
        return sections

    def _matrix(self, lines: tuple[str, ...], label: str) -> Matrix3:
        if len(lines) != 3:
            raise ValueError(f"{label} must contain three vectors")
        vectors = tuple(self._vector(line, label) for line in lines)
        return (vectors[0], vectors[1], vectors[2])

    def _counted_vectors(
        self, lines: tuple[str, ...], label: str
    ) -> tuple[Vector3, ...]:
        if not lines:
            raise ValueError(f"{label} section is empty")
        count = self._count(lines[0], f"{label} count")
        self._bounded_record_count(count, label)
        if len(lines) != count + 1:
            raise ValueError(f"{label} declared count disagrees with its records")
        return tuple(self._vector(line, label) for line in lines[1:])

    def _projections(
        self, lines: tuple[str, ...]
    ) -> tuple[Wannier90NnkpProjection, ...]:
        if not lines:
            raise ValueError("projections section is empty")
        count = self._count(lines[0], "projection count", allow_zero=True)
        if count:
            checked_product((count, 2), "projection", self.limits)
        if len(lines) != 1 + 2 * count:
            raise ValueError("projection declared count disagrees with its records")
        projections: list[Wannier90NnkpProjection] = []
        for index in range(count):
            first = lines[1 + 2 * index].split()
            second = lines[2 + 2 * index].split()
            if len(first) != 6 or len(second) != 7:
                raise ValueError("projection records must contain six and seven fields")
            try:
                angular, magnetic, radial = (int(value) for value in first[3:])
            except ValueError as error:
                raise ValueError("projection indices must be integers") from error
            projections.append(
                Wannier90NnkpProjection(
                    center_fractional=self._vector_fields(
                        first[:3], "projection center"
                    ),
                    angular_momentum=angular,
                    magnetic_index=magnetic,
                    radial_index=radial,
                    z_axis=self._vector_fields(second[:3], "projection z axis"),
                    x_axis=self._vector_fields(second[3:6], "projection x axis"),
                    radial_scale=parse_fortran_real(
                        second[6], "projection radial scale"
                    ),
                )
            )
        return tuple(projections)

    def _neighbors(
        self, lines: tuple[str, ...], kpoint_count: int
    ) -> tuple[int, tuple[Wannier90NnkpNeighbor, ...]]:
        if not lines:
            raise ValueError("nnkpts section is empty")
        neighbor_count = self._count(lines[0], "neighbor_count")
        expected = checked_product(
            (kpoint_count, neighbor_count), "nnkpts", self.limits
        )
        if len(lines) != expected + 1:
            raise ValueError("nnkpts declared count disagrees with its records")
        neighbors: list[Wannier90NnkpNeighbor] = []
        for line in lines[1:]:
            fields = line.split()
            if len(fields) != 5:
                raise ValueError("nnkpts records must contain five integers")
            try:
                values = tuple(int(field) for field in fields)
            except ValueError as error:
                raise ValueError("nnkpts records must contain integers") from error
            neighbors.append(
                Wannier90NnkpNeighbor(
                    values[0], values[1], (values[2], values[3], values[4])
                )
            )
        return neighbor_count, tuple(neighbors)

    def _excluded_bands(self, lines: tuple[str, ...]) -> tuple[int, ...]:
        if not lines:
            raise ValueError("exclude_bands section is empty")
        count = self._count(lines[0], "excluded-band count", allow_zero=True)
        self._bounded_record_count(count, "excluded-band")
        tokens = tuple(token for line in lines[1:] for token in line.split())
        if len(tokens) != count:
            raise ValueError("excluded-band declared count disagrees with its records")
        try:
            return tuple(int(token) for token in tokens)
        except ValueError as error:
            raise ValueError("excluded-band indices must be integers") from error

    def _count(self, line: str, label: str, *, allow_zero: bool = False) -> int:
        fields = line.split()
        if len(fields) != 1:
            raise ValueError(f"{label} must be one integer")
        try:
            value = int(fields[0])
        except ValueError as error:
            raise ValueError(f"{label} must be one integer") from error
        if allow_zero and value == 0:
            return 0
        return positive_dimension(value, label, self.limits)

    def _bounded_record_count(self, count: int, label: str) -> None:
        if count > self.limits.maximum_records:
            raise ValueError(
                f"{label} record count exceeds maximum_records "
                f"({self.limits.maximum_records})"
            )

    @classmethod
    def _vector(cls, line: str, label: str) -> Vector3:
        return cls._vector_fields(line.split(), label)

    @staticmethod
    def _vector_fields(fields: list[str], label: str) -> Vector3:
        if len(fields) != 3:
            raise ValueError(f"{label} must contain three values")
        return (
            parse_fortran_real(fields[0], label),
            parse_fortran_real(fields[1], label),
            parse_fortran_real(fields[2], label),
        )


def _validate_matrix(value: Matrix3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three vectors")
    for vector in value:
        _validate_vector(vector, label)


def _validate_vector(value: Vector3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three components")
    if any(
        type(component) is not float or not math.isfinite(component)
        for component in value
    ):
        raise ValueError(f"{label} must contain finite built-in floats")


__all__ = [
    "Wannier90NnkpCoordinateConvention",
    "Wannier90NnkpData",
    "Wannier90NnkpNeighbor",
    "Wannier90NnkpParser",
    "Wannier90NnkpProjection",
]
