from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from projectkoios.physkit.periodic.unit_cell import UnitCell, UnitCellJsonCodec
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation import (
    PwDftRelaxationScope,
    PwDftRelaxedStructurePublicationRequest,
    PwDftRelaxedStructurePublisher,
)
from projectkoios.simulations.structure import (
    ObservedStructureProvenance,
    ObservedStructureScope,
    StructureRepresentation,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    completed_relaxation_result,
    matching_relaxation_evidence,
    starting_structure_resolution,
)


@pytest.mark.parametrize(
    ("scope", "observed_scope"),
    (
        (
            PwDftRelaxationScope.ATOMIC_POSITIONS,
            ObservedStructureScope.atomic_positions,
        ),
        (
            PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL,
            ObservedStructureScope.atomic_positions_and_cell,
        ),
    ),
)
def test_publishes_exact_base_unit_cell_with_correlated_observed_provenance(
    tmp_path: Path,
    scope: PwDftRelaxationScope,
    observed_scope: ObservedStructureScope,
) -> None:
    result = completed_relaxation_result(scope)
    evidence = matching_relaxation_evidence(result)
    starting_structure = starting_structure_resolution(result, tmp_path)

    publication = PwDftRelaxedStructurePublisher().action(
        PwDftRelaxedStructurePublicationRequest(
            structure_id="Si.RelaxedUnitCell",
            starting_structure=starting_structure,
            relaxation_result=result,
            evidence=evidence,
        )
    )

    assert publication.record.representation is StructureRepresentation.unit_cell
    assert type(publication.record.provenance) is ObservedStructureProvenance
    assert publication.record.provenance.scope is observed_scope
    assert publication.record.provenance.relaxation_calculation.sha256 == (
        result.calculator_input.source.sha256
    )
    assert publication.record.provenance.relaxation_evidence.sha256 == evidence.sha256
    assert (
        type(
            UnitCellJsonCodec().loads(
                publication.content.decode(),
                expected_structure_id="Si.RelaxedUnitCell",
            )
        )
        is UnitCell
    )
    assert not (tmp_path / "Si.RelaxedUnitCell.json").exists()


@pytest.mark.parametrize(
    ("evidence_changes", "message"),
    (
        pytest.param(
            {"calculator_input_sha256": "f" * 64},
            "exact prepared-input",
            id="prepared-input-digest",
        ),
        pytest.param(
            {"integration_id": CalculatorIntegrationId("vasp")},
            "integrations",
            id="integration",
        ),
        pytest.param(
            {"calculator_name": "Different calculator"},
            "calculator names",
            id="calculator-name",
        ),
        pytest.param(
            {"calculator_version": "7.3"},
            "calculator versions",
            id="calculator-version",
        ),
        pytest.param(
            {"provider_completed": False},
            "completed converged",
            id="provider-completion",
        ),
    ),
)
def test_rejects_uncorrelated_evidence_fields(
    tmp_path: Path,
    evidence_changes: dict[str, object],
    message: str,
) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = replace(matching_relaxation_evidence(result), **evidence_changes)

    with pytest.raises(ValueError, match=message):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_evidence_with_a_different_simulation_source(tmp_path: Path) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = matching_relaxation_evidence(result)
    evidence = replace(
        evidence,
        simulation=replace(evidence.simulation, sha256="f" * 64),
    )

    with pytest.raises(ValueError, match="evidence simulation"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_evidence_with_different_native_artifact_bytes(
    tmp_path: Path,
) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = matching_relaxation_evidence(result)
    evidence = replace(
        evidence,
        native_artifacts=(replace(evidence.native_artifacts[0], sha256="f" * 64),),
    )

    with pytest.raises(ValueError, match="native artifacts"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_variable_cell_observation_without_cell_convergence(
    tmp_path: Path,
) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL)
    result = replace(
        result,
        observation=replace(result.observation, cell_converged=False),
    )
    evidence = matching_relaxation_evidence(result)

    with pytest.raises(ValueError, match="cell convergence"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_starting_cell_bytes_that_do_not_match_the_record(
    tmp_path: Path,
) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = matching_relaxation_evidence(result)
    starting = starting_structure_resolution(result, tmp_path)
    corrupted_record = replace(
        starting.record,
        sha256="f" * 64,
        provenance=replace(starting.record.provenance, result_sha256="f" * 64),
    )

    with pytest.raises(ValueError, match="starting structure bytes"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=replace(starting, record=corrupted_record),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_evidence_from_a_different_task(tmp_path: Path) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = replace(matching_relaxation_evidence(result), task_id="task-2")

    with pytest.raises(ValueError, match="evidence task"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )


def test_rejects_evidence_for_different_normalized_geometry(tmp_path: Path) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = matching_relaxation_evidence(result)
    altered_result = replace(
        result,
        observation=replace(
            result.observation,
            final_unit_cell=result.request.simulation.unit_cell,
        ),
    )

    with pytest.raises(ValueError, match="exact relaxation observation"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(
                    altered_result, tmp_path
                ),
                relaxation_result=altered_result,
                evidence=evidence,
            )
        )


def test_rejects_evidence_that_does_not_report_convergence(tmp_path: Path) -> None:
    result = completed_relaxation_result(PwDftRelaxationScope.ATOMIC_POSITIONS)
    evidence = replace(
        matching_relaxation_evidence(result),
        calculation_converged=False,
    )

    with pytest.raises(ValueError, match="completed converged"):
        PwDftRelaxedStructurePublisher().action(
            PwDftRelaxedStructurePublicationRequest(
                structure_id="Si.RelaxedUnitCell",
                starting_structure=starting_structure_resolution(result, tmp_path),
                relaxation_result=result,
                evidence=evidence,
            )
        )
