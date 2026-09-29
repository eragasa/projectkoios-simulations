"""Compose VASP line-mode spectra into calculator-neutral band-diagram data."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from projectkoios.integrations.vasp.data import VaspDataSources
from projectkoios.simulations.dft.pw.bands import (
    BandDiagramBranch,
    BandDiagramData,
    BandPath,
    PwDftBandsSimulation,
)


@dataclass(frozen=True, slots=True)
class VaspBandConsistency:
    """Report mechanical agreement among VASP line-mode data sources."""

    program_version_matches: bool
    atom_count_matches: bool
    kpoint_count_matches: bool
    configured_unit_cell_matches: bool
    path_coordinates_match: bool


@dataclass(frozen=True, slots=True)
class VaspBandData:
    """Facade common VASP sources and normalized band-diagram data."""

    sources: VaspDataSources
    diagram: BandDiagramData
    consistency: VaspBandConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if type(self.diagram) is not BandDiagramData:
            raise TypeError("diagram must be BandDiagramData")
        if type(self.consistency) is not VaspBandConsistency:
            raise TypeError("consistency must be VaspBandConsistency")


@dataclass(frozen=True, slots=True)
class VaspBandDataExtractor:
    """Extract line-mode bands while retaining native VASP source provenance."""

    coordinate_tolerance: float = 1.0e-7
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
        sources: VaspDataSources,
        *,
        calculation: PwDftBandsSimulation,
        points_per_segment: int,
        expected_band_count: int,
        reference_energy_ev: float | None = None,
        reference_label: str | None = None,
    ) -> VaspBandData:
        """Correlate XML k-points and eigenvalues with one declared line path."""
        if type(sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if type(calculation) is not PwDftBandsSimulation:
            raise TypeError("calculation must be a PwDftBandsSimulation")
        path = calculation.path
        if type(points_per_segment) is not int or points_per_segment < 2:
            raise ValueError("points_per_segment must be at least two")
        if type(expected_band_count) is not int or expected_band_count <= 0:
            raise ValueError("expected_band_count must be positive")
        run_xml = sources.vasprun
        if run_xml is None:
            raise ValueError("band extraction requires vasprun.xml")
        if run_xml.eigenvalues_ev is None or run_xml.occupations is None:
            raise ValueError("vasprun.xml lacks eigenvalues or occupations")
        if len(run_xml.eigenvalues_ev[0][0]) != expected_band_count:
            raise ValueError("vasprun.xml band count disagrees with the declaration")
        configured_cell_matches = _configured_unit_cell_matches(
            calculation,
            run_xml.atom_labels,
            run_xml.initial_structure.lattice_vectors_angstrom,
            run_xml.initial_structure.positions_fractional,
            tolerance=self.cell_tolerance,
        )
        if not configured_cell_matches:
            raise ValueError(
                "vasprun.xml unit cell disagrees with the configured simulation"
            )

        expected_kpoints, branches = _expected_vasp_samples(
            path,
            points_per_segment,
        )
        if len(run_xml.k_points) != len(expected_kpoints):
            raise ValueError("vasprun.xml k-point count disagrees with the band path")
        path_matches = all(
            all(
                abs(observed_value - expected_value) <= self.coordinate_tolerance
                for observed_value, expected_value in zip(
                    observed, expected, strict=True
                )
            )
            for observed, expected in zip(
                run_xml.k_points,
                expected_kpoints,
                strict=True,
            )
        )
        if not path_matches:
            raise ValueError(
                "vasprun.xml k-points disagree with the declared band path"
            )
        path_coordinate = _path_coordinate(
            run_xml.k_points,
            branches,
            calculation.simulation.lattice_vectors_angstrom,
        )
        diagram = BandDiagramData(
            calculation=calculation,
            sampled_kpoints_reciprocal_fractional=run_xml.k_points,
            path_coordinate=path_coordinate,
            path_coordinate_label="reciprocal distance (1/angstrom)",
            branches=branches,
            energies_ev=run_xml.eigenvalues_ev,
            occupations=run_xml.occupations,
            reference_energy_ev=reference_energy_ev,
            reference_label=reference_label,
        )
        return VaspBandData(
            sources=sources,
            diagram=diagram,
            consistency=VaspBandConsistency(
                program_version_matches=(
                    sources.outcar.program_version == run_xml.program_version
                ),
                atom_count_matches=(
                    sources.outcar.atom_count == len(run_xml.atom_labels)
                ),
                kpoint_count_matches=(
                    sources.outcar.irreducible_kpoint_count == len(run_xml.k_points)
                ),
                configured_unit_cell_matches=configured_cell_matches,
                path_coordinates_match=path_matches,
            ),
        )


def _configured_unit_cell_matches(
    calculation: PwDftBandsSimulation,
    observed_symbols: tuple[str, ...],
    observed_lattice: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
    observed_positions: tuple[tuple[float, float, float], ...],
    *,
    tolerance: float,
) -> bool:
    expected_sites = calculation.simulation.fractional_sites
    if observed_symbols != tuple(symbol for symbol, _ in expected_sites):
        return False
    expected_values = (
        *calculation.simulation.lattice_vectors_angstrom,
        *(position for _, position in expected_sites),
    )
    observed_values = (*observed_lattice, *observed_positions)
    return len(expected_values) == len(observed_values) and all(
        all(
            abs(expected_component - observed_component) <= tolerance
            for expected_component, observed_component in zip(
                expected,
                observed,
                strict=True,
            )
        )
        for expected, observed in zip(
            expected_values,
            observed_values,
            strict=True,
        )
    )


def _expected_vasp_samples(
    path: BandPath,
    points_per_segment: int,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[BandDiagramBranch, ...],
]:
    samples: list[tuple[float, float, float]] = []
    branches: list[BandDiagramBranch] = []
    for branch in path.branches:
        start_index = len(samples)
        tick_indices = [start_index]
        tick_labels = [branch.vertices[0].label]
        for first, second in zip(
            branch.vertices,
            branch.vertices[1:],
            strict=False,
        ):
            for index in range(points_per_segment):
                fraction = index / (points_per_segment - 1)
                samples.append(
                    (
                        first.coordinates[0]
                        + fraction * (second.coordinates[0] - first.coordinates[0]),
                        first.coordinates[1]
                        + fraction * (second.coordinates[1] - first.coordinates[1]),
                        first.coordinates[2]
                        + fraction * (second.coordinates[2] - first.coordinates[2]),
                    )
                )
            tick_indices.append(len(samples) - 1)
            tick_labels.append(second.label)
        branches.append(
            BandDiagramBranch(
                start_index=start_index,
                stop_index=len(samples),
                tick_indices=tuple(tick_indices),
                tick_labels=tuple(tick_labels),
            )
        )
    return tuple(samples), tuple(branches)


def _path_coordinate(
    kpoints: tuple[tuple[float, float, float], ...],
    branches: tuple[BandDiagramBranch, ...],
    lattice_vectors_angstrom: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
) -> tuple[float, ...]:
    direct = np.asarray(lattice_vectors_angstrom, dtype=np.float64)
    reciprocal = 2.0 * np.pi * np.linalg.inv(direct).T
    coordinates = [0.0] * len(kpoints)
    offset = 0.0
    for branch in branches:
        coordinates[branch.start_index] = offset
        previous = np.asarray(kpoints[branch.start_index], dtype=np.float64)
        for index in range(branch.start_index + 1, branch.stop_index):
            current = np.asarray(kpoints[index], dtype=np.float64)
            offset += float(np.linalg.norm((current - previous) @ reciprocal))
            coordinates[index] = offset
            previous = current
    return tuple(coordinates)
