"""Plane-wave DFT charge and spin binding for structural defect deltas."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.dft.electronic import DftSpinMode
from projectkoios.simulations.dft.pw.simulation import ResolvedPwDftSimulation
from projectkoios.simulations.structure.defect import UnitCellDefectDeltaResult


@dataclass(frozen=True, slots=True)
class PwDftDefectChargeBinding:
    """Bind a structural charge state to its electronic realization."""

    defect: UnitCellDefectDeltaResult
    simulation: ResolvedPwDftSimulation

    def __post_init__(self) -> None:
        if type(self.defect) is not UnitCellDefectDeltaResult:
            raise TypeError("defect must be UnitCellDefectDeltaResult")
        if type(self.simulation) is not ResolvedPwDftSimulation:
            raise TypeError("simulation must be ResolvedPwDftSimulation")
        if self.simulation.unit_cell is not self.defect.unit_cell:
            raise ValueError(
                "simulation must retain the exact derived defect unit cell"
            )
        if (
            self.simulation.simulation.charge.charge_state
            != self.defect.delta.charge_state
        ):
            raise ValueError(
                "structural charge_state must equal the DFT electronic charge_state"
            )
        if (
            self.simulation.simulation.charge.charge_state
            != -self.simulation.simulation.charge.delta_n_electrons
        ):
            raise ValueError("charge_state must equal -delta_n_electrons")

        removed_symbols = tuple(
            self.defect.delta.bulk_cell.atomic_basis.atoms[index].symbol
            for index in self.defect.delta.removals
        )
        added_symbols = tuple(atom.symbol for atom in self.defect.delta.additions)
        neutral_si_dopant = (
            self.defect.delta.charge_state == 0
            and removed_symbols == ("Si",)
            and added_symbols in {("B",), ("P",)}
        )
        if neutral_si_dopant and (
            self.simulation.simulation.spin.mode is not DftSpinMode.COLLINEAR
            or not self.simulation.simulation.spin.constrain_spin_channel_difference
            or abs(self.simulation.simulation.spin.spin_channel_electron_difference)
            != 1
        ):
            raise ValueError(
                "neutral substitutional Si:P and Si:B require a constrained "
                "collinear doublet"
            )
