"""Calculator-neutral plane-wave density-functional-theory simulations."""

from __future__ import annotations

from dataclasses import dataclass

from physkit.periodic.unit_cell import UnitCell

from projectkoios.simulations.dft.pw.settings import PwDftSettings


@dataclass(frozen=True, slots=True)
class PwDftSimulation:
    """Represent a plane-wave DFT simulation rooted in one unit cell."""

    unit_cell: UnitCell
    settings: PwDftSettings

    def __post_init__(self) -> None:
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")
        if type(self.settings) is not PwDftSettings:
            raise TypeError("settings must be PwDftSettings")
