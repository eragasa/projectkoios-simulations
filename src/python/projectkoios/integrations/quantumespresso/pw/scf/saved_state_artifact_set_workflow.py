"""Workflow SDK alpha adapter for pure QE SCF artifact-set projection."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from abc import abstractmethod

from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set import (
    QeScfSavedStateArtifactSetCanonicalCodec,
    QeScfSavedStateArtifactSetEncodingRequest,
    QeScfSavedStateArtifactSetIdentity,
    QeScfSavedStateArtifactSetProjectionRequest,
    QeScfSavedStateArtifactSetProjectionResult,
    QeScfSavedStateArtifactSetProjector,
    QeScfSavedStateManifestArtifactIdentity,
    QeScfSavedStateRetainedArtifact,
    QeScfSavedStateRetentionReference,
    QeScfSavedStateVerificationEvidenceIdentity,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifactRole,
    QeSavedStateManifestJsonCodec,
)
from projectkoios.workflow_sdk.firing import (
    Firer,
    WorkflowFirerDescriptor,
    WorkflowFiringBounds,
    WorkflowFiringFailed,
    WorkflowFiringRejected,
    WorkflowFiringRequest,
    WorkflowFiringResult,
    WorkflowFiringSucceeded,
    WorkflowTransitionFirerBinding,
)
from projectkoios.workflow_sdk.identities import (
    WorkflowDefinitionIdentity,
    WorkflowFirerIdentity,
    WorkflowFirerImplementationIdentity,
    WorkflowIntegrationIdentity,
    WorkflowIntegrationManifestIdentity,
    WorkflowPayloadCodecIdentity,
    WorkflowPayloadOwnerIdentity,
    WorkflowPayloadRepresentationIdentity,
    WorkflowPayloadSchemaIdentity,
    WorkflowPayloadTypeIdentity,
    WorkflowTransitionIdentity,
)
from projectkoios.workflow_sdk.integration import (
    WorkflowIntegrationManifest,
    WorkflowWorkerIntegration,
)
from projectkoios.workflow_sdk.payloads import (
    WorkflowInlinePayload,
    WorkflowPayloadContract,
)

_MAX_INLINE_BYTES = 4 * 1024 * 1024
_MAX_IDENTITY_BYTES = 256
_MAX_ARTIFACTS = 4096
_MAX_DOCUMENT_DEPTH = 8

_REQUEST_SCHEMA = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-projection-request:1"
)
_REQUEST_CODEC = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-projection-request-json:1"
)
_REQUEST_TYPE = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-projection-request"
)
_REQUEST_MEDIA_TYPE = (
    "application/vnd.projectkoios."
    "qe-pw-scf-saved-state-artifact-set-projection-request.v1+json"
)
_ARTIFACT_SET_SCHEMA = (
    "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set:1"
)
_ARTIFACT_SET_CODEC = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-json:1"
)
_ARTIFACT_SET_TYPE = (
    "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set"
)
_ARTIFACT_SET_MEDIA_TYPE = (
    "application/vnd.projectkoios.qe-pw-scf-saved-state-artifact-set.v1+json"
)
_ARTIFACT_SET_IDENTITY_SCHEMA = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-identity:1"
)
_ARTIFACT_SET_IDENTITY_CODEC = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-identity-ascii:1"
)
_ARTIFACT_SET_IDENTITY_TYPE = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-identity"
)
_ARTIFACT_SET_IDENTITY_MEDIA_TYPE = (
    "application/vnd.projectkoios.qe-pw-scf-saved-state-artifact-set-identity.v1+ascii"
)
_OWNER_IDENTITY = "projectkoios.simulations"
_JSON_REPRESENTATION_IDENTITY = "canonical-json:1"
_ASCII_REPRESENTATION_IDENTITY = "canonical-ascii:1"
_FIRER_IDENTITY = "projectkoios.simulations.qe-scf-saved-state-artifact-set.project"
_FIRER_IMPLEMENTATION_IDENTITY = (
    "projectkoios.simulations.qe-scf-saved-state-artifact-set.project:0.1.0a1.2"
)
_INTEGRATION_IDENTITY = "projectkoios.simulations.qe-scf-saved-state-artifact-set"
_PACKAGE_NAME = "projectkoios-simulations"
_FIXTURE_DEFINITION_IDENTITY = (
    "projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set:1"
)
_FIXTURE_TRANSITION_IDENTITY = (
    "projectkoios.workflow.fixture.qe-scf-saved-state-artifact-set-project:1"
)
_FIXTURE_BINDING_VERSION = "0.1.0a1_fixture.1"


class QeScfSavedStateArtifactSetProjectionRequestJsonCodec:
    """Encode the existing projection request for the bounded SDK pilot."""

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "QeScfSavedStateArtifactSetProjectionRequestJsonCodec is not subclassable"
        )

    def encode(self, value: QeScfSavedStateArtifactSetProjectionRequest) -> bytes:
        """Return strict canonical JSON for one existing domain request."""
        if type(value) is not QeScfSavedStateArtifactSetProjectionRequest:
            raise TypeError(
                "value must be a QeScfSavedStateArtifactSetProjectionRequest"
            )
        document = {
            "manifest_artifact_identity": self._opaque_identity(
                value.manifest_artifact_identity.value,
                "manifest_artifact_identity",
            ),
            "manifest_payload_base64": base64.b64encode(value.manifest_payload).decode(
                "ascii"
            ),
            "manifest_reference": self._opaque_identity(
                value.manifest_reference.value,
                "manifest_reference",
            ),
            "retained_artifacts": [
                {
                    "byte_size": artifact.byte_size,
                    "payload_reference": self._opaque_identity(
                        artifact.payload_reference.value,
                        "payload_reference",
                    ),
                    "relative_path": artifact.relative_path,
                    "role": artifact.role.value,
                    "sha256": artifact.sha256,
                }
                for artifact in value.retained_artifacts
            ],
            "schema_identity": _REQUEST_SCHEMA,
            "source_verification_evidence_identity": self._opaque_identity(
                value.source_verification_evidence_identity.value,
                "source_verification_evidence_identity",
            ),
        }
        payload = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if len(payload) > _MAX_INLINE_BYTES:
            raise ValueError("projection request exceeds the 4-MiB SDK pilot bound")
        return payload

    def decode(self, payload: bytes) -> QeScfSavedStateArtifactSetProjectionRequest:
        """Strictly reconstruct the unchanged domain projection request."""
        if type(payload) is not bytes:
            raise TypeError("payload must be built-in bytes")
        if not payload or len(payload) > _MAX_INLINE_BYTES:
            raise ValueError("payload must contain 1..4194304 bytes")
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("payload must not contain a UTF-8 BOM")
        try:
            document = json.loads(
                payload.decode("utf-8"),
                object_pairs_hook=self._reject_duplicate_pairs,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("payload must be valid UTF-8 JSON") from error
        except RecursionError as error:
            raise ValueError("payload exceeds maximum JSON depth") from error
        self._validate_depth(document, 1)
        root = self._mapping(document, "payload")
        self._closed_keys(
            root,
            {
                "schema_identity",
                "manifest_payload_base64",
                "manifest_reference",
                "manifest_artifact_identity",
                "retained_artifacts",
                "source_verification_evidence_identity",
            },
            "payload",
        )
        if self._string(root["schema_identity"], "schema_identity") != _REQUEST_SCHEMA:
            raise ValueError("unsupported projection-request schema identity")
        manifest_payload = self._base64(
            self._string(
                root["manifest_payload_base64"],
                "manifest_payload_base64",
            )
        )
        try:
            manifest = QeSavedStateManifestJsonCodec().loads(manifest_payload)
        except RecursionError as error:
            raise ValueError("manifest payload exceeds maximum JSON depth") from error
        artifacts_value = root["retained_artifacts"]
        if type(artifacts_value) is not list:
            raise TypeError("retained_artifacts must be an array")
        if not 1 <= len(artifacts_value) <= _MAX_ARTIFACTS:
            raise ValueError("retained_artifacts must contain 1..4096 values")
        retained_artifacts = tuple(
            self._artifact(value, index) for index, value in enumerate(artifacts_value)
        )
        result = QeScfSavedStateArtifactSetProjectionRequest(
            manifest=manifest,
            manifest_payload=manifest_payload,
            manifest_reference=QeScfSavedStateRetentionReference(
                self._opaque_identity(
                    self._string(root["manifest_reference"], "manifest_reference"),
                    "manifest_reference",
                )
            ),
            manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
                self._opaque_identity(
                    self._string(
                        root["manifest_artifact_identity"],
                        "manifest_artifact_identity",
                    ),
                    "manifest_artifact_identity",
                )
            ),
            retained_artifacts=retained_artifacts,
            source_verification_evidence_identity=(
                QeScfSavedStateVerificationEvidenceIdentity(
                    self._opaque_identity(
                        self._string(
                            root["source_verification_evidence_identity"],
                            "source_verification_evidence_identity",
                        ),
                        "source_verification_evidence_identity",
                    )
                )
            ),
        )
        if self.encode(result) != payload:
            raise ValueError("payload is not the exact canonical encoding")
        return result

    def _artifact(
        self,
        value: object,
        index: int,
    ) -> QeScfSavedStateRetainedArtifact:
        item = self._mapping(value, f"retained_artifacts[{index}]")
        self._closed_keys(
            item,
            {
                "role",
                "relative_path",
                "sha256",
                "byte_size",
                "payload_reference",
            },
            f"retained_artifacts[{index}]",
        )
        return QeScfSavedStateRetainedArtifact(
            role=QeSavedStateArtifactRole(
                self._string(item["role"], f"retained_artifacts[{index}].role")
            ),
            relative_path=self._string(
                item["relative_path"],
                f"retained_artifacts[{index}].relative_path",
            ),
            sha256=self._string(
                item["sha256"],
                f"retained_artifacts[{index}].sha256",
            ),
            byte_size=self._integer(
                item["byte_size"],
                f"retained_artifacts[{index}].byte_size",
            ),
            payload_reference=QeScfSavedStateRetentionReference(
                self._opaque_identity(
                    self._string(
                        item["payload_reference"],
                        f"retained_artifacts[{index}].payload_reference",
                    ),
                    f"retained_artifacts[{index}].payload_reference",
                )
            ),
        )

    def _reject_duplicate_pairs(
        self,
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def _validate_depth(self, value: object, depth: int) -> None:
        if depth > _MAX_DOCUMENT_DEPTH:
            raise ValueError("payload exceeds maximum JSON depth")
        if type(value) is dict:
            for child in value.values():
                self._validate_depth(child, depth + 1)
        elif type(value) is list:
            for child in value:
                self._validate_depth(child, depth + 1)

    def _mapping(self, value: object, label: str) -> dict[str, object]:
        if type(value) is not dict:
            raise TypeError(f"{label} must be an object")
        if any(type(key) is not str for key in value):
            raise TypeError(f"{label} keys must be strings")
        return value

    def _closed_keys(
        self,
        value: dict[str, object],
        expected: set[str],
        label: str,
    ) -> None:
        actual = set(value)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(f"{label} keys differ; missing={missing}, extra={extra}")

    def _string(self, value: object, label: str) -> str:
        if type(value) is not str:
            raise TypeError(f"{label} must be a string")
        return value

    def _integer(self, value: object, label: str) -> int:
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer")
        return value

    def _opaque_identity(self, value: str, label: str) -> str:
        if not value or value != value.strip():
            raise ValueError(f"{label} must be nonempty and stripped")
        try:
            payload = value.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError(f"{label} must contain ASCII only") from error
        if len(payload) > 512:
            raise ValueError(f"{label} exceeds 512 ASCII bytes")
        if any(byte < 0x20 or byte == 0x7F for byte in payload):
            raise ValueError(f"{label} must not contain controls or DEL")
        lowered = value.lower()
        if (
            value.startswith(("/", "~", "\\", "./", "../"))
            or value in {".", ".."}
            or "\\" in value
            or "/" in value
            or lowered.startswith("file:")
            or (
                len(value) >= 2
                and value[0].isascii()
                and value[0].isalpha()
                and value[1] == ":"
            )
        ):
            raise ValueError(f"{label} must not be a machine path or locator")
        return value

    def _base64(self, value: str) -> bytes:
        try:
            payload = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("manifest payload must be strict Base64") from error
        if base64.b64encode(payload).decode("ascii") != value:
            raise ValueError("manifest payload has noncanonical Base64")
        if not payload:
            raise ValueError("manifest payload must be nonempty")
        return payload


class QeScfSavedStateArtifactSetIdentityAsciiCodec:
    """Encode one owner logical artifact-set identity as canonical ASCII."""

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        del kwargs
        raise TypeError(
            "QeScfSavedStateArtifactSetIdentityAsciiCodec is not subclassable"
        )

    def encode(self, value: QeScfSavedStateArtifactSetIdentity) -> bytes:
        """Return exact bounded ASCII bytes without framing or whitespace."""
        if type(value) is not QeScfSavedStateArtifactSetIdentity:
            raise TypeError("value must be a QeScfSavedStateArtifactSetIdentity")
        try:
            payload = value.value.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("artifact-set identity must contain ASCII only") from error
        if not payload or len(payload) > _MAX_IDENTITY_BYTES:
            raise ValueError("artifact-set identity must contain 1..256 ASCII bytes")
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("artifact-set identity must not contain a UTF-8 BOM")
        if payload != payload.strip() or any(byte <= 0x20 for byte in payload):
            raise ValueError("artifact-set identity must not contain whitespace")
        if any(byte == 0x7F for byte in payload):
            raise ValueError("artifact-set identity must not contain DEL")
        return payload

    def decode(self, payload: bytes) -> QeScfSavedStateArtifactSetIdentity:
        """Strictly reconstruct one owner logical identity from exact bytes."""
        if type(payload) is not bytes:
            raise TypeError("payload must be built-in bytes")
        if not payload or len(payload) > _MAX_IDENTITY_BYTES:
            raise ValueError("payload must contain 1..256 ASCII bytes")
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("payload must not contain a UTF-8 BOM")
        try:
            value = payload.decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("payload must contain ASCII only") from error
        if payload != payload.strip() or any(byte <= 0x20 for byte in payload):
            raise ValueError("payload must not contain whitespace")
        if any(byte == 0x7F for byte in payload):
            raise ValueError("payload must not contain DEL")
        identity = QeScfSavedStateArtifactSetIdentity(value)
        if self.encode(identity) != payload:
            raise ValueError("payload is not the exact canonical identity encoding")
        return identity


QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT = WorkflowPayloadContract(
    role="projection_request",
    owner_identity=WorkflowPayloadOwnerIdentity(_OWNER_IDENTITY),
    payload_type_identity=WorkflowPayloadTypeIdentity(_REQUEST_TYPE),
    schema_identity=WorkflowPayloadSchemaIdentity(_REQUEST_SCHEMA),
    codec_identity=WorkflowPayloadCodecIdentity(_REQUEST_CODEC),
    representation_identity=WorkflowPayloadRepresentationIdentity(
        _JSON_REPRESENTATION_IDENTITY
    ),
    media_type=_REQUEST_MEDIA_TYPE,
    maximum_byte_length=_MAX_INLINE_BYTES,
)

QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT = WorkflowPayloadContract(
    role="artifact_set_identity",
    owner_identity=WorkflowPayloadOwnerIdentity(_OWNER_IDENTITY),
    payload_type_identity=WorkflowPayloadTypeIdentity(_ARTIFACT_SET_IDENTITY_TYPE),
    schema_identity=WorkflowPayloadSchemaIdentity(_ARTIFACT_SET_IDENTITY_SCHEMA),
    codec_identity=WorkflowPayloadCodecIdentity(_ARTIFACT_SET_IDENTITY_CODEC),
    representation_identity=WorkflowPayloadRepresentationIdentity(
        _ASCII_REPRESENTATION_IDENTITY
    ),
    media_type=_ARTIFACT_SET_IDENTITY_MEDIA_TYPE,
    maximum_byte_length=_MAX_IDENTITY_BYTES,
)

QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT = WorkflowPayloadContract(
    role="artifact_set",
    owner_identity=WorkflowPayloadOwnerIdentity(_OWNER_IDENTITY),
    payload_type_identity=WorkflowPayloadTypeIdentity(_ARTIFACT_SET_TYPE),
    schema_identity=WorkflowPayloadSchemaIdentity(_ARTIFACT_SET_SCHEMA),
    codec_identity=WorkflowPayloadCodecIdentity(_ARTIFACT_SET_CODEC),
    representation_identity=WorkflowPayloadRepresentationIdentity(
        _JSON_REPRESENTATION_IDENTITY
    ),
    media_type=_ARTIFACT_SET_MEDIA_TYPE,
    maximum_byte_length=_MAX_INLINE_BYTES,
)

QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR = WorkflowFirerDescriptor(
    identity=WorkflowFirerIdentity(_FIRER_IDENTITY),
    implementation_identity=WorkflowFirerImplementationIdentity(
        _FIRER_IMPLEMENTATION_IDENTITY
    ),
    input_contracts=(QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT,),
    output_contracts=(QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT,),
    evidence_contracts=(QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT,),
    bounds=WorkflowFiringBounds(
        maximum_input_count=1,
        maximum_output_count=1,
        maximum_evidence_count=1,
        maximum_input_bytes=_MAX_INLINE_BYTES,
        maximum_output_bytes=_MAX_IDENTITY_BYTES,
        maximum_total_bytes=_MAX_INLINE_BYTES + _MAX_IDENTITY_BYTES,
        maximum_reason_count=1,
    ),
)

QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING = WorkflowTransitionFirerBinding(
    definition_identity=WorkflowDefinitionIdentity(_FIXTURE_DEFINITION_IDENTITY),
    transition_identity=WorkflowTransitionIdentity(_FIXTURE_TRANSITION_IDENTITY),
    firer_identity=QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR.identity,
    input_roles=("projection_request",),
    output_roles=("artifact_set_identity",),
    binding_version=_FIXTURE_BINDING_VERSION,
)


class QeScfSavedStateArtifactSetWorkflowFirer(Firer):
    """Nominal Simulations boundary for the SDK alpha pure firing."""

    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "_fire" in cls.__dict__:
            raise TypeError(
                "QeScfSavedStateArtifactSetWorkflowFirer._fire is non-overridable"
            )

    @property
    def descriptor(self) -> WorkflowFirerDescriptor:
        """Return the exact immutable alpha descriptor."""
        return QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR

    def _fire(self, *, request: WorkflowFiringRequest) -> WorkflowFiringResult:
        try:
            owner_request = (
                QeScfSavedStateArtifactSetProjectionRequestJsonCodec().decode(
                    request.inputs[0].payload
                )
            )
        except TypeError, ValueError:
            return WorkflowFiringRejected(
                request_identity=request.identity,
                occurrence_identity=request.context.occurrence_identity,
                attempt_identity=request.context.attempt_identity,
                firer_identity=request.firer_identity,
                reason_codes=("invalid_projection_request",),
                evidence=(),
            )
        try:
            projection = self._project(request=owner_request)
            if type(projection) is not QeScfSavedStateArtifactSetProjectionResult:
                raise TypeError("projector returned an invalid result type")
            if projection.request != owner_request:
                raise ValueError("projection result differs from the owner request")
            projection = QeScfSavedStateArtifactSetProjectionResult(
                request=projection.request,
                artifact_set=projection.artifact_set,
                artifact_set_identity=projection.artifact_set_identity,
                candidate_saved_state=projection.candidate_saved_state,
            )
            encoded = QeScfSavedStateArtifactSetCanonicalCodec().encode(
                QeScfSavedStateArtifactSetEncodingRequest(
                    artifact_set=projection.artifact_set
                )
            )
            identity_payload = QeScfSavedStateArtifactSetIdentityAsciiCodec().encode(
                projection.artifact_set_identity
            )
        except TypeError, ValueError:
            return WorkflowFiringFailed(
                request_identity=request.identity,
                occurrence_identity=request.context.occurrence_identity,
                attempt_identity=request.context.attempt_identity,
                firer_identity=request.firer_identity,
                failure_codes=("artifact_set_projection_failed",),
                evidence=(),
            )
        if encoded.payload_byte_size > _MAX_INLINE_BYTES:
            return WorkflowFiringRejected(
                request_identity=request.identity,
                occurrence_identity=request.context.occurrence_identity,
                attempt_identity=request.context.attempt_identity,
                firer_identity=request.firer_identity,
                reason_codes=("artifact_set_evidence_exceeds_inline_transport_bound",),
                evidence=(),
            )
        output_contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT
        output = WorkflowInlinePayload(
            role=output_contract.role,
            owner_identity=output_contract.owner_identity,
            payload_type_identity=output_contract.payload_type_identity,
            schema_identity=output_contract.schema_identity,
            codec_identity=output_contract.codec_identity,
            representation_identity=output_contract.representation_identity,
            media_type=output_contract.media_type,
            payload=identity_payload,
            byte_length=len(identity_payload),
            payload_sha256=hashlib.sha256(identity_payload).hexdigest(),
        )
        evidence_contract = QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT
        evidence = WorkflowInlinePayload(
            role=evidence_contract.role,
            owner_identity=evidence_contract.owner_identity,
            payload_type_identity=evidence_contract.payload_type_identity,
            schema_identity=evidence_contract.schema_identity,
            codec_identity=evidence_contract.codec_identity,
            representation_identity=evidence_contract.representation_identity,
            media_type=evidence_contract.media_type,
            payload=encoded.payload,
            byte_length=encoded.payload_byte_size,
            payload_sha256=encoded.payload_sha256,
        )
        return WorkflowFiringSucceeded(
            request_identity=request.identity,
            occurrence_identity=request.context.occurrence_identity,
            attempt_identity=request.context.attempt_identity,
            firer_identity=request.firer_identity,
            outputs=(output,),
            evidence=(evidence,),
        )

    @abstractmethod
    def _project(
        self,
        *,
        request: QeScfSavedStateArtifactSetProjectionRequest,
    ) -> QeScfSavedStateArtifactSetProjectionResult:
        """Invoke one exact owner projection without transport side effects."""


class QeScfSavedStateArtifactSetProjectorFirer(QeScfSavedStateArtifactSetWorkflowFirer):
    """Adapt the existing pure artifact-set projector to the SDK alpha."""

    __slots__ = ()

    def _project(
        self,
        *,
        request: QeScfSavedStateArtifactSetProjectionRequest,
    ) -> QeScfSavedStateArtifactSetProjectionResult:
        return QeScfSavedStateArtifactSetProjector().action(request=request)


class QeScfSavedStateArtifactSetProjectorIntegration(WorkflowWorkerIntegration):
    """Expose the exact QE projector firer through one worker composition root."""

    __slots__ = ("_firers", "_manifest")

    def __init__(
        self,
        *,
        package_version: str,
        distribution_sha256: str,
        firer: QeScfSavedStateArtifactSetWorkflowFirer | None = None,
    ) -> None:
        selected_firer = firer or QeScfSavedStateArtifactSetProjectorFirer()
        if not isinstance(
            selected_firer,
            QeScfSavedStateArtifactSetWorkflowFirer,
        ):
            raise TypeError(
                "firer must implement QeScfSavedStateArtifactSetWorkflowFirer"
            )
        if selected_firer.descriptor != (
            QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR
        ):
            raise ValueError("firer descriptor differs from the QE projection contract")
        self._firers = (selected_firer,)
        self._manifest = WorkflowIntegrationManifest(
            integration_identity=WorkflowIntegrationIdentity(_INTEGRATION_IDENTITY),
            package_name=_PACKAGE_NAME,
            package_version=package_version,
            distribution_sha256=distribution_sha256,
            sdk_contract_version=(
                QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR.sdk_contract_version
            ),
            firer_descriptors=(QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR,),
        )

    @property
    def manifest(self) -> WorkflowIntegrationManifest:
        """Return the exact immutable manifest supplied to Workflow linking."""
        return self._manifest

    @property
    def manifest_identity(self) -> WorkflowIntegrationManifestIdentity:
        """Return the identity implemented by this worker composition."""
        return self._manifest.identity

    def firers(self) -> tuple[Firer, ...]:
        """Return the sole exact pure QE projector firer."""
        return self._firers


__all__ = [
    "QE_SCF_SAVED_STATE_ARTIFACT_SET_EVIDENCE_CONTRACT",
    "QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR",
    "QE_SCF_SAVED_STATE_ARTIFACT_SET_IDENTITY_CONTRACT",
    "QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT",
    "QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING",
    "QeScfSavedStateArtifactSetIdentityAsciiCodec",
    "QeScfSavedStateArtifactSetProjectionRequestJsonCodec",
    "QeScfSavedStateArtifactSetProjectorFirer",
    "QeScfSavedStateArtifactSetProjectorIntegration",
    "QeScfSavedStateArtifactSetWorkflowFirer",
]
