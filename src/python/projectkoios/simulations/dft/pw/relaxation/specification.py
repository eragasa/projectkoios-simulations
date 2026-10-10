"""Reusable calculator-neutral plane-wave DFT relaxation specifications."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from projectkoios.simulations.dft.electronic import (
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftCellRelaxationMode,
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationDegreesOfFreedom,
    PwDftRelaxationInitialization,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

_SIMULATION_ID = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z][A-Za-z0-9-]*)+")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationSpecification:
    """Declare reusable structural-relaxation scientific intent."""

    simulation_id: str
    simulation: PwDftSimulation
    kpoint_sampling: PwDftKPointSamplingPolicy
    wavefunction_cutoff_ev: float
    occupation: DftOccupationPolicy
    electronic_convergence: PwDftElectronicConvergencePolicy
    initialization: PwDftRelaxationInitialization
    degrees_of_freedom: PwDftRelaxationDegreesOfFreedom
    ionic_convergence: PwDftRelaxationConvergencePolicy

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
        if type(self.initialization) is not PwDftRelaxationInitialization:
            raise TypeError("initialization must be a PwDftRelaxationInitialization")
        if type(self.degrees_of_freedom) is not PwDftRelaxationDegreesOfFreedom:
            raise TypeError(
                "degrees_of_freedom must be a PwDftRelaxationDegreesOfFreedom"
            )
        if type(self.ionic_convergence) is not PwDftRelaxationConvergencePolicy:
            raise TypeError(
                "ionic_convergence must be a PwDftRelaxationConvergencePolicy"
            )

        # Pressure controls describe active lattice relaxation only. Keeping this
        # invariant here prevents providers from inferring scientific intent.
        has_pressure = self.ionic_convergence.target_pressure_kbar is not None
        has_pressure_tolerance = (
            self.ionic_convergence.pressure_tolerance_kbar is not None
        )
        if self.degrees_of_freedom.cell_mode is PwDftCellRelaxationMode.FIXED:
            if has_pressure or has_pressure_tolerance:
                raise ValueError(
                    "fixed-cell relaxation must not declare pressure controls"
                )
        elif not has_pressure or not has_pressure_tolerance:
            raise ValueError(
                "active-cell relaxation requires target and tolerance pressures"
            )

    @property
    def scope(self) -> PwDftRelaxationScope:
        """Return the backend-capability scope implied by lattice freedom."""
        if self.degrees_of_freedom.cell_mode is PwDftCellRelaxationMode.FIXED:
            return PwDftRelaxationScope.ATOMIC_POSITIONS
        return PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
