"""Provider-owned, path-free QE SCF saved-state candidate records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import ClassVar

from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
)
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.scf.base import PwDftScfWorkflowSucceeded
from projectkoios.simulations.evidence import SimulationEvidenceRecord

_SCHEMA_IDENTITY = (
    "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate:1"
)
_CODEC_IDENTITY = (
    "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-candidate-json:1"
)
_MEDIA_TYPE = "application/vnd.projectkoios.qe-pw-scf-saved-state-candidate.v1+json"
_CANDIDATE_KIND = "qe-pw-scf-saved-state"
_CANDIDATE_IDENTITY_PREFIX = f"{_SCHEMA_IDENTITY}:"
_MAX_DOCUMENT_BYTES = 262_144
_MAX_DOCUMENT_DEPTH = 6
_MAX_IDENTITY_BYTES = 512
_MAX_SIGNED_64 = 9_223_372_036_854_775_807
_MAX_SCHEMA_VERSION = 2_147_483_647
_MAX_PSEUDOPOTENTIALS = 256
_MAX_MANIFEST_ARTIFACTS = 4096
_MAX_SAVED_STATE_BYTES = 68_719_476_736
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EVALUATION_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_ROLE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SAFE_NAME_128 = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_SAFE_NAME_255 = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,254}\Z")
_ELEMENT = re.compile(r"[A-Z][a-z]?\Z")
_GIT_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_DRIVE_PREFIX = re.compile(r"[A-Za-z]:")


def _ascii(value: str, label: str, maximum: int) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be nonempty and stripped")
    try:
        payload = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"{label} must contain ASCII only") from error
    if len(payload) > maximum:
        raise ValueError(f"{label} exceeds {maximum} ASCII bytes")
    if any(byte < 0x20 or byte == 0x7F for byte in payload):
        raise ValueError(f"{label} must not contain controls or DEL")


def _identity(value: str, label: str) -> None:
    _ascii(value, label, _MAX_IDENTITY_BYTES)


def _artifact_identity(value: str, label: str) -> None:
    _identity(value, label)
    lowered = value.lower()
    if (
        value.startswith(("/", "~/", "\\\\"))
        or lowered.startswith("file:")
        or _DRIVE_PREFIX.match(value) is not None
    ):
        raise ValueError(f"{label} must not be a machine path")


def _sha256(value: str, label: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256")


def _positive_integer(value: int, label: str, maximum: int = _MAX_SIGNED_64) -> None:
    if type(value) is not int or value <= 0 or value > maximum:
        raise ValueError(f"{label} must be an integer in 1..{maximum}")


def _exact_true(value: bool, label: str) -> None:
    if type(value) is not bool or not value:
        raise ValueError(f"{label} must be true")


@dataclass(frozen=True, slots=True)
class QeScfCandidateProducer:
    """Identify the exact provider-side candidate assembler."""

    integration_identity: str
    adapter_identity: str
    adapter_version: str
    source_revision: str

    def __post_init__(self) -> None:
        if self.integration_identity != "quantum-espresso":
            raise ValueError("integration_identity must be quantum-espresso")
        _identity(self.adapter_identity, "adapter_identity")
        _ascii(self.adapter_version, "adapter_version", 128)
        if (
            type(self.source_revision) is not str
            or _GIT_REVISION.fullmatch(self.source_revision) is None
        ):
            raise ValueError("source_revision must be 40 lowercase hexadecimal digits")


@dataclass(frozen=True, slots=True)
class QeScfCandidateWorkflowCorrelation:
    """Bind one candidate to one exact Workflow-owned execution chain."""

    child_export_identity: str
    child_execution_plan_identity: str
    child_run_identity: str
    child_net_instance_identity: str
    calculator_request_identity: str
    calculator_transition_occurrence_identity: str
    calculator_plan_identity: str
    calculator_effect_intent_identity: str
    calculator_attempt_identity: str
    calculator_dispatch_authorization_identity: str
    calculator_execution_evidence_identity: str

    def __post_init__(self) -> None:
        for label, value in (
            ("child_export_identity", self.child_export_identity),
            ("child_execution_plan_identity", self.child_execution_plan_identity),
            ("child_run_identity", self.child_run_identity),
            ("child_net_instance_identity", self.child_net_instance_identity),
            ("calculator_request_identity", self.calculator_request_identity),
            (
                "calculator_transition_occurrence_identity",
                self.calculator_transition_occurrence_identity,
            ),
            ("calculator_plan_identity", self.calculator_plan_identity),
            (
                "calculator_effect_intent_identity",
                self.calculator_effect_intent_identity,
            ),
            ("calculator_attempt_identity", self.calculator_attempt_identity),
            (
                "calculator_dispatch_authorization_identity",
                self.calculator_dispatch_authorization_identity,
            ),
            (
                "calculator_execution_evidence_identity",
                self.calculator_execution_evidence_identity,
            ),
        ):
            _identity(value, label)


@dataclass(frozen=True, slots=True)
class QeScfCandidateSubject:
    """Identify the neutral SCF evaluation represented by a candidate."""

    evaluation_id: str
    task_id: str
    simulation_specification_reference_identity: str

    def __post_init__(self) -> None:
        if (
            type(self.evaluation_id) is not str
            or len(self.evaluation_id.encode("ascii", errors="ignore")) > 128
            or _EVALUATION_ID.fullmatch(self.evaluation_id) is None
        ):
            raise ValueError(
                "evaluation_id must be a lowercase slug of at most 128 bytes"
            )
        _ascii(self.task_id, "task_id", 256)
        _identity(
            self.simulation_specification_reference_identity,
            "simulation_specification_reference_identity",
        )


@dataclass(frozen=True, slots=True)
class QeScfCandidateRenderedInput:
    """Identify the exact rendered QE input bytes used by the attempt."""

    role: str
    filename: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if (
            type(self.role) is not str
            or len(self.role) > 64
            or _ROLE.fullmatch(self.role) is None
        ):
            raise ValueError("role must be a lowercase slug of at most 64 bytes")
        if (
            type(self.filename) is not str
            or _SAFE_NAME_255.fullmatch(self.filename) is None
            or self.filename in {".", ".."}
        ):
            raise ValueError("filename must be a safe ASCII basename")
        _positive_integer(self.byte_size, "byte_size")
        _sha256(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class QeScfCandidateStructure:
    """Retain the exact structure identity used by the saved-state producer."""

    structure_id: str
    representation: str
    schema_version: int
    byte_size: int
    sha256: str
    payload_reference_identity: str

    def __post_init__(self) -> None:
        _identity(self.structure_id, "structure_id")
        _ascii(self.representation, "representation", 128)
        _positive_integer(
            self.schema_version,
            "schema_version",
            _MAX_SCHEMA_VERSION,
        )
        _positive_integer(self.byte_size, "byte_size")
        _sha256(self.sha256, "sha256")
        _identity(self.payload_reference_identity, "payload_reference_identity")


@dataclass(frozen=True, slots=True)
class QeScfCandidateExecutable:
    """Retain the exact path-free ``pw.x`` executable evidence."""

    program: str
    reported_version: str
    byte_size: int
    sha256: str
    artifact_identity: str
    payload_reference_identity: str

    def __post_init__(self) -> None:
        if self.program != "pw.x":
            raise ValueError("program must be pw.x")
        _ascii(self.reported_version, "reported_version", 128)
        _positive_integer(self.byte_size, "byte_size")
        _sha256(self.sha256, "sha256")
        _artifact_identity(self.artifact_identity, "artifact_identity")
        _identity(self.payload_reference_identity, "payload_reference_identity")


@dataclass(frozen=True, slots=True)
class QeScfCandidatePseudopotential:
    """Retain one exact pseudopotential in rendered-input order."""

    element_symbol: str
    stable_file_identity: str
    filename: str
    format: str
    byte_size: int
    sha256: str
    provenance_identity: str
    payload_reference_identity: str

    def __post_init__(self) -> None:
        if (
            type(self.element_symbol) is not str
            or _ELEMENT.fullmatch(self.element_symbol) is None
        ):
            raise ValueError("element_symbol must be an ASCII element symbol")
        _identity(self.stable_file_identity, "stable_file_identity")
        if (
            type(self.filename) is not str
            or _SAFE_NAME_255.fullmatch(self.filename) is None
            or self.filename in {".", ".."}
        ):
            raise ValueError("filename must be a safe ASCII basename")
        _ascii(self.format, "format", 128)
        _positive_integer(self.byte_size, "byte_size")
        _sha256(self.sha256, "sha256")
        _identity(self.provenance_identity, "provenance_identity")
        _identity(self.payload_reference_identity, "payload_reference_identity")


@dataclass(frozen=True, slots=True)
class QeScfCandidateInputLineage:
    """Correlate prepared input, structure, executable, and pseudopotentials."""

    calculator_input_record_reference_identity: str
    calculator_input_record_sha256: str
    rendered_input: QeScfCandidateRenderedInput
    structure: QeScfCandidateStructure
    executable: QeScfCandidateExecutable
    pseudopotentials: tuple[QeScfCandidatePseudopotential, ...]

    def __post_init__(self) -> None:
        _identity(
            self.calculator_input_record_reference_identity,
            "calculator_input_record_reference_identity",
        )
        _sha256(self.calculator_input_record_sha256, "calculator_input_record_sha256")
        if type(self.rendered_input) is not QeScfCandidateRenderedInput:
            raise TypeError("rendered_input must be QeScfCandidateRenderedInput")
        if type(self.structure) is not QeScfCandidateStructure:
            raise TypeError("structure must be QeScfCandidateStructure")
        if type(self.executable) is not QeScfCandidateExecutable:
            raise TypeError("executable must be QeScfCandidateExecutable")
        if (
            type(self.pseudopotentials) is not tuple
            or not self.pseudopotentials
            or len(self.pseudopotentials) > _MAX_PSEUDOPOTENTIALS
            or any(
                type(value) is not QeScfCandidatePseudopotential
                for value in self.pseudopotentials
            )
        ):
            raise ValueError("pseudopotentials must contain 1..256 exact records")
        for values, label in (
            (
                tuple(value.element_symbol for value in self.pseudopotentials),
                "element symbols",
            ),
            (
                tuple(value.stable_file_identity for value in self.pseudopotentials),
                "stable identities",
            ),
            (
                tuple(value.filename for value in self.pseudopotentials),
                "filenames",
            ),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"pseudopotential {label} must be unique")


@dataclass(frozen=True, slots=True)
class QeScfCandidateSuccessEvidence:
    """Bind path-free provider success evidence without granting acceptance."""

    calculator_execution_record_reference_identity: str
    simulation_evidence_reference_identity: str
    normalized_observation_reference_identity: str
    execution_status: str
    returncode: int
    provider_completed: bool
    calculation_converged: bool

    def __post_init__(self) -> None:
        for label, value in (
            (
                "calculator_execution_record_reference_identity",
                self.calculator_execution_record_reference_identity,
            ),
            (
                "simulation_evidence_reference_identity",
                self.simulation_evidence_reference_identity,
            ),
            (
                "normalized_observation_reference_identity",
                self.normalized_observation_reference_identity,
            ),
        ):
            _identity(value, label)
        if self.execution_status != "succeeded":
            raise ValueError("execution_status must be succeeded")
        if type(self.returncode) is not int or self.returncode != 0:
            raise ValueError("returncode must be integer zero")
        _exact_true(self.provider_completed, "provider_completed")
        _exact_true(self.calculation_converged, "calculation_converged")


@dataclass(frozen=True, slots=True)
class QeScfCandidateSavedState:
    """Bind one verified immutable QE saved-state artifact set."""

    calculation: str
    prefix: str
    manifest_reference_identity: str
    manifest_artifact_identity: str
    manifest_sha256: str
    manifest_byte_size: int
    artifact_set_identity: str
    artifact_count: int
    total_byte_size: int
    source_verification_evidence_identity: str

    def __post_init__(self) -> None:
        if self.calculation != "scf":
            raise ValueError("calculation must be scf")
        if (
            type(self.prefix) is not str
            or _SAFE_NAME_128.fullmatch(self.prefix) is None
        ):
            raise ValueError("prefix must be a safe ASCII name of at most 128 bytes")
        _identity(self.manifest_reference_identity, "manifest_reference_identity")
        _artifact_identity(
            self.manifest_artifact_identity, "manifest_artifact_identity"
        )
        _sha256(self.manifest_sha256, "manifest_sha256")
        _positive_integer(self.manifest_byte_size, "manifest_byte_size")
        _artifact_identity(self.artifact_set_identity, "artifact_set_identity")
        _positive_integer(
            self.artifact_count,
            "artifact_count",
            _MAX_MANIFEST_ARTIFACTS,
        )
        _positive_integer(
            self.total_byte_size,
            "total_byte_size",
            _MAX_SAVED_STATE_BYTES,
        )
        _identity(
            self.source_verification_evidence_identity,
            "source_verification_evidence_identity",
        )


@dataclass(frozen=True, slots=True)
class QeScfCandidateTerminalCorrelation:
    """Correlate the post-terminal candidate to the unchanged child outcome."""

    child_definition_identity: str
    terminal_transition_occurrence_identity: str
    terminal_place_identity: str
    terminal_classification: str
    terminal_outcome_reference_identity: str
    terminal_history_head_identity: str

    def __post_init__(self) -> None:
        _identity(self.child_definition_identity, "child_definition_identity")
        _identity(
            self.terminal_transition_occurrence_identity,
            "terminal_transition_occurrence_identity",
        )
        if self.terminal_place_identity != "terminal_outcome":
            raise ValueError("terminal_place_identity must be terminal_outcome")
        if self.terminal_classification != "succeeded":
            raise ValueError("terminal_classification must be succeeded")
        _identity(
            self.terminal_outcome_reference_identity,
            "terminal_outcome_reference_identity",
        )
        _identity(
            self.terminal_history_head_identity,
            "terminal_history_head_identity",
        )


@dataclass(frozen=True, slots=True)
class QeScfSavedStateCandidate:
    """Represent one provider candidate, not project scientific acceptance."""

    schema_identity: ClassVar[str] = _SCHEMA_IDENTITY
    schema_version: ClassVar[int] = 1
    candidate_kind: ClassVar[str] = _CANDIDATE_KIND

    producer: QeScfCandidateProducer
    workflow: QeScfCandidateWorkflowCorrelation
    subject: QeScfCandidateSubject
    input_lineage: QeScfCandidateInputLineage
    success_evidence: QeScfCandidateSuccessEvidence
    saved_state: QeScfCandidateSavedState
    terminal: QeScfCandidateTerminalCorrelation

    def __post_init__(self) -> None:
        expected = (
            (self.producer, QeScfCandidateProducer, "producer"),
            (self.workflow, QeScfCandidateWorkflowCorrelation, "workflow"),
            (self.subject, QeScfCandidateSubject, "subject"),
            (self.input_lineage, QeScfCandidateInputLineage, "input_lineage"),
            (
                self.success_evidence,
                QeScfCandidateSuccessEvidence,
                "success_evidence",
            ),
            (self.saved_state, QeScfCandidateSavedState, "saved_state"),
            (self.terminal, QeScfCandidateTerminalCorrelation, "terminal"),
        )
        for value, expected_type, label in expected:
            if type(value) is not expected_type:
                raise TypeError(f"{label} must be {expected_type.__name__}")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateCandidateVerifier:
    """Verify exact retained records before a candidate may be referenced."""

    manifest_codec: QeSavedStateManifestJsonCodec = QeSavedStateManifestJsonCodec()

    def __post_init__(self) -> None:
        if type(self.manifest_codec) is not QeSavedStateManifestJsonCodec:
            raise TypeError("manifest_codec must be QeSavedStateManifestJsonCodec")

    def verify(
        self,
        *,
        candidate: QeScfSavedStateCandidate,
        manifest_payload: bytes,
        calculator_input: CalculatorInputRecord,
        simulation_evidence: SimulationEvidenceRecord,
        terminal_outcome: PwDftScfWorkflowSucceeded,
    ) -> QeSavedStateManifest:
        """Return the exact manifest after all available lineage checks pass."""
        if type(candidate) is not QeScfSavedStateCandidate:
            raise TypeError("candidate must be QeScfSavedStateCandidate")
        if type(manifest_payload) is not bytes:
            raise TypeError("manifest_payload must be bytes")
        if type(calculator_input) is not CalculatorInputRecord:
            raise TypeError("calculator_input must be CalculatorInputRecord")
        if type(simulation_evidence) is not SimulationEvidenceRecord:
            raise TypeError("simulation_evidence must be SimulationEvidenceRecord")
        if type(terminal_outcome) is not PwDftScfWorkflowSucceeded:
            raise TypeError("terminal_outcome must be PwDftScfWorkflowSucceeded")

        saved_state = candidate.saved_state
        if len(manifest_payload) != saved_state.manifest_byte_size:
            raise ValueError("manifest payload byte size differs from the candidate")
        if hashlib.sha256(manifest_payload).hexdigest() != saved_state.manifest_sha256:
            raise ValueError("manifest payload SHA-256 differs from the candidate")
        manifest = self.manifest_codec.loads(manifest_payload)
        if self.manifest_codec.dumps(manifest) != manifest_payload:
            raise ValueError("manifest payload is not canonical for its exact codec")

        lineage = candidate.input_lineage
        if lineage.calculator_input_record_sha256 != calculator_input.sha256:
            raise ValueError("calculator input record SHA-256 differs")
        if simulation_evidence.calculator_input_sha256 != calculator_input.sha256:
            raise ValueError("simulation evidence names another calculator input")
        if simulation_evidence.integration_id.value != "quantum-espresso":
            raise ValueError("simulation evidence is not from Quantum ESPRESSO")
        if not simulation_evidence.provider_completed:
            raise ValueError("simulation evidence does not establish completion")
        if not simulation_evidence.calculation_converged:
            raise ValueError("simulation evidence does not establish convergence")

        subject = candidate.subject
        result = terminal_outcome.result
        if simulation_evidence.evaluation_id != subject.evaluation_id:
            raise ValueError("simulation evidence evaluation differs")
        if simulation_evidence.task_id != subject.task_id:
            raise ValueError("simulation evidence task differs")
        if (
            result.evaluation_id != subject.evaluation_id
            or result.task_id != subject.task_id
        ):
            raise ValueError("terminal outcome subject differs")
        if not result.observation.completed or not result.observation.converged:
            raise ValueError("terminal observation is not complete and converged")

        rendered = lineage.rendered_input
        matching_input = tuple(
            artifact
            for artifact in calculator_input.artifacts
            if artifact.role == rendered.role and artifact.filename == rendered.filename
        )
        if len(matching_input) != 1:
            raise ValueError(
                "rendered input identity is not unique in the input record"
            )
        input_artifact = matching_input[0]
        if (
            input_artifact.byte_size != rendered.byte_size
            or input_artifact.sha256 != rendered.sha256
        ):
            raise ValueError("rendered input bytes differ from the input record")

        if manifest.calculation.value != saved_state.calculation:
            raise ValueError("manifest calculation differs from the candidate")
        if manifest.prefix != saved_state.prefix:
            raise ValueError("manifest prefix differs from the candidate")
        if manifest.input_sha256 != rendered.sha256:
            raise ValueError("manifest input differs from the rendered input")
        if manifest.structure_id != lineage.structure.structure_id:
            raise ValueError("manifest structure identity differs")
        if manifest.structure_sha256 != lineage.structure.sha256:
            raise ValueError("manifest structure bytes differ")
        if manifest.executable_sha256 != lineage.executable.sha256:
            raise ValueError("manifest executable bytes differ")
        if manifest.producer_version != lineage.executable.reported_version:
            raise ValueError("manifest executable version differs")
        if len(manifest.artifacts) != saved_state.artifact_count:
            raise ValueError("manifest artifact count differs")
        if sum(artifact.byte_size for artifact in manifest.artifacts) != (
            saved_state.total_byte_size
        ):
            raise ValueError("manifest total byte size differs")

        candidate_pseudopotentials = tuple(
            (
                value.element_symbol,
                value.filename,
                value.sha256,
                value.byte_size,
            )
            for value in lineage.pseudopotentials
        )
        manifest_pseudopotentials = tuple(
            (value.symbol, value.filename, value.sha256, value.byte_size)
            for value in manifest.pseudopotentials
        )
        if candidate_pseudopotentials != manifest_pseudopotentials:
            raise ValueError("manifest pseudopotentials differ from the candidate")
        requirements = tuple(
            (
                value.element_symbol,
                value.stable_id,
                value.filename,
                value.format,
                value.sha256,
                value.byte_size,
                value.provenance,
            )
            for value in calculator_input.external_requirements
        )
        candidate_requirements = tuple(
            (
                value.element_symbol,
                value.stable_file_identity,
                value.filename,
                value.format,
                value.sha256,
                value.byte_size,
                value.provenance_identity,
            )
            for value in lineage.pseudopotentials
        )
        if requirements != candidate_requirements:
            raise ValueError("input pseudopotential requirements differ")
        return manifest


@dataclass(frozen=True, slots=True)
class QeScfSavedStateCandidateEncodingMetadata:
    """Carry pure owner metadata needed for outer reference assembly."""

    payload_identity: str
    schema_identity: str
    media_type: str
    codec_identity: str

    def __post_init__(self) -> None:
        if not self.payload_identity.startswith(_CANDIDATE_IDENTITY_PREFIX):
            raise ValueError("payload_identity has the wrong candidate prefix")
        suffix = self.payload_identity.removeprefix(_CANDIDATE_IDENTITY_PREFIX)
        _sha256(suffix, "payload_identity digest")
        if self.schema_identity != _SCHEMA_IDENTITY:
            raise ValueError("schema_identity differs from the candidate schema")
        if self.media_type != _MEDIA_TYPE:
            raise ValueError("media_type differs from the candidate media type")
        if self.codec_identity != _CODEC_IDENTITY:
            raise ValueError("codec_identity differs from the candidate codec")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateCandidateJsonCodec:
    """Encode and decode the closed version-one candidate without effects."""

    def encode_canonical(
        self,
        candidate: QeScfSavedStateCandidate,
    ) -> tuple[bytes, QeScfSavedStateCandidateEncodingMetadata]:
        """Return canonical bytes and owner metadata without retaining them."""
        if type(candidate) is not QeScfSavedStateCandidate:
            raise TypeError("candidate must be QeScfSavedStateCandidate")
        payload = json.dumps(
            self._document(candidate),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        self._validate_document_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        return payload, QeScfSavedStateCandidateEncodingMetadata(
            payload_identity=f"{_CANDIDATE_IDENTITY_PREFIX}{digest}",
            schema_identity=_SCHEMA_IDENTITY,
            media_type=_MEDIA_TYPE,
            codec_identity=_CODEC_IDENTITY,
        )

    def decode_canonical(self, payload: bytes) -> QeScfSavedStateCandidate:
        """Decode exact canonical bytes or fail closed without repairing them."""
        self._validate_document_bytes(payload)
        try:
            document = json.loads(payload, object_pairs_hook=self._object_pairs)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("candidate must be valid UTF-8 JSON") from error
        self._validate_depth(document, depth=1)
        candidate = self._candidate(self._mapping(document, "candidate"))
        encoded, _ = self.encode_canonical(candidate)
        if encoded != payload:
            raise ValueError("candidate bytes are not canonical")
        return candidate

    def _document(self, candidate: QeScfSavedStateCandidate) -> dict[str, object]:
        producer = candidate.producer
        workflow = candidate.workflow
        subject = candidate.subject
        lineage = candidate.input_lineage
        success = candidate.success_evidence
        saved_state = candidate.saved_state
        terminal = candidate.terminal
        return {
            "candidate_kind": candidate.candidate_kind,
            "input_lineage": {
                "calculator_input_record_reference_identity": (
                    lineage.calculator_input_record_reference_identity
                ),
                "calculator_input_record_sha256": (
                    lineage.calculator_input_record_sha256
                ),
                "executable": {
                    "artifact_identity": lineage.executable.artifact_identity,
                    "byte_size": lineage.executable.byte_size,
                    "payload_reference_identity": (
                        lineage.executable.payload_reference_identity
                    ),
                    "program": lineage.executable.program,
                    "reported_version": lineage.executable.reported_version,
                    "sha256": lineage.executable.sha256,
                },
                "pseudopotentials": [
                    {
                        "byte_size": item.byte_size,
                        "element_symbol": item.element_symbol,
                        "filename": item.filename,
                        "format": item.format,
                        "payload_reference_identity": item.payload_reference_identity,
                        "provenance_identity": item.provenance_identity,
                        "sha256": item.sha256,
                        "stable_file_identity": item.stable_file_identity,
                    }
                    for item in lineage.pseudopotentials
                ],
                "rendered_input": {
                    "byte_size": lineage.rendered_input.byte_size,
                    "filename": lineage.rendered_input.filename,
                    "role": lineage.rendered_input.role,
                    "sha256": lineage.rendered_input.sha256,
                },
                "structure": {
                    "byte_size": lineage.structure.byte_size,
                    "payload_reference_identity": (
                        lineage.structure.payload_reference_identity
                    ),
                    "representation": lineage.structure.representation,
                    "schema_version": lineage.structure.schema_version,
                    "sha256": lineage.structure.sha256,
                    "structure_id": lineage.structure.structure_id,
                },
            },
            "producer": {
                "adapter_identity": producer.adapter_identity,
                "adapter_version": producer.adapter_version,
                "integration_identity": producer.integration_identity,
                "source_revision": producer.source_revision,
            },
            "saved_state": {
                "artifact_count": saved_state.artifact_count,
                "artifact_set_identity": saved_state.artifact_set_identity,
                "calculation": saved_state.calculation,
                "manifest_artifact_identity": saved_state.manifest_artifact_identity,
                "manifest_byte_size": saved_state.manifest_byte_size,
                "manifest_reference_identity": saved_state.manifest_reference_identity,
                "manifest_sha256": saved_state.manifest_sha256,
                "prefix": saved_state.prefix,
                "source_verification_evidence_identity": (
                    saved_state.source_verification_evidence_identity
                ),
                "total_byte_size": saved_state.total_byte_size,
            },
            "schema_identity": candidate.schema_identity,
            "schema_version": candidate.schema_version,
            "subject": {
                "evaluation_id": subject.evaluation_id,
                "simulation_specification_reference_identity": (
                    subject.simulation_specification_reference_identity
                ),
                "task_id": subject.task_id,
            },
            "success_evidence": {
                "calculation_converged": success.calculation_converged,
                "calculator_execution_record_reference_identity": (
                    success.calculator_execution_record_reference_identity
                ),
                "execution_status": success.execution_status,
                "normalized_observation_reference_identity": (
                    success.normalized_observation_reference_identity
                ),
                "provider_completed": success.provider_completed,
                "returncode": success.returncode,
                "simulation_evidence_reference_identity": (
                    success.simulation_evidence_reference_identity
                ),
            },
            "terminal": {
                "child_definition_identity": terminal.child_definition_identity,
                "terminal_classification": terminal.terminal_classification,
                "terminal_history_head_identity": (
                    terminal.terminal_history_head_identity
                ),
                "terminal_outcome_reference_identity": (
                    terminal.terminal_outcome_reference_identity
                ),
                "terminal_place_identity": terminal.terminal_place_identity,
                "terminal_transition_occurrence_identity": (
                    terminal.terminal_transition_occurrence_identity
                ),
            },
            "workflow": {
                "calculator_attempt_identity": workflow.calculator_attempt_identity,
                "calculator_dispatch_authorization_identity": (
                    workflow.calculator_dispatch_authorization_identity
                ),
                "calculator_effect_intent_identity": (
                    workflow.calculator_effect_intent_identity
                ),
                "calculator_execution_evidence_identity": (
                    workflow.calculator_execution_evidence_identity
                ),
                "calculator_plan_identity": workflow.calculator_plan_identity,
                "calculator_request_identity": workflow.calculator_request_identity,
                "calculator_transition_occurrence_identity": (
                    workflow.calculator_transition_occurrence_identity
                ),
                "child_execution_plan_identity": workflow.child_execution_plan_identity,
                "child_export_identity": workflow.child_export_identity,
                "child_net_instance_identity": workflow.child_net_instance_identity,
                "child_run_identity": workflow.child_run_identity,
            },
        }

    def _candidate(self, root: dict[str, object]) -> QeScfSavedStateCandidate:
        self._closed_keys(
            root,
            {
                "schema_identity",
                "schema_version",
                "candidate_kind",
                "producer",
                "workflow",
                "subject",
                "input_lineage",
                "success_evidence",
                "saved_state",
                "terminal",
            },
            "candidate",
        )
        if self._string(root["schema_identity"], "schema_identity") != _SCHEMA_IDENTITY:
            raise ValueError("schema_identity differs from the candidate schema")
        if self._integer(root["schema_version"], "schema_version") != 1:
            raise ValueError("schema_version must be one")
        if self._string(root["candidate_kind"], "candidate_kind") != _CANDIDATE_KIND:
            raise ValueError("candidate_kind differs from the candidate schema")
        return QeScfSavedStateCandidate(
            producer=self._producer(self._mapping(root["producer"], "producer")),
            workflow=self._workflow(self._mapping(root["workflow"], "workflow")),
            subject=self._subject(self._mapping(root["subject"], "subject")),
            input_lineage=self._input_lineage(
                self._mapping(root["input_lineage"], "input_lineage")
            ),
            success_evidence=self._success(
                self._mapping(root["success_evidence"], "success_evidence")
            ),
            saved_state=self._saved_state(
                self._mapping(root["saved_state"], "saved_state")
            ),
            terminal=self._terminal(self._mapping(root["terminal"], "terminal")),
        )

    def _producer(self, item: dict[str, object]) -> QeScfCandidateProducer:
        fields = {
            "integration_identity",
            "adapter_identity",
            "adapter_version",
            "source_revision",
        }
        self._closed_keys(item, fields, "producer")
        return QeScfCandidateProducer(
            integration_identity=self._string(
                item["integration_identity"], "integration_identity"
            ),
            adapter_identity=self._string(item["adapter_identity"], "adapter_identity"),
            adapter_version=self._string(item["adapter_version"], "adapter_version"),
            source_revision=self._string(item["source_revision"], "source_revision"),
        )

    def _workflow(self, item: dict[str, object]) -> QeScfCandidateWorkflowCorrelation:
        fields = {
            "child_export_identity",
            "child_execution_plan_identity",
            "child_run_identity",
            "child_net_instance_identity",
            "calculator_request_identity",
            "calculator_transition_occurrence_identity",
            "calculator_plan_identity",
            "calculator_effect_intent_identity",
            "calculator_attempt_identity",
            "calculator_dispatch_authorization_identity",
            "calculator_execution_evidence_identity",
        }
        self._closed_keys(item, fields, "workflow")
        return QeScfCandidateWorkflowCorrelation(
            **{field: self._string(item[field], field) for field in fields}
        )

    def _subject(self, item: dict[str, object]) -> QeScfCandidateSubject:
        fields = {
            "evaluation_id",
            "task_id",
            "simulation_specification_reference_identity",
        }
        self._closed_keys(item, fields, "subject")
        return QeScfCandidateSubject(
            evaluation_id=self._string(item["evaluation_id"], "evaluation_id"),
            task_id=self._string(item["task_id"], "task_id"),
            simulation_specification_reference_identity=self._string(
                item["simulation_specification_reference_identity"],
                "simulation_specification_reference_identity",
            ),
        )

    def _input_lineage(self, item: dict[str, object]) -> QeScfCandidateInputLineage:
        fields = {
            "calculator_input_record_reference_identity",
            "calculator_input_record_sha256",
            "rendered_input",
            "structure",
            "executable",
            "pseudopotentials",
        }
        self._closed_keys(item, fields, "input_lineage")
        pseudopotentials = self._array(item["pseudopotentials"], "pseudopotentials")
        return QeScfCandidateInputLineage(
            calculator_input_record_reference_identity=self._string(
                item["calculator_input_record_reference_identity"],
                "calculator_input_record_reference_identity",
            ),
            calculator_input_record_sha256=self._string(
                item["calculator_input_record_sha256"],
                "calculator_input_record_sha256",
            ),
            rendered_input=self._rendered_input(
                self._mapping(item["rendered_input"], "rendered_input")
            ),
            structure=self._structure(self._mapping(item["structure"], "structure")),
            executable=self._executable(
                self._mapping(item["executable"], "executable")
            ),
            pseudopotentials=tuple(
                self._pseudopotential(
                    self._mapping(value, f"pseudopotentials[{index}]")
                )
                for index, value in enumerate(pseudopotentials)
            ),
        )

    def _rendered_input(self, item: dict[str, object]) -> QeScfCandidateRenderedInput:
        self._closed_keys(
            item, {"role", "filename", "byte_size", "sha256"}, "rendered_input"
        )
        return QeScfCandidateRenderedInput(
            role=self._string(item["role"], "role"),
            filename=self._string(item["filename"], "filename"),
            byte_size=self._integer(item["byte_size"], "byte_size"),
            sha256=self._string(item["sha256"], "sha256"),
        )

    def _structure(self, item: dict[str, object]) -> QeScfCandidateStructure:
        fields = {
            "structure_id",
            "representation",
            "schema_version",
            "byte_size",
            "sha256",
            "payload_reference_identity",
        }
        self._closed_keys(item, fields, "structure")
        return QeScfCandidateStructure(
            structure_id=self._string(item["structure_id"], "structure_id"),
            representation=self._string(item["representation"], "representation"),
            schema_version=self._integer(item["schema_version"], "schema_version"),
            byte_size=self._integer(item["byte_size"], "byte_size"),
            sha256=self._string(item["sha256"], "sha256"),
            payload_reference_identity=self._string(
                item["payload_reference_identity"], "payload_reference_identity"
            ),
        )

    def _executable(self, item: dict[str, object]) -> QeScfCandidateExecutable:
        fields = {
            "program",
            "reported_version",
            "byte_size",
            "sha256",
            "artifact_identity",
            "payload_reference_identity",
        }
        self._closed_keys(item, fields, "executable")
        return QeScfCandidateExecutable(
            program=self._string(item["program"], "program"),
            reported_version=self._string(item["reported_version"], "reported_version"),
            byte_size=self._integer(item["byte_size"], "byte_size"),
            sha256=self._string(item["sha256"], "sha256"),
            artifact_identity=self._string(
                item["artifact_identity"], "artifact_identity"
            ),
            payload_reference_identity=self._string(
                item["payload_reference_identity"], "payload_reference_identity"
            ),
        )

    def _pseudopotential(
        self, item: dict[str, object]
    ) -> QeScfCandidatePseudopotential:
        fields = {
            "element_symbol",
            "stable_file_identity",
            "filename",
            "format",
            "byte_size",
            "sha256",
            "provenance_identity",
            "payload_reference_identity",
        }
        self._closed_keys(item, fields, "pseudopotential")
        return QeScfCandidatePseudopotential(
            element_symbol=self._string(item["element_symbol"], "element_symbol"),
            stable_file_identity=self._string(
                item["stable_file_identity"], "stable_file_identity"
            ),
            filename=self._string(item["filename"], "filename"),
            format=self._string(item["format"], "format"),
            byte_size=self._integer(item["byte_size"], "byte_size"),
            sha256=self._string(item["sha256"], "sha256"),
            provenance_identity=self._string(
                item["provenance_identity"], "provenance_identity"
            ),
            payload_reference_identity=self._string(
                item["payload_reference_identity"], "payload_reference_identity"
            ),
        )

    def _success(self, item: dict[str, object]) -> QeScfCandidateSuccessEvidence:
        fields = {
            "calculator_execution_record_reference_identity",
            "simulation_evidence_reference_identity",
            "normalized_observation_reference_identity",
            "execution_status",
            "returncode",
            "provider_completed",
            "calculation_converged",
        }
        self._closed_keys(item, fields, "success_evidence")
        return QeScfCandidateSuccessEvidence(
            calculator_execution_record_reference_identity=self._string(
                item["calculator_execution_record_reference_identity"],
                "calculator_execution_record_reference_identity",
            ),
            simulation_evidence_reference_identity=self._string(
                item["simulation_evidence_reference_identity"],
                "simulation_evidence_reference_identity",
            ),
            normalized_observation_reference_identity=self._string(
                item["normalized_observation_reference_identity"],
                "normalized_observation_reference_identity",
            ),
            execution_status=self._string(item["execution_status"], "execution_status"),
            returncode=self._integer(item["returncode"], "returncode"),
            provider_completed=self._boolean(
                item["provider_completed"], "provider_completed"
            ),
            calculation_converged=self._boolean(
                item["calculation_converged"], "calculation_converged"
            ),
        )

    def _saved_state(self, item: dict[str, object]) -> QeScfCandidateSavedState:
        fields = {
            "calculation",
            "prefix",
            "manifest_reference_identity",
            "manifest_artifact_identity",
            "manifest_sha256",
            "manifest_byte_size",
            "artifact_set_identity",
            "artifact_count",
            "total_byte_size",
            "source_verification_evidence_identity",
        }
        self._closed_keys(item, fields, "saved_state")
        return QeScfCandidateSavedState(
            calculation=self._string(item["calculation"], "calculation"),
            prefix=self._string(item["prefix"], "prefix"),
            manifest_reference_identity=self._string(
                item["manifest_reference_identity"], "manifest_reference_identity"
            ),
            manifest_artifact_identity=self._string(
                item["manifest_artifact_identity"], "manifest_artifact_identity"
            ),
            manifest_sha256=self._string(item["manifest_sha256"], "manifest_sha256"),
            manifest_byte_size=self._integer(
                item["manifest_byte_size"], "manifest_byte_size"
            ),
            artifact_set_identity=self._string(
                item["artifact_set_identity"], "artifact_set_identity"
            ),
            artifact_count=self._integer(item["artifact_count"], "artifact_count"),
            total_byte_size=self._integer(item["total_byte_size"], "total_byte_size"),
            source_verification_evidence_identity=self._string(
                item["source_verification_evidence_identity"],
                "source_verification_evidence_identity",
            ),
        )

    def _terminal(self, item: dict[str, object]) -> QeScfCandidateTerminalCorrelation:
        fields = {
            "child_definition_identity",
            "terminal_transition_occurrence_identity",
            "terminal_place_identity",
            "terminal_classification",
            "terminal_outcome_reference_identity",
            "terminal_history_head_identity",
        }
        self._closed_keys(item, fields, "terminal")
        return QeScfCandidateTerminalCorrelation(
            child_definition_identity=self._string(
                item["child_definition_identity"], "child_definition_identity"
            ),
            terminal_transition_occurrence_identity=self._string(
                item["terminal_transition_occurrence_identity"],
                "terminal_transition_occurrence_identity",
            ),
            terminal_place_identity=self._string(
                item["terminal_place_identity"], "terminal_place_identity"
            ),
            terminal_classification=self._string(
                item["terminal_classification"], "terminal_classification"
            ),
            terminal_outcome_reference_identity=self._string(
                item["terminal_outcome_reference_identity"],
                "terminal_outcome_reference_identity",
            ),
            terminal_history_head_identity=self._string(
                item["terminal_history_head_identity"],
                "terminal_history_head_identity",
            ),
        )

    def _validate_document_bytes(self, payload: bytes) -> None:
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        if not payload or len(payload) > _MAX_DOCUMENT_BYTES:
            raise ValueError("candidate document must contain 1..262144 bytes")
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("candidate document must not contain a UTF-8 BOM")

    def _object_pairs(self, pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def _validate_depth(self, value: object, *, depth: int) -> None:
        if depth > _MAX_DOCUMENT_DEPTH:
            raise ValueError("candidate JSON nesting exceeds depth six")
        if type(value) is dict:
            for child in value.values():
                self._validate_depth(child, depth=depth + 1)
        elif type(value) is list:
            for child in value:
                self._validate_depth(child, depth=depth + 1)

    def _mapping(self, value: object, label: str) -> dict[str, object]:
        if type(value) is not dict or any(type(key) is not str for key in value):
            raise TypeError(f"{label} must be an object with string keys")
        return value

    def _array(self, value: object, label: str) -> list[object]:
        if type(value) is not list:
            raise TypeError(f"{label} must be an array")
        return value

    def _closed_keys(
        self,
        value: dict[str, object],
        expected: set[str],
        label: str,
    ) -> None:
        actual = set(value)
        if actual != expected:
            raise ValueError(
                f"{label} keys differ: missing={sorted(expected - actual)!r}, "
                f"unexpected={sorted(actual - expected)!r}"
            )

    def _string(self, value: object, label: str) -> str:
        if type(value) is not str:
            raise TypeError(f"{label} must be a string")
        return value

    def _integer(self, value: object, label: str) -> int:
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer")
        return value

    def _boolean(self, value: object, label: str) -> bool:
        if type(value) is not bool:
            raise TypeError(f"{label} must be a Boolean")
        return value
