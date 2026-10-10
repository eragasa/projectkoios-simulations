"""Calculator-neutral plane-wave DFT relaxation observations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from projectkoios.physkit.mechanics.stress import StressTensor
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.simulations.calculator import CalculatorIntegrationId

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationNativeArtifact:
    """Identify one retained native artifact supporting an observation."""

    integration_id: CalculatorIntegrationId
    artifact_id: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be CalculatorIntegrationId")
        if (
            type(self.artifact_id) is not str
            or not self.artifact_id
            or self.artifact_id != self.artifact_id.strip()
        ):
            raise ValueError("artifact_id must be nonempty and stripped")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("artifact SHA-256 must be lowercase hexadecimal")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("artifact byte_size must be positive")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationObservation:
    """Retain normalized terminal geometry and mechanical convergence facts."""

    final_unit_cell: UnitCell
    ionic_step_count: int
    completed: bool
    ionic_converged: bool
    cell_converged: bool | None
    final_total_energy_ev: float | None
    maximum_force_ev_per_angstrom: float | None
    pressure_kbar: float | None
    stress_tensor: StressTensor | None
    total_magnetization_electrons: float | None
    program_version: str | None
    native_artifacts: tuple[PwDftRelaxationNativeArtifact, ...]

    def __post_init__(self) -> None:
        if type(self.final_unit_cell) is not UnitCell:
            raise TypeError("final_unit_cell must be an exact base UnitCell")
        if type(self.ionic_step_count) is not int or self.ionic_step_count < 0:
            raise ValueError("ionic_step_count must be nonnegative")
        if type(self.completed) is not bool or type(self.ionic_converged) is not bool:
            raise TypeError("completed and ionic_converged must be booleans")
        if self.cell_converged is not None and type(self.cell_converged) is not bool:
            raise TypeError("cell_converged must be a bool or None")
        for label, value in (
            ("final_total_energy_ev", self.final_total_energy_ev),
            (
                "maximum_force_ev_per_angstrom",
                self.maximum_force_ev_per_angstrom,
            ),
            ("pressure_kbar", self.pressure_kbar),
            (
                "total_magnetization_electrons",
                self.total_magnetization_electrons,
            ),
        ):
            if value is not None and (
                type(value) is not float or not math.isfinite(value)
            ):
                raise ValueError(f"{label} must be a finite float when represented")
        if self.maximum_force_ev_per_angstrom is not None and (
            self.maximum_force_ev_per_angstrom < 0.0
        ):
            raise ValueError("maximum_force_ev_per_angstrom must be nonnegative")
        if (
            self.stress_tensor is not None
            and type(self.stress_tensor) is not StressTensor
        ):
            raise TypeError("stress_tensor must be a StressTensor or None")
        if self.program_version is not None and (
            type(self.program_version) is not str
            or not self.program_version
            or self.program_version != self.program_version.strip()
        ):
            raise ValueError("program_version must be nonempty when represented")
        if type(self.native_artifacts) is not tuple or not self.native_artifacts:
            raise ValueError("native_artifacts must be a nonempty tuple")
        if any(
            type(value) is not PwDftRelaxationNativeArtifact
            for value in self.native_artifacts
        ):
            raise TypeError(
                "native_artifacts must contain PwDftRelaxationNativeArtifact values"
            )
