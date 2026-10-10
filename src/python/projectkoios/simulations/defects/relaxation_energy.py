"""Method-neutral defect relaxation-energy arithmetic."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.simulations.defects.compatibility import DefectEnergyCompatibility
from projectkoios.simulations.defects.energy import (
    DefectEnergyEvidence,
    DefectEnergyRole,
)


@dataclass(frozen=True, slots=True)
class DefectRelaxationEnergyRequest:
    """Declare compatible ideal, ion-only, and fully relaxed energies."""

    ideal: DefectEnergyEvidence
    ion_only: DefectEnergyEvidence
    fully_relaxed: DefectEnergyEvidence
    compatibility: DefectEnergyCompatibility
    external_pressure_gpa: float = 0.0

    def __post_init__(self) -> None:
        for label, evidence, role in (
            ("ideal", self.ideal, DefectEnergyRole.IDEAL_DEFECT),
            ("ion_only", self.ion_only, DefectEnergyRole.ION_RELAXED_DEFECT),
            (
                "fully_relaxed",
                self.fully_relaxed,
                DefectEnergyRole.FULLY_RELAXED_DEFECT,
            ),
        ):
            if type(evidence) is not DefectEnergyEvidence:
                raise TypeError(f"{label} must be DefectEnergyEvidence")
            if evidence.role is not role:
                raise ValueError(f"{label} evidence has the wrong energy role")
        if type(self.compatibility) is not DefectEnergyCompatibility:
            raise TypeError("compatibility must be DefectEnergyCompatibility")
        if type(self.external_pressure_gpa) is not float or not math.isfinite(
            self.external_pressure_gpa
        ):
            raise ValueError("external_pressure_gpa must be a finite float")
        if self.external_pressure_gpa != 0.0:
            raise ValueError(
                "implemented relaxation-energy arithmetic is qualified only at "
                "zero pressure"
            )


@dataclass(frozen=True, slots=True)
class DefectRelaxationEnergyResult:
    """Retain ionic, cell-constraint, and total relaxation energies."""

    ideal_energy_ev: float
    ion_only_energy_ev: float
    fully_relaxed_energy_ev: float
    ionic_relaxation_energy_ev: float
    cell_constraint_release_energy_ev: float
    total_relaxation_energy_ev: float
    external_pressure_gpa: float
    compatibility_qualification_id: str

    def __post_init__(self) -> None:
        values = (
            self.ideal_energy_ev,
            self.ion_only_energy_ev,
            self.fully_relaxed_energy_ev,
            self.ionic_relaxation_energy_ev,
            self.cell_constraint_release_energy_ev,
            self.total_relaxation_energy_ev,
            self.external_pressure_gpa,
        )
        if any(
            type(value) is not float or not math.isfinite(value) for value in values
        ):
            raise ValueError("relaxation-energy values must be finite floats")
        expected_ionic = self.ideal_energy_ev - self.ion_only_energy_ev
        expected_cell = self.ion_only_energy_ev - self.fully_relaxed_energy_ev
        expected_total = self.ideal_energy_ev - self.fully_relaxed_energy_ev
        for observed, expected in (
            (self.ionic_relaxation_energy_ev, expected_ionic),
            (self.cell_constraint_release_energy_ev, expected_cell),
            (self.total_relaxation_energy_ev, expected_total),
        ):
            if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError("relaxation-energy result terms are inconsistent")
        if self.external_pressure_gpa != 0.0:
            raise ValueError(
                "relaxation-energy result is qualified only at zero pressure"
            )
        if (
            type(self.compatibility_qualification_id) is not str
            or not self.compatibility_qualification_id
        ):
            raise ValueError("compatibility_qualification_id must be nonempty")


@dataclass(frozen=True, slots=True)
class DefectRelaxationEnergyAction:
    """Evaluate compatible zero-pressure defect relaxation energies."""

    def evaluate(
        self, request: DefectRelaxationEnergyRequest
    ) -> DefectRelaxationEnergyResult:
        """Return retained energy differences after compatibility checks."""
        if type(request) is not DefectRelaxationEnergyRequest:
            raise TypeError("request must be DefectRelaxationEnergyRequest")
        request.compatibility.require(
            (request.ideal, request.ion_only, request.fully_relaxed)
        )
        return DefectRelaxationEnergyResult(
            ideal_energy_ev=request.ideal.energy_ev,
            ion_only_energy_ev=request.ion_only.energy_ev,
            fully_relaxed_energy_ev=request.fully_relaxed.energy_ev,
            ionic_relaxation_energy_ev=(
                request.ideal.energy_ev - request.ion_only.energy_ev
            ),
            cell_constraint_release_energy_ev=(
                request.ion_only.energy_ev - request.fully_relaxed.energy_ev
            ),
            total_relaxation_energy_ev=(
                request.ideal.energy_ev - request.fully_relaxed.energy_ev
            ),
            external_pressure_gpa=request.external_pressure_gpa,
            compatibility_qualification_id=request.compatibility.qualification_id,
        )
