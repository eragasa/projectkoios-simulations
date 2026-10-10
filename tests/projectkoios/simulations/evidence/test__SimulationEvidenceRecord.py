from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import CalculatorInputSourceReference
from projectkoios.simulations.evidence import (
    EvidenceArtifactReference,
    EvidenceNormalizationRecord,
    SimulationEvidenceRecord,
)


def test_evidence_record_correlates_exact_inputs_artifacts_and_normalization() -> None:
    native = EvidenceArtifactReference(
        artifact_id="stdout",
        role="native-output",
        media_type="text/plain",
        byte_size=100,
        sha256="2" * 64,
    )
    record = SimulationEvidenceRecord(
        evidence_id="si-p-scf-evidence",
        schema_version=1,
        evaluation_id="si-p-scf-evaluation",
        task_id="task-1",
        simulation=CalculatorInputSourceReference(
            simulation_id="si-p-scf",
            representation="projectkoios.pw-dft-scf+json",
            schema_version=1,
            byte_size=200,
            sha256="1" * 64,
        ),
        calculator_input_sha256="3" * 64,
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version="7.4.1",
        execution=EvidenceArtifactReference(
            artifact_id="execution",
            role="execution-record",
            media_type="application/json",
            byte_size=80,
            sha256="4" * 64,
        ),
        native_artifacts=(native,),
        normalization=EvidenceNormalizationRecord(
            operation_id="projectkoios.qe.pw.scf.normalize",
            operation_version="1",
            source_artifact_ids=(native.artifact_id,),
            output_representation="projectkoios.pw-dft-scf-observation+json",
            output_schema_version=1,
            output_byte_size=64,
            output_sha256="5" * 64,
        ),
        provider_completed=True,
        calculation_converged=True,
    )

    payload = json.loads(record.canonical_bytes)

    assert record.normalization.source_artifact_ids == ("stdout",)
    assert payload["representation"] == "projectkoios.simulation-evidence+json"
    assert payload["evaluation_id"] == "si-p-scf-evaluation"
    assert payload["task_id"] == "task-1"
    assert record.byte_size == len(record.canonical_bytes)
    assert record.sha256 == hashlib.sha256(record.canonical_bytes).hexdigest()
    assert replace(record, calculation_converged=False).sha256 != record.sha256
    with pytest.raises(ValueError, match="schema_version must be one"):
        replace(record, schema_version=2)
    assert not hasattr(record, "accepted")
    assert not hasattr(record, "execution_authorized")


def test_evidence_record_rejects_unmatched_normalization_sources() -> None:
    native = EvidenceArtifactReference(
        artifact_id="stdout",
        role="native-output",
        media_type="text/plain",
        byte_size=100,
        sha256="2" * 64,
    )

    with pytest.raises(ValueError, match="exactly match"):
        SimulationEvidenceRecord(
            evidence_id="evidence",
            schema_version=1,
            evaluation_id="evaluation",
            task_id="task-1",
            simulation=CalculatorInputSourceReference(
                simulation_id="simulation",
                representation="test",
                schema_version=1,
                byte_size=10,
                sha256="1" * 64,
            ),
            calculator_input_sha256="3" * 64,
            integration_id=CalculatorIntegrationId("vasp"),
            calculator_name="VASP",
            calculator_version="6",
            execution=EvidenceArtifactReference(
                artifact_id="execution",
                role="execution-record",
                media_type="application/json",
                byte_size=10,
                sha256="4" * 64,
            ),
            native_artifacts=(native,),
            normalization=EvidenceNormalizationRecord(
                operation_id="normalize",
                operation_version="1",
                source_artifact_ids=("other",),
                output_representation="test",
                output_schema_version=1,
                output_byte_size=10,
                output_sha256="5" * 64,
            ),
            provider_completed=True,
            calculation_converged=True,
        )
