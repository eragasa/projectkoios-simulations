from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest import mock

import pytest

from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set import (
    QeScfSavedStateArtifactSetCanonicalCodec,
    QeScfSavedStateArtifactSetDecodingRequest,
    QeScfSavedStateArtifactSetEncodingRequest,
    QeScfSavedStateArtifactSetIdentity,
    QeScfSavedStateArtifactSetIdentityDerivationRequest,
    QeScfSavedStateArtifactSetIdentityDeriver,
    QeScfSavedStateArtifactSetProjectionRequest,
    QeScfSavedStateArtifactSetProjectionResult,
    QeScfSavedStateArtifactSetProjector,
    QeScfSavedStateArtifactSetRecord,
    QeScfSavedStateManifestArtifactIdentity,
    QeScfSavedStateRetainedArtifact,
    QeScfSavedStateRetentionReference,
    QeScfSavedStateVerificationEvidenceIdentity,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifact,
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
    QeSavedStatePseudopotential,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64
_MAX_SAVED_STATE_BYTES = 64 * 1024 * 1024 * 1024


def test_projects_owner_record_identity_and_exact_candidate_fragment() -> None:
    request = _request()

    with (
        mock.patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("projector must not read files"),
        ),
        mock.patch.object(
            Path,
            "open",
            side_effect=AssertionError("projector must not open files"),
        ),
        mock.patch.object(
            subprocess,
            "Popen",
            side_effect=AssertionError("projector must not start processes"),
        ),
    ):
        result = QeScfSavedStateArtifactSetProjector().action(request=request)

    artifact_set = result.artifact_set
    candidate = result.candidate_saved_state
    assert result.request is request
    assert artifact_set.retained_artifacts is request.retained_artifacts
    assert (
        artifact_set.manifest_sha256
        == hashlib.sha256(request.manifest_payload).hexdigest()
    )
    assert artifact_set.manifest_byte_size == len(request.manifest_payload)
    assert artifact_set.artifact_count == len(request.manifest.artifacts)
    assert artifact_set.total_byte_size == sum(
        artifact.byte_size for artifact in request.manifest.artifacts
    )
    assert type(result.artifact_set_identity) is QeScfSavedStateArtifactSetIdentity
    assert result.artifact_set_identity.value.endswith(
        QeScfSavedStateArtifactSetIdentityDeriver()
        .action(
            request=QeScfSavedStateArtifactSetIdentityDerivationRequest(
                artifact_set=artifact_set
            )
        )
        .semantic_sha256
    )
    assert candidate.calculation == artifact_set.calculation.value
    assert candidate.prefix == artifact_set.prefix
    assert candidate.manifest_reference_identity == (
        artifact_set.manifest_reference.value
    )
    assert candidate.manifest_artifact_identity == (
        artifact_set.manifest_artifact_identity.value
    )
    assert candidate.manifest_sha256 == artifact_set.manifest_sha256
    assert candidate.manifest_byte_size == artifact_set.manifest_byte_size
    assert candidate.artifact_set_identity == result.artifact_set_identity.value
    assert candidate.artifact_count == artifact_set.artifact_count
    assert candidate.total_byte_size == artifact_set.total_byte_size
    assert candidate.source_verification_evidence_identity == (
        artifact_set.source_verification_evidence_identity.value
    )


def test_logical_identity_excludes_retention_and_verification_metadata() -> None:
    first = QeScfSavedStateArtifactSetProjector().action(request=_request())
    request = _request()
    changed_artifacts = tuple(
        replace(
            artifact,
            payload_reference=QeScfSavedStateRetentionReference(
                f"other-retention:artifact:{index}"
            ),
        )
        for index, artifact in enumerate(request.retained_artifacts)
    )
    changed = QeScfSavedStateArtifactSetProjector().action(
        request=replace(
            request,
            manifest_reference=QeScfSavedStateRetentionReference(
                "other-retention:manifest"
            ),
            manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
                "other-owner:manifest"
            ),
            retained_artifacts=changed_artifacts,
            source_verification_evidence_identity=(
                QeScfSavedStateVerificationEvidenceIdentity(
                    "verification:saved-state:2"
                )
            ),
        )
    )

    assert changed.artifact_set_identity == first.artifact_set_identity
    first_encoding = QeScfSavedStateArtifactSetCanonicalCodec().encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=first.artifact_set)
    )
    changed_encoding = QeScfSavedStateArtifactSetCanonicalCodec().encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=changed.artifact_set)
    )
    assert changed_encoding.payload_sha256 != first_encoding.payload_sha256


