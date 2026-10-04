from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw2wannier90.provider import (
    QeWannier90PlaneWaveArtifactManifest,
    QeWannier90PlaneWaveManifestVerifier,
    QeWannier90ProviderArtifact,
    QeWannier90ProviderArtifactRole,
)


def _artifact(
    role: QeWannier90ProviderArtifactRole,
    path: str,
    *,
    kpoint_index: int | None = None,
    spin_channel_index: int | None = None,
) -> QeWannier90ProviderArtifact:
    return QeWannier90ProviderArtifact(
        role=role,
        relative_path=path,
        sha256="0" * 64,
        byte_size=1,
        kpoint_index=kpoint_index,
        spin_channel_index=spin_channel_index,
    )


def _manifest() -> QeWannier90PlaneWaveArtifactManifest:
    unks = tuple(
        _artifact(
            QeWannier90ProviderArtifactRole.unk,
            f"work/qe/UNK{index:05d}.1",
            kpoint_index=index,
            spin_channel_index=1,
        )
        for index in range(1, 65)
    )
    return QeWannier90PlaneWaveArtifactManifest(
        schema_version=1,
        run_id="silicon-example11-hminus-t-20261004T171505Z",
        qe_prefix="si",
        seedname="silicon",
        kpoint_count=64,
        band_count=12,
        wannier_count=4,
        spin_channel_count=1,
        selected_spin_channel_index=1,
        spinor_component_count=1,
        post_nscf_state_manifest=_artifact(
            QeWannier90ProviderArtifactRole.post_nscf_state_manifest,
            "manifests/qe-post-nscf-si.save.sha256.tsv",
        ),
        qexsd=_artifact(
            QeWannier90ProviderArtifactRole.qexsd,
            "work/qe/si.save/data-file-schema.xml",
        ),
        pseudopotentials=(
            _artifact(
                QeWannier90ProviderArtifactRole.pseudopotential,
                "pseudo/Si.pbe-n-van.UPF",
            ),
        ),
        wannier_input=_artifact(
            QeWannier90ProviderArtifactRole.wannier_input,
            "inputs/derived/silicon.win",
        ),
        neighbor_interface=_artifact(
            QeWannier90ProviderArtifactRole.neighbor_interface,
            "artifacts/wannier90/preprocess/silicon.nnkp",
        ),
        unks=unks,
        eigenvalues=_artifact(
            QeWannier90ProviderArtifactRole.eigenvalues,
            "work/qe/silicon.eig",
        ),
        gauge_matrix=_artifact(
            QeWannier90ProviderArtifactRole.gauge_matrix,
            "work/qe/silicon_u.mat",
        ),
        disentanglement_matrix=_artifact(
            QeWannier90ProviderArtifactRole.disentanglement_matrix,
            "work/qe/silicon_u_dis.mat",
        ),
        hamiltonian=_artifact(
            QeWannier90ProviderArtifactRole.hamiltonian,
            "artifacts/wannier90/localization/silicon_hr.dat",
        ),
    )


def test_manifest_closes_exact_preserved_inventory_shape() -> None:
    manifest = _manifest()

    assert len(manifest.unks) == 64
    assert manifest.unks[-1].kpoint_index == 64
    assert len(manifest.artifacts) == 73


def test_manifest_rejects_missing_unk() -> None:
    manifest = _manifest()

    with pytest.raises(ValueError, match="exactly one file"):
        replace(manifest, unks=manifest.unks[:-1])


def test_manifest_rejects_mixed_scalar_spin_channels() -> None:
    manifest = _manifest()
    wrong_channel = replace(
        manifest.unks[0],
        relative_path="work/qe/UNK00001.2",
        spin_channel_index=2,
    )

    with pytest.raises(ValueError, match="selected spin channel"):
        replace(manifest, unks=(wrong_channel, *manifest.unks[1:]))


def test_manifest_rejects_noncanonical_path() -> None:
    with pytest.raises(ValueError, match="safe relative POSIX path"):
        replace(_manifest().qexsd, relative_path="work//qe/data-file-schema.xml")


def test_verifier_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "post.tsv").write_bytes(b"x")
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    manifest = replace(
        _manifest(),
        post_nscf_state_manifest=_artifact(
            QeWannier90ProviderArtifactRole.post_nscf_state_manifest,
            "link/post.tsv",
        ),
    )

    with pytest.raises(ValueError, match="contains a symlink"):
        QeWannier90PlaneWaveManifestVerifier().verify(manifest, tmp_path)


def test_verifier_rejects_two_roles_bound_to_one_inode(tmp_path: Path) -> None:
    (tmp_path / "first").write_bytes(b"x")
    (tmp_path / "second").hardlink_to(tmp_path / "first")
    manifest = replace(
        _manifest(),
        post_nscf_state_manifest=replace(
            _artifact(
                QeWannier90ProviderArtifactRole.post_nscf_state_manifest,
                "first",
            ),
            sha256=hashlib.sha256(b"x").hexdigest(),
        ),
        qexsd=replace(
            _artifact(QeWannier90ProviderArtifactRole.qexsd, "second"),
            sha256=hashlib.sha256(b"x").hexdigest(),
        ),
    )

    with pytest.raises(ValueError, match="distinct files"):
        QeWannier90PlaneWaveManifestVerifier().verify(manifest, tmp_path)


def test_manifest_rejects_wrong_disentanglement_role() -> None:
    manifest = _manifest()

    with pytest.raises(ValueError, match="u_dis.mat"):
        replace(manifest, disentanglement_matrix=manifest.gauge_matrix)


def test_manifest_rejects_duplicate_path() -> None:
    manifest = _manifest()
    duplicate = replace(
        manifest.qexsd,
        relative_path=manifest.pseudopotentials[0].relative_path,
    )

    with pytest.raises(ValueError, match="paths must be unique"):
        replace(manifest, qexsd=duplicate)
