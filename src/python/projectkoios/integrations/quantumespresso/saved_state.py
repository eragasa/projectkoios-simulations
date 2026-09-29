"""Declare and verify immutable Quantum ESPRESSO saved-state evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class QeSavedStateCalculation(StrEnum):
    """Identify the ``pw.x`` calculation that produced a saved state."""

    scf = "scf"
    nscf = "nscf"


class QeSavedStateArtifactRole(StrEnum):
    """Identify required semantic roles without interpreting binary payloads."""

    qexsd = "qexsd"
    charge_density = "charge-density"
    wavefunction = "wavefunction"
    pseudopotential = "pseudopotential"
    augmentation = "augmentation"
    native = "native"


@dataclass(frozen=True, slots=True)
class QeSavedStateArtifact:
    """Identify one source-root-relative saved-state file."""

    role: QeSavedStateArtifactRole
    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.role) is not QeSavedStateArtifactRole:
            raise TypeError("role must be a QeSavedStateArtifactRole")
        _validate_relative_path(self.relative_path)
        _validate_sha256(self.sha256, "sha256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")


@dataclass(frozen=True, slots=True)
class QeSavedStatePseudopotential:
    """Retain one pseudopotential identity in saved-state lineage."""

    symbol: str
    filename: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.symbol) is not str or _NAME.fullmatch(self.symbol) is None:
            raise ValueError("symbol must be a safe name")
        if type(self.filename) is not str or _NAME.fullmatch(self.filename) is None:
            raise ValueError("filename must be a safe basename")
        _validate_sha256(self.sha256, "sha256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")


@dataclass(frozen=True, slots=True)
class QeSavedStateManifest:
    """Describe a minimal reproducible ``pw.x`` saved-state subset."""

    schema_version: int
    prefix: str
    calculation: QeSavedStateCalculation
    producer_program: str
    producer_version: str
    executable_sha256: str
    input_sha256: str
    structure_id: str
    structure_sha256: str
    pseudopotentials: tuple[QeSavedStatePseudopotential, ...]
    artifacts: tuple[QeSavedStateArtifact, ...]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported saved-state manifest schema version")
        if type(self.prefix) is not str or _NAME.fullmatch(self.prefix) is None:
            raise ValueError("prefix must be a safe native name")
        if type(self.calculation) is not QeSavedStateCalculation:
            raise TypeError("calculation must be a QeSavedStateCalculation")
        for label, value in (
            ("producer_program", self.producer_program),
            ("producer_version", self.producer_version),
            ("structure_id", self.structure_id),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if self.producer_program != "pw.x":
            raise ValueError("saved-state producer program must be pw.x")
        for label, value in (
            ("executable_sha256", self.executable_sha256),
            ("input_sha256", self.input_sha256),
            ("structure_sha256", self.structure_sha256),
        ):
            _validate_sha256(value, label)
        if type(self.pseudopotentials) is not tuple or not self.pseudopotentials:
            raise ValueError("pseudopotentials must be nonempty")
        if any(
            type(item) is not QeSavedStatePseudopotential
            for item in self.pseudopotentials
        ):
            raise TypeError(
                "pseudopotentials must contain QeSavedStatePseudopotential values"
            )
        if type(self.artifacts) is not tuple or not self.artifacts:
            raise ValueError("artifacts must be nonempty")
        if any(type(item) is not QeSavedStateArtifact for item in self.artifacts):
            raise TypeError("artifacts must contain QeSavedStateArtifact values")
        paths = tuple(item.relative_path for item in self.artifacts)
        if len(paths) != len(set(paths)):
            raise ValueError("saved-state artifact paths must be unique")
        prefix_directory = f"{self.prefix}.save"
        if any(PurePosixPath(path).parts[0] != prefix_directory for path in paths):
            raise ValueError(
                "saved-state artifacts must reside in the prefix save tree"
            )
        roles = tuple(item.role for item in self.artifacts)
        if roles.count(QeSavedStateArtifactRole.qexsd) != 1:
            raise ValueError("saved-state manifest requires exactly one QEXSD artifact")
        if roles.count(QeSavedStateArtifactRole.charge_density) != 1:
            raise ValueError(
                "saved-state manifest requires exactly one charge-density artifact"
            )
        if QeSavedStateArtifactRole.wavefunction not in roles:
            raise ValueError("saved-state manifest requires wavefunction artifacts")
        pseudopotential_artifacts = tuple(
            item
            for item in self.artifacts
            if item.role is QeSavedStateArtifactRole.pseudopotential
        )
        for pseudopotential in self.pseudopotentials:
            matching = tuple(
                item
                for item in pseudopotential_artifacts
                if PurePosixPath(item.relative_path).name == pseudopotential.filename
                and item.sha256 == pseudopotential.sha256
                and item.byte_size == pseudopotential.byte_size
            )
            if len(matching) != 1:
                raise ValueError(
                    "each pseudopotential lineage entry requires one matching "
                    "saved-state artifact"
                )


@dataclass(frozen=True, slots=True)
class QeSavedStateManifestJsonCodec:
    """Load and dump closed version-one saved-state manifests."""

    def dumps(self, manifest: QeSavedStateManifest) -> bytes:
        """Serialize one manifest deterministically without filesystem effects."""
        if type(manifest) is not QeSavedStateManifest:
            raise TypeError("manifest must be a QeSavedStateManifest")
        document = {
            "artifacts": [
                {
                    "byte_size": item.byte_size,
                    "relative_path": item.relative_path,
                    "role": item.role.value,
                    "sha256": item.sha256,
                }
                for item in manifest.artifacts
            ],
            "calculation": manifest.calculation.value,
            "input_sha256": manifest.input_sha256,
            "prefix": manifest.prefix,
            "producer": {
                "executable_sha256": manifest.executable_sha256,
                "program": manifest.producer_program,
                "version": manifest.producer_version,
            },
            "pseudopotentials": [
                {
                    "byte_size": item.byte_size,
                    "filename": item.filename,
                    "sha256": item.sha256,
                    "symbol": item.symbol,
                }
                for item in manifest.pseudopotentials
            ],
            "schema_version": manifest.schema_version,
            "structure": {
                "sha256": manifest.structure_sha256,
                "structure_id": manifest.structure_id,
            },
        }
        return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")

    def loads(self, payload: bytes) -> QeSavedStateManifest:
        """Parse one manifest without filesystem or calculator effects."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            document = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("saved-state manifest must be valid UTF-8 JSON") from error
        root = _mapping(document, "manifest")
        _closed_keys(
            root,
            {
                "schema_version",
                "prefix",
                "calculation",
                "producer",
                "input_sha256",
                "structure",
                "pseudopotentials",
                "artifacts",
            },
            "manifest",
        )
        producer = _mapping(root["producer"], "producer")
        _closed_keys(producer, {"program", "version", "executable_sha256"}, "producer")
        structure = _mapping(root["structure"], "structure")
        _closed_keys(structure, {"structure_id", "sha256"}, "structure")
        pseudopotentials_value = root["pseudopotentials"]
        artifacts_value = root["artifacts"]
        if type(pseudopotentials_value) is not list:
            raise TypeError("pseudopotentials must be a list")
        if type(artifacts_value) is not list:
            raise TypeError("artifacts must be a list")
        return QeSavedStateManifest(
            schema_version=_integer(root["schema_version"], "schema_version"),
            prefix=_string(root["prefix"], "prefix"),
            calculation=QeSavedStateCalculation(
                _string(root["calculation"], "calculation")
            ),
            producer_program=_string(producer["program"], "producer.program"),
            producer_version=_string(producer["version"], "producer.version"),
            executable_sha256=_string(
                producer["executable_sha256"],
                "producer.executable_sha256",
            ),
            input_sha256=_string(root["input_sha256"], "input_sha256"),
            structure_id=_string(structure["structure_id"], "structure.structure_id"),
            structure_sha256=_string(structure["sha256"], "structure.sha256"),
            pseudopotentials=tuple(
                self._pseudopotential(value, index)
                for index, value in enumerate(pseudopotentials_value)
            ),
            artifacts=tuple(
                self._artifact(value, index)
                for index, value in enumerate(artifacts_value)
            ),
        )

    @staticmethod
    def _pseudopotential(value: object, index: int) -> QeSavedStatePseudopotential:
        item = _mapping(value, f"pseudopotentials[{index}]")
        _closed_keys(
            item,
            {"symbol", "filename", "sha256", "byte_size"},
            f"pseudopotentials[{index}]",
        )
        return QeSavedStatePseudopotential(
            symbol=_string(item["symbol"], "symbol"),
            filename=_string(item["filename"], "filename"),
            sha256=_string(item["sha256"], "sha256"),
            byte_size=_integer(item["byte_size"], "byte_size"),
        )

    @staticmethod
    def _artifact(value: object, index: int) -> QeSavedStateArtifact:
        item = _mapping(value, f"artifacts[{index}]")
        _closed_keys(
            item,
            {"role", "relative_path", "sha256", "byte_size"},
            f"artifacts[{index}]",
        )
        return QeSavedStateArtifact(
            role=QeSavedStateArtifactRole(_string(item["role"], "role")),
            relative_path=_string(item["relative_path"], "relative_path"),
            sha256=_string(item["sha256"], "sha256"),
            byte_size=_integer(item["byte_size"], "byte_size"),
        )