def test_logical_identity_changes_with_saved_state_semantics() -> None:
    first = QeScfSavedStateArtifactSetProjector().action(request=_request())
    changed = QeScfSavedStateArtifactSetProjector().action(
        request=_request(_manifest(wavefunction_byte_size=4))
    )

    assert changed.artifact_set_identity != first.artifact_set_identity


def test_canonical_codec_round_trips_exact_owner_record() -> None:
    artifact_set = (
        QeScfSavedStateArtifactSetProjector().action(request=_request()).artifact_set
    )
    codec = QeScfSavedStateArtifactSetCanonicalCodec()

    encoded = codec.encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=artifact_set)
    )
    decoded = codec.decode(
        QeScfSavedStateArtifactSetDecodingRequest(payload=encoded.payload)
    )

    assert decoded.artifact_set == artifact_set
    assert decoded.payload_sha256 == encoded.payload_sha256
    assert decoded.payload_byte_size == encoded.payload_byte_size
    assert decoded.schema_identity == encoded.schema_identity
    assert decoded.codec_identity == encoded.codec_identity
    assert decoded.media_type == encoded.media_type


def test_record_rejects_manifest_reference_aliasing_different_member_bytes() -> None:
    request = _request()

    with pytest.raises(ValueError, match="must not identify different bytes"):
        QeScfSavedStateArtifactSetProjector().action(
            request=replace(
                request,
                manifest_reference=request.retained_artifacts[0].payload_reference,
            )
        )


def test_record_and_decoder_require_pseudopotential_artifacts() -> None:
    artifact_set = (
        QeScfSavedStateArtifactSetProjector().action(request=_request()).artifact_set
    )
    without_pseudopotential = tuple(
        artifact
        for artifact in artifact_set.retained_artifacts
        if artifact.role is not QeSavedStateArtifactRole.pseudopotential
    )

    with pytest.raises(ValueError, match="requires pseudopotential artifacts"):
        replace(artifact_set, retained_artifacts=without_pseudopotential)

    codec = QeScfSavedStateArtifactSetCanonicalCodec()
    payload = codec.encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=artifact_set)
    ).payload
    document = json.loads(payload)
    document["artifacts"] = [
        artifact
        for artifact in document["artifacts"]
        if artifact["role"] != QeSavedStateArtifactRole.pseudopotential.value
    ]
    invalid_payload = json.dumps(
        document,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    with pytest.raises(ValueError, match="requires pseudopotential artifacts"):
        codec.decode(QeScfSavedStateArtifactSetDecodingRequest(payload=invalid_payload))


def test_canonical_codec_rejects_noncanonical_and_duplicate_key_payloads() -> None:
    artifact_set = (
        QeScfSavedStateArtifactSetProjector().action(request=_request()).artifact_set
    )
    codec = QeScfSavedStateArtifactSetCanonicalCodec()
    payload = codec.encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=artifact_set)
    ).payload

    with pytest.raises(ValueError, match="exact canonical encoding"):
        codec.decode(QeScfSavedStateArtifactSetDecodingRequest(payload=payload + b" "))

    duplicate = payload.replace(
        b'{"artifacts":',
        (
            b'{"schema_identity":"projectkoios.integrations.quantumespresso.'
            b'qe-pw-scf-saved-state-artifact-set:1","artifacts":'
        ),
        1,
    )
    with pytest.raises(ValueError, match="duplicate JSON key: schema_identity"):
        codec.decode(QeScfSavedStateArtifactSetDecodingRequest(payload=duplicate))


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("unknown", "keys differ"),
        ("missing", "keys differ"),
        ("wrong-type", "prefix must be a string"),
    ],
)
def test_canonical_codec_rejects_closed_shape_mutations(
    mutation: str,
    match: str,
) -> None:
    artifact_set = (
        QeScfSavedStateArtifactSetProjector().action(request=_request()).artifact_set
    )
    codec = QeScfSavedStateArtifactSetCanonicalCodec()
    payload = codec.encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=artifact_set)
    ).payload
    document = json.loads(payload)
    if mutation == "unknown":
        document["unknown"] = None
    elif mutation == "missing":
        del document["prefix"]
    else:
        document["prefix"] = 1
    mutated = json.dumps(
        document,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    with pytest.raises((TypeError, ValueError), match=match):
        codec.decode(QeScfSavedStateArtifactSetDecodingRequest(payload=mutated))


def test_canonical_codec_rejects_bounded_payload_and_depth_failures() -> None:
    codec = QeScfSavedStateArtifactSetCanonicalCodec()

    with pytest.raises(ValueError, match="1..16777216 bytes"):
        QeScfSavedStateArtifactSetDecodingRequest(payload=b"")
    with pytest.raises(ValueError, match="UTF-8 BOM"):
        QeScfSavedStateArtifactSetDecodingRequest(payload=b"\xef\xbb\xbf{}")
    with pytest.raises(ValueError, match="1..16777216 bytes"):
        QeScfSavedStateArtifactSetDecodingRequest(payload=b"x" * (16 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="maximum JSON depth"):
        codec.decode(
            QeScfSavedStateArtifactSetDecodingRequest(payload=b"[[[[[[0]]]]]]")
        )
    with pytest.raises(ValueError, match="maximum JSON depth"):
        codec.decode(
            QeScfSavedStateArtifactSetDecodingRequest(
                payload=b"[" * 2000 + b"0" + b"]" * 2000
            )
        )


def test_record_rejects_unbounded_or_non_utf8_relative_paths() -> None:
    artifact = _request().retained_artifacts[0]

    with pytest.raises(ValueError, match="exceeds 512 UTF-8 bytes"):
        replace(artifact, relative_path=f"si.save/{'x' * 505}")
    with pytest.raises(ValueError, match="UTF-8 scalar values"):
        replace(artifact, relative_path="si.save/\ud800")


def test_projection_rejects_unbounded_manifest_before_comparison() -> None:
    request = _request()

    with pytest.raises(ValueError, match="1..16777216 bytes"):
        replace(request, manifest_payload=b"x" * (16 * 1024 * 1024 + 1))


def test_projection_preflights_typed_manifest_before_canonical_encoding() -> None:
    request = _request()
    oversized_manifest = replace(
        request.manifest,
        producer_version="x" * (16 * 1024 * 1024 + 1),
    )

    with pytest.raises(ValueError, match="manifest string content exceeds"):
        replace(request, manifest=oversized_manifest)


def test_public_operation_results_reject_mismatched_reconstruction() -> None:
    artifact_set = (
        QeScfSavedStateArtifactSetProjector().action(request=_request()).artifact_set
    )
    codec = QeScfSavedStateArtifactSetCanonicalCodec()
    encoded = codec.encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=artifact_set)
    )
    decoded = codec.decode(
        QeScfSavedStateArtifactSetDecodingRequest(payload=encoded.payload)
    )
    identity = QeScfSavedStateArtifactSetIdentityDeriver().action(
        request=QeScfSavedStateArtifactSetIdentityDerivationRequest(
            artifact_set=artifact_set
        )
    )

    with pytest.raises(ValueError, match="payload_sha256 differs"):
        replace(encoded, payload_sha256="0" * 64)
    with pytest.raises(ValueError, match="does not match the canonical payload"):
        replace(
            decoded,
            artifact_set=replace(
                artifact_set,
                source_verification_evidence_identity=(
                    QeScfSavedStateVerificationEvidenceIdentity(
                        "verification:saved-state:changed"
                    )
                ),
            ),
        )
    with pytest.raises(ValueError, match="semantic_sha256 differs"):
        replace(identity, semantic_sha256="0" * 64)


