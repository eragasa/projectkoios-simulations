"""Nominal Quantum ESPRESSO namelist and data-card records."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import ClassVar, Literal

import numpy as np
from numpy.typing import NDArray
from physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PW_CARD_NAMES,
    ControlBlock,
    PwInputGroup,
    QePwInputFile,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation

_ELEMENT_SYMBOL = re.compile(r"[A-Z][a-z]?")


@dataclass(frozen=True, slots=True)
class QeAtomicSpecies:
    """Declare one species line shared by ``pw.x`` calculation modes."""

    symbol: str
    mass_amu: float
    pseudopotential_filename: str

    def __post_init__(self) -> None:
        if type(self.symbol) is not str or not _ELEMENT_SYMBOL.fullmatch(self.symbol):
            raise ValueError("symbol must be an element symbol")
        if (
            type(self.mass_amu) is not float
            or not math.isfinite(self.mass_amu)
            or self.mass_amu <= 0.0
        ):
            raise ValueError("mass_amu must be positive and finite")
        filename = self.pseudopotential_filename
        if (
            type(filename) is not str
            or not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
        ):
            raise ValueError("pseudopotential_filename must be a basename")


@dataclass(frozen=True, slots=True)
class QeCard:
    """Represent one ordered QE namelist or data card."""

    lines: tuple[str, ...]
    option: str | None = None

    _kind: ClassVar[Literal["namelist", "card"]]
    _tag: ClassVar[str]
    _implemented: ClassVar[bool] = False

    def __post_init__(self) -> None:
        if type(self) is QeCard:
            raise TypeError("QeCard is a nominal base and cannot be instantiated")
        if self._kind not in {"namelist", "card"}:
            raise TypeError("QeCard subclass must declare a supported kind")
        if not self._tag:
            raise TypeError("QeCard subclass must declare a tag")
        if type(self.lines) is not tuple:
            raise TypeError("lines must be a tuple")
        for line in self.lines:
            if type(line) is not str:
                raise TypeError("lines must contain strings")
            if line != line.strip() or "\n" in line or "\r" in line:
                raise ValueError(
                    "lines must be stripped and contain no line terminators"
                )
        if self.option is not None:
            if type(self.option) is not str:
                raise TypeError("option must be a string or None")
            if (
                not self.option
                or self.option != self.option.strip()
                or "\n" in self.option
                or "\r" in self.option
            ):
                raise ValueError(
                    "option must be nonempty, stripped, and contain no line terminators"
                )
            if self._kind == "namelist":
                raise ValueError("QE namelists do not accept card options")

    @property
    def kind(self) -> Literal["namelist", "card"]:
        """Return whether this record is a namelist or data card."""
        return self._kind

    @property
    def tag(self) -> str:
        """Return the rendered group tag, including an optional card option."""
        if self.option is None:
            return self._tag
        return f"{self._tag} {self.option}"

    @property
    def implemented(self) -> bool:
        """Return whether this component has maintained semantic support."""
        return self._implemented

    def to_input_group(self) -> PwInputGroup:
        """Project a supported component into the maintained lexical model."""
        if not self.implemented:
            raise NotImplementedError(f"{type(self).__name__} is not implemented")
        return PwInputGroup(kind=self.kind, tag=self.tag, lines=self.lines)


class QeControlCard(QeCard):
    """Represent the required ``&CONTROL`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&CONTROL"
    _implemented = True


class QeSystemCard(QeCard):
    """Represent the required ``&SYSTEM`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&SYSTEM"
    _implemented = True


class QeElectronsCard(QeCard):
    """Represent the required ``&ELECTRONS`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&ELECTRONS"
    _implemented = True


class QeIonsCard(QeCard):
    """Represent the optional ``&IONS`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&IONS"
    _implemented = True


class QeCellCard(QeCard):
    """Represent the optional ``&CELL`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&CELL"
    _implemented = True


class QeFcpCard(QeCard):
    """Represent the optional ``&FCP`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&FCP"


class QeRismCard(QeCard):
    """Represent the optional ``&RISM`` namelist."""

    __slots__ = ()

    _kind = "namelist"
    _tag = "&RISM"


class QeAtomicSpeciesCard(QeCard):
    """Represent an ``ATOMIC_SPECIES`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "ATOMIC_SPECIES"
    _implemented = True


class QeAtomicPositionsCard(QeCard):
    """Represent an ``ATOMIC_POSITIONS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "ATOMIC_POSITIONS"
    _implemented = True


class QeKpointsCard(QeCard):
    """Represent a ``K_POINTS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "K_POINTS"
    _implemented = True


class QeAdditionalKpointsCard(QeCard):
    """Represent an ``ADDITIONAL_K_POINTS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "ADDITIONAL_K_POINTS"


class QeCellParametersCard(QeCard):
    """Represent a ``CELL_PARAMETERS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "CELL_PARAMETERS"
    _implemented = True


class QeOccupationsCard(QeCard):
    """Represent an ``OCCUPATIONS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "OCCUPATIONS"


class QeConstraintsCard(QeCard):
    """Represent a ``CONSTRAINTS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "CONSTRAINTS"


class QeAtomicVelocitiesCard(QeCard):
    """Represent an ``ATOMIC_VELOCITIES`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "ATOMIC_VELOCITIES"


