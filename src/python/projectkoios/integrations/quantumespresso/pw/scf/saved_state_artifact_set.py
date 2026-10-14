"""Pure QE SCF saved-state artifact-set records, codecs, and projection."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from projectkoios.integrations.quantumespresso.pw.scf.saved_state_candidate import (
    QeScfCandidateSavedState,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
)
from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject

_SCHEMA_IDENTITY_VALUE = (
    "projectkoios.integrations.quantumespresso.qe-pw-scf-saved-state-artifact-set:1"
)
_CODEC_IDENTITY_VALUE = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-json:1"
)
_IDENTITY_PROFILE_VALUE = (
    "projectkoios.integrations.quantumespresso."
    "qe-pw-scf-saved-state-artifact-set-semantic-identity:1"
)
_MEDIA_TYPE = "application/vnd.projectkoios.qe-pw-scf-saved-state-artifact-set.v1+json"
_ARTIFACT_SET_IDENTITY_PREFIX = f"{_IDENTITY_PROFILE_VALUE}:"
_MAX_ARTIFACTS = 4096
_MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
_MAX_DOCUMENT_DEPTH = 6
_MAX_IDENTITY_BYTES = 512
_MAX_PSEUDOPOTENTIALS = 256
_MAX_PREFIX_BYTES = 128
_MAX_RELATIVE_PATH_BYTES = 512
_MAX_TOTAL_BYTE_SIZE = 64 * 1024 * 1024 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_URI_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
_DRIVE_PREFIX = re.compile(r"[A-Za-z]:")
_SAFE_PREFIX = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def _validate_path_free_identity(value: str, label: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be nonempty and stripped")
    try:
        payload = value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"{label} must contain ASCII only") from error
    if len(payload) > _MAX_IDENTITY_BYTES:
        raise ValueError(f"{label} exceeds {_MAX_IDENTITY_BYTES} ASCII bytes")
    if any(byte < 0x20 or byte == 0x7F for byte in payload):
        raise ValueError(f"{label} must not contain controls or DEL")
    lowered = value.lower()
    if (
        value.startswith(("/", "~", "\\\\", "./", "../"))
        or value in {".", ".."}
        or "\\" in value
        or lowered.startswith("file:")
        or _DRIVE_PREFIX.match(value) is not None
        or ("/" in value and _URI_SCHEME.match(value) is None)
    ):
        raise ValueError(f"{label} must not be a machine path")


def _validate_sha256(value: str, label: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256")


def _validate_relative_path(value: str) -> None:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("relative_path must be a canonical relative POSIX path")
    try:
        payload = value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("relative_path must contain UTF-8 scalar values") from error
    if len(payload) > _MAX_RELATIVE_PATH_BYTES:
        raise ValueError(
            f"relative_path exceeds {_MAX_RELATIVE_PATH_BYTES} UTF-8 bytes"
        )
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path == PurePosixPath(".")
        or ".." in path.parts
        or str(path) != value
    ):
        raise ValueError("relative_path must be a canonical relative POSIX path")


def _validate_prefix(value: str) -> None:
    if (
        type(value) is not str
        or _SAFE_PREFIX.fullmatch(value) is None
        or len(value.encode("ascii")) > _MAX_PREFIX_BYTES
    ):
        raise ValueError("prefix must be a safe ASCII name of at most 128 bytes")


def _consume_manifest_json_string_budget(
    value: str,
    label: str,
    remaining: int,
) -> int:
    if len(value) > remaining:
        raise ValueError("manifest string content exceeds the 16-MiB JSON budget")
    size = 0
    for character in value:
        code_point = ord(character)
        if 0xD800 <= code_point <= 0xDFFF:
            raise ValueError(f"{label} must contain UTF-8 scalar values")
        if code_point in {8, 9, 10, 12, 13, 34, 92}:
            size += 2
        elif code_point <= 0x1F or 0x80 <= code_point <= 0xFFFF:
            size += 6
        elif code_point > 0xFFFF:
            size += 12
        else:
            size += 1
        if size > remaining:
            raise ValueError("manifest string content exceeds the 16-MiB JSON budget")
    return remaining - size


def _validate_manifest_encoding_budget(manifest: QeSavedStateManifest) -> None:
    remaining = _MAX_DOCUMENT_BYTES
    for label, value in (
        ("manifest.prefix", manifest.prefix),
        ("manifest.calculation", manifest.calculation.value),
        ("manifest.producer_program", manifest.producer_program),
        ("manifest.producer_version", manifest.producer_version),
        ("manifest.executable_sha256", manifest.executable_sha256),
        ("manifest.input_sha256", manifest.input_sha256),
        ("manifest.structure_id", manifest.structure_id),
        ("manifest.structure_sha256", manifest.structure_sha256),
    ):
        remaining = _consume_manifest_json_string_budget(value, label, remaining)
    for index, pseudopotential in enumerate(manifest.pseudopotentials):
        for label, value in (
            (f"manifest.pseudopotentials[{index}].symbol", pseudopotential.symbol),
            (
                f"manifest.pseudopotentials[{index}].filename",
                pseudopotential.filename,
            ),
            (f"manifest.pseudopotentials[{index}].sha256", pseudopotential.sha256),
        ):
            remaining = _consume_manifest_json_string_budget(value, label, remaining)
    for index, artifact in enumerate(manifest.artifacts):
        for label, value in (
            (f"manifest.artifacts[{index}].role", artifact.role.value),
            (f"manifest.artifacts[{index}].relative_path", artifact.relative_path),
            (f"manifest.artifacts[{index}].sha256", artifact.sha256),
        ):
            remaining = _consume_manifest_json_string_budget(value, label, remaining)


@dataclass(frozen=True, slots=True)
class QeScfSavedStateArtifactSetSchemaIdentity(DataObject):
    """Identify the provider-owned artifact-set document schema."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "schema identity")
        if self.value != _SCHEMA_IDENTITY_VALUE:
            raise ValueError("schema identity is not the artifact-set schema")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateArtifactSetCodecIdentity(DataObject):
    """Identify the exact canonical JSON codec contract."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "codec identity")
        if self.value != _CODEC_IDENTITY_VALUE:
            raise ValueError("codec identity is not the artifact-set JSON codec")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateArtifactSetIdentityProfile(DataObject):
    """Identify the semantic preimage used for logical identity derivation."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "identity profile")
        if self.value != _IDENTITY_PROFILE_VALUE:
            raise ValueError("identity profile is not the artifact-set profile")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateArtifactSetIdentity(DataObject):
    """Identify exact saved-state semantics independently of retention placement."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "artifact-set identity")
        if not self.value.startswith(_ARTIFACT_SET_IDENTITY_PREFIX):
            raise ValueError("artifact-set identity has the wrong prefix")
        _validate_sha256(
            self.value.removeprefix(_ARTIFACT_SET_IDENTITY_PREFIX),
            "artifact-set semantic digest",
        )


@dataclass(frozen=True, slots=True)
class QeScfSavedStateRetentionReference(DataObject):
    """Carry one externally issued opaque path-free retention reference."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "retention reference")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateManifestArtifactIdentity(DataObject):
    """Carry the outer owner's logical identity for the retained manifest."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "manifest artifact identity")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateVerificationEvidenceIdentity(DataObject):
    """Carry the outer owner's identity for source-verification evidence."""

    value: str

    def __post_init__(self) -> None:
        _validate_path_free_identity(self.value, "verification evidence identity")