def test_rejects_noncanonical_or_different_manifest_bytes_at_request_boundary() -> None:
    request = _request()

    with pytest.raises(ValueError, match="exact canonical manifest"):
        replace(request, manifest_payload=request.manifest_payload + b" ")


@pytest.mark.parametrize("mutation", ["role", "path", "sha256", "size", "order"])
def test_rejects_retained_artifacts_that_differ_from_manifest_at_request_boundary(
    mutation: str,
) -> None:
    request = _request()
    artifacts = list(request.retained_artifacts)
    if mutation == "role":
        artifacts[0] = replace(artifacts[0], role=QeSavedStateArtifactRole.native)
    elif mutation == "path":
        artifacts[0] = replace(
            artifacts[0],
            relative_path="si.save/different.xml",
        )
    elif mutation == "sha256":
        artifacts[0] = replace(artifacts[0], sha256="0" * 64)
    elif mutation == "size":
        artifacts[0] = replace(artifacts[0], byte_size=999)
    else:
        artifacts[0], artifacts[1] = artifacts[1], artifacts[0]

    with pytest.raises(ValueError, match="ordered manifest artifacts"):
        replace(request, retained_artifacts=tuple(artifacts))


def test_direct_result_reconstruction_requires_a_validated_request() -> None:
    request = _request()
    artifacts = list(request.retained_artifacts)
    artifacts[0] = replace(artifacts[0], sha256="0" * 64)

    with pytest.raises(ValueError, match="ordered manifest artifacts"):
        QeScfSavedStateArtifactSetProjectionRequest(
            manifest=request.manifest,
            manifest_payload=request.manifest_payload,
            manifest_reference=request.manifest_reference,
            manifest_artifact_identity=request.manifest_artifact_identity,
            retained_artifacts=tuple(artifacts),
            source_verification_evidence_identity=(
                request.source_verification_evidence_identity
            ),
        )


