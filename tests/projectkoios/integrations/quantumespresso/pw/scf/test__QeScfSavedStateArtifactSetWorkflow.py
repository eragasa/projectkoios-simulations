from __future__ import annotations

import hashlib
import inspect
import json
import tomllib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set import (
    QeScfSavedStateArtifactSetCanonicalCodec,
    QeScfSavedStateArtifactSetDecodingRequest,
    QeScfSavedStateArtifactSetIdentity,
    QeScfSavedStateArtifactSetProjectionRequest,
    QeScfSavedStateArtifactSetProjectionResult,
    QeScfSavedStateArtifactSetProjector,
    QeScfSavedStateManifestArtifactIdentity,
    QeScfSavedStateRetainedArtifact,
    QeScfSavedStateRetentionReference,
    QeScfSavedStateVerificationEvidenceIdentity,
)
from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set_workflow import (  # noqa: E501
    QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT,
    QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR,
    QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT,
    QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT,
    QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING,
    QeScfSavedStateArtifactSetIdentityAsciiCodec,
    QeScfSavedStateArtifactSetProjectionRequestJsonCodec,
    QeScfSavedStateArtifactSetProjectorFirer,
    QeScfSavedStateArtifactSetProjectorIntegration,
    QeScfSavedStateArtifactSetWorkflowFirer,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifact,
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
    QeSavedStatePseudopotential,
)
from projectkoios.workflow_sdk import WORKFLOW_SDK_VERSION
from projectkoios.workflow_sdk.firing import (
    WorkflowFiringFailed,
    WorkflowFiringRejected,
    WorkflowFiringRequest,
    WorkflowFiringResult,
    WorkflowFiringSucceeded,
    WorkflowOccurrenceContext,
)
from projectkoios.workflow_sdk.identities import (
    WorkflowAttemptIdentity,
    WorkflowMarkingIdentity,
    WorkflowNetInstanceIdentity,
    WorkflowOccurrenceIdentity,
    WorkflowPayloadSchemaIdentity,
)
from projectkoios.workflow_sdk.payloads import WorkflowInlinePayload
from projectkoios.workflow_sdk.serialization import (
    WorkflowFirerDescriptorJsonCodec,
    WorkflowFiringRequestJsonCodec,
    WorkflowFiringResultJsonCodec,
    WorkflowTransitionFirerBindingJsonCodec,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64
_SYNTHETIC_SELECTED_CPN_BINDING_SHA256 = hashlib.sha256(
    b"projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set."
    b"selected-cpn-binding:1"
).hexdigest()


def test_request_codec_round_trips_exact_existing_domain_request() -> None:
    request = _domain_request()
    codec = QeScfSavedStateArtifactSetProjectionRequestJsonCodec()

    payload = codec.encode(request)
    decoded = codec.decode(payload)

    assert decoded == request
    assert payload == json.dumps(
        json.loads(payload),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def test_identity_ascii_codec_round_trips_exact_owner_identity() -> None:
    identity = (
        QeScfSavedStateArtifactSetProjector()
        .action(request=_domain_request())
        .artifact_set_identity
    )
    codec = QeScfSavedStateArtifactSetIdentityAsciiCodec()

    payload = codec.encode(identity)

    assert payload == identity.value.encode("ascii")
    assert payload == payload.strip()
    assert b"\n" not in payload
    assert type(codec.decode(payload)) is QeScfSavedStateArtifactSetIdentity
    assert codec.decode(payload) == identity


def test_identity_ascii_codec_rejects_malformed_wrong_and_oversized_bytes() -> None:
    identity = (
        QeScfSavedStateArtifactSetProjector()
        .action(request=_domain_request())
        .artifact_set_identity
    )
    codec = QeScfSavedStateArtifactSetIdentityAsciiCodec()
    payload = codec.encode(identity)

    for malformed in (
        b"",
        b"x" * 257,
        b"\xef\xbb\xbf" + payload,
        payload + b"\n",
        b" " + payload,
        payload + b"trailing",
        b"wrong-owner-identity",
        b"\xff",
    ):
        with pytest.raises((TypeError, ValueError)):
            codec.decode(malformed)

    with pytest.raises(TypeError, match="QeScfSavedStateArtifactSetIdentity"):
        codec.encode("not-an-identity")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="not subclassable"):

        class _Codec(QeScfSavedStateArtifactSetIdentityAsciiCodec):
            pass


def test_descriptor_and_fixture_binding_are_exact_immutable_sdk_records() -> None:
    descriptor = QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR
    binding = QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING

    assert inspect.isabstract(QeScfSavedStateArtifactSetWorkflowFirer)
    assert not inspect.isabstract(QeScfSavedStateArtifactSetProjectorFirer)
    assert descriptor.identity.value == (
        "projectkoios.simulations.qe-scf-saved-state-artifact-set.project"
    )
    assert descriptor.input_contracts == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT,
    )
    assert descriptor.output_contracts == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT,
    )
    assert descriptor.evidence_contracts == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT,
    )
    identity_contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT
    assert identity_contract.role == "artifact_set_identity"
    assert identity_contract.payload_type_identity.value == (
        "projectkoios.integrations.quantumespresso."
        "qe-pw-scf-saved-state-artifact-set-identity"
    )
    assert identity_contract.schema_identity.value.endswith(
        "qe-pw-scf-saved-state-artifact-set-identity:1"
    )
    assert identity_contract.codec_identity.value.endswith(
        "qe-pw-scf-saved-state-artifact-set-identity-ascii:1"
    )
    assert identity_contract.representation_identity.value == "canonical-ascii:1"
    assert identity_contract.media_type.endswith(
        "qe-pw-scf-saved-state-artifact-set-identity.v1+ascii"
    )
    assert identity_contract.maximum_byte_length == 256
    assert descriptor.bounds.maximum_total_bytes == 4 * 1024 * 1024 + 256
    assert descriptor.sdk_contract_version == WORKFLOW_SDK_VERSION
    assert binding.definition_identity.value == (
        "projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set:1"
    )
    assert binding.transition_identity.value == (
        "projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set-project:1"
    )
    assert binding.input_roles == ("projection_request",)
    assert binding.output_roles == ("artifact_set_identity",)
    assert binding.binding_version == "0.1.0a1_fixture.1"
    assert binding.firer_identity == descriptor.identity
    assert binding.identity.value != _SYNTHETIC_SELECTED_CPN_BINDING_SHA256

    assert (
        WorkflowFirerDescriptorJsonCodec().decode(
            WorkflowFirerDescriptorJsonCodec().encode(descriptor)
        )
        == descriptor
    )
    assert (
        WorkflowTransitionFirerBindingJsonCodec().decode(
            WorkflowTransitionFirerBindingJsonCodec().encode(binding)
        )
        == binding
    )

    with pytest.raises(FrozenInstanceError):
        descriptor.sdk_contract_version = "changed"  # type: ignore[misc]


