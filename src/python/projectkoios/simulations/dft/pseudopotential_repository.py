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
        identities = tuple(
            (
                entry.pseudopotential_file.symbol,
                entry.pseudopotential_file.filename,
                entry.pseudopotential_file.sha256,
                entry.pseudopotential_file.byte_size,
            )
            for entry in self.entries
        )
        if len(identities) != len(set(identities)):
            raise ValueError("repository pseudopotential identities must be unique")

    def resolve(self, required: PseudopotentialFile) -> Path:
        """Return the verified local path for one exact required identity."""
        if not isinstance(required, PseudopotentialFile):
            raise TypeError("required must inherit from PseudopotentialFile")
        matches = tuple(
            entry
            for entry in self.entries
            if _identity(entry.pseudopotential_file) == _identity(required)
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


def _identity(pseudopotential_file: PseudopotentialFile) -> tuple[str, str, str, int]:
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
