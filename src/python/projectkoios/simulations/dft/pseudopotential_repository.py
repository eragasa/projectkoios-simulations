"""Resolve exact pseudopotential identities from an explicit local repository."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialFile,
)


class PseudopotentialNotFoundError(LookupError):
    """Report an undeclared or unavailable required pseudopotential artifact."""


class PseudopotentialIntegrityError(ValueError):
    """Report a repository artifact that fails its declared byte identity."""


@dataclass(frozen=True, slots=True)
class PseudopotentialLibrary:
    """Discover exact pseudopotential requirements beneath one explicit root.

    The library supplies deployment locations only. Scientific code must provide a
    complete :class:`PseudopotentialFile` requirement, including metadata, filename,
    byte size, and SHA-256. Resolution never chooses a pseudopotential by element,
    filename, or library ordering.
    """

    root: Path

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("root must be a Path")
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("root must be absolute without parent traversal")
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("root must be an existing nonsymlink directory")

    def resolve(self, required: PseudopotentialFile) -> Path:
        """Return a deterministic local path whose bytes match ``required``."""
        if not isinstance(required, PseudopotentialFile):
            raise TypeError("required must inherit from PseudopotentialFile")
        candidates = tuple(sorted(self.root.rglob(required.filename)))
        verified = tuple(
            path
            for path in candidates
            if _matches_required_artifact(self.root, path, required)
        )
        if verified:
            return verified[0]
        if candidates:
            raise PseudopotentialIntegrityError(
                "files with the required pseudopotential filename were found, but "
                "none matched its byte size and SHA-256: "
                f"{required.filename} beneath {self.root}"
            )
        raise PseudopotentialNotFoundError(
            "required pseudopotential filename is unavailable beneath the library: "
            f"{required.filename} beneath {self.root}"
        )

    def build_repository(
        self, required: tuple[PseudopotentialFile, ...]
    ) -> PseudopotentialRepository:
        """Resolve requirements into an exact, byte-verifying repository."""
        if type(required) is not tuple:
            raise TypeError("required must be a tuple")
        if any(not isinstance(item, PseudopotentialFile) for item in required):
            raise TypeError("required must contain PseudopotentialFile values")
        return PseudopotentialRepository(
            entries=tuple(
                PseudopotentialRepositoryEntry(
                    pseudopotential_file=item,
                    path=self.resolve(item),
                )
                for item in required
            )
        )


@dataclass(frozen=True, slots=True)
class PseudopotentialRepositoryEntry:
    """Bind one declared pseudopotential file identity to its local path."""

    pseudopotential_file: PseudopotentialFile
    path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.pseudopotential_file, PseudopotentialFile):
            raise TypeError(
                "pseudopotential_file must inherit from PseudopotentialFile"
            )
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")


@dataclass(frozen=True, slots=True)
class PseudopotentialRepository:
    """Resolve required pseudopotentials from explicitly declared local entries."""

    entries: tuple[PseudopotentialRepositoryEntry, ...]

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise TypeError("repository entries must be a tuple")
        if any(
            type(entry) is not PseudopotentialRepositoryEntry for entry in self.entries
        ):
            raise TypeError(
                "repository entries must contain PseudopotentialRepositoryEntry values"
            )
        artifact_identities = tuple(
            _artifact_identity(entry.pseudopotential_file) for entry in self.entries
        )
        if len(artifact_identities) != len(set(artifact_identities)):
            raise ValueError(
                "repository artifact identities must be unique across metadata"
            )

    def resolve(self, required: PseudopotentialFile) -> Path:
        """Return the verified local path for one exact required identity."""
        if not isinstance(required, PseudopotentialFile):
            raise TypeError("required must inherit from PseudopotentialFile")
        matches = tuple(
            entry for entry in self.entries if entry.pseudopotential_file == required
        )
        if not matches:
            raise PseudopotentialNotFoundError(
                "required pseudopotential is not declared in the repository: "
                f"{required.symbol}/{required.filename}/{required.sha256}"
            )
        entry = matches[0]
        path = entry.path
        if not path.is_file() or path.is_symlink():
            raise PseudopotentialNotFoundError(
                f"declared pseudopotential file is unavailable: {path}"
            )
        observed_size = path.stat().st_size
        if observed_size != required.byte_size:
            raise PseudopotentialIntegrityError(
                "pseudopotential byte-size mismatch: "
                f"expected {required.byte_size}, observed {observed_size}: {path}"
            )
        observed_sha256 = _sha256(path)
        if observed_sha256 != required.sha256:
            raise PseudopotentialIntegrityError(
                "pseudopotential SHA-256 mismatch: "
                f"expected {required.sha256}, observed {observed_sha256}: {path}"
            )
        return path


def _matches_required_artifact(
    root: Path,
    path: Path,
    required: PseudopotentialFile,
) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    resolved_root = root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_relative_to(resolved_root):
        return False
    if resolved_path.stat().st_size != required.byte_size:
        return False
    return _sha256(resolved_path) == required.sha256


def _artifact_identity(
    pseudopotential_file: PseudopotentialFile,
) -> tuple[str, str, str, int]:
    return (
        pseudopotential_file.symbol,
        pseudopotential_file.filename,
        pseudopotential_file.sha256,
        pseudopotential_file.byte_size,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
