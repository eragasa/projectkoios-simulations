"""Reusable calculator-neutral plane-wave DFT SCF specifications."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from projectkoios.simulations.dft.electronic import (
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

_SIMULATION_ID = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z][A-Za-z0-9-]*)+")


@dataclass(frozen=True, slots=True)
class PwDftScfSpecification:
    """Declare reusable scientific SCF intent without occurrence identity."""

    simulation_id: str
    simulation: PwDftSimulation
    kpoint_sampling: PwDftKPointSamplingPolicy
    wavefunction_cutoff_ev: float
    occupation: DftOccupationPolicy
    electronic_convergence: PwDftElectronicConvergencePolicy

    def __post_init__(self) -> None:
        if type(self.simulation_id) is not str or not _SIMULATION_ID.fullmatch(
            self.simulation_id
        ):
            raise ValueError("simulation_id must be a qualified stable identifier")
        if type(self.simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if type(self.kpoint_sampling) is not PwDftKPointSamplingPolicy:
            raise TypeError("kpoint_sampling must be a PwDftKPointSamplingPolicy")
        if (
            type(self.wavefunction_cutoff_ev) is not float
            or not math.isfinite(self.wavefunction_cutoff_ev)
            or self.wavefunction_cutoff_ev <= 0.0
        ):
            raise ValueError("wavefunction_cutoff_ev must be positive and finite")
        if type(self.occupation) is not DftOccupationPolicy:
            raise TypeError("occupation must be a DftOccupationPolicy")
        if type(self.electronic_convergence) is not PwDftElectronicConvergencePolicy:
            raise TypeError(
                "electronic_convergence must be a PwDftElectronicConvergencePolicy"
            )