@pytest.mark.parametrize(
    "identity",
    [
        "/tmp/payload",
        "~/payload",
        r"\\server\share",
        "file:///tmp/payload",
        r"C:\payload",
        "./payload",
        "../payload",
        "directory/payload",
        r"directory\payload",
    ],
)
def test_rejects_machine_path_retention_references(identity: str) -> None:
    with pytest.raises(ValueError, match="must not be a machine path"):
        QeScfSavedStateRetentionReference(identity)


@pytest.mark.parametrize("identity", ["évidence", "bad\nidentity", "x" * 513])
def test_rejects_unbounded_or_non_ascii_retention_references(
    identity: str,
) -> None:
    with pytest.raises(ValueError, match="ASCII only|controls|exceeds 512"):
        QeScfSavedStateRetentionReference(identity)


@pytest.mark.parametrize(
    "identity",
    ["artifact:namespace/member", "https://artifacts.example/member"],
)
def test_allows_qualified_non_file_retention_references(identity: str) -> None:
    request = _request()
    artifacts = list(request.retained_artifacts)
    artifacts[0] = replace(
        artifacts[0],
        payload_reference=QeScfSavedStateRetentionReference(identity),
    )

    result = QeScfSavedStateArtifactSetProjector().action(
        request=replace(request, retained_artifacts=tuple(artifacts))
    )

    assert result.artifact_set.retained_artifacts[0].payload_reference.value == identity


def test_rejects_one_retention_reference_bound_to_different_bytes() -> None:
    request = _request()
    artifacts = list(request.retained_artifacts)
    artifacts[1] = replace(
        artifacts[1],
        payload_reference=artifacts[0].payload_reference,
    )

    with pytest.raises(ValueError, match="must not identify different bytes"):
        QeScfSavedStateArtifactSetProjector().action(
            request=replace(request, retained_artifacts=tuple(artifacts))
        )


def test_allows_content_addressed_deduplication_of_identical_bytes() -> None:
    manifest = _manifest(
        extra_artifacts=(
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.native,
                relative_path="si.save/native-a.dat",
                sha256="e" * 64,
                byte_size=5,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.native,
                relative_path="si.save/native-b.dat",
                sha256="e" * 64,
                byte_size=5,
            ),
        )
    )
    request = _request(manifest)
    artifacts = list(request.retained_artifacts)
    artifacts[-1] = replace(
        artifacts[-1],
        payload_reference=artifacts[-2].payload_reference,
    )

    result = QeScfSavedStateArtifactSetProjector().action(
        request=replace(request, retained_artifacts=tuple(artifacts))
    )

    assert result.artifact_set.artifact_count == 6


def test_rejects_more_than_256_pseudopotentials() -> None:
    with pytest.raises(ValueError, match="1..256 pseudopotentials"):
        _request(_pseudopotential_manifest(257))


def test_rejects_pseudopotential_filenames_over_255_ascii_bytes() -> None:
    filename = f"{'x' * 252}.upf"

    with pytest.raises(ValueError, match="at most 255 bytes"):
        _request(_pseudopotential_manifest(1, filename=filename))


def test_rejects_more_than_4096_manifest_artifacts() -> None:
    extras = tuple(
        QeSavedStateArtifact(
            role=QeSavedStateArtifactRole.native,
            relative_path=f"si.save/native-{index}.dat",
            sha256=f"{index:064x}",
            byte_size=1,
        )
        for index in range(4093)
    )

    with pytest.raises(ValueError, match="1..4096"):
        _request(_manifest(extra_artifacts=extras))


def test_rejects_more_than_64_gib_declared_saved_state_bytes() -> None:
    with pytest.raises(ValueError, match="exceeds 64 GiB"):
        _request(_manifest(wavefunction_byte_size=_MAX_SAVED_STATE_BYTES))


