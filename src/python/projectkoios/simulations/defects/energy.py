"""Method-neutral exact energy-evidence records for defect arithmetic."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

_SHA256 = re.compile(r"[0-9a-f]{64}")


class DefectEnergyRole(StrEnum):
    """Identify the scientific role of one retained total energy."""

    PRISTINE = "pristine"
    DEFECT = "defect"
    IDEAL_DEFECT = "ideal-defect"
    ION_RELAXED_DEFECT = "ion-relaxed-defect"
    FULLY_RELAXED_DEFECT = "fully-relaxed-defect"
    ELEMENTAL_REFERENCE = "elemental-reference"


@dataclass(frozen=True, slots=True)
class DefectContentReference:
    """Identify exact retained content without importing its owning package."""

    stable_id: str
    representation: str
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("stable_id", self.stable_id),
            ("representation", self.representation),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.schema_version) is not int or self.schema_version <= 0:
            raise ValueError("schema_version must be a positive integer")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be a positive integer")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("SHA-256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class DefectEnergyEvidence:
    """Retain one exact total energy with method and structure correlation."""

    energy_id: str
    role: DefectEnergyRole
    energy_ev: float
    atom_count: int
    structure: DefectContentReference
    calculation: DefectContentReference
    method_id: str
    model_id: str
    qualification_id: str
    final_single_point: bool
    completed: bool
    converged: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("energy_id", self.energy_id),
            ("method_id", self.method_id),
            ("model_id", self.model_id),
            ("qualification_id", self.qualification_id),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.role) is not DefectEnergyRole:
            raise TypeError("role must be a DefectEnergyRole")
        if type(self.energy_ev) is not float or not math.isfinite(self.energy_ev):
            raise ValueError("energy_ev must be a finite float")
        if type(self.atom_count) is not int or self.atom_count <= 0:
            raise ValueError("atom_count must be a positive integer")
        if type(self.structure) is not DefectContentReference:
            raise TypeError("structure must be a DefectContentReference")
        if type(self.calculation) is not DefectContentReference:
            raise TypeError("calculation must be a DefectContentReference")
        if any(
            type(value) is not bool
            for value in (self.final_single_point, self.completed, self.converged)
        ):
            raise TypeError(
                "final_single_point, completed, and converged must be booleans"
            )
