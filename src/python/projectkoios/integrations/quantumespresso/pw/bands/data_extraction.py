"""Extract calculator-neutral band data from a parsed QE QEXSD document."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, cast

from projectkoios.integrations.quantumespresso.pw.bands.path import (
    QeBandsPathProjection,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
)
from projectkoios.simulations.dft.pw.bands import BandDiagramData
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

# CODATA 2018 values used only for an explicit QEXSD Hartree/bohr conversion.
_HARTREE_TO_EV = 27.211386245988
_BOHR_TO_ANGSTROM = 0.529177210903
_REQUIRED_SPECTRAL_FIELDS = (
    "declared_unit_system_label",
    "atomic_structure_alat",
    "reciprocal_lattice_coefficients",
    "reciprocal_lattice_source_label",
    "k_points",
    "k_point_source_label",
    "eigenvalues",
    "occupations",
    "eigenvalue_source_label",
    "sampled_k_point_count",
    "band_count",
)

type _Vector3 = tuple[float, float, float]
type _Spectrum = tuple[tuple[float, ...], ...]


class _QexsdBandDocument(Protocol):
    declared_unit_system_label: str
    atomic_structure_alat: float
    reciprocal_lattice_coefficients: tuple[_Vector3, ...]
    reciprocal_lattice_source_label: str
    k_points: tuple[_Vector3, ...]
    k_point_source_label: str
    eigenvalues: _Spectrum
    occupations: _Spectrum | None
    eigenvalue_source_label: str
    sampled_k_point_count: int
    band_count: int


class QeBandsDataError(ValueError):
    """Report QEXSD/path disagreement or unsupported spectral data."""


@dataclass(frozen=True, slots=True)
class QeBandsData:
    """Retain QEXSD evidence and its calculator-neutral band projection."""

    qexsd: QeQexsdData
    diagram: BandDiagramData
    maximum_kpoint_deviation: float

    def __post_init__(self) -> None:
        if type(self.qexsd) is not QeQexsdData:
            raise TypeError("qexsd must be QeQexsdData")
        if type(self.diagram) is not BandDiagramData:
            raise TypeError("diagram must be BandDiagramData")
        if (
            type(self.maximum_kpoint_deviation) is not float
            or not math.isfinite(self.maximum_kpoint_deviation)
            or self.maximum_kpoint_deviation < 0.0
        ):
            raise ValueError("maximum_kpoint_deviation must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class QeBandsDataExtractor:
    """Project full-precision QEXSD spectra without using plotting files."""

    coordinate_tolerance: float = 1.0e-10
    cell_tolerance: float = 1.0e-7

    def __post_init__(self) -> None:
        for label, value in (
            ("coordinate_tolerance", self.coordinate_tolerance),
            ("cell_tolerance", self.cell_tolerance),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")

    def extract(
        self,
        qexsd: QeQexsdData,
        *,
        projection: QeBandsPathProjection,
        expected_band_count: int | None = None,
        reference_energy_ev: float | None = None,
        reference_label: str | None = None,
    ) -> QeBandsData:
        """Validate QEXSD k-points and convert native Hartree values to eV."""
        if type(qexsd) is not QeQexsdData:
            raise TypeError("qexsd must be QeQexsdData")
        if type(projection) is not QeBandsPathProjection:
            raise TypeError("projection must be QeBandsPathProjection")
        if expected_band_count is not None and (
            type(expected_band_count) is not int or expected_band_count <= 0
        ):
            raise ValueError("expected_band_count must be positive or None")
        document = qexsd.document
        if any(not hasattr(document, name) for name in _REQUIRED_SPECTRAL_FIELDS):
            raise TypeError(
                "QEXSD document must be produced by QuantumEspressoXsdDocumentParser"
            )
        parsed = cast("_QexsdBandDocument", document)
        observed_simulation = PwDftSimulation(
            unit_cell=qexsd.final_structure.unit_cell,
            settings=projection.calculation.simulation.settings,
        )
        if not _simulations_use_same_cell(
            projection.calculation.simulation,
            observed_simulation,
            tolerance=self.cell_tolerance,
        ):
            raise QeBandsDataError(
                "QEXSD unit cell disagrees with the configured simulation"
            )
        if parsed.declared_unit_system_label != "Hartree atomic units":
            raise QeBandsDataError("unsupported QEXSD declared unit system")
        if parsed.sampled_k_point_count != projection.expected_sample_count:
            raise QeBandsDataError("QEXSD sample count disagrees with the band path")
        if (
            len(parsed.k_points) != parsed.sampled_k_point_count
            or len(parsed.eigenvalues) != parsed.sampled_k_point_count
        ):
            raise QeBandsDataError("QEXSD spectral array shape is inconsistent")
        if expected_band_count is not None and parsed.band_count != expected_band_count:
            raise QeBandsDataError("QEXSD band count disagrees with the declaration")
        if any(len(row) != parsed.band_count for row in parsed.eigenvalues):
            raise QeBandsDataError("QEXSD eigenvalue rows have inconsistent shapes")
        if parsed.occupations is not None and (
            len(parsed.occupations) != len(parsed.eigenvalues)
            or any(len(row) != parsed.band_count for row in parsed.occupations)
        ):
            raise QeBandsDataError("QEXSD occupation rows have inconsistent shapes")
        reciprocal = _matrix3(parsed.reciprocal_lattice_coefficients)
        expected_fractional = _expected_crystal_samples(projection)
        expected_cartesian = tuple(
            _row_vector_matrix_product(point, reciprocal)
            for point in expected_fractional
        )
        deviations = tuple(
            _distance(observed, expected)
            for observed, expected in zip(
                parsed.k_points,
                expected_cartesian,
                strict=True,
            )
        )
        maximum_deviation = max(deviations, default=0.0)
        if maximum_deviation > self.coordinate_tolerance:
            raise QeBandsDataError("QEXSD k-points disagree with the projected path")
        if (
            type(parsed.atomic_structure_alat) is not float
            or not math.isfinite(parsed.atomic_structure_alat)
            or parsed.atomic_structure_alat <= 0.0
        ):
            raise QeBandsDataError("QEXSD alat must be positive and finite")
        reciprocal_scale = (
            2.0 * math.pi / (parsed.atomic_structure_alat * _BOHR_TO_ANGSTROM)
        )
        coordinate = _branchwise_path_coordinate(
            parsed.k_points,
            projection,
            reciprocal_scale,
        )
        energies_ev = tuple(
            tuple(value * _HARTREE_TO_EV for value in row) for row in parsed.eigenvalues
        )
        diagram = BandDiagramData(
            calculation=projection.calculation,
            sampled_kpoints_reciprocal_fractional=expected_fractional,
            path_coordinate=coordinate,
            path_coordinate_label="reciprocal-path distance (1/angstrom)",
            branches=projection.diagram_branches(),
            energies_ev=(energies_ev,),
            occupations=(parsed.occupations,)
            if parsed.occupations is not None
            else None,
            reference_energy_ev=reference_energy_ev,
            reference_label=reference_label,
        )
        return QeBandsData(
            qexsd=qexsd,
            diagram=diagram,
            maximum_kpoint_deviation=maximum_deviation,
        )


def _simulations_use_same_cell(
    expected: PwDftSimulation,
    observed: PwDftSimulation,
    *,
    tolerance: float,
) -> bool:
    if tuple(symbol for symbol, _ in expected.fractional_sites) != tuple(
        symbol for symbol, _ in observed.fractional_sites
    ):
        return False
    expected_values = (
        *expected.lattice_vectors_angstrom,
        *(position for _, position in expected.fractional_sites),
    )
    observed_values = (
        *observed.lattice_vectors_angstrom,
        *(position for _, position in observed.fractional_sites),
    )
    return len(expected_values) == len(observed_values) and all(
        _distance(left, right) <= tolerance
        for left, right in zip(expected_values, observed_values, strict=True)
    )


def _matrix3(values: tuple[_Vector3, ...]) -> tuple[_Vector3, _Vector3, _Vector3]:
    if type(values) is not tuple or len(values) != 3:
        raise QeBandsDataError("QEXSD reciprocal lattice must contain three vectors")
    rows: list[_Vector3] = []
    for row in values:
        if type(row) is not tuple or len(row) != 3:
            raise QeBandsDataError("QEXSD reciprocal lattice must be three-dimensional")
        if any(type(value) is not float or not math.isfinite(value) for value in row):
            raise QeBandsDataError("QEXSD reciprocal lattice must be finite")
        rows.append(row)
    return (rows[0], rows[1], rows[2])


def _row_vector_matrix_product(
    point: _Vector3,
    matrix: tuple[_Vector3, ...],
) -> _Vector3:
    return (
        point[0] * matrix[0][0] + point[1] * matrix[1][0] + point[2] * matrix[2][0],
        point[0] * matrix[0][1] + point[1] * matrix[1][1] + point[2] * matrix[2][1],
        point[0] * matrix[0][2] + point[1] * matrix[1][2] + point[2] * matrix[2][2],
    )


def _expected_crystal_samples(
    projection: QeBandsPathProjection,
) -> tuple[_Vector3, ...]:
    samples: list[_Vector3] = []
    count = projection.points_per_segment
    for branch in projection.path.branches:
        for start, stop in zip(branch.vertices, branch.vertices[1:], strict=False):
            samples.extend(
                _interpolate(start.coordinates, stop.coordinates, step / count)
                for step in range(count)
            )
        samples.append(branch.vertices[-1].coordinates)
    return tuple(samples)


def _interpolate(start: _Vector3, stop: _Vector3, fraction: float) -> _Vector3:
    return (
        start[0] + (stop[0] - start[0]) * fraction,
        start[1] + (stop[1] - start[1]) * fraction,
        start[2] + (stop[2] - start[2]) * fraction,
    )


def _branchwise_path_coordinate(
    k_points: tuple[_Vector3, ...],
    projection: QeBandsPathProjection,
    scale: float,
) -> tuple[float, ...]:
    coordinate = [0.0] * len(k_points)
    for branch in projection.diagram_branches():
        if branch.start_index > 0:
            coordinate[branch.start_index] = coordinate[branch.start_index - 1]
        for index in range(branch.start_index + 1, branch.stop_index):
            coordinate[index] = coordinate[index - 1] + scale * _distance(
                k_points[index], k_points[index - 1]
            )
    return tuple(coordinate)


def _distance(left: _Vector3, right: _Vector3) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))
