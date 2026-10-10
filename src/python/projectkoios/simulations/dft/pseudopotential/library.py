"""Resolve exact pseudopotential identities from an explicit local library."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from projectkoios.simulations.dft.pseudopotential.model import PseudopotentialFile


class PseudopotentialNotFoundError(LookupError):
    """Report an undeclared or unavailable required pseudopotential artifact."""


class PseudopotentialIntegrityError(ValueError):
    """Report a library artifact that fails its declared byte identity."""


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
        if self.root.is_symlink() or not self.root.is_dir():
            raise PseudopotentialNotFoundError(
                f"pseudopotential library root is unavailable: {self.root}"
            )
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


def _matches_required_artifact(
    root: Path,
    path: Path,
    required: PseudopotentialFile,
) -> bool:
    current = path
    while current != root:
        if current.is_symlink():
            return False
        current = current.parent
    if not path.is_file():
        return False
    resolved_root = root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_relative_to(resolved_root):
        return False
    if resolved_path.stat().st_size != required.byte_size:
        return False
    return _sha256(resolved_path) == required.sha256


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
