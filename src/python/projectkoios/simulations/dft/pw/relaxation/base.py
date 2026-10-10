"""Calculator-neutral declarations for plane-wave DFT structural relaxation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


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
