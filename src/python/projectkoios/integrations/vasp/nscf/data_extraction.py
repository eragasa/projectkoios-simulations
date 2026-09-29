"""Compose structured VASP NSCF data from common retained sources."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.integrations.vasp.data import VaspDataSources
from projectkoios.integrations.vasp.run_xml import VaspSpectrum


@dataclass(frozen=True, slots=True)
class VaspNscfSpectralData:
    """Retain native VASP k-point and band observations."""

    k_points: tuple[tuple[float, float, float], ...]
    k_point_weights: tuple[float, ...]
    eigenvalues_ev: VaspSpectrum
    occupations: VaspSpectrum
    fermi_energy_ev: float | None

    def __post_init__(self) -> None:
        if type(self.k_points) is not tuple or not self.k_points:
            raise ValueError("k_points must be a nonempty tuple")
        if type(self.k_point_weights) is not tuple or len(self.k_point_weights) != len(
            self.k_points
        ):
            raise ValueError("k-point weights must match k-points")
        if not self.eigenvalues_ev or len(self.eigenvalues_ev) != len(self.occupations):
            raise ValueError("eigenvalue and occupation spin counts must agree")
        for eigen_spin, occupation_spin in zip(
            self.eigenvalues_ev,
            self.occupations,
            strict=True,
        ):
            if len(eigen_spin) != len(self.k_points) or len(occupation_spin) != len(
                self.k_points
            ):
                raise ValueError("spectral k-point counts must agree")
            for eigen_row, occupation_row in zip(
                eigen_spin,
                occupation_spin,
                strict=True,
            ):
                if not eigen_row or len(eigen_row) != len(occupation_row):
                    raise ValueError("band and occupation row sizes must agree")
        if self.fermi_energy_ev is not None and (
            type(self.fermi_energy_ev) is not float
            or not math.isfinite(self.fermi_energy_ev)
        ):
            raise ValueError("fermi_energy_ev must be finite or None")

    @property
    def spin_count(self) -> int:
        return len(self.eigenvalues_ev)

    @property
    def kpoint_count(self) -> int:
        return len(self.k_points)

    @property
    def band_count(self) -> int:
        return len(self.eigenvalues_ev[0][0])


@dataclass(frozen=True, slots=True)
class VaspNscfConsistency:
    """Report mechanical NSCF source agreement."""

    program_version_matches: bool
    atom_count_matches: bool
    kpoint_count_matches: bool
    declared_band_count_matches: bool
    declared_kpoint_count_matches: bool


@dataclass(frozen=True, slots=True)
class VaspNscfData:
    """Facade common VASP sources and native NSCF spectral data."""

    sources: VaspDataSources
    spectral: VaspNscfSpectralData
    consistency: VaspNscfConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if self.sources.vasprun is None:
            raise ValueError("NSCF data requires parsed vasprun.xml")
        if type(self.spectral) is not VaspNscfSpectralData:
            raise TypeError("spectral must be VaspNscfSpectralData")
        if type(self.consistency) is not VaspNscfConsistency:
            raise TypeError("consistency must be VaspNscfConsistency")


@dataclass(frozen=True, slots=True)
class VaspNscfDataExtractor:
    """Extract an NSCF facade from common VASP sources."""

    def extract(
        self,
        sources: VaspDataSources,
        *,
        expected_band_count: int,
        expected_kpoint_count: int,
    ) -> VaspNscfData:
        if type(sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if type(expected_band_count) is not int or expected_band_count <= 0:
            raise ValueError("expected_band_count must be positive")
        if type(expected_kpoint_count) is not int or expected_kpoint_count <= 0:
            raise ValueError("expected_kpoint_count must be positive")
        run_xml = sources.vasprun
        if run_xml is None:
            raise ValueError("NSCF extraction requires vasprun.xml")
        if run_xml.eigenvalues_ev is None or run_xml.occupations is None:
            raise ValueError("vasprun.xml lacks eigenvalues or occupations")
        spectral = VaspNscfSpectralData(
            k_points=run_xml.k_points,
            k_point_weights=run_xml.k_point_weights,
            eigenvalues_ev=run_xml.eigenvalues_ev,
            occupations=run_xml.occupations,
            fermi_energy_ev=run_xml.fermi_energy_ev,
        )
        if spectral.band_count != expected_band_count:
            raise ValueError("vasprun.xml band count disagrees with NSCF declaration")
        if spectral.kpoint_count != expected_kpoint_count:
            raise ValueError(
                "vasprun.xml k-point count disagrees with NSCF declaration"
            )
        consistency = VaspNscfConsistency(
            program_version_matches=(
                sources.outcar.program_version == run_xml.program_version
            ),
            atom_count_matches=(sources.outcar.atom_count == len(run_xml.atom_labels)),
            kpoint_count_matches=(
                sources.outcar.irreducible_kpoint_count == spectral.kpoint_count
            ),
            declared_band_count_matches=True,
            declared_kpoint_count_matches=True,
        )
        return VaspNscfData(
            sources=sources,
            spectral=spectral,
            consistency=consistency,
        )