def test_worker_integration_exposes_exact_manifest_and_firer() -> None:
    integration = QeScfSavedStateArtifactSetProjectorIntegration(
        package_version="0.1.0.dev0",
        distribution_sha256="9" * 64,
    )

    assert integration.manifest_identity == integration.manifest.identity
    assert integration.manifest.package_name == "projectkoios-simulations"
    assert integration.manifest.package_version == "0.1.0.dev0"
    assert integration.manifest.distribution_sha256 == "9" * 64
    assert integration.manifest.firer_descriptors == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR,
    )
    assert len(integration.firers()) == 1
    assert type(integration.firers()[0]) is QeScfSavedStateArtifactSetProjectorFirer
    assert integration.firers()[0].descriptor == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR
    )


def test_concrete_firer_outputs_identity_and_retains_artifact_set_evidence() -> None:
    owner_request = _domain_request()
    request = _workflow_request(owner_request)

    result = QeScfSavedStateArtifactSetProjectorFirer().fire(request=request)

    assert type(result) is WorkflowFiringSucceeded
    assert result.request_identity == request.identity
    assert result.occurrence_identity == request.context.occurrence_identity
    assert result.attempt_identity == request.context.attempt_identity
    assert result.firer_identity == request.firer_identity
    assert len(result.outputs) == 1
    assert len(result.evidence) == 1
    expected = QeScfSavedStateArtifactSetProjector().action(request=owner_request)

    output = result.outputs[0]
    output_contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT
    assert output.role == "artifact_set_identity"
    assert output.owner_identity == output_contract.owner_identity
    assert output.payload_type_identity == output_contract.payload_type_identity
    assert output.schema_identity == output_contract.schema_identity
    assert output.codec_identity == output_contract.codec_identity
    assert output.representation_identity == output_contract.representation_identity
    assert output.media_type == output_contract.media_type
    assert output.byte_length == len(output.payload)
    assert output.payload_sha256 == hashlib.sha256(output.payload).hexdigest()
    decoded_identity = QeScfSavedStateArtifactSetIdentityAsciiCodec().decode(
        output.payload
    )
    assert decoded_identity == expected.artifact_set_identity

    evidence = result.evidence[0]
    evidence_contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT
    assert evidence.role == "artifact_set"
    assert evidence.owner_identity == evidence_contract.owner_identity
    assert evidence.payload_type_identity == evidence_contract.payload_type_identity
    assert evidence.schema_identity == evidence_contract.schema_identity
    assert evidence.codec_identity == evidence_contract.codec_identity
    assert evidence.representation_identity == evidence_contract.representation_identity
    assert evidence.media_type == evidence_contract.media_type
    assert evidence.payload_sha256 == hashlib.sha256(evidence.payload).hexdigest()
    decoded_evidence = QeScfSavedStateArtifactSetCanonicalCodec().decode(
        QeScfSavedStateArtifactSetDecodingRequest(payload=evidence.payload)
    )
    assert decoded_evidence.artifact_set == expected.artifact_set

    assert (
        WorkflowFiringRequestJsonCodec().decode(
            WorkflowFiringRequestJsonCodec().encode(request)
        )
        == request
    )
    assert (
        WorkflowFiringResultJsonCodec().decode(
            WorkflowFiringResultJsonCodec().encode(result)
        )
        == result
    )


