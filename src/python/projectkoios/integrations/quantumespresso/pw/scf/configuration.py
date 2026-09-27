"""Immutable Quantum ESPRESSO policy for common SCF projection."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_ELEMENT = re.compile(r"[A-Z][a-z]?")


@dataclass(frozen=True, slots=True)
class QeScfSpeciesConfiguration:
    """Declare one QE species mass and external pseudopotential filename."""

    symbol: str
    mass_amu: float
    pseudopotential_filename: str

    def __post_init__(self) -> None:
        if not _ELEMENT.fullmatch(self.symbol):
            raise ValueError("symbol must be an element symbol")
        if not math.isfinite(self.mass_amu) or self.mass_amu <= 0.0:
            raise ValueError("mass_amu must be positive and finite")
        filename = self.pseudopotential_filename
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
        ):
            raise ValueError("pseudopotential_filename must be a basename")


@dataclass(frozen=True, slots=True)
class QeScfProjectionConfiguration:
    """Declare QE-native controls not implied by common SCF intent."""

    species: tuple[QeScfSpeciesConfiguration, ...]
    charge_density_cutoff_ratio: float = 8.0
    electronic_tolerance_ry: float = 1.0e-6
    prefix: str = "system"
    pseudo_dir: str = "./"
    outdir: str = "./tmp/"
    input_filename: str = "pw.in"
    coordinate_precision: int = 8

    def __post_init__(self) -> None:
        if type(self.species) is not tuple or not self.species:
            raise ValueError("species must be a nonempty tuple")
        if any(type(item) is not QeScfSpeciesConfiguration for item in self.species):
            raise TypeError("species must contain QeScfSpeciesConfiguration values")
        symbols = tuple(item.symbol for item in self.species)
        filenames = tuple(item.pseudopotential_filename for item in self.species)
        if len(set(symbols)) != len(symbols):
            raise ValueError("species symbols must be unique")
        if len(set(filenames)) != len(filenames):
            raise ValueError("pseudopotential filenames must be unique")
        if (
            not math.isfinite(self.charge_density_cutoff_ratio)
            or self.charge_density_cutoff_ratio <= 0.0
        ):
            raise ValueError("charge_density_cutoff_ratio must be positive and finite")
        if (
            not math.isfinite(self.electronic_tolerance_ry)
            or self.electronic_tolerance_ry <= 0.0
        ):
            raise ValueError("electronic_tolerance_ry must be positive and finite")
        for label, value in (
            ("prefix", self.prefix),
            ("pseudo_dir", self.pseudo_dir),
            ("outdir", self.outdir),
        ):
            if not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        filename = self.input_filename
        if (
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
        ):
            raise ValueError("input_filename must be a basename")
        if type(self.coordinate_precision) is not int or self.coordinate_precision < 1:
            raise ValueError("coordinate_precision must be a positive integer")
