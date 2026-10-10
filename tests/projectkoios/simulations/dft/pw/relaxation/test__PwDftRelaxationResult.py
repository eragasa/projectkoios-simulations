from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from projectkoios.physkit.mechanics.stress import (
    StressSignConvention,
    StressTensor,
)
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    MatrixQuantity,
    PhysicalUnit,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputRecord,
)
from projectkoios.simulations.dft.pw.relaxation import (
    PwDftRelaxationNativeArtifact,
    PwDftRelaxationObservation,
    PwDftRelaxationResult,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.library import simulation_source_reference
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution


def _input_record(
    integration_id: CalculatorIntegrationId,
    request: PwDftRelaxationRequest,
) -> CalculatorInputRecord:
    content = b"relaxation input\n"
    return CalculatorInputRecord(
        input_id="silicon-relaxation-input",
        schema_version=1,
        source=simulation_source_reference(request.specification),
        integration_id=integration_id,
        calculator_name="test calculator",
        calculator_version_constraint="1",
        representation="test-input",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename="input.txt",
                media_type="text/plain",
                content=content,
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
        ),
        external_requirements=(),
        mappings=(),
        preparation_operation="test.render",
        preparation_version="1",
    )


def _final_cell(starting: UnitCell, lattice_scale: float = 1.0) -> UnitCell:
    first, second = starting.atomic_basis.atoms
    return UnitCell(
        direct_lattice=starting.direct_lattice,
        lattice_parameter=type(starting.lattice_parameter)(
            starting.lattice_parameter.magnitude * lattice_scale,
            starting.lattice_parameter.unit,
        ),
        atomic_basis=AtomicBasis(
            atoms=(
                Atom(
                    first.symbol,
                    VectorQuantity(np.array((0.01, 0.0, 0.0)), Unitless()),
                ),
                Atom(
                    second.symbol,
                    VectorQuantity(np.array((0.26, 0.25, 0.25)), Unitless()),
                ),
            )
        ),
    )


def _observation(
    final_cell: UnitCell,
    integration_id: CalculatorIntegrationId,
    cell_converged: bool | None,
    stress_tensor: StressTensor | None = None,
) -> PwDftRelaxationObservation:
    return PwDftRelaxationObservation(
        final_unit_cell=final_cell,
        ionic_step_count=6,
        completed=True,
        ionic_converged=True,
        cell_converged=cell_converged,
        final_total_energy_ev=-10.0,
        maximum_force_ev_per_angstrom=0.005,
        pressure_kbar=0.1,
        stress_tensor=stress_tensor,
        total_magnetization_electrons=0.0,
        program_version="test-1",
        native_artifacts=(
            PwDftRelaxationNativeArtifact(
                integration_id=integration_id,
                artifact_id="stdout",
                sha256="2" * 64,
                byte_size=100,
            ),
        ),
    )


def test_fixed_cell_result_preserves_lattice_and_allows_position_changes() -> None:
    request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
    integration_id = CalculatorIntegrationId("quantum-espresso")
    starting_structure = silicon_structure_resolution()

    result = PwDftRelaxationResult(
        evaluation_id=request.evaluation_id,
        task_id="task-1",
        request=request,
        starting_structure=starting_structure,
        calculator_input=_input_record(integration_id, request),
        observation=_observation(
            _final_cell(starting_structure.unit_cell), integration_id, None
        ),
    )

    assert result.observation.ionic_converged
    assert result.observation.cell_converged is None


def test_observation_identity_canonicalizes_stress_to_si_tension_positive() -> None:
    request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
    integration_id = CalculatorIntegrationId("quantum-espresso")
    starting_structure = silicon_structure_resolution()
    native_stress = StressTensor(
        components=MatrixQuantity(
            np.diag(np.asarray((1.0, 2.0, 3.0), dtype=np.float64)),
            PhysicalUnit("gigapascal"),
        ),
        sign_convention=StressSignConvention.COMPRESSION_POSITIVE,
    )
    result = PwDftRelaxationResult(
        evaluation_id=request.evaluation_id,
        task_id="task-1",
        request=request,
        starting_structure=starting_structure,
        calculator_input=_input_record(integration_id, request),
        observation=_observation(
            _final_cell(starting_structure.unit_cell),
            integration_id,
            None,
            native_stress,
        ),
    )

    payload = json.loads(result.canonical_observation_bytes)

    assert payload["schema_version"] == 2
    assert payload["stress_tensor"] == {
        "components": [
            [-1.0e9, -0.0, -0.0],
            [-0.0, -2.0e9, -0.0],
            [-0.0, -0.0, -3.0e9],
        ],
        "sign_convention": "tension-positive",
        "unit": "pascal",
    }


def test_fixed_cell_result_rejects_lattice_change() -> None:
    request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
    integration_id = CalculatorIntegrationId("quantum-espresso")
    starting_structure = silicon_structure_resolution()

    with pytest.raises(ValueError, match="preserve lattice parameter"):
        PwDftRelaxationResult(
            evaluation_id=request.evaluation_id,
            task_id="task-1",
            request=request,
            starting_structure=starting_structure,
            calculator_input=_input_record(integration_id, request),
            observation=_observation(
                _final_cell(starting_structure.unit_cell, 1.01), integration_id, None
            ),
        )