@dataclass(frozen=True, slots=True)
class QeSavedStateManifestVerifier:
    """Verify every selected regular file before saved-state staging."""

    max_artifact_count: int = 4096
    max_total_byte_size: int = 64 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        if type(self.max_artifact_count) is not int or self.max_artifact_count <= 0:
            raise ValueError("max_artifact_count must be positive")
        if type(self.max_total_byte_size) is not int or self.max_total_byte_size <= 0:
            raise ValueError("max_total_byte_size must be positive")

    def verify(
        self,
        manifest: QeSavedStateManifest,
        source_root: Path,
    ) -> tuple[Path, ...]:
        """Return verified paths in manifest order or fail closed."""
        if type(manifest) is not QeSavedStateManifest:
            raise TypeError("manifest must be a QeSavedStateManifest")
        if not isinstance(source_root, Path):
            raise TypeError("source_root must be a Path")
        if source_root.is_symlink() or not source_root.is_dir():
            raise ValueError("saved-state source root must be a regular directory")
        if len(manifest.artifacts) > self.max_artifact_count:
            raise ValueError("saved-state artifact count exceeds the bound")
        total_byte_size = sum(item.byte_size for item in manifest.artifacts)
        if total_byte_size > self.max_total_byte_size:
            raise ValueError("saved-state total byte size exceeds the bound")
        verified: list[Path] = []
        for artifact in manifest.artifacts:
            parts = PurePosixPath(artifact.relative_path).parts
            parent = source_root
            for part in parts[:-1]:
                parent /= part
                if parent.is_symlink() or not parent.is_dir():
                    raise ValueError(
                        "saved-state artifact parent is not a regular directory: "
                        f"{artifact.relative_path}"
                    )
            path = source_root.joinpath(*parts)
            _verify_artifact_file(path, artifact)
            verified.append(path)
        return tuple(verified)


