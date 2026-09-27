"""Define provenance-bound Quantum ESPRESSO relaxation calculations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)

type QeRelaxationPhase = Literal["relax", "vc-relax"]

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ELEMENT_SYMBOL = re.compile(r"[A-Z][a-z]?")


@dataclass(frozen=True, slots=True)
class FileIdentity:
    """Identify one external regular file by byte size and SHA-256."""

    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be a positive integer")
        _validate_sha256(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class StructureIdentity(FileIdentity):
    """Identify one source-controlled unit-cell declaration."""

    repository_path: str
    structure_id: str

    def __post_init__(self) -> None:
        super(StructureIdentity, self).__post_init__()
        _validate_string(self.repository_path, "repository_path")
        repository_path = PurePosixPath(self.repository_path)
        if repository_path.is_absolute() or "\\" in self.repository_path:
            raise ValueError("repository_path must be a relative POSIX path")
        _validate_string(self.structure_id, "structure_id")


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationConfiguration:
    """Hold reviewed scientific, resource, and native QE declarations."""

    calculation_id: str
    phase: QeRelaxationPhase
    integration_id: str
    energy_convergence_tolerance_mev_per_atom: float
    structure: StructureIdentity
    calculator: FileIdentity
    calculator_program: str
    calculator_version: str
    calculator_source_revision: str
    pseudopotential: FileIdentity
    pseudopotential_symbol: str
    pseudopotential_filename: str
    pseudopotential_exchange_correlation: str
    pseudopotential_formalism: str
    pseudopotential_relativistic_treatment: str
    pseudopotential_upf_version: str
    pseudopotential_mass_amu: float
    kpoint_mesh: tuple[int, int, int]
    kpoint_shift: tuple[int, int, int]
    wavefunction_cutoff_ry: float
    charge_density_cutoff_ry: float
    electronic_tolerance_ry: float
    maximum_ionic_steps: int
    total_energy_tolerance_ry: float
    force_tolerance_ry_per_bohr: float
    target_pressure_kbar: float | None
    pressure_tolerance_kbar: float | None
    prefix: str
    pseudo_dir: str
    outdir: str
    input_filename: str
    coordinate_precision: int
    ion_dynamics: QeIonDynamics
    cell_dynamics: QeCellDynamics | None
    cell_degrees_of_freedom: QeCellDegreesOfFreedom | None
    qualification_statements: tuple[str, ...]

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.calculation_id):
            raise ValueError("calculation_id must be a lowercase slug")
        if self.phase not in ("relax", "vc-relax"):
            raise ValueError("phase must be relax or vc-relax")
        if self.integration_id != "quantum-espresso":
            raise ValueError("integration_id must be quantum-espresso")
        _positive_float(
            self.energy_convergence_tolerance_mev_per_atom,
            "energy_convergence_tolerance_mev_per_atom",
        )
        if type(self.structure) is not StructureIdentity:
            raise TypeError("structure must be a StructureIdentity")
        if type(self.calculator) is not FileIdentity:
            raise TypeError("calculator must be a FileIdentity")
        if type(self.pseudopotential) is not FileIdentity:
            raise TypeError("pseudopotential must be a FileIdentity")
        if self.calculator_program != "pw.x":
            raise ValueError("calculator_program must be pw.x")
        _validate_string(self.calculator_version, "calculator_version")
        _validate_sha1(self.calculator_source_revision, "calculator_source_revision")
        if not _ELEMENT_SYMBOL.fullmatch(self.pseudopotential_symbol):
            raise ValueError("pseudopotential_symbol must be an element symbol")
        _validate_basename(
            self.pseudopotential_filename,
            "pseudopotential_filename",
        )
        for label, text_value in (
            (
                "pseudopotential_exchange_correlation",
                self.pseudopotential_exchange_correlation,
            ),
            ("pseudopotential_formalism", self.pseudopotential_formalism),
            (
                "pseudopotential_relativistic_treatment",
                self.pseudopotential_relativistic_treatment,
            ),
            ("pseudopotential_upf_version", self.pseudopotential_upf_version),
        ):
            _validate_string(text_value, label)
        for label, numeric_value in (
            ("pseudopotential_mass_amu", self.pseudopotential_mass_amu),
            ("wavefunction_cutoff_ry", self.wavefunction_cutoff_ry),
            ("charge_density_cutoff_ry", self.charge_density_cutoff_ry),
            ("electronic_tolerance_ry", self.electronic_tolerance_ry),
            ("total_energy_tolerance_ry", self.total_energy_tolerance_ry),
            ("force_tolerance_ry_per_bohr", self.force_tolerance_ry_per_bohr),
        ):
            _positive_float(numeric_value, label)
        if self.charge_density_cutoff_ry < self.wavefunction_cutoff_ry:
            raise ValueError(
                "charge_density_cutoff_ry must not be below wavefunction cutoff"
            )
        _validate_positive_triplet(self.kpoint_mesh, "kpoint_mesh")
        if len(self.kpoint_shift) != 3 or any(
            type(value) is not int or value not in {0, 1} for value in self.kpoint_shift
        ):
            raise ValueError("kpoint_shift must contain three zero-or-one integers")
        if type(self.maximum_ionic_steps) is not int or self.maximum_ionic_steps <= 0:
            raise ValueError("maximum_ionic_steps must be a positive integer")
        if self.target_pressure_kbar is not None:
            _finite_float(self.target_pressure_kbar, "target_pressure_kbar")
        if self.pressure_tolerance_kbar is not None:
            _positive_float(self.pressure_tolerance_kbar, "pressure_tolerance_kbar")
        if not _IDENTIFIER.fullmatch(self.prefix):
            raise ValueError("prefix must be a lowercase slug")
        if self.pseudo_dir != "./":
            raise ValueError("pseudo_dir must be ./")
        if self.outdir != "./tmp/":
            raise ValueError("outdir must be ./tmp/")
        _validate_basename(self.input_filename, "input_filename")
        if type(self.coordinate_precision) is not int or self.coordinate_precision <= 0:
            raise ValueError("coordinate_precision must be a positive integer")
        if type(self.ion_dynamics) is not QeIonDynamics:
            raise TypeError("ion_dynamics must be a QeIonDynamics")
        if (
            self.cell_dynamics is not None
            and type(self.cell_dynamics) is not QeCellDynamics
        ):
            raise TypeError("cell_dynamics must be a QeCellDynamics or None")
        if self.cell_degrees_of_freedom is not None and (
            type(self.cell_degrees_of_freedom) is not QeCellDegreesOfFreedom
        ):
            raise TypeError(
                "cell_degrees_of_freedom must be a QeCellDegreesOfFreedom or None"
            )
        if self.phase == "relax":
            if any(
                value is not None
                for value in (
                    self.target_pressure_kbar,
                    self.pressure_tolerance_kbar,
                    self.cell_dynamics,
                    self.cell_degrees_of_freedom,
                )
            ):
                raise ValueError("relax must not declare cell controls")
        elif any(
            value is None
            for value in (
                self.target_pressure_kbar,
                self.pressure_tolerance_kbar,
                self.cell_dynamics,
                self.cell_degrees_of_freedom,
            )
        ):
            raise ValueError("vc-relax requires pressure and cell controls")
        if not self.qualification_statements or any(
            type(statement) is not str
            or not statement
            or statement != statement.strip()
            for statement in self.qualification_statements
        ):
            raise ValueError("qualification_statements must be nonempty strings")


def _validate_string(value: object, label: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be a nonempty stripped string")


def _validate_basename(value: str, label: str) -> None:
    _validate_string(value, label)
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be a basename")


def _validate_sha256(value: str, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")


def _validate_sha1(value: str, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase Git SHA-1")


def _positive_float(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{label} must be positive and finite")


def _finite_float(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _validate_positive_triplet(value: tuple[int, int, int], label: str) -> None:
    if len(value) != 3 or any(type(item) is not int or item <= 0 for item in value):
        raise ValueError(f"{label} must contain three positive integers")
