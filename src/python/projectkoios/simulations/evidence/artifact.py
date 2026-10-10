"""Exact immutable artifact identities for retained simulation evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class EvidenceArtifactReference:
    """Identify retained artifact bytes without embedding a local path."""

    artifact_id: str
    role: str
    media_type: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("artifact_id", self.artifact_id),
            ("role", self.role),
            ("media_type", self.media_type),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be a positive integer")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("SHA-256 must be lowercase hexadecimal")
