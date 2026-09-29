"""Compose complete structured VASP ionic-relaxation trajectory data."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.integrations.vasp.data import VaspDataSources
from projectkoios.integrations.vasp.run_xml import (
    VaspIonicStep,
    VaspStructure,
)


@dataclass(frozen=True, slots=True)
class VaspRelaxConsistency:
    """Report mechanical agreement among VASP relaxation sources."""

    program_version_matches: bool
    atom_count_matches: bool
    kpoint_count_matches: bool
    final_energy_matches: bool
    final_xml_structures_match: bool


@dataclass(frozen=True, slots=True)
class VaspRelaxData:
    """Facade common VASP sources and the complete XML ionic trajectory."""

    sources: VaspDataSources
    trajectory: tuple[VaspIonicStep, ...]
    final_structure: VaspStructure
    consistency: VaspRelaxConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if self.sources.vasprun is None:
            raise ValueError("relaxation data requires parsed vasprun.xml")
        if type(self.trajectory) is not tuple or not self.trajectory:
            raise ValueError("trajectory must be a nonempty tuple")
        if any(type(step) is not VaspIonicStep for step in self.trajectory):
            raise TypeError("trajectory must contain VaspIonicStep values")
        if type(self.final_structure) is not VaspStructure:
            raise TypeError("final_structure must be VaspStructure")
        if type(self.consistency) is not VaspRelaxConsistency:
            raise TypeError("consistency must be VaspRelaxConsistency")


@dataclass(frozen=True, slots=True)
class VaspRelaxDataExtractor:
    """Extract a complete ionic trajectory from common VASP sources."""

    def extract(self, sources: VaspDataSources) -> VaspRelaxData:
        if type(sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        run_xml = sources.vasprun
        if run_xml is None:
            raise ValueError("relaxation extraction requires vasprun.xml")
        if run_xml.incar_nsw <= 0 or run_xml.incar_ibrion == -1:
            raise ValueError("vasprun.xml does not describe ionic relaxation")
        final_step = run_xml.ionic_steps[-1]
        final_xml_structures_match = final_step.structure == run_xml.final_structure
        consistency = VaspRelaxConsistency(
            program_version_matches=(
                sources.outcar.program_version == run_xml.program_version
            ),
            atom_count_matches=(sources.outcar.atom_count == len(run_xml.atom_labels)),
            kpoint_count_matches=(
                sources.outcar.irreducible_kpoint_count == len(run_xml.k_points)
            ),
            final_energy_matches=math.isclose(
                sources.outcar.total_energy_toten_ev,
                final_step.free_energy_ev,
                rel_tol=0.0,
                abs_tol=1.0e-8,
            ),
            final_xml_structures_match=final_xml_structures_match,
        )
        return VaspRelaxData(
            sources=sources,
            trajectory=run_xml.ionic_steps,
            final_structure=run_xml.final_structure,
            consistency=consistency,
        )
