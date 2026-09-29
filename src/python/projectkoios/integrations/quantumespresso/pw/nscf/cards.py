"""Typed NSCF specializations of the maintained ``pw.x`` base cards."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
    QeAtomicSpeciesCard,
    QeElectronsCard,
    QeKpointsCard,
    QeSystemCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
    PwInputGroup,
)
from projectkoios.simulations.dft.pw.settings import CalculationType


class QeNscfVerbosity(StrEnum):
    """Represent supported native ``&CONTROL.verbosity`` values."""

    low = "low"
    high = "high"


class QeNscfDiagonalization(StrEnum):
    """Represent the maintained NSCF diagonalization algorithms."""

    conjugate_gradient = "cg"
    davidson = "david"


class QeNscfOccupations(StrEnum):
    """Represent documented QE NSCF occupation modes."""

    fixed = "fixed"
    smearing = "smearing"
    tetrahedra = "tetrahedra"


@dataclass(frozen=True, slots=True)
class QeNscfControlBlock(ControlBlock):
    """Extend the common control block with typed NSCF diagnostics controls."""

    verbosity: QeNscfVerbosity = QeNscfVerbosity.high
    iprint: int = 2

    def __post_init__(self) -> None:
        super(QeNscfControlBlock, self).__post_init__()
        if self.calculation_type is not CalculationType.nscf:
            raise ValueError("NSCF control calculation type must be nscf")
        if type(self.verbosity) is not QeNscfVerbosity:
            raise TypeError("verbosity must be a QeNscfVerbosity")
        if type(self.iprint) is not int or self.iprint < 0:
            raise ValueError("iprint must be a nonnegative integer")

    def to_input_group(self) -> PwInputGroup:
        """Return the specialized native ``&CONTROL`` namelist."""
        common = super().to_input_group()
        return PwInputGroup(
            kind="namelist",
            tag="&CONTROL",
            lines=(
                *common.lines,
                f"iprint = {self.iprint}",
                f"verbosity = '{self.verbosity.value}'",
            ),
        )


def _build_nscf_system_card(
    *,
    atom_count: int,
    species_count: int,
    band_count: int,
    wavefunction_cutoff_ry: float,
    charge_density_cutoff_ry: float | None,
    occupations: QeNscfOccupations,
    disable_symmetry: bool,
    disable_time_reversal: bool,
) -> QeSystemCard:
    """Build one common system card from validated NSCF semantics."""
    for label, value in (
        ("atom_count", atom_count),
        ("species_count", species_count),
        ("band_count", band_count),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{label} must be positive")
    if (
        type(wavefunction_cutoff_ry) is not float
        or not math.isfinite(wavefunction_cutoff_ry)
        or wavefunction_cutoff_ry <= 0.0
    ):
        raise ValueError("wavefunction_cutoff_ry must be positive and finite")
    if charge_density_cutoff_ry is not None and (
        type(charge_density_cutoff_ry) is not float
        or not math.isfinite(charge_density_cutoff_ry)
        or charge_density_cutoff_ry < wavefunction_cutoff_ry
    ):
        raise ValueError(
            "charge_density_cutoff_ry must be finite and not below ecutwfc"
        )
    if type(occupations) is not QeNscfOccupations:
        raise TypeError("occupations must be a QeNscfOccupations")
    if type(disable_symmetry) is not bool or type(disable_time_reversal) is not bool:
        raise TypeError("symmetry controls must be booleans")
    lines = [
        "ibrav = 0",
        f"nat = {atom_count}",
        f"ntyp = {species_count}",
        f"nbnd = {band_count}",
        f"ecutwfc = {wavefunction_cutoff_ry:.10f}",
    ]
    if charge_density_cutoff_ry is not None:
        lines.append(f"ecutrho = {charge_density_cutoff_ry:.10f}")
    lines.extend(
        (
            f"occupations = '{occupations.value}'",
            f"nosym = {_logical(disable_symmetry)}",
            f"noinv = {_logical(disable_time_reversal)}",
        )
    )
    return QeSystemCard(lines=tuple(lines))


def _build_nscf_electrons_card(
    *,
    tolerance_ry: float,
    diagonalization: QeNscfDiagonalization,
    full_diagonalization_accuracy: bool,
) -> QeElectronsCard:
    """Build one common electrons card from validated NSCF semantics."""
    if (
        type(tolerance_ry) is not float
        or not math.isfinite(tolerance_ry)
        or tolerance_ry <= 0.0
    ):
        raise ValueError("tolerance_ry must be positive and finite")
    if type(diagonalization) is not QeNscfDiagonalization:
        raise TypeError("diagonalization must be a QeNscfDiagonalization")
    if type(full_diagonalization_accuracy) is not bool:
        raise TypeError("full_diagonalization_accuracy must be a boolean")
    return QeElectronsCard(
        lines=(
            f"conv_thr = {tolerance_ry:.10e}",
            f"diagonalization = '{diagonalization.value}'",
            f"diago_full_acc = {_logical(full_diagonalization_accuracy)}",
        )
    )


def _build_nscf_atomic_species_card(
    species: tuple[QeAtomicSpecies, ...],
) -> QeAtomicSpeciesCard:
    """Build one common source-ordered atomic-species card."""
    if type(species) is not tuple or not species:
        raise ValueError("species must be a nonempty tuple")
    if any(type(item) is not QeAtomicSpecies for item in species):
        raise TypeError("species must contain QeAtomicSpecies values")
    return QeAtomicSpeciesCard(
        lines=tuple(
            f"{item.symbol} {item.mass_amu:.10g} {item.pseudopotential_filename}"
            for item in species
        )
    )


def _build_nscf_kpoints_card(
    kpoints: tuple[tuple[tuple[float, float, float], float], ...],
    *,
    precision: int,
) -> QeKpointsCard:
    """Build one common explicit ``K_POINTS crystal`` card."""
    if type(kpoints) is not tuple or not kpoints:
        raise ValueError("kpoints must be a nonempty tuple")
    if type(precision) is not int or precision <= 0:
        raise ValueError("precision must be positive")
    lines = [str(len(kpoints))]
    for coordinates, weight in kpoints:
        if type(coordinates) is not tuple or len(coordinates) != 3:
            raise ValueError("k-point coordinates must contain three values")
        values = (*coordinates, weight)
        if any(
            type(value) is not float or not math.isfinite(value) for value in values
        ):
            raise ValueError("k-point values must be finite floats")
        if weight <= 0.0:
            raise ValueError("k-point weight must be positive")
        lines.append(" ".join(f"{value:.{precision}f}" for value in values))
    if not math.isclose(
        sum(weight for _, weight in kpoints),
        1.0,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    ):
        raise ValueError("k-point weights must sum to one")
    return QeKpointsCard(option="crystal", lines=tuple(lines))


def _logical(value: bool) -> str:
    return ".true." if value else ".false."
