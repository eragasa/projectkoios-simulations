"""Verify declared ``epw.x`` output artifacts without scientific interpretation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class QeEpwArtifactRole(StrEnum):
    """Classify retained EPW process and provider-native artifacts."""

    input = "input"
    stdout = "stdout"
    stderr = "stderr"
    execution_record = "execution-record"
    native_output = "native-output"
    intermediate = "intermediate"


@dataclass(frozen=True, slots=True)
class QeEpwArtifactDeclaration:
    """Declare one exact regular artifact beneath an EPW output directory."""

    role: QeEpwArtifactRole
    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.role) is not QeEpwArtifactRole:
            raise TypeError("role must be a QeEpwArtifactRole")
        _relative_path(self.relative_path)
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class QeEpwArtifactObservation:
    """Retain verified artifact identities and bounded aggregate sizes."""

    artifacts: tuple[QeEpwArtifactDeclaration, ...]
    producer_execution_record_sha256: str
    artifact_count: int
    total_byte_size: int


@dataclass(frozen=True, slots=True)
class QeEpwArtifactInspector:
    """Fail closed on missing, altered, symlinked, or excessive artifacts."""

    max_artifact_count: int = 8192
    max_total_byte_size: int = 512 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        for label, value in (
            ("max_artifact_count", self.max_artifact_count),
            ("max_total_byte_size", self.max_total_byte_size),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")

    def inspect(
        self,
        *,
        output_directory: Path,
        producer_execution_record_sha256: str,
        declarations: tuple[QeEpwArtifactDeclaration, ...],
    ) -> QeEpwArtifactObservation:
        """Verify exact declarations without discovering undeclared filesystem data."""
        if not isinstance(output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if output_directory.is_symlink() or not output_directory.is_dir():
            raise ValueError("output_directory must be a regular directory")
        if (
            type(producer_execution_record_sha256) is not str
            or _SHA256.fullmatch(producer_execution_record_sha256) is None
        ):
            raise ValueError("producer execution record identity must be SHA-256")
        if type(declarations) is not tuple or not declarations:
            raise ValueError("declarations must be a nonempty tuple")
        if any(type(item) is not QeEpwArtifactDeclaration for item in declarations):
            raise TypeError(
                "declarations must contain QeEpwArtifactDeclaration records"
            )
        if len(declarations) > self.max_artifact_count:
            raise ValueError("EPW artifact count exceeds the bound")
        paths = tuple(item.relative_path for item in declarations)
        if len(paths) != len(set(paths)):
            raise ValueError("artifact relative paths must be unique")
        total_byte_size = sum(item.byte_size for item in declarations)
        if total_byte_size > self.max_total_byte_size:
            raise ValueError("EPW artifact total byte size exceeds the bound")
        by_role: dict[QeEpwArtifactRole, list[QeEpwArtifactDeclaration]] = {}
        for declaration in declarations:
            by_role.setdefault(declaration.role, []).append(declaration)
        required = {
            QeEpwArtifactRole.stdout: "epw.out",
            QeEpwArtifactRole.stderr: "epw.err",
            QeEpwArtifactRole.execution_record: "execution.json",
        }
        for role, expected_path in required.items():
            values = by_role.get(role, [])
            if len(values) != 1 or values[0].relative_path != expected_path:
                raise ValueError(
                    f"exactly one canonical {role.value} artifact is required"
                )
        execution_declaration = by_role[QeEpwArtifactRole.execution_record][0]
        if execution_declaration.sha256 != producer_execution_record_sha256:
            raise ValueError(
                "execution-record identity disagrees with producer identity"
            )
        for declaration in declarations:
            _verify(output_directory, declaration)
        return QeEpwArtifactObservation(
            artifacts=declarations,
            producer_execution_record_sha256=producer_execution_record_sha256,
            artifact_count=len(declarations),
            total_byte_size=total_byte_size,
        )


def _relative_path(value: str) -> Path:
    if type(value) is not str or not value or "\\" in value or "\0" in value:
        raise ValueError("relative_path must be a safe POSIX relative path")
    path = Path(value)
    if (
        path.is_absolute()
        or path in {Path("."), Path("")}
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise ValueError("relative_path must be a safe POSIX relative path")
    return path


def _verify(
    output_directory: Path,
    declaration: QeEpwArtifactDeclaration,
) -> None:
    path = output_directory
    for part in Path(declaration.relative_path).parts:
        path /= part
        if path.is_symlink():
            raise ValueError(f"symlinked artifact path: {declaration.relative_path}")
    if not path.is_file():
        raise ValueError(f"missing regular artifact: {declaration.relative_path}")
    if path.stat().st_size != declaration.byte_size:
        raise ValueError(f"artifact size mismatch: {declaration.relative_path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != declaration.sha256:
        raise ValueError(f"artifact hash mismatch: {declaration.relative_path}")