def test_malformed_owner_payload_is_a_correlated_rejection() -> None:
    owner_request = _domain_request()
    request = _workflow_request(owner_request)
    malformed_payload = request.inputs[0].payload + b" "
    malformed = replace(
        request.inputs[0],
        payload=malformed_payload,
        byte_length=len(malformed_payload),
        payload_sha256=hashlib.sha256(malformed_payload).hexdigest(),
    )
    malformed_request = WorkflowFiringRequest(
        context=request.context,
        binding_identity=request.binding_identity,
        firer_identity=request.firer_identity,
        inputs=(malformed,),
    )

    result = QeScfSavedStateArtifactSetProjectorFirer().fire(request=malformed_request)

    assert type(result) is WorkflowFiringRejected
    assert result.request_identity == malformed_request.identity
    assert result.reason_codes == ("invalid_projection_request",)
    assert result.evidence == ()


def test_artifact_set_evidence_above_inline_bound_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    oversized_payload = b"x" * (4 * 1024 * 1024 + 1)

    class _OversizedEncodingResult:
        payload = oversized_payload
        payload_byte_size = len(oversized_payload)
        payload_sha256 = hashlib.sha256(oversized_payload).hexdigest()

    def _oversized_encode(*args: object, **kwargs: object) -> object:
        del args, kwargs
        return _OversizedEncodingResult()

    monkeypatch.setattr(
        QeScfSavedStateArtifactSetCanonicalCodec,
        "encode",
        _oversized_encode,
    )
    request = _workflow_request(_domain_request())

    result = QeScfSavedStateArtifactSetProjectorFirer().fire(request=request)

    assert type(result) is WorkflowFiringRejected
    assert result.request_identity == request.identity
    assert result.reason_codes == (
        "artifact_set_evidence_exceeds_inline_transport_bound",
    )
    assert result.evidence == ()


def test_known_pure_projection_failure_is_correlated_and_has_no_output() -> None:
    class _FailingFirer(QeScfSavedStateArtifactSetWorkflowFirer):
        def _project(
            self,
            *,
            request: QeScfSavedStateArtifactSetProjectionRequest,
        ) -> object:  # type: ignore[override]
            del request
            raise ValueError("known pure failure")

    request = _workflow_request(_domain_request())
    result = _FailingFirer().fire(request=request)

    assert type(result) is WorkflowFiringFailed
    assert result.request_identity == request.identity
    assert result.failure_codes == ("artifact_set_projection_failed",)
    assert result.evidence == ()


