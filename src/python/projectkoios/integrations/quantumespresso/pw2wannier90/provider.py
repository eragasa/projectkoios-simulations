"""Immutable artifact bindings for read-only QE/Wannier90 providers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_UNK_NAME = re.compile(r"UNK(?P<kpoint>[0-9]{5})\.(?P<spin>[1-9][0-9]*|NC)\Z")


class QeWannier90ProviderArtifactRole(StrEnum):
    """Identify one role in the closed plane-wave provider inventory."""

    post_nscf_state_manifest = "post-nscf-state-manifest"
    qexsd = "qexsd"
    pseudopotential = "pseudopotential"
    wannier_input = "win"
    neighbor_interface = "nnkp"
    unk = "unk"
    eigenvalues = "eig"
    gauge_matrix = "u.mat"
    disentanglement_matrix = "u_dis.mat"
    hamiltonian = "hr"


@dataclass(frozen=True, slots=True)
class QeWannier90ProviderArtifact:
    """Bind one run-root-relative artifact to exact bytes and semantic role."""

    role: QeWannier90ProviderArtifactRole
    relative_path: str
    sha256: str
    byte_size: int
    kpoint_index: int | None = None
    spin_channel_index: int | None = None

    def __post_init__(self) -> None:
        if type(self.role) is not QeWannier90ProviderArtifactRole:
            raise TypeError("role must be a QeWannier90ProviderArtifactRole")
        _validate_relative_path(self.relative_path)
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")
        if self.role is QeWannier90ProviderArtifactRole.unk:
            if type(self.kpoint_index) is not int or self.kpoint_index <= 0:
                raise ValueError("UNK artifacts require a positive kpoint_index")
            basename = PurePosixPath(self.relative_path).name
            match = _UNK_NAME.fullmatch(basename)
            if match is None or int(match.group("kpoint")) != self.kpoint_index:
                raise ValueError("UNK path and kpoint_index disagree")
            native_spin = match.group("spin")
            if native_spin == "NC":
                if self.spin_channel_index is not None:
                    raise ValueError("noncollinear UNK must not declare a spin channel")
            elif (
                type(self.spin_channel_index) is not int
                or self.spin_channel_index <= 0
                or int(native_spin) != self.spin_channel_index
            ):
                raise ValueError("UNK path and spin_channel_index disagree")
        elif self.kpoint_index is not None or self.spin_channel_index is not None:
            raise ValueError("only UNK artifacts may carry k-point or spin indices")

    @property
    def basename(self) -> str:
        """Return the native basename without discarding the bound relative path."""
        return PurePosixPath(self.relative_path).name

    def authenticate(self, payload: bytes) -> None:
        """Fail closed unless supplied bytes exactly match this binding."""
        if type(payload) is not bytes:
            raise TypeError("payload must be built-in bytes")
        if len(payload) != self.byte_size:
            raise ValueError(f"artifact byte-size mismatch: {self.relative_path}")
        if hashlib.sha256(payload).hexdigest() != self.sha256:
            raise ValueError(f"artifact SHA-256 mismatch: {self.relative_path}")


@dataclass(frozen=True, slots=True)
class QeWannier90PlaneWaveArtifactManifest:
    """Bind a completed Wannier frame to its post-NSCF and native artifacts.

    The post-NSCF manifest is treated as a content-addressed transitive binding;
    this record neither invents missing lineage nor interprets its payload.
    """

    schema_version: int
    run_id: str
    qe_prefix: str
    seedname: str
    kpoint_count: int
    band_count: int
    wannier_count: int
    spin_channel_count: int
    selected_spin_channel_index: int | None
    spinor_component_count: int
    post_nscf_state_manifest: QeWannier90ProviderArtifact
    qexsd: QeWannier90ProviderArtifact
    pseudopotentials: tuple[QeWannier90ProviderArtifact, ...]
    wannier_input: QeWannier90ProviderArtifact
    neighbor_interface: QeWannier90ProviderArtifact
    unks: tuple[QeWannier90ProviderArtifact, ...]
    eigenvalues: QeWannier90ProviderArtifact
    gauge_matrix: QeWannier90ProviderArtifact
    disentanglement_matrix: QeWannier90ProviderArtifact
    hamiltonian: QeWannier90ProviderArtifact

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported provider manifest schema version")
        names = {
            "run_id": self.run_id,
            "qe_prefix": self.qe_prefix,
            "seedname": self.seedname,
        }
        for label, name in names.items():
            if type(name) is not str or _SAFE_NAME.fullmatch(name) is None:
                raise ValueError(f"{label} must be a safe nonempty name")
        counts = {
            "kpoint_count": self.kpoint_count,
            "band_count": self.band_count,
            "wannier_count": self.wannier_count,
        }
        for label, count in counts.items():
            if type(count) is not int or count <= 0:
                raise ValueError(f"{label} must be positive")
        if self.wannier_count > self.band_count:
            raise ValueError("wannier_count must not exceed band_count")
        if type(self.spin_channel_count) is not int or self.spin_channel_count <= 0:
            raise ValueError("spin_channel_count must be positive")
        if type(
            self.spinor_component_count
        ) is not int or self.spinor_component_count not in {1, 2}:
            raise ValueError("spinor_component_count must be one or two")
        if self.spinor_component_count == 2:
            if self.spin_channel_count != 1:
                raise ValueError("spinor frames must have one spin channel")
            if self.selected_spin_channel_index is not None:
                raise ValueError("spinor frames must not select a scalar spin channel")
        elif (
            type(self.selected_spin_channel_index) is not int
            or not 1 <= self.selected_spin_channel_index <= self.spin_channel_count
        ):
            raise ValueError(
                "scalar frames require a selected spin channel within channel_count"
            )
        self._require_role(
            self.post_nscf_state_manifest,
            QeWannier90ProviderArtifactRole.post_nscf_state_manifest,
        )
        self._require_role(self.qexsd, QeWannier90ProviderArtifactRole.qexsd)
        if type(self.pseudopotentials) is not tuple or not self.pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        for artifact in self.pseudopotentials:
            self._require_role(
                artifact, QeWannier90ProviderArtifactRole.pseudopotential
            )
        for artifact, role, expected_basename in (
            (
                self.wannier_input,
                QeWannier90ProviderArtifactRole.wannier_input,
                f"{self.seedname}.win",
            ),
            (
                self.neighbor_interface,
                QeWannier90ProviderArtifactRole.neighbor_interface,
                f"{self.seedname}.nnkp",
            ),
        ):
            self._require_role(artifact, role)
            if artifact.basename != expected_basename:
                raise ValueError(f"{role.value} basename must match seedname")
        if type(self.unks) is not tuple or len(self.unks) != self.kpoint_count:
            raise ValueError("UNK inventory must contain exactly one file per k-point")
        expected_indices = tuple(range(1, self.kpoint_count + 1))
        if tuple(item.kpoint_index for item in self.unks) != expected_indices:
            raise ValueError(
                "UNK inventory must be ordered by contiguous k-point index"
            )
        for artifact in self.unks:
            self._require_role(artifact, QeWannier90ProviderArtifactRole.unk)
            if self.spinor_component_count == 2:
                if not artifact.basename.endswith(".NC"):
                    raise ValueError("two-component frames require native .NC UNKs")
            elif artifact.basename.endswith(".NC"):
                raise ValueError("scalar frames must not use native .NC UNKs")
            elif artifact.spin_channel_index != self.selected_spin_channel_index:
                raise ValueError("scalar UNKs must all use the selected spin channel")
        for artifact, role, expected_basename in (
            (
                self.eigenvalues,
                QeWannier90ProviderArtifactRole.eigenvalues,
                f"{self.seedname}.eig",
            ),
            (
                self.gauge_matrix,
                QeWannier90ProviderArtifactRole.gauge_matrix,
                f"{self.seedname}_u.mat",
            ),
            (
                self.disentanglement_matrix,
                QeWannier90ProviderArtifactRole.disentanglement_matrix,
                f"{self.seedname}_u_dis.mat",
            ),
            (
                self.hamiltonian,
                QeWannier90ProviderArtifactRole.hamiltonian,
                f"{self.seedname}_hr.dat",
            ),
        ):
            self._require_role(artifact, role)
            if artifact.basename != expected_basename:
                raise ValueError(f"{role.value} basename must match seedname")
        artifacts = self.artifacts
        paths = tuple(item.relative_path for item in artifacts)
        if len(paths) != len(set(paths)):
            raise ValueError("provider artifact paths must be unique")

    @staticmethod
    def _require_role(
        artifact: QeWannier90ProviderArtifact,
        role: QeWannier90ProviderArtifactRole,
    ) -> None:
        if type(artifact) is not QeWannier90ProviderArtifact:
            raise TypeError("manifest entries must be provider artifacts")
        if artifact.role is not role:
            raise ValueError(f"manifest entry must have role {role.value}")

    @property
    def artifacts(self) -> tuple[QeWannier90ProviderArtifact, ...]:
        """Return the complete closed inventory in stable semantic order."""
        return (
            self.post_nscf_state_manifest,
            self.qexsd,
            *self.pseudopotentials,
            self.wannier_input,
            self.neighbor_interface,
            *self.unks,
            self.eigenvalues,
            self.gauge_matrix,
            self.disentanglement_matrix,
            self.hamiltonian,
        )


@dataclass(frozen=True, slots=True)
class QeWannier90PlaneWaveManifestVerifier:
    """Read-only verification of every regular file in a provider manifest."""

    max_artifact_count: int = 4096
    max_total_byte_size: int = 256 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        if type(self.max_artifact_count) is not int or self.max_artifact_count <= 0:
            raise ValueError("max_artifact_count must be positive")
        if type(self.max_total_byte_size) is not int or self.max_total_byte_size <= 0:
            raise ValueError("max_total_byte_size must be positive")

    def verify(
        self,
        manifest: QeWannier90PlaneWaveArtifactManifest,
        run_root: Path,
    ) -> tuple[Path, ...]:
        """Return authenticated paths in manifest order without modifying them."""
        if type(manifest) is not QeWannier90PlaneWaveArtifactManifest:
            raise TypeError("manifest must be a provider artifact manifest")
        if not isinstance(run_root, Path):
            raise TypeError("run_root must be a Path")
        if run_root.is_symlink() or not run_root.is_dir():
            raise ValueError("run_root must be an existing nonsymlink directory")
        artifacts = manifest.artifacts
        if len(artifacts) > self.max_artifact_count:
            raise ValueError("provider artifact count exceeds the bound")
        if sum(item.byte_size for item in artifacts) > self.max_total_byte_size:
            raise ValueError("provider artifact total byte size exceeds the bound")
        root = run_root.resolve()
        verified: list[Path] = []
        physical_files: set[tuple[int, int]] = set()
        for artifact in artifacts:
            relative_parts = PurePosixPath(artifact.relative_path).parts
            path = root.joinpath(*relative_parts)
            candidate = root
            for part in relative_parts:
                candidate /= part
                if candidate.is_symlink():
                    raise ValueError(
                        f"artifact path contains a symlink: {artifact.relative_path}"
                    )
            if not path.is_file():
                raise ValueError(
                    f"artifact is not a regular file: {artifact.relative_path}"
                )
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("artifact escapes run_root")
            stat = path.stat()
            physical_identity = (stat.st_dev, stat.st_ino)
            if physical_identity in physical_files:
                raise ValueError("provider artifact paths must identify distinct files")
            physical_files.add(physical_identity)
            if stat.st_size != artifact.byte_size:
                raise ValueError(
                    f"artifact byte-size mismatch: {artifact.relative_path}"
                )
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            if digest.hexdigest() != artifact.sha256:
                raise ValueError(f"artifact SHA-256 mismatch: {artifact.relative_path}")
            verified.append(resolved)
        return tuple(verified)


def _validate_relative_path(value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError("relative_path must be a nonempty string")
    path = PurePosixPath(value)
    if (
        "\\" in value
        or path.is_absolute()
        or path == PurePosixPath(".")
        or ".." in path.parts
        or str(path) != value
    ):
        raise ValueError("relative_path must be a safe relative POSIX path")
