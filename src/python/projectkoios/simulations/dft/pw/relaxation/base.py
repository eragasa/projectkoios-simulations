"""Calculator-neutral declarations for plane-wave DFT structural relaxation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.simulations.dft.pw.settings import CalculationType
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class PwDftRelaxationObject:
    """Base nominal identity for plane-wave DFT relaxation records."""

    __slots__ = ()


class PwDftRelaxationInitialization(StrEnum):
    """Select the exact source of the initial relaxation geometry."""

    FROM_EXACT_STARTING_STRUCTURE = "from-exact-starting-structure"


class PwDftCellRelaxationMode(StrEnum):
    """Select active lattice degrees of freedom."""

    FIXED = "fixed"
    VOLUME_ONLY = "volume-only"
    SHAPE_AT_FIXED_VOLUME = "shape-at-fixed-volume"
    SELECTED_COMPONENTS = "selected-components"
    UNRESTRICTED_VECTORS = "unrestricted-vectors"


@dataclass(frozen=True, slots=True)
class PwDftRelaxationDegreesOfFreedom(PwDftRelaxationObject):
    """Declare ionic and lattice degrees of freedom without provider tags."""

    relax_atomic_positions: bool
    cell_mode: PwDftCellRelaxationMode
    selected_strain_components: tuple[bool, bool, bool, bool, bool, bool] | None = None

    def __post_init__(self) -> None:
        if type(self.relax_atomic_positions) is not bool:
            raise TypeError("relax_atomic_positions must be a bool")
        if not self.relax_atomic_positions:
            raise ValueError("version one requires active atomic positions")
        if type(self.cell_mode) is not PwDftCellRelaxationMode:
            raise TypeError("cell_mode must be a PwDftCellRelaxationMode")
        if self.cell_mode is PwDftCellRelaxationMode.SELECTED_COMPONENTS:
            if (
                type(self.selected_strain_components) is not tuple
                or len(self.selected_strain_components) != 6
                or any(
                    type(value) is not bool for value in self.selected_strain_components
                )
                or not any(self.selected_strain_components)
            ):
                raise ValueError(
                    "selected-components mode requires a nonempty six-boolean "
                    "strain mask"
                )
        elif self.selected_strain_components is not None:
            raise ValueError(
                "only selected-components mode carries a strain-component mask"
            )


class PwDftRelaxationScope(StrEnum):
    """Select the calculator-neutral geometry degrees of freedom."""

    ATOMIC_POSITIONS = "atomic-positions"
    ATOMIC_POSITIONS_AND_CELL = "atomic-positions-and-cell"


@dataclass(frozen=True, slots=True)
class PwDftRelaxationSampling(PwDftRelaxationObject):
    """Declare k-point sampling and wavefunction cutoff for each ionic step."""

    kpoint_mesh: tuple[int, int, int]
    kpoint_shift: tuple[int, int, int]
    wavefunction_cutoff_ev: float

    def __post_init__(self) -> None:
        if len(self.kpoint_mesh) != 3 or any(
            type(value) is not int or value <= 0 for value in self.kpoint_mesh
        ):
            raise ValueError("kpoint_mesh must contain three positive integers")
        if len(self.kpoint_shift) != 3 or any(
            type(value) is not int or value not in {0, 1} for value in self.kpoint_shift
        ):
            raise ValueError("kpoint_shift must contain three zero-or-one integers")
        if (
            type(self.wavefunction_cutoff_ev) is not float
            or not math.isfinite(self.wavefunction_cutoff_ev)
            or self.wavefunction_cutoff_ev <= 0.0
        ):
            raise ValueError("wavefunction_cutoff_ev must be positive and finite")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationConvergencePolicy(PwDftRelaxationObject):
    """Declare common termination quantities without choosing backend algorithms."""

    maximum_ionic_steps: int
    total_energy_tolerance_ev: float
    force_tolerance_ev_per_angstrom: float
    target_pressure_kbar: float | None
    pressure_tolerance_kbar: float | None

    def __post_init__(self) -> None:
        if type(self.maximum_ionic_steps) is not int or self.maximum_ionic_steps <= 0:
            raise ValueError("maximum_ionic_steps must be a positive integer")
        for label, value in (
            ("total_energy_tolerance_ev", self.total_energy_tolerance_ev),
            (
                "force_tolerance_ev_per_angstrom",
                self.force_tolerance_ev_per_angstrom,
            ),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")
        if self.target_pressure_kbar is not None and (
            type(self.target_pressure_kbar) is not float
            or not math.isfinite(self.target_pressure_kbar)
        ):
            raise ValueError("target_pressure_kbar must be finite when represented")
        if self.pressure_tolerance_kbar is not None and (
            type(self.pressure_tolerance_kbar) is not float
            or not math.isfinite(self.pressure_tolerance_kbar)
            or self.pressure_tolerance_kbar <= 0.0
        ):
            raise ValueError(
                "pressure_tolerance_kbar must be positive and finite when represented"
            )


@dataclass(frozen=True, slots=True)
class PwDftRelaxationRequest(PwDftRelaxationObject):
    """Declare one backend-independent structural-relaxation projection request."""

    evaluation_id: str
    simulation: PwDftSimulation
    scope: PwDftRelaxationScope
    sampling: PwDftRelaxationSampling
    convergence: PwDftRelaxationConvergencePolicy

    def __post_init__(self) -> None:
        if type(self.evaluation_id) is not str or not _IDENTIFIER.fullmatch(
            self.evaluation_id
        ):
            raise ValueError("evaluation_id must be a lowercase slug")
        if type(self.simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if type(self.scope) is not PwDftRelaxationScope:
            raise TypeError("scope must be a PwDftRelaxationScope")
        if type(self.sampling) is not PwDftRelaxationSampling:
            raise TypeError("sampling must be a PwDftRelaxationSampling")
        if type(self.convergence) is not PwDftRelaxationConvergencePolicy:
            raise TypeError("convergence must be a PwDftRelaxationConvergencePolicy")
        expected_calculation = {
            PwDftRelaxationScope.ATOMIC_POSITIONS: CalculationType.relax,
            PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL: CalculationType.vc_relax,
        }[self.scope]
        if self.simulation.settings.calculation_type is not expected_calculation:
            raise ValueError("simulation calculation type does not match scope")
        has_pressure = self.convergence.target_pressure_kbar is not None
        has_pressure_tolerance = self.convergence.pressure_tolerance_kbar is not None
        if self.scope is PwDftRelaxationScope.ATOMIC_POSITIONS:
            if has_pressure or has_pressure_tolerance:
                raise ValueError(
                    "fixed-cell relaxation must not declare pressure controls"
                )
        elif not has_pressure or not has_pressure_tolerance:
            raise ValueError(
                "variable-cell relaxation requires target and tolerance pressures"
            )