@dataclass(frozen=True, slots=True)
class QeScfSavedStateRetainedArtifact(DataObject):
    """Bind one manifest member to an externally retained payload reference."""

    role: QeSavedStateArtifactRole
    relative_path: str
    sha256: str
    byte_size: int
    payload_reference: QeScfSavedStateRetentionReference

    def __post_init__(self) -> None:
        if type(self.role) is not QeSavedStateArtifactRole:
            raise TypeError("role must be a QeSavedStateArtifactRole")
        _validate_relative_path(self.relative_path)
        _validate_sha256(self.sha256, "artifact sha256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")
        if type(self.payload_reference) is not QeScfSavedStateRetentionReference:
            raise TypeError(
                "payload_reference must be a QeScfSavedStateRetentionReference"
            )


@dataclass(frozen=True, slots=True)
class QeScfSavedStateArtifactSetRecord(DataObject):
    """Record one immutable SCF saved-state set without machine paths."""

    calculation: QeSavedStateCalculation
    prefix: str
    manifest_reference: QeScfSavedStateRetentionReference
    manifest_artifact_identity: QeScfSavedStateManifestArtifactIdentity
    manifest_sha256: str
    manifest_byte_size: int
    retained_artifacts: tuple[QeScfSavedStateRetainedArtifact, ...]
    source_verification_evidence_identity: QeScfSavedStateVerificationEvidenceIdentity

    def __post_init__(self) -> None:
        if self.calculation is not QeSavedStateCalculation.scf:
            raise ValueError("calculation must be scf")
        _validate_prefix(self.prefix)
        if type(self.manifest_reference) is not QeScfSavedStateRetentionReference:
            raise TypeError(
                "manifest_reference must be a QeScfSavedStateRetentionReference"
            )
        if (
            type(self.manifest_artifact_identity)
            is not QeScfSavedStateManifestArtifactIdentity
        ):
            raise TypeError(
                "manifest_artifact_identity must be a "
                "QeScfSavedStateManifestArtifactIdentity"
            )
        _validate_sha256(self.manifest_sha256, "manifest sha256")
        if type(self.manifest_byte_size) is not int or self.manifest_byte_size <= 0:
            raise ValueError("manifest_byte_size must be positive")
        if (
            type(self.retained_artifacts) is not tuple
            or not self.retained_artifacts
            or len(self.retained_artifacts) > _MAX_ARTIFACTS
        ):
            raise ValueError("retained_artifacts must contain 1..4096 records")
        if any(
            type(value) is not QeScfSavedStateRetainedArtifact
            for value in self.retained_artifacts
        ):
            raise TypeError(
                "retained_artifacts must contain QeScfSavedStateRetainedArtifact values"
            )
        paths = tuple(value.relative_path for value in self.retained_artifacts)
        if len(paths) != len(set(paths)):
            raise ValueError("retained artifact relative paths must be unique")
        prefix_directory = f"{self.prefix}.save"
        if any(
            PurePosixPath(value.relative_path).parts[0] != prefix_directory
            for value in self.retained_artifacts
        ):
            raise ValueError("retained artifacts must reside in the prefix save tree")
        roles = tuple(value.role for value in self.retained_artifacts)
        if roles.count(QeSavedStateArtifactRole.qexsd) != 1:
            raise ValueError("artifact set requires exactly one QEXSD artifact")
        if roles.count(QeSavedStateArtifactRole.charge_density) != 1:
            raise ValueError(
                "artifact set requires exactly one charge-density artifact"
            )
        if QeSavedStateArtifactRole.wavefunction not in roles:
            raise ValueError("artifact set requires wavefunction artifacts")
        if QeSavedStateArtifactRole.pseudopotential not in roles:
            raise ValueError("artifact set requires pseudopotential artifacts")
        if self.total_byte_size > _MAX_TOTAL_BYTE_SIZE:
            raise ValueError("artifact set total byte size exceeds 64 GiB")
        bindings: dict[str, tuple[str, int]] = {
            self.manifest_reference.value: (
                self.manifest_sha256,
                self.manifest_byte_size,
            )
        }
        for artifact in self.retained_artifacts:
            previous = bindings.setdefault(
                artifact.payload_reference.value,
                (artifact.sha256, artifact.byte_size),
            )
            if previous != (artifact.sha256, artifact.byte_size):
                raise ValueError(
                    "one retention reference must not identify different bytes"
                )
        if (
            type(self.source_verification_evidence_identity)
            is not QeScfSavedStateVerificationEvidenceIdentity
        ):
            raise TypeError(
                "source_verification_evidence_identity must be a "
                "QeScfSavedStateVerificationEvidenceIdentity"
            )
        QeScfSavedStateArtifactSetCanonicalCodec()._encode_record(self)

    @property
    def artifact_count(self) -> int:
        """Return the exact number of ordered manifest members."""
        return len(self.retained_artifacts)

    @property
    def total_byte_size(self) -> int:
        """Return the manifest-declared byte total without deduplication."""
        return sum(value.byte_size for value in self.retained_artifacts)


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetEncodingRequest(DataObject):
    """Request canonical encoding of one admitted artifact-set record."""

    artifact_set: QeScfSavedStateArtifactSetRecord

    def __post_init__(self) -> None:
        if type(self.artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetDecodingRequest(DataObject):
    """Request strict decoding of one bounded canonical payload."""

    payload: bytes

    def __post_init__(self) -> None:
        if (
            type(self.payload) is not bytes
            or not self.payload
            or len(self.payload) > _MAX_DOCUMENT_BYTES
        ):
            raise ValueError("payload must contain 1..16777216 bytes")
        if self.payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("payload must not contain a UTF-8 BOM")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetEncodingResult(ResultsObject):
    """Bind canonical bytes and byte evidence to the exact encoding request."""

    request: QeScfSavedStateArtifactSetEncodingRequest
    payload: bytes
    schema_identity: QeScfSavedStateArtifactSetSchemaIdentity
    codec_identity: QeScfSavedStateArtifactSetCodecIdentity
    media_type: str
    payload_byte_size: int
    payload_sha256: str

    def __post_init__(self) -> None:
        if type(self.request) is not QeScfSavedStateArtifactSetEncodingRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetEncodingRequest"
            )
        expected = QeScfSavedStateArtifactSetCanonicalCodec()._encode_record(
            self.request.artifact_set
        )
        if self.payload != expected:
            raise ValueError("payload does not canonically encode the request")
        if self.schema_identity != QeScfSavedStateArtifactSetSchemaIdentity(
            _SCHEMA_IDENTITY_VALUE
        ):
            raise ValueError("schema_identity differs from the codec schema")
        if self.codec_identity != QeScfSavedStateArtifactSetCodecIdentity(
            _CODEC_IDENTITY_VALUE
        ):
            raise ValueError("codec_identity differs from the canonical codec")
        if self.media_type != _MEDIA_TYPE:
            raise ValueError("media_type differs from the canonical codec")
        if self.payload_byte_size != len(self.payload):
            raise ValueError("payload_byte_size differs from the payload")
        _validate_sha256(self.payload_sha256, "payload_sha256")
        if self.payload_sha256 != hashlib.sha256(self.payload).hexdigest():
            raise ValueError("payload_sha256 differs from the payload")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetDecodingResult(ResultsObject):
    """Bind one exact canonical payload to its reconstructed owner record."""

    request: QeScfSavedStateArtifactSetDecodingRequest
    artifact_set: QeScfSavedStateArtifactSetRecord
    schema_identity: QeScfSavedStateArtifactSetSchemaIdentity
    codec_identity: QeScfSavedStateArtifactSetCodecIdentity
    media_type: str
    payload_byte_size: int
    payload_sha256: str

    def __post_init__(self) -> None:
        if type(self.request) is not QeScfSavedStateArtifactSetDecodingRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetDecodingRequest"
            )
        if type(self.artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")
        expected = QeScfSavedStateArtifactSetCanonicalCodec()._encode_record(
            self.artifact_set
        )
        if self.request.payload != expected:
            raise ValueError("artifact_set does not match the canonical payload")
        if self.schema_identity != QeScfSavedStateArtifactSetSchemaIdentity(
            _SCHEMA_IDENTITY_VALUE
        ):
            raise ValueError("schema_identity differs from the codec schema")
        if self.codec_identity != QeScfSavedStateArtifactSetCodecIdentity(
            _CODEC_IDENTITY_VALUE
        ):
            raise ValueError("codec_identity differs from the canonical codec")
        if self.media_type != _MEDIA_TYPE:
            raise ValueError("media_type differs from the canonical codec")
        if self.payload_byte_size != len(self.request.payload):
            raise ValueError("payload_byte_size differs from the payload")
        _validate_sha256(self.payload_sha256, "payload_sha256")
        if self.payload_sha256 != hashlib.sha256(self.request.payload).hexdigest():
            raise ValueError("payload_sha256 differs from the payload")


class QeScfSavedStateArtifactSetCanonicalCodec:
    """Encode and decode one closed provider-owned artifact-set document."""

    __slots__ = ()

    def encode(
        self,
        request: QeScfSavedStateArtifactSetEncodingRequest,
    ) -> QeScfSavedStateArtifactSetEncodingResult:
        """Return canonical bytes without retention effects or authority issuance."""
        if type(request) is not QeScfSavedStateArtifactSetEncodingRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetEncodingRequest"
            )
        payload = self._encode_record(request.artifact_set)
        return QeScfSavedStateArtifactSetEncodingResult(
            request=request,
            payload=payload,
            schema_identity=QeScfSavedStateArtifactSetSchemaIdentity(
                _SCHEMA_IDENTITY_VALUE
            ),
            codec_identity=QeScfSavedStateArtifactSetCodecIdentity(
                _CODEC_IDENTITY_VALUE
            ),
            media_type=_MEDIA_TYPE,
            payload_byte_size=len(payload),
            payload_sha256=hashlib.sha256(payload).hexdigest(),
        )

    def decode(
        self,
        request: QeScfSavedStateArtifactSetDecodingRequest,
    ) -> QeScfSavedStateArtifactSetDecodingResult:
        """Strictly reconstruct the exact owner record from canonical bytes."""
        if type(request) is not QeScfSavedStateArtifactSetDecodingRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetDecodingRequest"
            )
        try:
            document = json.loads(
                request.payload,
                object_pairs_hook=self._object_pairs,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("payload must be valid UTF-8 JSON") from error
        except RecursionError as error:
            raise ValueError("payload exceeds maximum JSON depth") from error
        self._validate_depth(document, depth=1)
        root = self._mapping(document, "artifact set")
        self._closed_keys(
            root,
            {
                "artifacts",
                "calculation",
                "manifest",
                "prefix",
                "schema_identity",
                "source_verification_evidence_identity",
            },
            "artifact set",
        )
        if self._string(root["schema_identity"], "schema_identity") != (
            _SCHEMA_IDENTITY_VALUE
        ):
            raise ValueError("schema_identity is not the artifact-set schema")
        manifest = self._mapping(root["manifest"], "manifest")
        self._closed_keys(
            manifest,
            {
                "artifact_identity",
                "byte_size",
                "reference",
                "sha256",
            },
            "manifest",
        )
        artifacts = self._array(root["artifacts"], "artifacts")
        artifact_set = QeScfSavedStateArtifactSetRecord(
            calculation=QeSavedStateCalculation(
                self._string(root["calculation"], "calculation")
            ),
            prefix=self._string(root["prefix"], "prefix"),
            manifest_reference=QeScfSavedStateRetentionReference(
                self._string(manifest["reference"], "manifest reference")
            ),
            manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
                self._string(
                    manifest["artifact_identity"],
                    "manifest artifact identity",
                )
            ),
            manifest_sha256=self._string(manifest["sha256"], "manifest sha256"),
            manifest_byte_size=self._integer(
                manifest["byte_size"],
                "manifest byte_size",
            ),
            retained_artifacts=tuple(
                self._artifact(self._mapping(value, f"artifacts[{index}]"))
                for index, value in enumerate(artifacts)
            ),
            source_verification_evidence_identity=(
                QeScfSavedStateVerificationEvidenceIdentity(
                    self._string(
                        root["source_verification_evidence_identity"],
                        "source verification evidence identity",
                    )
                )
            ),
        )
        if self._encode_record(artifact_set) != request.payload:
            raise ValueError("payload is not the exact canonical encoding")
        return QeScfSavedStateArtifactSetDecodingResult(
            request=request,
            artifact_set=artifact_set,
            schema_identity=QeScfSavedStateArtifactSetSchemaIdentity(
                _SCHEMA_IDENTITY_VALUE
            ),
            codec_identity=QeScfSavedStateArtifactSetCodecIdentity(
                _CODEC_IDENTITY_VALUE
            ),
            media_type=_MEDIA_TYPE,
            payload_byte_size=len(request.payload),
            payload_sha256=hashlib.sha256(request.payload).hexdigest(),
        )

    def _encode_record(self, artifact_set: QeScfSavedStateArtifactSetRecord) -> bytes:
        if type(artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")
        document = {
            "artifacts": [
                {
                    "byte_size": artifact.byte_size,
                    "payload_reference": artifact.payload_reference.value,
                    "relative_path": artifact.relative_path,
                    "role": artifact.role.value,
                    "sha256": artifact.sha256,
                }
                for artifact in artifact_set.retained_artifacts
            ],
            "calculation": artifact_set.calculation.value,
            "manifest": {
                "artifact_identity": artifact_set.manifest_artifact_identity.value,
                "byte_size": artifact_set.manifest_byte_size,
                "reference": artifact_set.manifest_reference.value,
                "sha256": artifact_set.manifest_sha256,
            },
            "prefix": artifact_set.prefix,
            "schema_identity": _SCHEMA_IDENTITY_VALUE,
            "source_verification_evidence_identity": (
                artifact_set.source_verification_evidence_identity.value
            ),
        }
        payload = json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if not payload or len(payload) > _MAX_DOCUMENT_BYTES:
            raise ValueError("encoded payload must contain 1..16777216 bytes")
        return payload

    def _artifact(
        self,
        item: dict[str, object],
    ) -> QeScfSavedStateRetainedArtifact:
        self._closed_keys(
            item,
            {
                "byte_size",
                "payload_reference",
                "relative_path",
                "role",
                "sha256",
            },
            "artifact",
        )
        return QeScfSavedStateRetainedArtifact(
            role=QeSavedStateArtifactRole(self._string(item["role"], "artifact role")),
            relative_path=self._string(
                item["relative_path"],
                "artifact relative_path",
            ),
            sha256=self._string(item["sha256"], "artifact sha256"),
            byte_size=self._integer(item["byte_size"], "artifact byte_size"),
            payload_reference=QeScfSavedStateRetentionReference(
                self._string(
                    item["payload_reference"],
                    "artifact payload_reference",
                )
            ),
        )

    def _object_pairs(self, pairs: list[tuple[str, object]]) -> dict[str, object]:
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
            for nested in value.values():
                self._validate_depth(nested, depth + 1)
        elif type(value) is list:
            for nested in value:
                self._validate_depth(nested, depth + 1)

    def _mapping(self, value: object, label: str) -> dict[str, object]:
        if type(value) is not dict:
            raise TypeError(f"{label} must be an object")
        if any(type(key) is not str for key in value):
            raise TypeError(f"{label} keys must be strings")
        return value

    def _array(self, value: object, label: str) -> list[object]:
        if type(value) is not list:
            raise TypeError(f"{label} must be an array")
        return value

    def _string(self, value: object, label: str) -> str:
        if type(value) is not str:
            raise TypeError(f"{label} must be a string")
        return value

    def _integer(self, value: object, label: str) -> int:
        if type(value) is not int:
            raise TypeError(f"{label} must be an integer")
        return value

    def _closed_keys(
        self,
        item: dict[str, object],
        expected: set[str],
        label: str,
    ) -> None:
        actual = set(item)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(f"{label} keys differ; missing={missing}, extra={extra}")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetIdentityDerivationRequest(DataObject):
    """Request logical identity derivation for one admitted owner record."""

    artifact_set: QeScfSavedStateArtifactSetRecord

    def __post_init__(self) -> None:
        if type(self.artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetIdentityDerivationResult(ResultsObject):
    """Bind one semantic preimage and logical identity to the exact request."""

    request: QeScfSavedStateArtifactSetIdentityDerivationRequest
    identity_profile: QeScfSavedStateArtifactSetIdentityProfile
    semantic_bytes: bytes
    semantic_sha256: str
    identity: QeScfSavedStateArtifactSetIdentity

    def __post_init__(self) -> None:
        if (
            type(self.request)
            is not QeScfSavedStateArtifactSetIdentityDerivationRequest
        ):
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetIdentityDerivationRequest"
            )
        if self.identity_profile != QeScfSavedStateArtifactSetIdentityProfile(
            _IDENTITY_PROFILE_VALUE
        ):
            raise ValueError("identity_profile differs from the semantic profile")
        expected = QeScfSavedStateArtifactSetIdentityDeriver()._semantic_bytes(
            self.request.artifact_set
        )
        if self.semantic_bytes != expected:
            raise ValueError("semantic_bytes differ from the exact request")
        _validate_sha256(self.semantic_sha256, "semantic_sha256")
        if self.semantic_sha256 != hashlib.sha256(self.semantic_bytes).hexdigest():
            raise ValueError("semantic_sha256 differs from semantic_bytes")
        expected_identity = QeScfSavedStateArtifactSetIdentity(
            f"{_ARTIFACT_SET_IDENTITY_PREFIX}{self.semantic_sha256}"
        )
        if self.identity != expected_identity:
            raise ValueError("identity differs from the semantic projection")


class QeScfSavedStateArtifactSetIdentityDeriver(
    DataObjectActionizer[
        QeScfSavedStateArtifactSetIdentityDerivationRequest,
        QeScfSavedStateArtifactSetIdentityDerivationResult,
    ]
):
    """Derive retention-independent identity from versioned saved-state semantics."""

    __slots__ = ()

    def action(
        self,
        *,
        request: QeScfSavedStateArtifactSetIdentityDerivationRequest,
    ) -> QeScfSavedStateArtifactSetIdentityDerivationResult:
        """Return the closed semantic preimage and its domain-separated identity."""
        if type(request) is not QeScfSavedStateArtifactSetIdentityDerivationRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetIdentityDerivationRequest"
            )
        semantic_bytes = self._semantic_bytes(request.artifact_set)
        semantic_sha256 = hashlib.sha256(semantic_bytes).hexdigest()
        return QeScfSavedStateArtifactSetIdentityDerivationResult(
            request=request,
            identity_profile=QeScfSavedStateArtifactSetIdentityProfile(
                _IDENTITY_PROFILE_VALUE
            ),
            semantic_bytes=semantic_bytes,
            semantic_sha256=semantic_sha256,
            identity=QeScfSavedStateArtifactSetIdentity(
                f"{_ARTIFACT_SET_IDENTITY_PREFIX}{semantic_sha256}"
            ),
        )

    def _semantic_bytes(
        self,
        artifact_set: QeScfSavedStateArtifactSetRecord,
    ) -> bytes:
        if type(artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")
        document = {
            "artifacts": [
                {
                    "byte_size": artifact.byte_size,
                    "relative_path": artifact.relative_path,
                    "role": artifact.role.value,
                    "sha256": artifact.sha256,
                }
                for artifact in artifact_set.retained_artifacts
            ],
            "calculation": artifact_set.calculation.value,
            "identity_profile": _IDENTITY_PROFILE_VALUE,
            "manifest": {
                "byte_size": artifact_set.manifest_byte_size,
                "sha256": artifact_set.manifest_sha256,
            },
            "prefix": artifact_set.prefix,
        }
        return json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetProjectionRequest(DataObject):
    """Supply canonical manifest bytes and already-retained payload references."""

    manifest: QeSavedStateManifest
    manifest_payload: bytes
    manifest_reference: QeScfSavedStateRetentionReference
    manifest_artifact_identity: QeScfSavedStateManifestArtifactIdentity
    retained_artifacts: tuple[QeScfSavedStateRetainedArtifact, ...]
    source_verification_evidence_identity: QeScfSavedStateVerificationEvidenceIdentity

    def __post_init__(self) -> None:
        if type(self.manifest) is not QeSavedStateManifest:
            raise TypeError("manifest must be a QeSavedStateManifest")
        if (
            type(self.manifest_payload) is not bytes
            or not self.manifest_payload
            or len(self.manifest_payload) > _MAX_DOCUMENT_BYTES
        ):
            raise ValueError("manifest_payload must contain 1..16777216 bytes")
        if type(self.manifest_reference) is not QeScfSavedStateRetentionReference:
            raise TypeError(
                "manifest_reference must be a QeScfSavedStateRetentionReference"
            )
        if (
            type(self.manifest_artifact_identity)
            is not QeScfSavedStateManifestArtifactIdentity
        ):
            raise TypeError(
                "manifest_artifact_identity must be a "
                "QeScfSavedStateManifestArtifactIdentity"
            )
        if type(self.retained_artifacts) is not tuple:
            raise TypeError("retained_artifacts must be a tuple")
        if any(
            type(value) is not QeScfSavedStateRetainedArtifact
            for value in self.retained_artifacts
        ):
            raise TypeError(
                "retained_artifacts must contain QeScfSavedStateRetainedArtifact values"
            )
        if (
            type(self.source_verification_evidence_identity)
            is not QeScfSavedStateVerificationEvidenceIdentity
        ):
            raise TypeError(
                "source_verification_evidence_identity must be a "
                "QeScfSavedStateVerificationEvidenceIdentity"
            )
        if self.manifest.calculation is not QeSavedStateCalculation.scf:
            raise ValueError("artifact-set projection requires an SCF manifest")
        if not 1 <= len(self.manifest.pseudopotentials) <= _MAX_PSEUDOPOTENTIALS:
            raise ValueError("SCF manifest must contain 1..256 pseudopotentials")
        for pseudopotential in self.manifest.pseudopotentials:
            filename = pseudopotential.filename
            if (
                type(filename) is not str
                or _SAFE_PREFIX.fullmatch(filename) is None
                or len(filename.encode("ascii")) > 255
            ):
                raise ValueError(
                    "pseudopotential filename must be a safe ASCII basename of at "
                    "most 255 bytes"
                )
        if len(self.manifest.artifacts) > _MAX_ARTIFACTS:
            raise ValueError("retained_artifacts must contain 1..4096 records")
        if (
            sum(artifact.byte_size for artifact in self.manifest.artifacts)
            > _MAX_TOTAL_BYTE_SIZE
        ):
            raise ValueError("artifact set total byte size exceeds 64 GiB")
        _validate_manifest_encoding_budget(self.manifest)
        canonical_manifest = QeSavedStateManifestJsonCodec().dumps(self.manifest)
        if len(canonical_manifest) > _MAX_DOCUMENT_BYTES:
            raise ValueError("canonical manifest exceeds 16777216 bytes")
        if canonical_manifest != self.manifest_payload:
            raise ValueError("manifest_payload is not the exact canonical manifest")
        expected_artifacts = tuple(
            (
                artifact.role,
                artifact.relative_path,
                artifact.sha256,
                artifact.byte_size,
            )
            for artifact in self.manifest.artifacts
        )
        retained_artifacts = tuple(
            (
                artifact.role,
                artifact.relative_path,
                artifact.sha256,
                artifact.byte_size,
            )
            for artifact in self.retained_artifacts
        )
        if retained_artifacts != expected_artifacts:
            raise ValueError(
                "retained artifacts differ from the ordered manifest artifacts"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfSavedStateArtifactSetProjectionResult(ResultsObject):
    """Correlate one projection with its record, identity, and candidate fragment."""

    request: QeScfSavedStateArtifactSetProjectionRequest
    artifact_set: QeScfSavedStateArtifactSetRecord
    artifact_set_identity: QeScfSavedStateArtifactSetIdentity
    candidate_saved_state: QeScfCandidateSavedState

    def __post_init__(self) -> None:
        if type(self.request) is not QeScfSavedStateArtifactSetProjectionRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetProjectionRequest"
            )
        if type(self.artifact_set) is not QeScfSavedStateArtifactSetRecord:
            raise TypeError("artifact_set must be a QeScfSavedStateArtifactSetRecord")
        if type(self.artifact_set_identity) is not QeScfSavedStateArtifactSetIdentity:
            raise TypeError(
                "artifact_set_identity must be a QeScfSavedStateArtifactSetIdentity"
            )
        if type(self.candidate_saved_state) is not QeScfCandidateSavedState:
            raise TypeError("candidate_saved_state must be a QeScfCandidateSavedState")
        manifest_sha256 = hashlib.sha256(self.request.manifest_payload).hexdigest()
        if (
            self.artifact_set.calculation is not self.request.manifest.calculation
            or self.artifact_set.prefix != self.request.manifest.prefix
            or self.artifact_set.manifest_reference
            is not self.request.manifest_reference
            or self.artifact_set.manifest_artifact_identity
            is not self.request.manifest_artifact_identity
            or self.artifact_set.manifest_sha256 != manifest_sha256
            or self.artifact_set.manifest_byte_size
            != len(self.request.manifest_payload)
            or self.artifact_set.retained_artifacts
            is not self.request.retained_artifacts
            or self.artifact_set.source_verification_evidence_identity
            is not self.request.source_verification_evidence_identity
        ):
            raise ValueError("artifact_set does not retain the exact request")
        identity = (
            QeScfSavedStateArtifactSetIdentityDeriver()
            .action(
                request=QeScfSavedStateArtifactSetIdentityDerivationRequest(
                    artifact_set=self.artifact_set
                )
            )
            .identity
        )
        if self.artifact_set_identity != identity:
            raise ValueError("artifact_set_identity differs from the artifact set")
        candidate = self.candidate_saved_state
        if (
            candidate.calculation != self.artifact_set.calculation.value
            or candidate.prefix != self.artifact_set.prefix
            or candidate.manifest_reference_identity
            != self.artifact_set.manifest_reference.value
            or candidate.manifest_artifact_identity
            != self.artifact_set.manifest_artifact_identity.value
            or candidate.manifest_sha256 != self.artifact_set.manifest_sha256
            or candidate.manifest_byte_size != self.artifact_set.manifest_byte_size
            or candidate.artifact_set_identity != self.artifact_set_identity.value
            or candidate.artifact_count != self.artifact_set.artifact_count
            or candidate.total_byte_size != self.artifact_set.total_byte_size
            or candidate.source_verification_evidence_identity
            != self.artifact_set.source_verification_evidence_identity.value
        ):
            raise ValueError("candidate_saved_state does not describe the artifact set")


class QeScfSavedStateArtifactSetProjector(
    DataObjectActionizer[
        QeScfSavedStateArtifactSetProjectionRequest,
        QeScfSavedStateArtifactSetProjectionResult,
    ]
):
    """Project retained owner records without effects or Workflow access."""

    __slots__ = ()

    def action(
        self,
        *,
        request: QeScfSavedStateArtifactSetProjectionRequest,
    ) -> QeScfSavedStateArtifactSetProjectionResult:
        """Return the artifact set, logical identity, and candidate fragment."""
        if type(request) is not QeScfSavedStateArtifactSetProjectionRequest:
            raise TypeError(
                "request must be a QeScfSavedStateArtifactSetProjectionRequest"
            )
        artifact_set = QeScfSavedStateArtifactSetRecord(
            calculation=request.manifest.calculation,
            prefix=request.manifest.prefix,
            manifest_reference=request.manifest_reference,
            manifest_artifact_identity=request.manifest_artifact_identity,
            manifest_sha256=hashlib.sha256(request.manifest_payload).hexdigest(),
            manifest_byte_size=len(request.manifest_payload),
            retained_artifacts=request.retained_artifacts,
            source_verification_evidence_identity=(
                request.source_verification_evidence_identity
            ),
        )
        artifact_set_identity = (
            QeScfSavedStateArtifactSetIdentityDeriver()
            .action(
                request=QeScfSavedStateArtifactSetIdentityDerivationRequest(
                    artifact_set=artifact_set
                )
            )
            .identity
        )
        candidate_saved_state = QeScfCandidateSavedState(
            calculation=artifact_set.calculation.value,
            prefix=artifact_set.prefix,
            manifest_reference_identity=artifact_set.manifest_reference.value,
            manifest_artifact_identity=artifact_set.manifest_artifact_identity.value,
            manifest_sha256=artifact_set.manifest_sha256,
            manifest_byte_size=artifact_set.manifest_byte_size,
            artifact_set_identity=artifact_set_identity.value,
            artifact_count=artifact_set.artifact_count,
            total_byte_size=artifact_set.total_byte_size,
            source_verification_evidence_identity=(
                artifact_set.source_verification_evidence_identity.value
            ),
        )
        return QeScfSavedStateArtifactSetProjectionResult(
            request=request,
            artifact_set=artifact_set,
            artifact_set_identity=artifact_set_identity,
            candidate_saved_state=candidate_saved_state,
        )