class QeAtomicForcesCard(QeCard):
    """Represent an ``ATOMIC_FORCES`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "ATOMIC_FORCES"


class QeSolventsCard(QeCard):
    """Represent a ``SOLVENTS`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "SOLVENTS"


class QeHubbardCard(QeCard):
    """Represent a ``HUBBARD`` data card."""

    __slots__ = ()

    _kind = "card"
    _tag = "HUBBARD"


@dataclass(frozen=True, slots=True)
class QePwInputFileAssembler:
    """Assemble typed ``pw.x`` input state from common components."""

    def assemble(
        self,
        simulation: PwDftSimulation,
        groups: tuple[PwInputGroup, ...],
        *,
        prefix: str | None = None,
        pseudo_dir: str | None = None,
        outdir: str | None = None,
        cell_parameters_unit: Literal["alat", "angstrom", "bohr"],
        atomic_positions_unit: Literal["crystal"],
        coordinate_precision: int,
        card_order: tuple[str, ...],
    ) -> QePwInputFile:
        """Add canonical structure components to validated caller groups."""
        if type(simulation) is not PwDftSimulation:
            raise TypeError("simulation must be a PwDftSimulation")
        if type(groups) is not tuple:
            raise TypeError("groups must be a tuple")
        generated_card_names = {"ATOMIC_POSITIONS", "CELL_PARAMETERS"}
        if any(
            group.kind == "card"
            and group.tag.split(maxsplit=1)[0].upper() in generated_card_names
            for group in groups
        ):
            raise ValueError("groups must not duplicate generated structure cards")
        combined_groups = (
            *groups,
            *_structure_groups(
                simulation,
                cell_parameters_unit,
                atomic_positions_unit,
                coordinate_precision,
            ),
        )
        namelists = tuple(
            group for group in combined_groups if group.kind == "namelist"
        )
        cards = tuple(group for group in combined_groups if group.kind == "card")
        if type(card_order) is not tuple or len(set(card_order)) != len(card_order):
            raise ValueError("card_order must be a tuple of unique card names")
        card_priority = {name.upper(): index for index, name in enumerate(card_order)}
        default_priority = {
            name: index + len(card_priority) for index, name in enumerate(PW_CARD_NAMES)
        }
        ordered_cards = tuple(
            sorted(
                cards,
                key=lambda group: card_priority.get(
                    group.tag.split(maxsplit=1)[0].upper(),
                    default_priority.get(
                        group.tag.split(maxsplit=1)[0].upper(),
                        len(card_priority) + len(default_priority),
                    ),
                ),
            )
        )
        return QePwInputFile(
            control_block=ControlBlock(
                calculation_type=simulation.settings.calculation_type,
                prefix=prefix,
                pseudo_dir=pseudo_dir,
                outdir=outdir,
            ),
            unit_cell=simulation.unit_cell,
            groups=(*namelists, *ordered_cards),
        )


def _structure_groups(
    simulation: PwDftSimulation,
    cell_parameters_unit: Literal["alat", "angstrom", "bohr"],
    atomic_positions_unit: Literal["crystal"],
    coordinate_precision: int,
) -> tuple[PwInputGroup, ...]:
    if type(coordinate_precision) is not int or coordinate_precision < 1:
        raise ValueError("coordinate_precision must be a positive integer")
    unit_cell = simulation.unit_cell
    lattice_matrix = unit_cell.A.magnitude
    if cell_parameters_unit != "alat":
        conversion_factor = MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
            unit_cell.H.unit,
            PhysicalUnit(cell_parameters_unit),
        )
        lattice_matrix = unit_cell.H.magnitude * conversion_factor
    lattice_vectors = tuple(lattice_matrix[:, index] for index in range(3))
    return (
        QeAtomicPositionsCard(
            option=f"({atomic_positions_unit})",
            lines=tuple(
                atom.symbol
                + " "
                + _format_vector(
                    atom.position_fractional.magnitude,
                    coordinate_precision,
                )
                for atom in unit_cell.atomic_basis.atoms
            ),
        ).to_input_group(),
        QeCellParametersCard(
            option=f"({cell_parameters_unit})",
            lines=tuple(
                _format_vector(vector, coordinate_precision)
                for vector in lattice_vectors
            ),
        ).to_input_group(),
    )


def _format_vector(vector: NDArray[np.float64], precision: int) -> str:
    first, second, third = vector
    return (
        f"{float(first):.{precision}f} "
        f"{float(second):.{precision}f} "
        f"{float(third):.{precision}f}"
    )
