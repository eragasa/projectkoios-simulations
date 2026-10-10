"""Method-neutral chemical-potential records for defect formation energies."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.simulations.defects.energy import (
    DefectEnergyEvidence,
    DefectEnergyRole,
)


@dataclass(frozen=True, slots=True)
class ElementChemicalPotential:
    """Bind one elemental chemical potential to exact compatible evidence."""

    symbol: str
    energy_ev_per_atom: float
    evidence: DefectEnergyEvidence

    def __post_init__(self) -> None:
        if (
            type(self.symbol) is not str
            or not self.symbol
            or not self.symbol[0].isupper()
            or (bool(self.symbol[1:]) and not self.symbol[1:].islower())
            or len(self.symbol) > 3
        ):
            raise ValueError("symbol must be a chemical element symbol")
        if type(self.energy_ev_per_atom) is not float or not math.isfinite(
            self.energy_ev_per_atom
        ):
            raise ValueError("energy_ev_per_atom must be a finite float")
        if type(self.evidence) is not DefectEnergyEvidence:
            raise TypeError("evidence must be DefectEnergyEvidence")
        if self.evidence.role is not DefectEnergyRole.ELEMENTAL_REFERENCE:
            raise ValueError("chemical-potential evidence must be elemental-reference")
        observed = self.evidence.energy_ev / self.evidence.atom_count
        if not math.isclose(
            observed, self.energy_ev_per_atom, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError(
                "energy_ev_per_atom must equal evidence energy divided by atom count"
            )
