"""Immutable VASP-native policy used when projecting common SCF intent."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VaspScfProjectionConfiguration:
    """Declare VASP electronic controls not implied by common SCF intent."""

    system_label: str = "Plane-wave DFT SCF"
    poscar_comment: str = "Plane-wave DFT SCF"
    algorithm: str = "Normal"
    maximum_electronic_steps: int = 60
    electronic_tolerance_ev: float = 1.0e-6
    smearing_method: int = 0
    smearing_width_ev: float = 0.05
    spin_polarization: int = 1
    real_space_projection: bool = False

    def __post_init__(self) -> None:
        if not self.system_label or self.system_label != self.system_label.strip():
            raise ValueError("system_label must be nonempty and stripped")
        if (
            not self.poscar_comment
            or self.poscar_comment != self.poscar_comment.strip()
        ):
            raise ValueError("poscar_comment must be nonempty and stripped")
        if not self.algorithm or self.algorithm != self.algorithm.strip():
            raise ValueError("algorithm must be nonempty and stripped")
        if self.maximum_electronic_steps <= 0:
            raise ValueError("maximum_electronic_steps must be positive")
        if (
            not math.isfinite(self.electronic_tolerance_ev)
            or self.electronic_tolerance_ev <= 0.0
        ):
            raise ValueError("electronic_tolerance_ev must be positive and finite")
        if not math.isfinite(self.smearing_width_ev) or self.smearing_width_ev < 0.0:
            raise ValueError("smearing_width_ev must be nonnegative and finite")
        if self.spin_polarization not in {1, 2}:
            raise ValueError("spin_polarization must be 1 or 2")
