"""Owner-controlled immutable input source for the QE saved-state Workflow action."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from string import hexdigits
from typing import final

from projectkoios.integrations.quantumespresso.pw.scf import (
    saved_state_artifact_set_workflow as owner_workflow,
)
from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set import (
    QeScfSavedStateArtifactSetProjectionRequest,
)
from projectkoios.workflow.actions import (
    ExperimentalWorkflowInputSourceProfileIdentity,
)
from projectkoios.workflow.runtime import (
    ExperimentalWorkflowPureActionInputSourceEvidence,
    ExperimentalWorkflowPureActionInputSourceLoadResult,
    ExperimentalWorkflowPureActionInputSourceLoadStatus,
    ExperimentalWorkflowPureActionInputSourceReference,
    ExperimentalWorkflowPureActionInputSourceRepository,
    ExperimentalWorkflowPureActionInputSourceRevisionIdentity,
)
from projectkoios.workflow_sdk.payloads import WorkflowInlinePayload

QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND = (
    "qe-scf-saved-state-artifact-set-projection-request"
)
QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE = (
    ExperimentalWorkflowInputSourceProfileIdentity(
        "projectkoios.simulations.qe-scf-saved-state-artifact-set-projection-request:1"
    )
)

_SOURCE_IDENTITY_PREFIX = "qe-scf-saved-state-projection-request.sha256."
_MAX_PAYLOAD_BYTES = 4 * 1024 * 1024


class _CorruptSourceError(Exception):
    pass


@final
@dataclass(frozen=True, slots=True)
class QeScfSavedStateProjectionRequestSourceRepository(
    ExperimentalWorkflowPureActionInputSourceRepository
):
    """Retain and resolve immutable canonical owner requests by content identity.

    Private filesystem paths remain inside this owner adapter. Workflow receives
    only an opaque content-derived source identity and the canonical request bytes.
    """

    root: Path

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("root must be pathlib.Path")
        object.__setattr__(self, "root", self.root.expanduser().resolve(strict=False))

    def retain(
        self,
        request: QeScfSavedStateArtifactSetProjectionRequest,
    ) -> ExperimentalWorkflowPureActionInputSourceReference:
        """Atomically retain one canonical request without replacing revisions."""
        codec = owner_workflow.QeScfSavedStateArtifactSetProjectionRequestJsonCodec()
        payload = codec.encode(request)
        digest = hashlib.sha256(payload).hexdigest()
        reference = self._reference(digest)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = self._path(digest)
        temporary_path: str | None = None
        descriptor: int | None = None
        try:
            descriptor, temporary_path = tempfile.mkstemp(
                prefix=".pending-",
                suffix=".json",
                dir=self.root,
            )
            os.fchmod(descriptor, 0o600)
            _write_all(descriptor, payload)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            try:
                os.link(temporary_path, target, follow_symlinks=False)
            except FileExistsError:
                if self._read_payload(target) != payload:
                    raise ValueError(
                        "retained source identity conflicts with existing bytes"
                    ) from None
            _fsync_directory(self.root)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temporary_path is not None:
                with suppress(FileNotFoundError):
                    os.unlink(temporary_path)
        return reference

    def load(
        self,
        reference: ExperimentalWorkflowPureActionInputSourceReference,
    ) -> ExperimentalWorkflowPureActionInputSourceLoadResult:
        """Resolve exact canonical bytes and classify every bounded failure."""
        if type(reference) is not ExperimentalWorkflowPureActionInputSourceReference:
            raise TypeError(
                "reference must be ExperimentalWorkflowPureActionInputSourceReference"
            )
        if (
            reference.source_kind != QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND
            or reference.source_profile_identity
            != QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE
        ):
            return _failure(
                reference, "incompatible_source_contract", incompatible=True
            )
        digest = _source_digest(reference.source_identity)
        if digest is None:
            return _failure(
                reference, "incompatible_source_identity", incompatible=True
            )
        try:
            payload = self._read_payload(self._path(digest))
        except FileNotFoundError:
            return _failure(reference, "source_absent")
        except _CorruptSourceError:
            return _failure(reference, "source_corrupt", corrupt=True)
        except OSError:
            return _failure(reference, "source_repository_error", error=True)
        if hashlib.sha256(payload).hexdigest() != digest:
            return _failure(reference, "source_digest_mismatch", corrupt=True)
        try:
            codec = (
                owner_workflow.QeScfSavedStateArtifactSetProjectionRequestJsonCodec()
            )
            codec.decode(payload)
        except TypeError, ValueError:
            return _failure(reference, "source_payload_invalid", corrupt=True)
        contract = (
            owner_workflow.QE_SCF_SAVED_STATE_ARTIFACT_SET_PROJECTION_REQUEST_CONTRACT
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
            payload_sha256=digest,
        )
        evidence = ExperimentalWorkflowPureActionInputSourceEvidence(
            source_kind=reference.source_kind,
            source_profile_identity=reference.source_profile_identity,
            source_identity=reference.source_identity,
            payload=inline,
        )
        return ExperimentalWorkflowPureActionInputSourceLoadResult(
            status=ExperimentalWorkflowPureActionInputSourceLoadStatus.LOADED,
            reference=reference,
            revision_identity=(
                ExperimentalWorkflowPureActionInputSourceRevisionIdentity(
                    evidence.identity.value
                )
            ),
            evidence=evidence,
            diagnostics=(),
        )

    def _reference(
        self,
        digest: str,
    ) -> ExperimentalWorkflowPureActionInputSourceReference:
        return ExperimentalWorkflowPureActionInputSourceReference(
            source_kind=QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND,
            source_profile_identity=(
                QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE
            ),
            source_identity=f"{_SOURCE_IDENTITY_PREFIX}{digest}",
        )

    def _path(self, digest: str) -> Path:
        return self.root / f"{digest}.json"

    def _read_payload(self, path: Path) -> bytes:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise _CorruptSourceError("source is not a regular file")
            if not 1 <= metadata.st_size <= _MAX_PAYLOAD_BYTES:
                raise _CorruptSourceError("source byte size is outside bounds")
            chunks: list[bytes] = []
            remaining = _MAX_PAYLOAD_BYTES + 1
            while remaining:
                chunk = os.read(descriptor, min(remaining, 64 * 1024))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            payload = b"".join(chunks)
            if len(payload) != metadata.st_size or len(payload) > _MAX_PAYLOAD_BYTES:
                raise _CorruptSourceError("source changed during bounded read")
            return payload
        finally:
            os.close(descriptor)


def _failure(
    reference: ExperimentalWorkflowPureActionInputSourceReference,
    diagnostic: str,
    *,
    incompatible: bool = False,
    corrupt: bool = False,
    error: bool = False,
) -> ExperimentalWorkflowPureActionInputSourceLoadResult:
    status = ExperimentalWorkflowPureActionInputSourceLoadStatus.ABSENT
    if incompatible:
        status = ExperimentalWorkflowPureActionInputSourceLoadStatus.INCOMPATIBLE
    elif corrupt:
        status = ExperimentalWorkflowPureActionInputSourceLoadStatus.CORRUPT
    elif error:
        status = ExperimentalWorkflowPureActionInputSourceLoadStatus.ERROR
    return ExperimentalWorkflowPureActionInputSourceLoadResult(
        status=status,
        reference=reference,
        revision_identity=None,
        evidence=None,
        diagnostics=(diagnostic,),
    )


def _source_digest(source_identity: str) -> str | None:
    if not source_identity.startswith(_SOURCE_IDENTITY_PREFIX):
        return None
    digest = source_identity.removeprefix(_SOURCE_IDENTITY_PREFIX)
    if (
        len(digest) != 64
        or digest != digest.lower()
        or any(character not in hexdigits for character in digest)
    ):
        return None
    return digest


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("failed to retain source bytes")
        view = view[written:]


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND",
    "QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE",
    "QeScfSavedStateProjectionRequestSourceRepository",
]
