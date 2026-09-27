"""Verify native ``pw2wannier90.x`` artifacts and interface dimensions."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class QePw2Wannier90ArtifactRole(StrEnum):
    """Identify required and accepted optional converter artifacts."""

    amn = "amn"
    mmn = "mmn"
    eig = "eig"
    unk = "unk"
    spn = "spn"
    uhu = "uHu"
    uiu = "uIu"


@dataclass(frozen=True, slots=True)
class QePw2Wannier90ArtifactDeclaration:
    """Declare one exact native converter output artifact."""

    role: QePw2Wannier90ArtifactRole
    filename: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.role) is not QePw2Wannier90ArtifactRole:
            raise TypeError("role must be a QePw2Wannier90ArtifactRole")
        if type(self.filename) is not str or _NAME.fullmatch(self.filename) is None:
            raise ValueError("filename must be a safe basename")
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90ArtifactObservation:
    """Retain verified converter artifacts and native interface dimensions."""

    artifacts: tuple[QePw2Wannier90ArtifactDeclaration, ...]
    producer_execution_record_sha256: str
    band_count: int
    kpoint_count: int
    wannier_function_count: int
    neighbor_count: int
    eigenvalue_count: int

    def __post_init__(self) -> None:
        if type(self.artifacts) is not tuple or not self.artifacts:
            raise ValueError("artifacts must be nonempty")
        if (
            type(self.producer_execution_record_sha256) is not str
            or _SHA256.fullmatch(self.producer_execution_record_sha256) is None
        ):
            raise ValueError("producer execution record identity must be SHA-256")
        for label, value in (
            ("band_count", self.band_count),
            ("kpoint_count", self.kpoint_count),
            ("wannier_function_count", self.wannier_function_count),
            ("neighbor_count", self.neighbor_count),
            ("eigenvalue_count", self.eigenvalue_count),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90ArtifactInspector:
    """Fail closed on missing, altered, or dimensionally inconsistent output."""

    max_artifact_count: int = 4096
    max_total_byte_size: int = 128 * 1024 * 1024 * 1024
    max_eigenvalue_byte_size: int = 2 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        for label, value in (
            ("max_artifact_count", self.max_artifact_count),
            ("max_total_byte_size", self.max_total_byte_size),
            ("max_eigenvalue_byte_size", self.max_eigenvalue_byte_size),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")

    def inspect(
        self,
        *,
        output_directory: Path,
        seedname: str,
        producer_execution_record_sha256: str,
        declarations: tuple[QePw2Wannier90ArtifactDeclaration, ...],
    ) -> QePw2Wannier90ArtifactObservation:
        """Verify exact identities and bounded native header semantics."""
        if not isinstance(output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if output_directory.is_symlink() or not output_directory.is_dir():
            raise ValueError("output_directory must be a regular directory")
        if type(seedname) is not str or _NAME.fullmatch(seedname) is None:
            raise ValueError("seedname must be a safe native name")
        if (
            type(producer_execution_record_sha256) is not str
            or _SHA256.fullmatch(producer_execution_record_sha256) is None
        ):
            raise ValueError("producer execution record identity must be SHA-256")
        if type(declarations) is not tuple or any(
            type(item) is not QePw2Wannier90ArtifactDeclaration for item in declarations
        ):
            raise TypeError("declarations must contain artifact declarations")
        if len(declarations) > self.max_artifact_count:
            raise ValueError("converter artifact count exceeds the bound")
        if sum(item.byte_size for item in declarations) > self.max_total_byte_size:
            raise ValueError("converter artifact total byte size exceeds the bound")
        roles = tuple(item.role for item in declarations)
        for required in (
            QePw2Wannier90ArtifactRole.amn,
            QePw2Wannier90ArtifactRole.mmn,
            QePw2Wannier90ArtifactRole.eig,
        ):
            if roles.count(required) != 1:
                raise ValueError(f"exactly one {required.value} artifact is required")
        filenames = tuple(item.filename for item in declarations)
        if len(filenames) != len(set(filenames)):
            raise ValueError("artifact filenames must be unique")
        by_role = {item.role: item for item in declarations}
        for role in (
            QePw2Wannier90ArtifactRole.amn,
            QePw2Wannier90ArtifactRole.mmn,
            QePw2Wannier90ArtifactRole.eig,
        ):
            if by_role[role].filename != f"{seedname}.{role.value}":
                raise ValueError(f"{role.value} filename must match seedname")
        if (
            by_role[QePw2Wannier90ArtifactRole.eig].byte_size
            > self.max_eigenvalue_byte_size
        ):
            raise ValueError("EIG byte size exceeds the parsing bound")
        for declaration in declarations:
            _verify(output_directory / declaration.filename, declaration)
        amn_dimensions = _header_dimensions(
            output_directory / by_role[QePw2Wannier90ArtifactRole.amn].filename,
            expected_count=3,
            label="AMN",
        )
        mmn_dimensions = _header_dimensions(
            output_directory / by_role[QePw2Wannier90ArtifactRole.mmn].filename,
            expected_count=3,
            label="MMN",
        )
        amn_bands, amn_kpoints, wannier_functions = amn_dimensions
        mmn_bands, mmn_kpoints, neighbors = mmn_dimensions
        if (amn_bands, amn_kpoints) != (mmn_bands, mmn_kpoints):
            raise ValueError("AMN and MMN dimensions disagree")
        eigenvalue_count = _inspect_eigenvalues(
            output_directory / by_role[QePw2Wannier90ArtifactRole.eig].filename,
            band_count=amn_bands,
            kpoint_count=amn_kpoints,
        )
        return QePw2Wannier90ArtifactObservation(
            artifacts=declarations,
            producer_execution_record_sha256=producer_execution_record_sha256,
            band_count=amn_bands,
            kpoint_count=amn_kpoints,
            wannier_function_count=wannier_functions,
            neighbor_count=neighbors,
            eigenvalue_count=eigenvalue_count,
        )


def _verify(path: Path, declaration: QePw2Wannier90ArtifactDeclaration) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing regular artifact: {declaration.filename}")
    if path.stat().st_size != declaration.byte_size:
        raise ValueError(f"artifact size mismatch: {declaration.filename}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != declaration.sha256:
        raise ValueError(f"artifact hash mismatch: {declaration.filename}")


def _header_dimensions(
    path: Path,
    *,
    expected_count: int,
    label: str,
) -> tuple[int, ...]:
    with path.open("r", encoding="ascii") as stream:
        if not stream.readline():
            raise ValueError(f"{label} header is missing")
        values = stream.readline().split()
    if len(values) != expected_count:
        raise ValueError(f"{label} dimension header is malformed")
    try:
        dimensions = tuple(int(value) for value in values)
    except ValueError as error:
        raise ValueError(f"{label} dimensions must be integers") from error
    if any(value <= 0 for value in dimensions):
        raise ValueError(f"{label} dimensions must be positive")
    return dimensions


def _inspect_eigenvalues(path: Path, *, band_count: int, kpoint_count: int) -> int:
    seen: set[tuple[int, int]] = set()
    with path.open("r", encoding="ascii") as stream:
        for line_number, line in enumerate(stream, start=1):
            values = line.split()
            if len(values) != 3:
                raise ValueError(f"EIG row {line_number} is malformed")
            try:
                band = int(values[0])
                kpoint = int(values[1])
                eigenvalue = float(values[2])
            except ValueError as error:
                raise ValueError(f"EIG row {line_number} is malformed") from error
            if not 1 <= band <= band_count or not 1 <= kpoint <= kpoint_count:
                raise ValueError(f"EIG row {line_number} index is out of bounds")
            if not math.isfinite(eigenvalue):
                raise ValueError(f"EIG row {line_number} value is not finite")
            key = (band, kpoint)
            if key in seen:
                raise ValueError(f"EIG row {line_number} duplicates an index")
            seen.add(key)
    expected = band_count * kpoint_count
    if len(seen) != expected:
        raise ValueError("EIG does not contain the complete band-by-k-point grid")
    return len(seen)