@dataclass(frozen=True, slots=True)
class QeSavedStateManifestBuilder:
    """Inventory one bounded native save tree into an immutable manifest."""

    max_artifact_count: int = 4096
    max_total_byte_size: int = 64 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        if type(self.max_artifact_count) is not int or self.max_artifact_count <= 0:
            raise ValueError("max_artifact_count must be positive")
        if type(self.max_total_byte_size) is not int or self.max_total_byte_size <= 0:
            raise ValueError("max_total_byte_size must be positive")

    def build(
        self,
        *,
        source_root: Path,
        prefix: str,
        calculation: QeSavedStateCalculation,
        producer_version: str,
        executable_sha256: str,
        input_sha256: str,
        structure_id: str,
        structure_sha256: str,
        pseudopotentials: tuple[QeSavedStatePseudopotential, ...],
    ) -> QeSavedStateManifest:
        """Build an exact manifest without interpreting native scientific data."""
        if not isinstance(source_root, Path):
            raise TypeError("source_root must be a Path")
        if source_root.is_symlink() or not source_root.is_dir():
            raise ValueError("source_root must be a regular directory")
        if type(prefix) is not str or _NAME.fullmatch(prefix) is None:
            raise ValueError("prefix must be a safe native name")
        resolved_source_root = source_root.resolve()
        save_candidate = source_root / f"{prefix}.save"
        if save_candidate.is_symlink() or not save_candidate.is_dir():
            raise ValueError("prefix save tree must be a regular directory")
        save_root = save_candidate.resolve()
        if save_root.parent != resolved_source_root:
            raise ValueError("prefix save tree must remain inside source_root")
        descendants = tuple(save_root.rglob("*"))
        if any(path.is_symlink() for path in descendants):
            raise ValueError("saved-state tree must not contain symbolic links")
        files = tuple(sorted(path for path in descendants if path.is_file()))
        if not files or len(files) > self.max_artifact_count:
            raise ValueError("saved-state artifact count is empty or exceeds the bound")
        total_byte_size = sum(path.stat().st_size for path in files)
        if total_byte_size > self.max_total_byte_size:
            raise ValueError("saved-state total byte size exceeds the bound")
        pseudo_by_name = {item.filename: item for item in pseudopotentials}
        artifacts = tuple(
            QeSavedStateArtifact(
                role=_saved_state_role(path.name, pseudo_by_name),
                relative_path=path.relative_to(resolved_source_root).as_posix(),
                sha256=_sha256_file(path),
                byte_size=path.stat().st_size,
            )
            for path in files
        )
        return QeSavedStateManifest(
            schema_version=1,
            prefix=prefix,
            calculation=calculation,
            producer_program="pw.x",
            producer_version=producer_version,
            executable_sha256=executable_sha256,
            input_sha256=input_sha256,
            structure_id=structure_id,
            structure_sha256=structure_sha256,
            pseudopotentials=pseudopotentials,
            artifacts=artifacts,
        )


