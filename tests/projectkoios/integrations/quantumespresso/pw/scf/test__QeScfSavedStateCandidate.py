from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from projectkoios.integrations.quantumespresso.pw.scf.saved_state_candidate import (
    QeScfCandidateExecutable,
    QeScfCandidateInputLineage,
    QeScfCandidateProducer,
    QeScfCandidatePseudopotential,
    QeScfCandidateRenderedInput,
    QeScfCandidateSavedState,
    QeScfCandidateStructure,
    QeScfCandidateSubject,
    QeScfCandidateSuccessEvidence,
    QeScfCandidateTerminalCorrelation,
    QeScfCandidateWorkflowCorrelation,
    QeScfSavedStateCandidate,
    QeScfSavedStateCandidateJsonCodec,
    QeScfSavedStateCandidateVerifier,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifact,
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
    QeSavedStatePseudopotential,
)
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfNativeArtifact,
    PwDftScfObservation,
    PwDftScfResult,
    PwDftScfWorkflowSucceeded,
)
from projectkoios.simulations.evidence import (
    EvidenceArtifactReference,
    EvidenceNormalizationRecord,
    SimulationEvidenceRecord,
)
from tests.projectkoios.integrations.quantumespresso.pw.scf.support import (
    qe_prepared_input,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64


def _candidate() -> QeScfSavedStateCandidate:
    return QeScfSavedStateCandidate(
        producer=QeScfCandidateProducer(
            integration_identity="quantum-espresso",
            adapter_identity="qe-scf-candidate-assembler",
            adapter_version="1",
            source_revision="a" * 40,
        ),
        workflow=QeScfCandidateWorkflowCorrelation(
            child_export_identity="child-export:1",
            child_execution_plan_identity="workflow-plan:1",
            child_run_identity="workflow-run:1",
            child_net_instance_identity="net-instance:1",
            calculator_request_identity="request:1",
            calculator_transition_occurrence_identity="occurrence:1",
            calculator_plan_identity="calculator-plan:1",
            calculator_effect_intent_identity="effect-intent:1",
            calculator_attempt_identity="attempt:1",
            calculator_dispatch_authorization_identity="authority:1",
            calculator_execution_evidence_identity="execution-evidence:1",
        ),
        subject=QeScfCandidateSubject(
            evaluation_id="silicon-scf",
            task_id="task-1",
            simulation_specification_reference_identity="payload-reference:simulation",
        ),
        input_lineage=QeScfCandidateInputLineage(
            calculator_input_record_reference_identity="payload-reference:input",
            calculator_input_record_sha256=_SHA_A,
            rendered_input=QeScfCandidateRenderedInput(
                role="calculator-input",
                filename="pw.in",
                byte_size=20,
                sha256=_SHA_B,
            ),
            structure=QeScfCandidateStructure(
                structure_id="Si.PrimitiveUnitCell",
                representation="projectkoios.unit-cell+json",
                schema_version=1,
                byte_size=200,
                sha256=_SHA_A,
                payload_reference_identity="payload-reference:structure",
            ),
            executable=QeScfCandidateExecutable(
                program="pw.x",
                reported_version="7.5",
                byte_size=1000,
                sha256=_SHA_B,
                artifact_identity="artifact:pw-x",
                payload_reference_identity="payload-reference:executable",
            ),
            pseudopotentials=(
                QeScfCandidatePseudopotential(
                    element_symbol="Si",
                    stable_file_identity="pseudo:si-pbe",
                    filename="Si.upf",
                    format="upf",
                    byte_size=500,
                    sha256=_SHA_A,
                    provenance_identity="provenance:pseudo-si",
                    payload_reference_identity="payload-reference:pseudo-si",
                ),
            ),
        ),
        success_evidence=QeScfCandidateSuccessEvidence(
            calculator_execution_record_reference_identity="payload-reference:execution",
            simulation_evidence_reference_identity="payload-reference:evidence",
            normalized_observation_reference_identity="payload-reference:observation",
            execution_status="succeeded",
            returncode=0,
            provider_completed=True,
            calculation_converged=True,
        ),
        saved_state=QeScfCandidateSavedState(
            calculation="scf",
            prefix="si",
            manifest_reference_identity="payload-reference:manifest",
            manifest_artifact_identity="artifact:manifest",
            manifest_sha256=_SHA_B,
            manifest_byte_size=300,
            artifact_set_identity="artifact-set:saved-state",
            artifact_count=4,
            total_byte_size=4000,
            source_verification_evidence_identity="verification:saved-state",
        ),
        terminal=QeScfCandidateTerminalCorrelation(
            child_definition_identity="dft_pw_scf",
            terminal_transition_occurrence_identity="occurrence:accept-analysis",
            terminal_place_identity="terminal_outcome",
            terminal_classification="succeeded",
            terminal_outcome_reference_identity="payload-reference:terminal-outcome",
            terminal_history_head_identity="history-head:1",
        ),
    )


def _verified_records() -> tuple[
    QeScfSavedStateCandidate,
    bytes,
    CalculatorInputRecord,
    SimulationEvidenceRecord,
    PwDftScfWorkflowSucceeded,
]:
    candidate = _candidate()
    prepared_input = qe_prepared_input()
    primary_input = prepared_input.artifacts[0]
    requirement = prepared_input.external_requirements[0]
    executable = candidate.input_lineage.executable
    structure = candidate.input_lineage.structure
    pseudopotential = QeSavedStatePseudopotential(
        symbol="Si",
        filename=requirement.filename,
        sha256=requirement.sha256,
        byte_size=requirement.byte_size,
    )
    artifacts = (
        QeSavedStateArtifact(
            QeSavedStateArtifactRole.qexsd,
            "si.save/data-file-schema.xml",
            "1" * 64,
            1,
        ),
        QeSavedStateArtifact(
            QeSavedStateArtifactRole.charge_density,
            "si.save/charge-density.dat",
            "2" * 64,
            2,
        ),
        QeSavedStateArtifact(
            QeSavedStateArtifactRole.wavefunction,
            "si.save/wfc1.dat",
            "3" * 64,
            3,
        ),
        QeSavedStateArtifact(
            QeSavedStateArtifactRole.pseudopotential,
            f"si.save/{requirement.filename}",
            requirement.sha256,
            requirement.byte_size,
        ),
    )
    manifest = QeSavedStateManifest(
        schema_version=1,
        prefix="si",
        calculation=QeSavedStateCalculation.scf,
        producer_program="pw.x",
        producer_version=executable.reported_version,
        executable_sha256=executable.sha256,
        input_sha256=primary_input.sha256,
        structure_id=structure.structure_id,
        structure_sha256=structure.sha256,
        pseudopotentials=(pseudopotential,),
        artifacts=artifacts,
    )
    manifest_payload = QeSavedStateManifestJsonCodec().dumps(manifest)
    candidate = replace(
        candidate,
        input_lineage=replace(
            candidate.input_lineage,
            calculator_input_record_sha256=prepared_input.sha256,
            rendered_input=QeScfCandidateRenderedInput(
                role=primary_input.role,
                filename=primary_input.filename,
                byte_size=primary_input.byte_size,
                sha256=primary_input.sha256,
            ),
            pseudopotentials=(
                QeScfCandidatePseudopotential(
                    element_symbol="Si",
                    stable_file_identity=requirement.stable_id,
                    filename=requirement.filename,
                    format=requirement.format,
                    byte_size=requirement.byte_size,
                    sha256=requirement.sha256,
                    provenance_identity=requirement.provenance,
                    payload_reference_identity="payload-reference:pseudo-si",
                ),
            ),
        ),
        saved_state=replace(
            candidate.saved_state,
            manifest_sha256=hashlib.sha256(manifest_payload).hexdigest(),
            manifest_byte_size=len(manifest_payload),
            artifact_count=len(artifacts),
            total_byte_size=sum(value.byte_size for value in artifacts),
        ),
    )
    native = EvidenceArtifactReference(
        artifact_id="pw.out",
        role="stdout",
        media_type="text/plain",
        byte_size=10,
        sha256="4" * 64,
    )
    evidence = SimulationEvidenceRecord(
        evidence_id="evidence:1",
        schema_version=1,
        evaluation_id=candidate.subject.evaluation_id,
        task_id=candidate.subject.task_id,
        simulation=prepared_input.source,
        calculator_input_sha256=prepared_input.sha256,
        integration_id=prepared_input.integration_id,
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version=executable.reported_version,
        execution=EvidenceArtifactReference(
            artifact_id="execution.json",
            role="execution-record",
            media_type="application/json",
            byte_size=10,
            sha256="5" * 64,
        ),
        native_artifacts=(native,),
        normalization=EvidenceNormalizationRecord(
            operation_id="qe-scf-normalize",
            operation_version="1",
            source_artifact_ids=(native.artifact_id,),
            output_representation="projectkoios.pw-dft-scf-observation+json",
            output_schema_version=1,
            output_byte_size=10,
            output_sha256="6" * 64,
        ),
        provider_completed=True,
        calculation_converged=True,
    )
    native_observation = PwDftScfNativeArtifact(
        integration_id=prepared_input.integration_id,
        artifact_id=native.artifact_id,
        sha256=native.sha256,
        byte_size=native.byte_size,
    )
    outcome = PwDftScfWorkflowSucceeded(
        PwDftScfResult(
            candidate.subject.evaluation_id,
            candidate.subject.task_id,
            PwDftScfObservation(
                total_energy_ev=-100.0,
                atom_count=2,
                electronic_iteration_count=5,
                converged=True,
                completed=True,
                native_artifact=native_observation,
            ),
        )
    )
    return candidate, manifest_payload, prepared_input, evidence, outcome


def test_canonical_round_trip_and_identity_are_stable() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    candidate = _candidate()

    payload, metadata = codec.encode_canonical(candidate)

    assert payload == codec.encode_canonical(candidate)[0]
    assert not payload.endswith(b"\n")
    assert codec.decode_canonical(payload) == candidate
    assert metadata.payload_identity.endswith(hashlib.sha256(payload).hexdigest())
    assert metadata.schema_identity.endswith("saved-state-candidate:1")
    assert metadata.codec_identity.endswith("saved-state-candidate-json:1")
    assert metadata.media_type.endswith("saved-state-candidate.v1+json")


def test_changed_export_or_attempt_lineage_changes_candidate_identity() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    candidate = _candidate()
    changed_attempt = replace(
        candidate,
        workflow=replace(candidate.workflow, calculator_attempt_identity="attempt:2"),
    )
    changed_export = replace(
        candidate,
        workflow=replace(candidate.workflow, child_export_identity="child-export:2"),
    )
    identity = codec.encode_canonical(candidate)[1].payload_identity

    assert identity != codec.encode_canonical(changed_attempt)[1].payload_identity
    assert identity != codec.encode_canonical(changed_export)[1].payload_identity


def test_decoder_requires_child_export_identity() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    payload, _ = codec.encode_canonical(_candidate())
    document = json.loads(payload)
    del document["workflow"]["child_export_identity"]
    hostile = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(ValueError, match="missing=.*child_export_identity"):
        codec.decode_canonical(hostile)


def test_decoder_rejects_noncanonical_key_order() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    payload, _ = codec.encode_canonical(_candidate())
    document = json.loads(payload)
    reversed_document = dict(reversed(tuple(document.items())))
    noncanonical = json.dumps(
        reversed_document,
        separators=(",", ":"),
        sort_keys=False,
    ).encode()
    assert noncanonical != payload

    with pytest.raises(ValueError, match="not canonical"):
        codec.decode_canonical(noncanonical)


def test_decoder_rejects_duplicate_key() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()

    with pytest.raises(ValueError, match="duplicate JSON key"):
        codec.decode_canonical(b'{"schema_identity":"a","schema_identity":"b"}')


def test_decoder_rejects_unknown_acceptance_claim() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    payload, _ = codec.encode_canonical(_candidate())
    document = json.loads(payload)
    document["scientifically_accepted"] = True
    hostile = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(ValueError, match="unexpected=.*scientifically_accepted"):
        codec.decode_canonical(hostile)


def test_decoder_rejects_boolean_as_integer() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    payload, _ = codec.encode_canonical(_candidate())
    document = json.loads(payload)
    document["saved_state"]["manifest_byte_size"] = True
    hostile = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(TypeError, match="manifest_byte_size must be an integer"):
        codec.decode_canonical(hostile)


@pytest.mark.parametrize(
    "identity",
    ("/tmp/state", "~/state", "file:/tmp/state", "C:state", "\\\\server\\state"),
)
def test_saved_state_rejects_machine_path_artifact_identity(identity: str) -> None:
    candidate = _candidate()

    with pytest.raises(ValueError, match="must not be a machine path"):
        replace(candidate.saved_state, artifact_set_identity=identity)


def test_exact_lexical_bounds_fail_closed() -> None:
    candidate = _candidate()
    assert replace(candidate.workflow, child_export_identity="a" * 512)
    assert replace(candidate.workflow, child_run_identity="a" * 512)
    assert replace(candidate.subject, task_id="a" * 256)
    assert replace(candidate.saved_state, prefix="a" * 128)
    assert replace(candidate.input_lineage.rendered_input, filename="a" * 255)

    with pytest.raises(ValueError, match="exceeds 512"):
        replace(candidate.workflow, child_export_identity="a" * 513)
    with pytest.raises(ValueError, match="exceeds 512"):
        replace(candidate.workflow, child_run_identity="a" * 513)
    with pytest.raises(ValueError, match="exceeds 256"):
        replace(candidate.subject, task_id="a" * 257)
    with pytest.raises(ValueError, match="at most 128"):
        replace(candidate.saved_state, prefix="a" * 129)
    with pytest.raises(ValueError, match="safe ASCII basename"):
        replace(candidate.input_lineage.rendered_input, filename="a" * 256)
    with pytest.raises(ValueError, match="ASCII only"):
        replace(candidate.workflow, child_run_identity="run:é")
    with pytest.raises(ValueError, match="controls"):
        replace(candidate.workflow, child_run_identity="run:\n1")


def test_pseudopotential_collection_bound_is_exact() -> None:
    candidate = _candidate()
    base = candidate.input_lineage.pseudopotentials[0]
    symbols = tuple(
        chr(ord("A") + index // 26) + chr(ord("a") + index % 26) for index in range(256)
    )
    maximum = tuple(
        replace(
            base,
            element_symbol=symbols[index],
            stable_file_identity=f"pseudo:{index}",
            filename=f"p{index}.upf",
        )
        for index in range(256)
    )
    assert replace(candidate.input_lineage, pseudopotentials=maximum)
    over_limit = (base,) * 257
    with pytest.raises(ValueError, match="1..256"):
        replace(candidate.input_lineage, pseudopotentials=over_limit)


def test_pseudopotential_identity_sets_must_be_unique() -> None:
    candidate = _candidate()
    first = candidate.input_lineage.pseudopotentials[0]
    duplicate = replace(first, payload_reference_identity="payload-reference:other")

    with pytest.raises(ValueError, match="element symbols must be unique"):
        replace(candidate.input_lineage, pseudopotentials=(first, duplicate))


def test_decoder_rejects_excess_nesting_before_schema_construction() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    nested: object = "value"
    for _ in range(7):
        nested = {"nested": nested}
    payload = json.dumps(nested, separators=(",", ":"), sort_keys=True).encode()

    with pytest.raises(ValueError, match="nesting exceeds depth six"):
        codec.decode_canonical(payload)


def test_collection_and_document_bounds_fail_closed() -> None:
    codec = QeScfSavedStateCandidateJsonCodec()
    candidate = _candidate()

    with pytest.raises(ValueError, match="artifact_count"):
        replace(candidate.saved_state, artifact_count=4097)
    with pytest.raises(ValueError, match="total_byte_size"):
        replace(candidate.saved_state, total_byte_size=68_719_476_737)
    with pytest.raises(ValueError, match="1..262144"):
        codec.decode_canonical(b" " * 262_145)


def test_verifier_accepts_exact_cross_record_lineage() -> None:
    candidate, manifest_payload, prepared_input, evidence, outcome = _verified_records()

    manifest = QeScfSavedStateCandidateVerifier().verify(
        candidate=candidate,
        manifest_payload=manifest_payload,
        calculator_input=prepared_input,
        simulation_evidence=evidence,
        terminal_outcome=outcome,
    )

    assert manifest.input_sha256 == candidate.input_lineage.rendered_input.sha256


def test_verifier_rejects_manifest_and_attempt_lineage_tamper() -> None:
    candidate, manifest_payload, prepared_input, evidence, outcome = _verified_records()
    verifier = QeScfSavedStateCandidateVerifier()

    with pytest.raises(ValueError, match="manifest payload SHA-256"):
        verifier.verify(
            candidate=replace(
                candidate,
                saved_state=replace(candidate.saved_state, manifest_sha256="0" * 64),
            ),
            manifest_payload=manifest_payload,
            calculator_input=prepared_input,
            simulation_evidence=evidence,
            terminal_outcome=outcome,
        )
    with pytest.raises(ValueError, match="simulation evidence task differs"):
        verifier.verify(
            candidate=candidate,
            manifest_payload=manifest_payload,
            calculator_input=prepared_input,
            simulation_evidence=replace(evidence, task_id="other-task"),
            terminal_outcome=outcome,
        )


def test_candidate_is_provider_evidence_not_authority_or_acceptance() -> None:
    payload, _ = QeScfSavedStateCandidateJsonCodec().encode_canonical(_candidate())

    assert b"scientific" not in payload
    assert b"accepted_parent" not in payload
    assert b"execution_authorized" not in payload
    assert b"working_directory" not in payload
