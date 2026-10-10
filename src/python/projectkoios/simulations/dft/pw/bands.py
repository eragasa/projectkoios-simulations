"""Calculator-neutral reciprocal paths and band-diagram data records."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.physkit.core.data import DataObject
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation

type BandVector3 = tuple[float, float, float]
type BandSpectrum = tuple[tuple[tuple[float, ...], ...], ...]
type BandPathDirectBasisTransform = tuple[
    tuple[int, int, int],
    tuple[int, int, int],
    tuple[int, int, int],
]


class BandPathCoordinateSystem(StrEnum):
    """Declare how band-path coordinate triples depend on a unit cell."""

    reciprocal_fractional = "reciprocal-fractional"


@dataclass(frozen=True, slots=True)
class BandPathVertex(DataObject):
    """Name one reciprocal-fractional point on a declared band path."""

    label: str
    coordinates: BandVector3

    def __post_init__(self) -> None:
        if (
            type(self.label) is not str
            or not self.label
            or self.label != self.label.strip()
        ):
            raise ValueError("band-path label must be nonempty and stripped")
        _validate_vector(self.coordinates, "band-path coordinates")


@dataclass(frozen=True, slots=True)
class BandPathBranch(DataObject):
    """Retain one continuous source-ordered sequence of path vertices."""

    vertices: tuple[BandPathVertex, ...]

    def __post_init__(self) -> None:
        if type(self.vertices) is not tuple or len(self.vertices) < 2:
            raise ValueError("a band-path branch requires at least two vertices")
        if any(type(vertex) is not BandPathVertex for vertex in self.vertices):
            raise TypeError("vertices must contain BandPathVertex values")
        if any(
            first.coordinates == second.coordinates
            for first, second in zip(
                self.vertices,
                self.vertices[1:],
                strict=False,
            )
        ):
            raise ValueError("adjacent band-path vertices must be distinct")


@dataclass(frozen=True, slots=True)
class BandPathConventionProvenance(DataObject):
    """Identify a published path convention and its exact direct-basis binding."""

    convention_name: str
    convention_revision: str
    source_doi: str
    bravais_lattice: str
    appendix_a_case: str
    direct_basis_transform: BandPathDirectBasisTransform

    def __post_init__(self) -> None:
        for label, value in (
            ("convention_name", self.convention_name),
            ("convention_revision", self.convention_revision),
            ("source_doi", self.source_doi),
            ("bravais_lattice", self.bravais_lattice),
            ("appendix_a_case", self.appendix_a_case),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        transform = self.direct_basis_transform
        if (
            type(transform) is not tuple
            or len(transform) != 3
            or any(
                type(row) is not tuple
                or len(row) != 3
                or any(type(component) is not int for component in row)
                for row in transform
            )
        ):
            raise ValueError(
                "direct_basis_transform must be a three-by-three tuple of integers"
            )
        if abs(_integer_matrix_determinant(transform)) != 1:
            raise ValueError("direct_basis_transform must be integer-unimodular")

    @property
    def basis_transformed(self) -> bool:
        """Return whether the bound basis differs from the convention basis."""
        return self.direct_basis_transform != ((1, 0, 0), (0, 1, 0), (0, 0, 1))


@dataclass(frozen=True, slots=True)
class BandPath(DataObject):
    """Declare cell-relative branches under an explicit coordinate convention."""

    branches: tuple[BandPathBranch, ...]
    coordinate_system: BandPathCoordinateSystem
    convention: str
    provenance: BandPathConventionProvenance | None = None

    def __post_init__(self) -> None:
        if type(self.branches) is not tuple or not self.branches:
            raise ValueError("band path requires at least one branch")
        if any(type(branch) is not BandPathBranch for branch in self.branches):
            raise TypeError("branches must contain BandPathBranch values")
        if type(self.coordinate_system) is not BandPathCoordinateSystem:
            raise TypeError("coordinate_system must be a BandPathCoordinateSystem")
        if (
            type(self.convention) is not str
            or not self.convention
            or self.convention != self.convention.strip()
        ):
            raise ValueError("convention must be nonempty and stripped")
        if (
            self.provenance is not None
            and type(self.provenance) is not BandPathConventionProvenance
        ):
            raise TypeError("provenance must be a BandPathConventionProvenance or None")

    @property
    def segment_count(self) -> int:
        return sum(len(branch.vertices) - 1 for branch in self.branches)


@dataclass(frozen=True, slots=True)
class PwDftBandsSimulation(DataObject):
    """Bind a band path to the exact unit cell owned by a PW-DFT simulation."""

    simulation: ResolvedPwDftSimulation
    path: BandPath

    def __post_init__(self) -> None:
        if type(self.simulation) is not ResolvedPwDftSimulation:
            raise TypeError("simulation must be a ResolvedPwDftSimulation")
        if type(self.path) is not BandPath:
            raise TypeError("path must be a BandPath")


@dataclass(frozen=True, slots=True)
class BandDiagramBranch(DataObject):
    """Map one continuous path branch onto sampled diagram indices and ticks."""

    start_index: int
    stop_index: int
    tick_indices: tuple[int, ...]
    tick_labels: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.start_index) is not int or self.start_index < 0:
            raise ValueError("start_index must be nonnegative")
        if type(self.stop_index) is not int or self.stop_index <= self.start_index:
            raise ValueError("stop_index must be greater than start_index")
        if type(self.tick_indices) is not tuple or len(self.tick_indices) < 2:
            raise ValueError("tick_indices must contain at least two values")
        if type(self.tick_labels) is not tuple or len(self.tick_labels) != len(
            self.tick_indices
        ):
            raise ValueError("tick labels must match tick indices")
        if self.tick_indices[0] != self.start_index:
            raise ValueError("the first tick must equal start_index")
        if self.tick_indices[-1] != self.stop_index - 1:
            raise ValueError("the final tick must equal the final branch index")
        if any(
            type(index) is not int
            or index < self.start_index
            or index >= self.stop_index
            for index in self.tick_indices
        ):
            raise ValueError("tick indices must remain inside the branch")
        if any(
            second <= first
            for first, second in zip(
                self.tick_indices,
                self.tick_indices[1:],
                strict=False,
            )
        ):
            raise ValueError("tick indices must be strictly source ordered")
        if any(type(label) is not str or not label for label in self.tick_labels):
            raise ValueError("tick labels must be nonempty strings")


@dataclass(frozen=True, slots=True)
class BandDiagramData(DataObject):
    """Retain cell-bound provider bands and explicit plotting coordinates."""

    calculation: PwDftBandsSimulation
    sampled_kpoints_reciprocal_fractional: tuple[BandVector3, ...] | None
    path_coordinate: tuple[float, ...]
    path_coordinate_label: str
    branches: tuple[BandDiagramBranch, ...]
    energies_ev: BandSpectrum
    occupations: BandSpectrum | None = None
    reference_energy_ev: float | None = None
    reference_label: str | None = None

    def __post_init__(self) -> None:
        if type(self.calculation) is not PwDftBandsSimulation:
            raise TypeError("calculation must be a PwDftBandsSimulation")
        if self.sampled_kpoints_reciprocal_fractional is not None:
            if type(self.sampled_kpoints_reciprocal_fractional) is not tuple:
                raise TypeError("sampled k-points must be a tuple or None")
            for vector in self.sampled_kpoints_reciprocal_fractional:
                _validate_vector(vector, "sampled k-point")
        if type(self.path_coordinate) is not tuple or len(self.path_coordinate) < 2:
            raise ValueError("path_coordinate must contain at least two values")
        if any(
            type(value) is not float or not math.isfinite(value)
            for value in self.path_coordinate
        ):
            raise ValueError("path coordinates must be finite floats")
        if any(
            second < first
            for first, second in zip(
                self.path_coordinate,
                self.path_coordinate[1:],
                strict=False,
            )
        ):
            raise ValueError("path coordinates must be nondecreasing")
        if (
            type(self.path_coordinate_label) is not str
            or not self.path_coordinate_label
            or self.path_coordinate_label != self.path_coordinate_label.strip()
        ):
            raise ValueError("path_coordinate_label must be nonempty and stripped")
        if type(self.branches) is not tuple or len(self.branches) != len(
            self.path.branches
        ):
            raise ValueError("diagram branches must match path branches")
        if any(type(branch) is not BandDiagramBranch for branch in self.branches):
            raise TypeError("branches must contain BandDiagramBranch values")
        for diagram_branch, path_branch in zip(
            self.branches,
            self.path.branches,
            strict=True,
        ):
            if diagram_branch.tick_labels != tuple(
                vertex.label for vertex in path_branch.vertices
            ):
                raise ValueError("diagram tick labels must match path vertices")
        sample_count = len(self.path_coordinate)
        if self.branches[0].start_index != 0:
            raise ValueError("diagram branches must start at zero")
        if self.branches[-1].stop_index != sample_count:
            raise ValueError("diagram branches must span all samples")
        if any(
            first.stop_index != second.start_index
            for first, second in zip(
                self.branches,
                self.branches[1:],
                strict=False,
            )
        ):
            raise ValueError("diagram branches must be contiguous")
        if (
            self.sampled_kpoints_reciprocal_fractional is not None
            and len(self.sampled_kpoints_reciprocal_fractional) != sample_count
        ):
            raise ValueError("sampled k-points must match path coordinate count")
        _validate_spectrum(self.energies_ev, sample_count, "energies_ev")
        if self.occupations is not None:
            _validate_spectrum(self.occupations, sample_count, "occupations")
            if _shape(self.occupations) != _shape(self.energies_ev):
                raise ValueError("occupation and energy shapes must agree")
        if self.reference_energy_ev is not None and (
            type(self.reference_energy_ev) is not float
            or not math.isfinite(self.reference_energy_ev)
        ):
            raise ValueError("reference_energy_ev must be finite or None")
        if (self.reference_energy_ev is None) is not (self.reference_label is None):
            raise ValueError(
                "reference energy and label must both be present or absent"
            )
        if self.reference_label is not None and (
            type(self.reference_label) is not str
            or not self.reference_label
            or self.reference_label != self.reference_label.strip()
        ):
            raise ValueError("reference_label must be nonempty and stripped or None")

    @property
    def path(self) -> BandPath:
        """Return the path bound to the retained simulation unit cell."""
        return self.calculation.path

    @property
    def spin_count(self) -> int:
        return len(self.energies_ev)

    @property
    def kpoint_count(self) -> int:
        return len(self.path_coordinate)

    @property
    def band_count(self) -> int:
        return len(self.energies_ev[0][0])

    @property
    def shifted_energies_ev(self) -> BandSpectrum:
        """Return energies relative to the explicit reference when supplied."""
        reference = self.reference_energy_ev or 0.0
        return tuple(
            tuple(tuple(value - reference for value in row) for row in spin)
            for spin in self.energies_ev
        )


def _integer_matrix_determinant(value: BandPathDirectBasisTransform) -> int:
    return (
        value[0][0] * (value[1][1] * value[2][2] - value[1][2] * value[2][1])
        - value[0][1] * (value[1][0] * value[2][2] - value[1][2] * value[2][0])
        + value[0][2] * (value[1][0] * value[2][1] - value[1][1] * value[2][0])
    )


def _validate_vector(value: BandVector3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three values")
    if any(type(item) is not float or not math.isfinite(item) for item in value):
        raise ValueError(f"{label} must contain finite floats")


def _validate_spectrum(value: BandSpectrum, sample_count: int, label: str) -> None:
    if type(value) is not tuple or not value:
        raise ValueError(f"{label} must contain at least one spin channel")
    band_count: int | None = None
    for spin in value:
        if type(spin) is not tuple or len(spin) != sample_count:
            raise ValueError(f"{label} must match the sampled k-point count")
        for row in spin:
            if type(row) is not tuple or not row:
                raise ValueError(f"{label} band rows must be nonempty tuples")
            if band_count is None:
                band_count = len(row)
            elif len(row) != band_count:
                raise ValueError(f"{label} band counts must agree")
            if any(type(item) is not float or not math.isfinite(item) for item in row):
                raise ValueError(f"{label} must contain finite floats")


def _shape(value: BandSpectrum) -> tuple[int, int, int]:
    return len(value), len(value[0]), len(value[0][0])