def test_mismatched_owner_projection_result_is_a_correlated_failure() -> None:
    other_request = replace(
        _domain_request(),
        manifest_reference=QeScfSavedStateRetentionReference(
            "pilot.other-retention.manifest"
        ),
    )

    class _MismatchedFirer(QeScfSavedStateArtifactSetWorkflowFirer):
        def _project(
            self,
            *,
            request: QeScfSavedStateArtifactSetProjectionRequest,
        ) -> object:  # type: ignore[override]
            del request
            return QeScfSavedStateArtifactSetProjector().action(request=other_request)

    request = _workflow_request(_domain_request())
    result = _MismatchedFirer().fire(request=request)

    assert type(result) is WorkflowFiringFailed
    assert result.request_identity == request.identity
    assert result.failure_codes == ("artifact_set_projection_failed",)
    assert result.evidence == ()


def test_semantically_wrong_owner_identity_is_a_correlated_failure() -> None:
    owner_request = _domain_request()
    valid = QeScfSavedStateArtifactSetProjector().action(request=owner_request)
    prefix = valid.artifact_set_identity.value.rsplit(":", 1)[0]
    wrong_identity = QeScfSavedStateArtifactSetIdentity(f"{prefix}:{'0' * 64}")
    forged = object.__new__(QeScfSavedStateArtifactSetProjectionResult)
    object.__setattr__(forged, "request", valid.request)
    object.__setattr__(forged, "artifact_set", valid.artifact_set)
    object.__setattr__(forged, "artifact_set_identity", wrong_identity)
    object.__setattr__(forged, "candidate_saved_state", valid.candidate_saved_state)

    class _WrongIdentityFirer(QeScfSavedStateArtifactSetWorkflowFirer):
        def _project(
            self,
            *,
            request: QeScfSavedStateArtifactSetProjectionRequest,
        ) -> QeScfSavedStateArtifactSetProjectionResult:
            assert request == owner_request
            return forged

    request = _workflow_request(owner_request)
    result = _WrongIdentityFirer().fire(request=request)

    assert type(result) is WorkflowFiringFailed
    assert result.request_identity == request.identity
    assert result.failure_codes == ("artifact_set_projection_failed",)
    assert result.evidence == ()


def test_owner_and_sdk_template_methods_cannot_be_overridden() -> None:
    with pytest.raises(TypeError, match="_fire is non-overridable"):

        class _InvalidOwnerFirer(QeScfSavedStateArtifactSetWorkflowFirer):
            def _fire(
                self,
                *,
                request: WorkflowFiringRequest,
            ) -> WorkflowFiringResult:
                raise AssertionError(request)

            def _project(
                self,
                *,
                request: QeScfSavedStateArtifactSetProjectionRequest,
            ) -> object:
                raise AssertionError(request)

    with pytest.raises(TypeError, match="non-overridable template method"):

        class _InvalidSdkFirer(QeScfSavedStateArtifactSetWorkflowFirer):
            def fire(
                self,
                *,
                request: WorkflowFiringRequest,
            ) -> WorkflowFiringResult:
                raise AssertionError(request)

            def _project(
                self,
                *,
                request: QeScfSavedStateArtifactSetProjectionRequest,
            ) -> object:
                raise AssertionError(request)


def test_sdk_rejects_payload_metadata_or_firer_correlation_mismatch() -> None:
    request = _workflow_request(_domain_request())
    wrong_payload = replace(
        request.inputs[0],
        schema_identity=WorkflowPayloadSchemaIdentity("owner.schema:changed"),
    )
    wrong_metadata = WorkflowFiringRequest(
        context=request.context,
        binding_identity=request.binding_identity,
        firer_identity=request.firer_identity,
        inputs=(wrong_payload,),
    )

    with pytest.raises(ValueError, match="metadata differs"):
        QeScfSavedStateArtifactSetProjectorFirer().fire(request=wrong_metadata)

    wrong_firer = replace(
        request,
        firer_identity=replace(request.firer_identity, value="other.firer"),
    )
    with pytest.raises(ValueError, match="firer identity differs"):
        QeScfSavedStateArtifactSetProjectorFirer().fire(request=wrong_firer)


