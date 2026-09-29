"""Typed Quantum ESPRESSO ionic and lattice-vector relaxation options."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)


@dataclass(frozen=True, slots=True)
class QeIonicRelaxationOptions:
    """Hold validated QE options governing ionic-coordinate relaxation."""

    dynamics: QeIonDynamics
    maximum_steps: int
    total_energy_tolerance_ry: float
    force_tolerance_ry_per_bohr: float

    def __post_init__(self) -> None:
        if type(self.dynamics) is not QeIonDynamics:
            raise TypeError("dynamics must be a QeIonDynamics")
        if type(self.maximum_steps) is not int or self.maximum_steps <= 0:
            raise ValueError("maximum_steps must be positive")
        for label, value in (
            ("total_energy_tolerance_ry", self.total_energy_tolerance_ry),
            ("force_tolerance_ry_per_bohr", self.force_tolerance_ry_per_bohr),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")


@dataclass(frozen=True, slots=True)
class QeLatticeVectorRelaxationOptions:
    """Hold validated QE options governing lattice-vector relaxation."""

    dynamics: QeCellDynamics
    degrees_of_freedom: QeCellDegreesOfFreedom
    target_pressure_kbar: float
    pressure_tolerance_kbar: float

    def __post_init__(self) -> None:
        if type(self.dynamics) is not QeCellDynamics:
            raise TypeError("dynamics must be a QeCellDynamics")
        if type(self.degrees_of_freedom) is not QeCellDegreesOfFreedom:
            raise TypeError("degrees_of_freedom must be a QeCellDegreesOfFreedom")
        if type(self.target_pressure_kbar) is not float or not math.isfinite(
            self.target_pressure_kbar
        ):
            raise ValueError("target_pressure_kbar must be finite")
        if (
            type(self.pressure_tolerance_kbar) is not float
            or not math.isfinite(self.pressure_tolerance_kbar)
            or self.pressure_tolerance_kbar <= 0.0
        ):
            raise ValueError("pressure_tolerance_kbar must be positive and finite")