def _saved_state_role(
    filename: str,
    pseudopotentials: dict[str, QeSavedStatePseudopotential],
) -> QeSavedStateArtifactRole:
    if filename == "data-file-schema.xml":
        return QeSavedStateArtifactRole.qexsd
    if filename == "charge-density.dat":
        return QeSavedStateArtifactRole.charge_density
    if filename in pseudopotentials:
        return QeSavedStateArtifactRole.pseudopotential
    if filename.startswith("wfc"):
        return QeSavedStateArtifactRole.wavefunction
    if filename.startswith("augmentation"):
        return QeSavedStateArtifactRole.augmentation
    return QeSavedStateArtifactRole.native


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_relative_path(value: str) -> None:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("relative_path must be a safe relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or path == PurePosixPath(".") or ".." in path.parts:
        raise ValueError("relative_path must be a safe relative POSIX path")


def _validate_sha256(value: str, label: str) -> None:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256")


def _mapping(value: object, label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise TypeError(f"{label} must be an object with string keys")
    return value


def _closed_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    keys = set(value)
    if keys != expected:
        raise ValueError(
            f"{label} keys differ: missing={sorted(expected - keys)!r}, "
            f"unexpected={sorted(keys - expected)!r}"
        )


def _string(value: object, label: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be a string")
    return value


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an integer")
    return value


def _verify_artifact_file(path: Path, artifact: QeSavedStateArtifact) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise ValueError(
            f"saved-state artifact is not a regular file: {artifact.relative_path}"
        ) from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(
                f"saved-state artifact is not regular: {artifact.relative_path}"
            )
        if before.st_size != artifact.byte_size:
            raise ValueError(
                f"saved-state artifact size mismatch: {artifact.relative_path}"
            )
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        after = os.fstat(descriptor)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_after != identity_before:
            raise ValueError(
                "saved-state artifact changed during verification: "
                f"{artifact.relative_path}"
            )
        if digest.hexdigest() != artifact.sha256:
            raise ValueError(
                f"saved-state artifact hash mismatch: {artifact.relative_path}"
            )
    finally:
        os.close(descriptor)
