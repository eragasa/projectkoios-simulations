"""Calculator-neutral pseudopotential records."""

from __future__ import annotations

import re
from dataclasses import dataclass

_ELEMENT_SYMBOL = re.compile(r"[A-Z][a-z]?")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class Pseudopotential:
    """Represent calculator-neutral pseudopotential metadata."""

    symbol: str
    exchange_correlation: str
    formalism: str
    relativistic_treatment: str
    valence_electrons: int

    def __post_init__(self) -> None:
        if not _ELEMENT_SYMBOL.fullmatch(self.symbol):
            raise ValueError("pseudopotential symbol must be an element symbol")
        for label, value in (
            ("exchange_correlation", self.exchange_correlation),
            ("formalism", self.formalism),
            ("relativistic_treatment", self.relativistic_treatment),
        ):
            if type(value) is not str:
                raise TypeError(f"{label} must be a string")
            if not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.valence_electrons) is not int:
            raise TypeError("valence_electrons must be an integer")
        if self.valence_electrons <= 0:
            raise ValueError("valence_electrons must be positive")


@dataclass(frozen=True, slots=True)
class PseudopotentialFile:
    """Bind one pseudopotential definition to exact external file identity."""

    pseudopotential: Pseudopotential
    filename: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.pseudopotential, Pseudopotential):
            raise TypeError("pseudopotential must inherit from Pseudopotential")
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("pseudopotential filename must be a basename")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("pseudopotential SHA-256 must be lowercase hexadecimal")
        if type(self.byte_size) is not int:
            raise TypeError("pseudopotential byte_size must be an integer")
        if self.byte_size <= 0:
            raise ValueError("pseudopotential byte_size must be positive")

    @property
    def symbol(self) -> str:
        """Return the bound pseudopotential's element symbol."""
        return self.pseudopotential.symbol