def test_adapter_rejects_private_locator_references_without_success() -> None:
    request_with_locator = replace(
        _domain_request(),
        manifest_reference=QeScfSavedStateRetentionReference(
            "https://private.example/artifacts/manifest"
        ),
    )
    codec = QeScfSavedStateArtifactSetProjectionRequestJsonCodec()

    with pytest.raises(ValueError, match="machine path or locator"):
        codec.encode(request_with_locator)

    request = _workflow_request(_domain_request())
    document = json.loads(request.inputs[0].payload)
    document["manifest_reference"] = "https://private.example/artifacts/manifest"
    locator_payload = _canonical_json(document)
    locator_input = replace(
        request.inputs[0],
        payload=locator_payload,
        byte_length=len(locator_payload),
        payload_sha256=hashlib.sha256(locator_payload).hexdigest(),
    )
    locator_request = WorkflowFiringRequest(
        context=request.context,
        binding_identity=request.binding_identity,
        firer_identity=request.firer_identity,
        inputs=(locator_input,),
    )

    result = QeScfSavedStateArtifactSetProjectorFirer().fire(request=locator_request)
    assert type(result) is WorkflowFiringRejected
    assert result.reason_codes == ("invalid_projection_request",)
    assert result.evidence == ()


def test_request_codec_rejects_duplicate_unknown_base64_depth_and_size() -> None:
    codec = QeScfSavedStateArtifactSetProjectionRequestJsonCodec()
    payload = codec.encode(_domain_request())

    duplicate = payload.replace(
        b'{"manifest_artifact_identity":',
        b'{"manifest_artifact_identity":"duplicate","manifest_artifact_identity":',
        1,
    )
    with pytest.raises(ValueError, match="duplicate JSON key"):
        codec.decode(duplicate)

    document = json.loads(payload)
    document["unknown"] = None
    with pytest.raises(ValueError, match="keys differ"):
        codec.decode(_canonical_json(document))

    document.pop("unknown")
    document["manifest_payload_base64"] = "e30"
    with pytest.raises(ValueError, match="Base64"):
        codec.decode(_canonical_json(document))

    with pytest.raises(ValueError, match="maximum JSON depth"):
        codec.decode(b"[[[[[[[[0]]]]]]]]")
    with pytest.raises(ValueError, match="1..4194304 bytes"):
        codec.decode(b"x" * (4 * 1024 * 1024 + 1))


def test_request_codec_rejects_noncanonical_bytes_and_is_not_subclassable() -> None:
    codec = QeScfSavedStateArtifactSetProjectionRequestJsonCodec()
    payload = codec.encode(_domain_request())

    with pytest.raises(ValueError, match="exact canonical encoding"):
        codec.decode(payload + b" ")
    with pytest.raises(TypeError, match="not subclassable"):

        class _Codec(QeScfSavedStateArtifactSetProjectionRequestJsonCodec):
            pass


