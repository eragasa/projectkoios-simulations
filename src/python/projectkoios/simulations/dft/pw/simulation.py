"""Calculator-neutral plane-wave density-functional-theory simulations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit
from projectkoios.simulations.dft.pw.settings import PwDftSettings

type PwVector3 = tuple[float, float, float]
type PwMatrix3 = tuple[PwVector3, PwVector3, PwVector3]
type PwFractionalSite = tuple[str, PwVector3]

_ANGSTROM = PhysicalUnit("angstrom")


@dataclass(frozen=True, slots=True)
class PwDftSimulation(DataObject):
    """Represent a plane-wave DFT simulation rooted in one unit cell."""

    unit_cell: UnitCell
    settings: PwDftSettings

    def __post_init__(self) -> None:
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")
        if type(self.settings) is not PwDftSettings:
            raise TypeError("settings must be PwDftSettings")

    @property
    def lattice_vectors_angstrom(self) -> PwMatrix3:
        """Return source-ordered physical lattice vectors as immutable rows."""
        factor = MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
            self.unit_cell.H.unit,
            _ANGSTROM,
        )
        matrix = np.asarray(self.unit_cell.H.magnitude * factor, dtype=np.float64)
        return (
            _vector3(matrix[:, 0]),
            _vector3(matrix[:, 1]),
            _vector3(matrix[:, 2]),
        )

    @property
    def fractional_sites(self) -> tuple[PwFractionalSite, ...]:
        """Return source-ordered symbols and fractional positions."""
        return tuple(
            (
                atom.symbol,
                _vector3(
                    np.asarray(
                        atom.position_fractional.magnitude,
                        dtype=np.float64,
                    )
                ),
            )
            for atom in self.unit_cell.atomic_basis.atoms
        )


def _vector3(values: NDArray[np.float64]) -> PwVector3:
    if values.shape != (3,):
        raise ValueError("unit-cell vectors must contain three values")
    return float(values[0]), float(values[1]), float(values[2])
