"""Generic calculator-neutral unit-cell defect deltas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell


@dataclass(frozen=True, slots=True, kw_only=True)
class UnitCellDefectDelta(DataObject):
    """Declare removals and additions relative to one exact bulk unit cell."""

    bulk_cell: UnitCell
    removals: tuple[int, ...]
    additions: tuple[Atom, ...]
    charge_state: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.bulk_cell, UnitCell):
            raise TypeError("bulk_cell must inherit from UnitCell")
        if type(self.removals) is not tuple or any(
            type(index) is not int for index in self.removals
        ):
            raise TypeError("removals must be a tuple of built-in ints")
        if tuple(sorted(set(self.removals))) != self.removals:
            raise ValueError("removals must be unique and strictly increasing")
        atom_count = len(self.bulk_cell.atomic_basis.atoms)
        if any(index < 0 or index >= atom_count for index in self.removals):
            raise ValueError("removal index is outside the bulk atomic basis")
        if type(self.additions) is not tuple or any(
            type(atom) is not Atom for atom in self.additions
        ):
            raise TypeError("additions must be a tuple of Atom values")
        for atom in self.additions:
            coordinates = atom.position_fractional.magnitude
            if (
                not np.all(np.isfinite(coordinates))
                or np.any(coordinates < 0.0)
                or np.any(coordinates >= 1.0)
            ):
                raise ValueError(
                    "addition fractional coordinates must lie in the half-open "
                    "interval [0, 1)"
                )
        if not self.removals and not self.additions:
            raise ValueError("a defect delta must remove or add at least one atom")
        if atom_count - len(self.removals) + len(self.additions) <= 0:
            raise ValueError("a defect delta must retain at least one atom")
        if type(self.charge_state) is not int:
            raise TypeError("charge_state must be a built-in int")

        removed = set(self.removals)
        occupied = tuple(
            atom.position_fractional.magnitude
            for index, atom in enumerate(self.bulk_cell.atomic_basis.atoms)
            if index not in removed
        )
        for addition_index, addition in enumerate(self.additions):
            position = addition.position_fractional.magnitude
            if any(np.array_equal(position, candidate) for candidate in occupied):
                raise ValueError("addition position is already occupied after removals")
            if any(
                np.array_equal(
                    position,
                    prior.position_fractional.magnitude,
                )
                for prior in self.additions[:addition_index]
            ):
                raise ValueError("addition positions must be unique")


@dataclass(frozen=True, slots=True, kw_only=True)
class UnitCellDefectDeltaResult(ResultsObject):
    """Correlate one exact delta with its mechanically derived unit cell."""

    delta: UnitCellDefectDelta
    unit_cell: UnitCell

    def __post_init__(self) -> None:
        if type(self.delta) is not UnitCellDefectDelta:
            raise TypeError("delta must be a UnitCellDefectDelta")
        if type(self.unit_cell) is not UnitCell:
            raise TypeError("unit_cell must be an exact base UnitCell")
        bulk = self.delta.bulk_cell
        if not np.array_equal(self.unit_cell.A.magnitude, bulk.A.magnitude):
            raise ValueError("defect delta must preserve the bulk lattice")
        if self.unit_cell.lattice_parameter != bulk.lattice_parameter:
            raise ValueError("defect delta must preserve the bulk lattice parameter")
        removed = set(self.delta.removals)
        expected = (
            tuple(
                atom
                for index, atom in enumerate(bulk.atomic_basis.atoms)
                if index not in removed
            )
            + self.delta.additions
        )
        actual = self.unit_cell.atomic_basis.atoms
        if len(actual) != len(expected):
            raise ValueError("defect delta result atom count is inconsistent")
        for expected_atom, actual_atom in zip(expected, actual, strict=True):
            if expected_atom.symbol != actual_atom.symbol or not np.array_equal(
                expected_atom.position_fractional.magnitude,
                actual_atom.position_fractional.magnitude,
            ):
                raise ValueError(
                    "defect delta result must contain retained atoms followed by "
                    "additions"
                )


class UnitCellDefectDeltaApplicator(
    DataObjectActionizer[UnitCellDefectDelta, UnitCellDefectDeltaResult]
):
    """Apply removals simultaneously, then append additions in declared order."""

    __slots__ = ()

    def action(
        self,
        *,
        request: UnitCellDefectDelta,
    ) -> UnitCellDefectDeltaResult:
        """Return a base unit cell without inferring a named defect category."""
        if type(request) is not UnitCellDefectDelta:
            raise TypeError("request must be a UnitCellDefectDelta")
        removed = set(request.removals)
        atoms = (
            tuple(
                atom
                for index, atom in enumerate(request.bulk_cell.atomic_basis.atoms)
                if index not in removed
            )
            + request.additions
        )
        unit_cell = UnitCell(
            direct_lattice=request.bulk_cell.direct_lattice,
            lattice_parameter=request.bulk_cell.lattice_parameter,
            atomic_basis=AtomicBasis(atoms=atoms),
        )
        return UnitCellDefectDeltaResult(delta=request, unit_cell=unit_cell)
