from __future__ import annotations

import hashlib

import numpy as np
import pytest

from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import Unitless, VectorQuantity
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.dft.pw.relaxation import (
    PwDftRelaxationNativeArtifact,
    PwDftRelaxationObservation,
    PwDftRelaxationResult,
    PwDftRelaxationScope,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)


def _input_record(integration_id: CalculatorIntegrationId) -> CalculatorInputRecord:
    content = b"relaxation input\n"
    return CalculatorInputRecord(
        input_id="silicon-relaxation-input",
        schema_version=1,
        source=CalculatorInputSourceReference(
            simulation_id="silicon-relaxation",
            representation="test",
            schema_version=1,
            byte_size=10,
            sha256="1" * 64,
        ),
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

    result = PwDftRelaxationResult(
        evaluation_id=request.evaluation_id,
        task_id="task-1",
        request=request,
        calculator_input=_input_record(integration_id),
        observation=_observation(
            _final_cell(request.simulation.unit_cell), integration_id, None
        ),
    )

    assert result.observation.ionic_converged
    assert result.observation.cell_converged is None


def test_fixed_cell_result_rejects_lattice_change() -> None:
    request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
    integration_id = CalculatorIntegrationId("quantum-espresso")

    with pytest.raises(ValueError, match="preserve lattice parameter"):
        PwDftRelaxationResult(
            evaluation_id=request.evaluation_id,
            task_id="task-1",
            request=request,
            calculator_input=_input_record(integration_id),
            observation=_observation(
                _final_cell(request.simulation.unit_cell, 1.01), integration_id, None
            ),
        )
