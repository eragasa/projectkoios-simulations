"""Bind qualified plane-wave DFT final-SCF observations to defect energies."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.defects import (
    DefectContentReference,
    DefectEnergyEvidence,
    DefectEnergyRole,
)
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObservation
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation


@dataclass(frozen=True, slots=True)
class PwDftDefectEnergyBinding:
    """Qualify one final SCF as method-neutral defect-energy evidence."""

    energy_id: str
    role: DefectEnergyRole
    simulation_id: str
    simulation: PwDftSimulation
    calculator_input: CalculatorInputRecord
    observation: PwDftScfObservation
    structure: DefectContentReference
    calculation: DefectContentReference
    model_id: str
    qualification_id: str

    def __post_init__(self) -> None:
        for label, value in (
            ("energy_id", self.energy_id),
            ("simulation_id", self.simulation_id),
            ("model_id", self.model_id),
            ("qualification_id", self.qualification_id),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.role) is not DefectEnergyRole:
            raise TypeError("role must be DefectEnergyRole")
        if type(self.simulation) is not PwDftSimulation:
            raise TypeError("simulation must be PwDftSimulation")
        if not self.simulation.pseudopotentials:
            raise ValueError(
                "DFT defect-energy binding requires exact pseudopotentials"
            )
        if type(self.calculator_input) is not CalculatorInputRecord:
            raise TypeError("calculator_input must be CalculatorInputRecord")
        if self.calculator_input.source.simulation_id != self.simulation_id:
            raise ValueError("calculator input must reference the bound simulation")
        if type(self.observation) is not PwDftScfObservation:
            raise TypeError("observation must be PwDftScfObservation")
        if not self.observation.completed or not self.observation.converged:
            raise ValueError("defect-energy binding requires a completed converged SCF")
        if self.observation.atom_count != len(
            self.simulation.unit_cell.atomic_basis.atoms
        ):
            raise ValueError("observed atom count must match the simulation")
        if (
            self.observation.native_artifact.integration_id
            != self.calculator_input.integration_id
        ):
            raise ValueError(
                "observation and calculator input integration identities must match"
            )
        mapping_by_field = {
            value.neutral_field: value for value in self.calculator_input.mappings
        }
        charge_mapping = mapping_by_field.get("delta_n_electrons")
        if charge_mapping is None:
            raise ValueError("calculator input must record the charge mapping")
        if charge_mapping.neutral_value != str(
            self.simulation.charge.delta_n_electrons
        ):
            raise ValueError(
                "calculator input charge mapping disagrees with simulation"
            )
        spin_mapping = mapping_by_field.get("spin")
        if spin_mapping is None:
            raise ValueError("calculator input must record the spin mapping")
        if spin_mapping.neutral_value.split(";", maxsplit=1)[0] != (
            self.simulation.spin.mode.value
        ):
            raise ValueError("calculator input spin mapping disagrees with simulation")
        if type(self.structure) is not DefectContentReference:
            raise TypeError("structure must be DefectContentReference")
        if type(self.calculation) is not DefectContentReference:
            raise TypeError("calculation must be DefectContentReference")

    def to_energy_evidence(self) -> DefectEnergyEvidence:
        """Return method-neutral evidence after DFT-specific qualification."""
        return DefectEnergyEvidence(
            energy_id=self.energy_id,
            role=self.role,
            energy_ev=float(self.observation.total_energy_ev),
            atom_count=self.observation.atom_count,
            structure=self.structure,
            calculation=self.calculation,
            method_id="plane-wave-dft",
            model_id=self.model_id,
            qualification_id=self.qualification_id,
            final_single_point=True,
            completed=self.observation.completed,
            converged=self.observation.converged,
        )
