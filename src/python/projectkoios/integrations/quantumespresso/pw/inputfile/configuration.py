"""Shared validated configuration for ``pw.x`` input projection."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)


@dataclass(frozen=True, slots=True)
class QeRelaxationInputConfiguration:
    """Declare native fields shared by fixed- and variable-cell relaxation."""

    species: tuple[QeAtomicSpecies, ...]
    ion_dynamics: QeIonDynamics
    charge_density_cutoff_ratio: float
    electronic_tolerance_ry: float
    prefix: str
    pseudo_dir: str
    outdir: str
    input_filename: str
    coordinate_precision: int

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
        if type(self.ion_dynamics) is not QeIonDynamics:
            raise TypeError("ion_dynamics must be a QeIonDynamics")
        for label, value in (
            ("charge_density_cutoff_ratio", self.charge_density_cutoff_ratio),
            ("electronic_tolerance_ry", self.electronic_tolerance_ry),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")
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
                or "\n" in text_value
                or "\r" in text_value
            ):
                raise ValueError(f"{label} must be nonempty, stripped, and unquoted")
        if (
            type(self.input_filename) is not str
            or not self.input_filename
            or self.input_filename in {".", ".."}
            or "/" in self.input_filename
            or "\\" in self.input_filename
        ):
            raise ValueError("input_filename must be a basename")
        if type(self.coordinate_precision) is not int or self.coordinate_precision <= 0:
            raise ValueError("coordinate_precision must be a positive integer")