def test_projection_result_rejects_request_candidate_or_identity_mutation() -> None:
    request = _request()
    result = QeScfSavedStateArtifactSetProjector().action(request=request)
    changed_request = replace(
        request,
        source_verification_evidence_identity=(
            QeScfSavedStateVerificationEvidenceIdentity("verification:saved-state:2")
        ),
    )

    with pytest.raises(ValueError, match="exact request"):
        QeScfSavedStateArtifactSetProjectionResult(
            request=changed_request,
            artifact_set=result.artifact_set,
            artifact_set_identity=result.artifact_set_identity,
            candidate_saved_state=result.candidate_saved_state,
        )
    with pytest.raises(ValueError, match="does not describe"):
        QeScfSavedStateArtifactSetProjectionResult(
            request=request,
            artifact_set=result.artifact_set,
            artifact_set_identity=result.artifact_set_identity,
            candidate_saved_state=replace(
                result.candidate_saved_state,
                artifact_set_identity="artifact-set:changed",
            ),
        )
    with pytest.raises(ValueError, match="differs from the artifact set"):
        QeScfSavedStateArtifactSetProjectionResult(
            request=request,
            artifact_set=result.artifact_set,
            artifact_set_identity=QeScfSavedStateArtifactSetIdentity(
                result.artifact_set_identity.value[:-64] + "0" * 64
            ),
            candidate_saved_state=result.candidate_saved_state,
        )


def _request(
    manifest: QeSavedStateManifest | None = None,
) -> QeScfSavedStateArtifactSetProjectionRequest:
    exact_manifest = manifest or _manifest()
    manifest_payload = QeSavedStateManifestJsonCodec().dumps(exact_manifest)
    retained_artifacts = tuple(
        QeScfSavedStateRetainedArtifact(
            role=artifact.role,
            relative_path=artifact.relative_path,
            sha256=artifact.sha256,
            byte_size=artifact.byte_size,
            payload_reference=QeScfSavedStateRetentionReference(
                f"payload-reference:artifact:{index}"
            ),
        )
        for index, artifact in enumerate(exact_manifest.artifacts)
    )
    return QeScfSavedStateArtifactSetProjectionRequest(
        manifest=exact_manifest,
        manifest_payload=manifest_payload,
        manifest_reference=QeScfSavedStateRetentionReference(
            "payload-reference:manifest"
        ),
        manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
            "artifact:manifest"
        ),
        retained_artifacts=retained_artifacts,
        source_verification_evidence_identity=(
            QeScfSavedStateVerificationEvidenceIdentity("verification:saved-state")
        ),
    )


def _manifest(
    *,
    wavefunction_byte_size: int = 3,
    extra_artifacts: tuple[QeSavedStateArtifact, ...] = (),
) -> QeSavedStateManifest:
    pseudopotential = QeSavedStatePseudopotential(
        symbol="Si",
        filename="Si.upf",
        sha256=_SHA_D,
        byte_size=4,
    )
    artifacts = (
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
            byte_size=wavefunction_byte_size,
        ),
        QeSavedStateArtifact(
            role=QeSavedStateArtifactRole.pseudopotential,
            relative_path="si.save/Si.upf",
            sha256=pseudopotential.sha256,
            byte_size=pseudopotential.byte_size,
        ),
        *extra_artifacts,
    )
    return QeSavedStateManifest(
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
        artifacts=artifacts,
    )


def _pseudopotential_manifest(
    count: int,
    *,
    filename: str | None = None,
) -> QeSavedStateManifest:
    pseudopotentials = tuple(
        QeSavedStatePseudopotential(
            symbol=f"X{index}",
            filename=(
                filename if index == 0 and filename is not None else f"X{index}.upf"
            ),
            sha256=f"{index:064x}",
            byte_size=index + 1,
        )
        for index in range(count)
    )
    pseudopotential_artifacts = tuple(
        QeSavedStateArtifact(
            role=QeSavedStateArtifactRole.pseudopotential,
            relative_path=f"si.save/{pseudopotential.filename}",
            sha256=pseudopotential.sha256,
            byte_size=pseudopotential.byte_size,
        )
        for pseudopotential in pseudopotentials
    )
    return QeSavedStateManifest(
        schema_version=1,
        prefix="si",
        calculation=QeSavedStateCalculation.scf,
        producer_program="pw.x",
        producer_version="7.5",
        executable_sha256="f" * 64,
        input_sha256="1" * 64,
        structure_id="Si.PrimitiveUnitCell",
        structure_sha256="2" * 64,
        pseudopotentials=pseudopotentials,
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
            *pseudopotential_artifacts,
        ),
    )


def test_record_is_public_data_object_and_codec_payload_is_path_free() -> None:
    result = QeScfSavedStateArtifactSetProjector().action(request=_request())
    encoded = QeScfSavedStateArtifactSetCanonicalCodec().encode(
        QeScfSavedStateArtifactSetEncodingRequest(artifact_set=result.artifact_set)
    )

    assert type(result.artifact_set) is QeScfSavedStateArtifactSetRecord
    assert b"/tmp/" not in encoded.payload