def test_dependency_and_exact_local_sdk_pilot_identity_are_documented() -> None:
    repository = Path(__file__).resolve().parents[6]
    with (repository / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    documentation = (
        repository
        / "docs/architecture/projectkoios/integrations/quantumespresso/pw/scf/"
        "saved_state_artifact_set/workflow_sdk/index.md"
    ).read_text()

    assert "projectkoios-workflow-sdk==0.1.0a1" in project["dependencies"]
    assert (
        "925f6974c49c8935ebf2f002b18c86d29375e1b11c3ffc17a29d305fb8095ff4"
        in documentation
    )


def test_pilot_does_not_change_existing_domain_or_candidate_sources() -> None:
    repository = Path(__file__).resolve().parents[6]
    artifact_set_source = repository / (
        "src/python/projectkoios/integrations/quantumespresso/pw/scf/"
        "saved_state_artifact_set.py"
    )
    candidate_source = repository / (
        "src/python/projectkoios/integrations/quantumespresso/pw/scf/"
        "saved_state_candidate.py"
    )

    assert hashlib.sha256(artifact_set_source.read_bytes()).hexdigest() == (
        "6e1ad5c573dff8c0304157c2ca5eff4d8d0819fbca3efee7ecace84c5226b5d6"
    )
    assert hashlib.sha256(candidate_source.read_bytes()).hexdigest() == (
        "d605a8fa30f9da3456a17777c02250eee3666e0b498bdab03a4d8657c5aea6b1"
    )


def _workflow_request(
    owner_request: QeScfSavedStateArtifactSetProjectionRequest,
) -> WorkflowFiringRequest:
    contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT
    payload = QeScfSavedStateArtifactSetProjectionRequestJsonCodec().encode(
        owner_request
    )
    inline = WorkflowInlinePayload(
        role=contract.role,
        owner_identity=contract.owner_identity,
        payload_type_identity=contract.payload_type_identity,
        schema_identity=contract.schema_identity,
        codec_identity=contract.codec_identity,
        representation_identity=contract.representation_identity,
        media_type=contract.media_type,
        payload=payload,
        byte_length=len(payload),
        payload_sha256=hashlib.sha256(payload).hexdigest(),
    )
    binding = QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING
    return WorkflowFiringRequest(
        context=WorkflowOccurrenceContext(
            definition_identity=binding.definition_identity,
            net_instance_identity=WorkflowNetInstanceIdentity("fixture.net:1"),
            transition_identity=binding.transition_identity,
            predecessor_marking_identity=WorkflowMarkingIdentity("fixture.marking:1"),
            predecessor_revision=7,
            selected_binding_sha256=_SYNTHETIC_SELECTED_CPN_BINDING_SHA256,
            occurrence_identity=WorkflowOccurrenceIdentity("fixture.occurrence:1"),
            attempt_identity=WorkflowAttemptIdentity("fixture.attempt:1"),
            attempt_ordinal=0,
        ),
        binding_identity=binding.identity,
        firer_identity=binding.firer_identity,
        inputs=(inline,),
    )


def _domain_request() -> QeScfSavedStateArtifactSetProjectionRequest:
    pseudopotential = QeSavedStatePseudopotential(
        symbol="Si",
        filename="Si.upf",
        sha256=_SHA_D,
        byte_size=4,
    )
    manifest = QeSavedStateManifest(
        schema_version=1,
        prefix="si",
        calculation=QeSavedStateCalculation.scf,
        producer_program="pw.x",
        producer_version="7.5",
        executable_sha256="f" * 64,
        input_sha256="1" * 64,
        structure_id="Si.PrimitiveUnitCell",
        structure_sha256="2" * 64,
        pseudopotentials=(pseudopotential,),
        artifacts=(
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.qexsd,
                relative_path="si.save/data-file-schema.xml",
                sha256=_SHA_A,
                byte_size=1,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.charge_density,
                relative_path="si.save/charge-density.dat",
                sha256=_SHA_B,
                byte_size=2,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.wavefunction,
                relative_path="si.save/wfc1.dat",
                sha256=_SHA_C,
                byte_size=3,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.pseudopotential,
                relative_path="si.save/Si.upf",
                sha256=_SHA_D,
                byte_size=4,
            ),
        ),
    )
    manifest_payload = QeSavedStateManifestJsonCodec().dumps(manifest)
    retained = tuple(
        QeScfSavedStateRetainedArtifact(
            role=artifact.role,
            relative_path=artifact.relative_path,
            sha256=artifact.sha256,
            byte_size=artifact.byte_size,
            payload_reference=QeScfSavedStateRetentionReference(
                f"pilot.retention.artifact:{index}"
            ),
        )
        for index, artifact in enumerate(manifest.artifacts)
    )
    return QeScfSavedStateArtifactSetProjectionRequest(
        manifest=manifest,
        manifest_payload=manifest_payload,
        manifest_reference=QeScfSavedStateRetentionReference(
            "pilot.retention.manifest"
        ),
        manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
            "pilot.manifest.identity"
        ),
        retained_artifacts=retained,
        source_verification_evidence_identity=(
            QeScfSavedStateVerificationEvidenceIdentity("pilot.verification.evidence")
        ),
    )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
