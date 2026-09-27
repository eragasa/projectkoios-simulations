"""Immutable native policy for Wannier-oriented Quantum ESPRESSO NSCF input."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class QeNscfOccupations(StrEnum):
    """Represent documented QE NSCF occupation modes."""

    fixed = "fixed"
    smearing = "smearing"
    tetrahedra = "tetrahedra"


@dataclass(frozen=True, slots=True)
class QeNscfKPoint:
    """Declare one source-ordered crystal-coordinate k-point and weight."""

    coordinates: tuple[float, float, float]
    weight: float

    def __post_init__(self) -> None:
        if type(self.coordinates) is not tuple or len(self.coordinates) != 3:
            raise ValueError("coordinates must contain three values")
        if any(
            type(value) is not float or not math.isfinite(value)
            for value in self.coordinates
        ):
            raise ValueError("coordinates must contain finite floats")
        if type(self.weight) is not float or not math.isfinite(self.weight):
            raise ValueError("weight must be a finite float")
        if self.weight <= 0.0:
            raise ValueError("weight must be positive")


@dataclass(frozen=True, slots=True)
class QeNscfProjectionConfiguration:
    """Declare all QE-native controls required for deterministic NSCF projection."""

    species: tuple[QeAtomicSpecies, ...]
    kpoints: tuple[QeNscfKPoint, ...]
    band_count: int
    wavefunction_cutoff_ry: float
    charge_density_cutoff_ry: float
    electronic_tolerance_ry: float
    occupations: QeNscfOccupations
    prefix: str
    pseudo_dir: str
    outdir: str
    input_filename: str
    parent_saved_state_manifest_sha256: str
    disable_symmetry: bool = True
    disable_time_reversal: bool = True
    coordinate_precision: int = 8
    kpoint_precision: int = 12

    def __post_init__(self) -> None:
        if not self.species or any(
            type(item) is not QeAtomicSpecies for item in self.species
        ):
            raise TypeError("species must contain QeAtomicSpecies values")
        symbols = tuple(item.symbol for item in self.species)
        filenames = tuple(item.pseudopotential_filename for item in self.species)
        if len(symbols) != len(set(symbols)):
            raise ValueError("species symbols must be unique")
        if len(filenames) != len(set(filenames)):
            raise ValueError("pseudopotential filenames must be unique")
        if not self.kpoints or any(
            type(item) is not QeNscfKPoint for item in self.kpoints
        ):
            raise TypeError("kpoints must contain QeNscfKPoint values")
        if not math.isclose(
            sum(item.weight for item in self.kpoints),
            1.0,
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        ):
            raise ValueError("k-point weights must sum to one")
        if type(self.band_count) is not int or self.band_count <= 0:
            raise ValueError("band_count must be a positive integer")
        for label, numeric_value in (
            ("wavefunction_cutoff_ry", self.wavefunction_cutoff_ry),
            ("charge_density_cutoff_ry", self.charge_density_cutoff_ry),
            ("electronic_tolerance_ry", self.electronic_tolerance_ry),
        ):
            if (
                type(numeric_value) is not float
                or not math.isfinite(numeric_value)
                or numeric_value <= 0.0
            ):
                raise ValueError(f"{label} must be positive and finite")
        if self.charge_density_cutoff_ry < self.wavefunction_cutoff_ry:
            raise ValueError(
                "charge-density cutoff must not be below wavefunction cutoff"
            )
        if type(self.occupations) is not QeNscfOccupations:
            raise TypeError("occupations must be a QeNscfOccupations")
        for label, text_value in (
            ("prefix", self.prefix),
            ("pseudo_dir", self.pseudo_dir),
            ("outdir", self.outdir),
        ):
            if (
                type(text_value) is not str
                or not text_value
                or text_value != text_value.strip()
                or "'" in text_value
            ):
                raise ValueError(f"{label} must be nonempty, stripped, and unquoted")
        if not _IDENTIFIER.fullmatch(self.prefix):
            raise ValueError("prefix must be a lowercase slug")
        if (
            type(self.input_filename) is not str
            or not self.input_filename
            or self.input_filename in {".", ".."}
            or "/" in self.input_filename
            or "\\" in self.input_filename
        ):
            raise ValueError("input_filename must be a basename")
        if (
            type(self.parent_saved_state_manifest_sha256) is not str
            or _SHA256.fullmatch(self.parent_saved_state_manifest_sha256) is None
        ):
            raise ValueError("parent saved-state manifest identity must be SHA-256")
        if (
            type(self.disable_symmetry) is not bool
            or type(self.disable_time_reversal) is not bool
        ):
            raise TypeError("symmetry controls must be booleans")
        if not self.disable_symmetry or not self.disable_time_reversal:
            raise ValueError(
                "Wannier-oriented NSCF projection requires symmetry and "
                "inversion reduction disabled"
            )
        for label, value in (
            ("coordinate_precision", self.coordinate_precision),
            ("kpoint_precision", self.kpoint_precision),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be a positive integer")
