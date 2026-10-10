"""Calculator-neutral plane-wave density-functional-theory simulations."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit
from projectkoios.simulations.dft.electronic import DftChargeState, DftSpinTreatment
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
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
    charge: DftChargeState = field(default_factory=DftChargeState)
    spin: DftSpinTreatment = field(default_factory=DftSpinTreatment)
    pseudopotentials: tuple[PseudopotentialFile, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")
        if type(self.settings) is not PwDftSettings:
            raise TypeError("settings must be PwDftSettings")
        if type(self.charge) is not DftChargeState:
            raise TypeError("charge must be DftChargeState")
        if type(self.spin) is not DftSpinTreatment:
            raise TypeError("spin must be DftSpinTreatment")
        if type(self.pseudopotentials) is not tuple or any(
            type(value) is not PseudopotentialFile for value in self.pseudopotentials
        ):
            raise TypeError("pseudopotentials must contain PseudopotentialFile values")
        if self.pseudopotentials:
            symbols = tuple(atom.symbol for atom in self.unit_cell.atomic_basis.atoms)
            pseudopotential_symbols = tuple(
                value.symbol for value in self.pseudopotentials
            )
            if len(pseudopotential_symbols) != len(set(pseudopotential_symbols)):
                raise ValueError("pseudopotentials must have unique element symbols")
            if set(pseudopotential_symbols) != set(symbols):
                raise ValueError(
                    "pseudopotentials must exactly cover unit-cell element symbols"
                )
            electron_count = (
                sum(
                    symbols.count(value.symbol)
                    * value.pseudopotential.valence_electrons
                    for value in self.pseudopotentials
                )
                + self.charge.delta_n_electrons
            )
            if electron_count <= 0:
                raise ValueError("simulation electron count must be positive")
            spin_difference = self.spin.spin_channel_electron_difference
            if abs(spin_difference) > electron_count:
                raise ValueError(
                    "spin-channel electron difference exceeds electron count"
                )
            if (electron_count - spin_difference) % 2 != 0:
                raise ValueError(
                    "electron count and spin-channel difference have "
                    "incompatible parity"
                )
        if self.spin.initial_site_magnetic_moments_mu_b and len(
            self.spin.initial_site_magnetic_moments_mu_b
        ) != len(self.unit_cell.atomic_basis.atoms):
            raise ValueError(
                "initial site magnetic moments must correspond one-to-one to atoms"
            )
        if self.spin.initial_site_magnetic_moment_vectors_mu_b and len(
            self.spin.initial_site_magnetic_moment_vectors_mu_b
        ) != len(self.unit_cell.atomic_basis.atoms):
            raise ValueError(
                "initial site magnetic-moment vectors must correspond one-to-one "
                "to atoms"
            )

    @property
    def electron_count(self) -> int | None:
        """Return the exact valence-electron count when pseudopotentials are bound."""
        if not self.pseudopotentials:
            return None
        symbols = tuple(atom.symbol for atom in self.unit_cell.atomic_basis.atoms)
        return (
            sum(
                symbols.count(value.symbol) * value.pseudopotential.valence_electrons
                for value in self.pseudopotentials
            )
            + self.charge.delta_n_electrons
        )

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
