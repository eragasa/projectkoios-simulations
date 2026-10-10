"""Correlation records for normalized plane-wave DFT relaxation results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from projectkoios.physkit.periodic.unit_cell import UnitCellJsonCodec
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.observation import (
    PwDftRelaxationObservation,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.structure import StructureResolution


@dataclass(frozen=True, slots=True)
class PwDftRelaxationResult:
    """Correlate a request, prepared inputs, and terminal observation."""

    observation_representation: ClassVar[str] = (
        "projectkoios.pw-dft-relaxation-observation+json"
    )
    observation_schema_version: ClassVar[int] = 1

    evaluation_id: str
    task_id: str
    request: PwDftRelaxationRequest
    starting_structure: StructureResolution
    calculator_input: CalculatorInputRecord
    observation: PwDftRelaxationObservation

    def __post_init__(self) -> None:
        if type(self.request) is not PwDftRelaxationRequest:
            raise TypeError("request must be PwDftRelaxationRequest")
        if self.evaluation_id != self.request.evaluation_id:
            raise ValueError("evaluation_id must match the relaxation request")
        if type(self.task_id) is not str or not self.task_id.strip():
            raise ValueError("task_id must be nonempty and stripped")
        if type(self.starting_structure) is not StructureResolution:
            raise TypeError("starting_structure must be StructureResolution")
        if (
            self.starting_structure.record
            != self.request.specification.simulation.structure
        ):
            raise ValueError(
                "starting_structure must match the specification dependency"
            )
        if type(self.calculator_input) is not CalculatorInputRecord:
            raise TypeError("calculator_input must be CalculatorInputRecord")
        # Local import avoids coupling the relaxation package initializer back
        # into the specification codec while both modules are being initialized.
        from projectkoios.simulations.library.codec import simulation_source_reference

        # This closes the publication-correlation gap: evidence cannot be paired
        # with prepared inputs derived from a different exact specification.
        if self.calculator_input.source != simulation_source_reference(
            self.request.specification
        ):
            raise ValueError(
                "calculator input source must identify the exact request specification"
            )
        if type(self.observation) is not PwDftRelaxationObservation:
            raise TypeError("observation must be PwDftRelaxationObservation")
        if any(
            value.integration_id != self.calculator_input.integration_id
            for value in self.observation.native_artifacts
        ):
            raise ValueError(
                "relaxation artifacts and calculator input integration must match"
            )
        starting = self.starting_structure.unit_cell
        final = self.observation.final_unit_cell
        if len(starting.atomic_basis.atoms) != len(final.atomic_basis.atoms):
            raise ValueError("relaxation must preserve atom count")
        if tuple(atom.symbol for atom in starting.atomic_basis.atoms) != tuple(
            atom.symbol for atom in final.atomic_basis.atoms
        ):
            raise ValueError("relaxation must preserve source-ordered atom symbols")
        if self.request.specification.scope is PwDftRelaxationScope.ATOMIC_POSITIONS:
            if self.observation.cell_converged is not None:
                raise ValueError("fixed-cell relaxation has no cell convergence state")
            if not np.array_equal(starting.A.magnitude, final.A.magnitude):
                raise ValueError("fixed-cell relaxation must preserve lattice vectors")
            if starting.lattice_parameter != final.lattice_parameter:
                raise ValueError(
                    "fixed-cell relaxation must preserve lattice parameter"
                )
        elif self.observation.cell_converged is None:
            raise ValueError(
                "variable-cell relaxation must represent cell convergence state"
            )

    @property
    def canonical_observation_bytes(self) -> bytes:
        """Return versioned canonical JSON for the normalized observation."""
        observation = self.observation
        final_unit_cell = json.loads(
            UnitCellJsonCodec().dumps(
                observation.final_unit_cell,
                structure_id="PwDftRelaxationObservation.FinalUnitCell",
            )
        )
        payload = {
            "cell_converged": observation.cell_converged,
            "completed": observation.completed,
            "evaluation_id": self.evaluation_id,
            "final_total_energy_ev": observation.final_total_energy_ev,
            "final_unit_cell": final_unit_cell,
            "ionic_converged": observation.ionic_converged,
            "ionic_step_count": observation.ionic_step_count,
            "maximum_force_ev_per_angstrom": (
                observation.maximum_force_ev_per_angstrom
            ),
            "native_artifacts": [
                {
                    "artifact_id": artifact.artifact_id,
                    "byte_size": artifact.byte_size,
                    "integration_id": artifact.integration_id.value,
                    "sha256": artifact.sha256,
                }
                for artifact in observation.native_artifacts
            ],
            "pressure_kbar": observation.pressure_kbar,
            "program_version": observation.program_version,
            "representation": self.observation_representation,
            "schema_version": self.observation_schema_version,
            "scope": self.request.specification.scope.value,
            "task_id": self.task_id,
            "total_magnetization_electrons": (
                observation.total_magnetization_electrons
            ),
        }
        return (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    @property
    def observation_byte_size(self) -> int:
        """Return the canonical normalized-observation byte size."""
        return len(self.canonical_observation_bytes)

    @property
    def observation_sha256(self) -> str:
        """Return the canonical normalized-observation SHA-256."""
        return hashlib.sha256(self.canonical_observation_bytes).hexdigest()
