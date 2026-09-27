"""Immutable, execution-disabled LAMMPS reconstruction observations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

_SHA256 = re.compile(r"[0-9a-f]{64}")
_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,127}")
AtomStyle = str
Bounds3 = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
Vector3 = tuple[float, float, float]


def _relative(value: str, label: str = "LAMMPS path") -> None:
    path = PurePosixPath(value)
    if (
        not value
        or value == "."
        or value != path.as_posix()
        or path.is_absolute()
        or "." in path.parts
        or ".." in path.parts
    ):
        raise ValueError(f"{label} must be normalized and relative")


@dataclass(frozen=True, slots=True)
class SourceFileEvidence:
    """Identify one retained source file without granting read authority."""

    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        _relative(self.relative_path, "relative_path")
        if _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        if type(self.byte_size) is not int or not 0 <= self.byte_size <= 1_000_000_000:
            raise ValueError("byte_size is outside the reconstruction bound")

    def to_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "sha256": self.sha256,
            "byte_size": self.byte_size,
        }


@dataclass(frozen=True, slots=True)
class ObservedSetting:
    """Retain one source-located historical configuration setting."""

    key: str
    values: tuple[str, ...]
    evidence_path: str
    line_number: int

    def __post_init__(self) -> None:
        if _NAME.fullmatch(self.key) is None:
            raise ValueError("setting key is invalid")
        if not isinstance(self.values, tuple) or not 1 <= len(self.values) <= 32:
            raise ValueError("setting values are outside the reconstruction bound")
        if any(
            type(value) is not str or not value or len(value) > 512
            for value in self.values
        ):
            raise ValueError("setting value is invalid")
        _relative(self.evidence_path, "evidence_path")
        if type(self.line_number) is not int or not 1 <= self.line_number <= 1_000_000:
            raise ValueError("line_number is invalid")


@dataclass(frozen=True, slots=True)
class LammpsCommandIntent:
    simulation_name: str
    executable_environment_variable: str
    input_script: str
    stdout_artifact: str
    runner_script: SourceFileEvidence
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if (
            type(self.simulation_name) is not str
            or not self.simulation_name
            or len(self.simulation_name) > 128
        ):
            raise ValueError("simulation name is invalid")
        if self.executable_environment_variable != "LAMMPS_BIN":
            raise ValueError("only the explicit LAMMPS_BIN boundary is supported")
        _relative(self.input_script)
        _relative(self.stdout_artifact)
        if type(self.runner_script) is not SourceFileEvidence:
            raise TypeError("runner_script must be SourceFileEvidence")
        if self.execution_authorized:
            raise ValueError("a LAMMPS command intent cannot authorize execution")

    def to_dict(self) -> dict[str, object]:
        return {
            "simulation_name": self.simulation_name,
            "program": "lammps",
            "executable_environment_variable": self.executable_environment_variable,
            "arguments": ["-i", self.input_script],
            "stdout_artifact": self.stdout_artifact,
            "runner_script": self.runner_script.to_dict(),
            "execution_authorized": self.execution_authorized,
        }


@dataclass(frozen=True, slots=True)
class LammpsTemplateObservation:
    simulation_name: str
    template_directory: str
    files: tuple[SourceFileEvidence, ...]
    command_intent: LammpsCommandIntent

    def __post_init__(self) -> None:
        _relative(self.template_directory)
        if not isinstance(self.files, tuple) or not self.files:
            raise ValueError("LAMMPS template must retain file evidence")
        if any(type(item) is not SourceFileEvidence for item in self.files):
            raise TypeError("LAMMPS template files must be SourceFileEvidence")
        paths = tuple(item.relative_path for item in self.files)
        if paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
            raise ValueError("LAMMPS template files must have unique sorted paths")
        if type(self.command_intent) is not LammpsCommandIntent:
            raise TypeError("command_intent must be LammpsCommandIntent")
        if self.command_intent.simulation_name != self.simulation_name:
            raise ValueError("command intent simulation name does not agree")

    def to_dict(self) -> dict[str, object]:
        return {
            "simulation_name": self.simulation_name,
            "template_directory": self.template_directory,
            "files": [item.to_dict() for item in self.files],
            "command_intent": self.command_intent.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class LammpsIntegrationObservation:
    templates: tuple[LammpsTemplateObservation, ...]
    external_execution_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.templates, tuple) or not self.templates:
            raise ValueError("LAMMPS integration requires templates")
        if any(type(item) is not LammpsTemplateObservation for item in self.templates):
            raise TypeError("templates must contain LammpsTemplateObservation")
        names = tuple(item.simulation_name for item in self.templates)
        if len(names) != len(set(names)):
            raise ValueError("LAMMPS simulation names must be unique")
        if self.external_execution_authorized:
            raise ValueError("LAMMPS integration cannot authorize execution")

    def to_dict(self) -> dict[str, object]:
        return {
            "calculator": "lammps",
            "templates": [item.to_dict() for item in self.templates],
            "external_execution_authorized": self.external_execution_authorized,
            "numerical_verification_claimed": False,
            "scientific_validation_claimed": False,
        }


@dataclass(frozen=True, slots=True)
class LammpsDataStructureObservation:
    """Retain bounded syntax observations from one LAMMPS data-file text."""

    name: str
    evidence: SourceFileEvidence
    species_order: tuple[str, ...]
    atom_count: int
    atom_type_count: int
    atom_style: AtomStyle
    bounds: Bounds3
    tilt_factors: Vector3

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name or len(self.name) > 128:
            raise ValueError("structure name is invalid")
        if type(self.evidence) is not SourceFileEvidence:
            raise TypeError("evidence must be SourceFileEvidence")
        if not self.species_order or len(self.species_order) != len(
            set(self.species_order)
        ):
            raise ValueError("species order must be nonempty and unique")
        if self.atom_count <= 0 or self.atom_type_count != len(self.species_order):
            raise ValueError("atom and atom-type counts are inconsistent")
        if self.atom_style not in {"atomic", "charge"}:
            raise ValueError("LAMMPS atom style is unsupported")
        if len(self.bounds) != 3 or any(
            len(bound) != 2
            or not all(math.isfinite(value) for value in bound)
            or bound[0] >= bound[1]
            for bound in self.bounds
        ):
            raise ValueError("LAMMPS bounds must be three finite increasing pairs")
        if len(self.tilt_factors) != 3 or not all(
            math.isfinite(value) for value in self.tilt_factors
        ):
            raise ValueError("tilt factors must contain three finite values")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "evidence": self.evidence.to_dict(),
            "species_order": list(self.species_order),
            "atom_count": self.atom_count,
            "atom_type_count": self.atom_type_count,
            "atom_style": self.atom_style,
            "bounds": [list(bound) for bound in self.bounds],
            "tilt_factors": list(self.tilt_factors),
            "calculator_execution_authorized": False,
            "scientific_validation_claimed": False,
        }
