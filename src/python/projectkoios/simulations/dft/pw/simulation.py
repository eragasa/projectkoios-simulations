"""Calculator-neutral and exactly resolved plane-wave DFT simulations."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftExchangeCorrelationModel,
    DftSpinTreatment,
)
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.structure.library import (
    StructureRecord,
    StructureResolution,
)

type PwVector3 = tuple[float, float, float]
type PwMatrix3 = tuple[PwVector3, PwVector3, PwVector3]
type PwFractionalSite = tuple[str, PwVector3]

_ANGSTROM = PhysicalUnit("angstrom")


@dataclass(frozen=True, slots=True)
class PwDftSimulation(DataObject):
    """Represent scientific intent shared by every plane-wave DFT stage."""

    # The canonical specification owns only exact dependency identity. Decoded
    # geometry belongs to ResolvedPwDftSimulation so bytes are never duplicated.
    structure: StructureRecord
    exchange_correlation: DftExchangeCorrelationModel
    charge: DftChargeState = field(default_factory=DftChargeState)
    spin: DftSpinTreatment = field(default_factory=DftSpinTreatment)
    pseudopotentials: tuple[PseudopotentialFile, ...] = ()

    def __post_init__(self) -> None:
        if type(self.structure) is not StructureRecord:
            raise TypeError("structure must be a StructureRecord")
        if type(self.exchange_correlation) is not DftExchangeCorrelationModel:
            raise TypeError(
                "exchange_correlation must be a DftExchangeCorrelationModel"
            )
        if type(self.charge) is not DftChargeState:
            raise TypeError("charge must be DftChargeState")
        if type(self.spin) is not DftSpinTreatment:
            raise TypeError("spin must be DftSpinTreatment")
        if type(self.pseudopotentials) is not tuple or any(
            type(value) is not PseudopotentialFile for value in self.pseudopotentials
        ):
            raise TypeError("pseudopotentials must contain PseudopotentialFile values")

        # Symbol ordering is canonical, not a provider search preference.
        symbols = tuple(value.symbol for value in self.pseudopotentials)
        if symbols != tuple(sorted(symbols)):
            raise ValueError("pseudopotentials must be ordered by element symbol")
        if len(symbols) != len(set(symbols)):
            raise ValueError("pseudopotentials must have unique element symbols")
        if any(
            value.pseudopotential.exchange_correlation
            != self.exchange_correlation.pseudopotential_compatibility_label
            for value in self.pseudopotentials
        ):
            raise ValueError(
                "pseudopotentials must match exchange-correlation compatibility"
            )


@dataclass(frozen=True, slots=True)
class ResolvedPwDftSimulation(DataObject):
    """Bind shared intent to its verified decoded structure dependency."""

    simulation: PwDftSimulation
    structure: StructureResolution

    def __post_init__(self) -> None:
        if type(self.simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if type(self.structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        if self.structure.record != self.simulation.structure:
            raise ValueError(
                "resolved structure must match the exact simulation record"
            )

        # Composition-dependent checks can run only after exact structure bytes
        # have been verified and decoded by StructureLibrary.
        symbols = tuple(atom.symbol for atom in self.unit_cell.atomic_basis.atoms)
        pseudopotential_symbols = tuple(
            value.symbol for value in self.simulation.pseudopotentials
        )
        if pseudopotential_symbols and set(pseudopotential_symbols) != set(symbols):
            raise ValueError(
                "pseudopotentials must exactly cover structure element symbols"
            )
        if self.simulation.pseudopotentials:
            electron_count = self.electron_count
            if electron_count is None:
                raise AssertionError(
                    "bound pseudopotentials must define electron count"
                )
            if electron_count <= 0:
                raise ValueError("simulation electron count must be positive")
            spin_difference = self.simulation.spin.spin_channel_electron_difference
            if abs(spin_difference) > electron_count:
                raise ValueError(
                    "spin-channel electron difference exceeds electron count"
                )
            if (electron_count - spin_difference) % 2 != 0:
                raise ValueError(
                    "electron count and spin-channel difference have "
                    "incompatible parity"
                )

        atom_count = len(self.unit_cell.atomic_basis.atoms)
        if (
            self.simulation.spin.initial_site_magnetic_moments_mu_b
            and len(self.simulation.spin.initial_site_magnetic_moments_mu_b)
            != atom_count
        ):
            raise ValueError(
                "initial site magnetic moments must correspond one-to-one to atoms"
            )
        if (
            self.simulation.spin.initial_site_magnetic_moment_vectors_mu_b
            and len(self.simulation.spin.initial_site_magnetic_moment_vectors_mu_b)
            != atom_count
        ):
            raise ValueError(
                "initial site magnetic-moment vectors must correspond one-to-one "
                "to atoms"
            )

    @property
    def unit_cell(self) -> UnitCell:
        """Return the verified decoded unit cell."""
        return self.structure.unit_cell

    @property
    def electron_count(self) -> int | None:
        """Return exact valence-electron count when pseudopotentials are bound."""
        if not self.simulation.pseudopotentials:
            return None
        symbols = tuple(atom.symbol for atom in self.unit_cell.atomic_basis.atoms)
        return (
            sum(
                symbols.count(value.symbol) * value.pseudopotential.valence_electrons
                for value in self.simulation.pseudopotentials
            )
            + self.simulation.charge.delta_n_electrons
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
