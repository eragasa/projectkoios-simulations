"""Method-neutral neutral-defect formation-energy arithmetic."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.simulations.defects.chemical_potential import (
    ElementChemicalPotential,
)
from projectkoios.simulations.defects.compatibility import DefectEnergyCompatibility
from projectkoios.simulations.defects.energy import (
    DefectEnergyEvidence,
    DefectEnergyRole,
)


@dataclass(frozen=True, slots=True)
class ElementCountDelta:
    """Record added-positive or removed-negative atom count for one element."""

    symbol: str
    count: int

    def __post_init__(self) -> None:
        if (
            type(self.symbol) is not str
            or not self.symbol
            or not self.symbol[0].isupper()
            or (bool(self.symbol[1:]) and not self.symbol[1:].islower())
            or len(self.symbol) > 3
        ):
            raise ValueError("symbol must be a chemical element symbol")
        if type(self.count) is not int or self.count == 0:
            raise ValueError("count must be a nonzero integer")


@dataclass(frozen=True, slots=True)
class NeutralDefectFormationEnergyRequest:
    """Declare exact neutral-defect formation-energy inputs."""

    defect: DefectEnergyEvidence
    pristine: DefectEnergyEvidence
    atom_count_deltas: tuple[ElementCountDelta, ...]
    chemical_potentials: tuple[ElementChemicalPotential, ...]
    compatibility: DefectEnergyCompatibility
    charge_state: int = 0

    def __post_init__(self) -> None:
        if type(self.defect) is not DefectEnergyEvidence:
            raise TypeError("defect must be DefectEnergyEvidence")
        if self.defect.role not in {
            DefectEnergyRole.DEFECT,
            DefectEnergyRole.IDEAL_DEFECT,
            DefectEnergyRole.ION_RELAXED_DEFECT,
            DefectEnergyRole.FULLY_RELAXED_DEFECT,
        }:
            raise ValueError("defect evidence must have a defect energy role")
        if type(self.pristine) is not DefectEnergyEvidence:
            raise TypeError("pristine must be DefectEnergyEvidence")
        if self.pristine.role is not DefectEnergyRole.PRISTINE:
            raise ValueError("pristine evidence must have the pristine role")
        if type(self.charge_state) is not int or self.charge_state != 0:
            raise ValueError(
                "neutral formation-energy arithmetic requires charge_state zero"
            )
        if type(self.atom_count_deltas) is not tuple or not self.atom_count_deltas:
            raise ValueError("atom_count_deltas must be a nonempty tuple")
        if any(
            type(value) is not ElementCountDelta for value in self.atom_count_deltas
        ):
            raise TypeError("atom_count_deltas must contain ElementCountDelta values")
        if len({value.symbol for value in self.atom_count_deltas}) != len(
            self.atom_count_deltas
        ):
            raise ValueError("atom_count_deltas must contain unique element symbols")
        if type(self.chemical_potentials) is not tuple or not self.chemical_potentials:
            raise ValueError("chemical_potentials must be a nonempty tuple")
        if any(
            type(value) is not ElementChemicalPotential
            for value in self.chemical_potentials
        ):
            raise TypeError(
                "chemical_potentials must contain ElementChemicalPotential values"
            )
        if len({value.symbol for value in self.chemical_potentials}) != len(
            self.chemical_potentials
        ):
            raise ValueError("chemical_potentials must contain unique element symbols")
        if {value.symbol for value in self.atom_count_deltas} != {
            value.symbol for value in self.chemical_potentials
        }:
            raise ValueError(
                "chemical potentials must exactly cover atom-count delta elements"
            )
        if type(self.compatibility) is not DefectEnergyCompatibility:
            raise TypeError("compatibility must be DefectEnergyCompatibility")


@dataclass(frozen=True, slots=True)
class NeutralDefectFormationEnergyResult:
    """Retain the terms and result of neutral formation-energy arithmetic."""

    defect_energy_ev: float
    pristine_energy_ev: float
    reservoir_energy_ev: float
    formation_energy_ev: float
    compatibility_qualification_id: str

    def __post_init__(self) -> None:
        if any(
            type(value) is not float or not math.isfinite(value)
            for value in (
                self.defect_energy_ev,
                self.pristine_energy_ev,
                self.reservoir_energy_ev,
                self.formation_energy_ev,
            )
        ):
            raise ValueError("formation-energy terms must be finite floats")
        expected = (
            self.defect_energy_ev - self.pristine_energy_ev - self.reservoir_energy_ev
        )
        if not math.isclose(
            self.formation_energy_ev,
            expected,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("formation_energy_ev must equal the retained terms")
        if (
            type(self.compatibility_qualification_id) is not str
            or not self.compatibility_qualification_id
        ):
            raise ValueError("compatibility_qualification_id must be nonempty")


@dataclass(frozen=True, slots=True)
class NeutralDefectFormationEnergyAction:
    """Evaluate neutral formation energy after exact compatibility checks."""

    def evaluate(
        self, request: NeutralDefectFormationEnergyRequest
    ) -> NeutralDefectFormationEnergyResult:
        """Return method-neutral formation-energy arithmetic."""
        if type(request) is not NeutralDefectFormationEnergyRequest:
            raise TypeError("request must be NeutralDefectFormationEnergyRequest")
        evidence = (
            request.defect,
            request.pristine,
            *(value.evidence for value in request.chemical_potentials),
        )
        request.compatibility.require(evidence)
        chemical_potential_by_symbol = {
            value.symbol: value.energy_ev_per_atom
            for value in request.chemical_potentials
        }
        reservoir_energy_ev = float(
            sum(
                value.count * chemical_potential_by_symbol[value.symbol]
                for value in request.atom_count_deltas
            )
        )
        return NeutralDefectFormationEnergyResult(
            defect_energy_ev=request.defect.energy_ev,
            pristine_energy_ev=request.pristine.energy_ev,
            reservoir_energy_ev=reservoir_energy_ev,
            formation_energy_ev=(
                request.defect.energy_ev
                - request.pristine.energy_ev
                - reservoir_energy_ev
            ),
            compatibility_qualification_id=request.compatibility.qualification_id,
        )
