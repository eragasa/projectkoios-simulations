"""Exact calculator-input artifact and external requirement records."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_SHA256 = re.compile(r"[0-9a-f]{64}")
_ROLE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class CalculatorInputArtifact:
    """Retain one exact rendered calculator input file."""

    role: str
    filename: str
    media_type: str
    content: bytes
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if type(self.role) is not str or not _ROLE.fullmatch(self.role):
            raise ValueError("calculator input artifact role must be a lowercase slug")
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("calculator input artifact filename must be a basename")
        if (
            type(self.media_type) is not str
            or not self.media_type
            or self.media_type != self.media_type.strip()
        ):
            raise ValueError("calculator input artifact media_type must be nonempty")
        if type(self.content) is not bytes:
            raise TypeError("calculator input artifact content must be bytes")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("calculator input artifact byte_size must be positive")
        if self.byte_size != len(self.content):
            raise ValueError("calculator input artifact byte_size must match content")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError(
                "calculator input artifact SHA-256 must be lowercase hexadecimal"
            )
        if hashlib.sha256(self.content).hexdigest() != self.sha256:
            raise ValueError("calculator input artifact SHA-256 must match content")


@dataclass(frozen=True, slots=True)
class CalculatorExternalInputRequirement:
    """Require one exact external input without resolving a local path."""

    role: str
    stable_id: str
    filename: str
    format: str
    byte_size: int
    sha256: str
    provenance: str
    element_symbol: str | None = None

    def __post_init__(self) -> None:
        if type(self.role) is not str or not _ROLE.fullmatch(self.role):
            raise ValueError("external input role must be a lowercase slug")
        for label, value in (
            ("stable_id", self.stable_id),
            ("format", self.format),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(
                    f"external input {label} must be nonempty and stripped"
                )
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("external input filename must be a basename")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("external input byte_size must be positive")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("external input SHA-256 must be lowercase hexadecimal")
        if (
            type(self.provenance) is not str
            or not self.provenance
            or self.provenance != self.provenance.strip()
        ):
            raise ValueError("external input provenance must be nonempty and stripped")
        if self.element_symbol is not None and (
            type(self.element_symbol) is not str
            or not re.fullmatch(r"[A-Z][a-z]?", self.element_symbol)
        ):
            raise ValueError("element_symbol must be an element symbol or None")
