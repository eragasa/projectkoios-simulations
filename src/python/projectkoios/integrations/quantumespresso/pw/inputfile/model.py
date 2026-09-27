"""Immutable ``pw.x`` input records with bounded parsing and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from physkit.periodic.unit_cell import UnitCell

from projectkoios.simulations.dft.pw.settings import CalculationType

_MAX_INPUT_BYTES = 10_000_000
PW_INPUT_DOCUMENTATION_URL = "https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1"
PW_INPUT_DOCUMENTATION_VERSION = "7.5"
PW_NAMELIST_NAMES = (
    "&CONTROL",
    "&SYSTEM",
    "&ELECTRONS",
    "&IONS",
    "&CELL",
    "&FCP",
    "&RISM",
)
PW_CARD_NAMES = (
    "ATOMIC_SPECIES",
    "ATOMIC_POSITIONS",
    "K_POINTS",
    "CELL_PARAMETERS",
    "OCCUPATIONS",
    "CONSTRAINTS",
    "ATOMIC_VELOCITIES",
    "ATOMIC_FORCES",
    "ADDITIONAL_K_POINTS",
    "SOLVENTS",
    "HUBBARD",
)
_CARD_NAMES = frozenset(PW_CARD_NAMES)


class QuantumEspressoInputError(ValueError):
    """Report malformed or unsupported ``pw.x`` input syntax."""


@dataclass(frozen=True, slots=True)
class ControlBlock:
    """Represent the required calculation selection in ``pw.x`` ``&CONTROL``."""

    calculation_type: CalculationType
    prefix: str | None = None
    pseudo_dir: str | None = None
    outdir: str | None = None

    def __post_init__(self) -> None:
        if type(self.calculation_type) is not CalculationType:
            raise TypeError("calculation_type must be a CalculationType")
        for label, value in (
            ("prefix", self.prefix),
            ("pseudo_dir", self.pseudo_dir),
            ("outdir", self.outdir),
        ):
            if value is None:
                continue
            if type(value) is not str:
                raise TypeError(f"{label} must be a string or None")
            if (
                not value
                or value != value.strip()
                or "'" in value
                or "\n" in value
                or "\r" in value
            ):
                raise ValueError(
                    f"{label} must be nonempty, stripped, single-line, and unquoted"
                )


@dataclass(frozen=True, slots=True)
class PwInputGroup:
    """Represent one ordered Fortran namelist or Quantum ESPRESSO card."""

    kind: Literal["namelist", "card"]
    tag: str
    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.kind not in {"namelist", "card"}:
            raise ValueError("input group kind must be 'namelist' or 'card'")
        if not self.tag or self.tag != self.tag.strip():
            raise ValueError("input group tag must be nonempty and stripped")
        if "\n" in self.tag or "\r" in self.tag:
            raise ValueError("input group tag must not contain line terminators")
        if self.kind == "namelist" and not self.tag.startswith("&"):
            raise ValueError("namelist tag must start with '&'")
        if self.kind == "card" and self.tag.startswith("&"):
            raise ValueError("card tag must not start with '&'")
        if type(self.lines) is not tuple:
            raise TypeError("input group lines must be a tuple")
        for line in self.lines:
            if type(line) is not str:
                raise TypeError("input group lines must contain strings")
            if line != line.strip():
                raise ValueError("input group lines must be stripped")
            if "\n" in line or "\r" in line:
                raise ValueError("input group lines must not contain line terminators")


@dataclass(frozen=True, slots=True)
class PwInput:
    """Represent ordered ``pw.x`` input groups without scientific defaults."""

    groups: tuple[PwInputGroup, ...]

    def __post_init__(self) -> None:
        if type(self.groups) is not tuple:
            raise TypeError("pw.x input groups must be a tuple")
        if not self.groups:
            raise ValueError("pw.x input must contain at least one group")
        if any(type(group) is not PwInputGroup for group in self.groups):
            raise TypeError("pw.x input groups must contain PwInputGroup values")


@dataclass(frozen=True, slots=True)
class QePwInputFile:
    """Compose typed ``pw.x`` input state around the simulation's unit cell."""

    control_block: ControlBlock
    unit_cell: UnitCell
    groups: tuple[PwInputGroup, ...]

    def __post_init__(self) -> None:
        if type(self.control_block) is not ControlBlock:
            raise TypeError("control_block must be a ControlBlock")
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")
        if type(self.groups) is not tuple:
            raise TypeError("pw.x input groups must be a tuple")
        if any(type(group) is not PwInputGroup for group in self.groups):
            raise TypeError("pw.x input groups must contain PwInputGroup values")
        if any(
            group.kind == "namelist" and group.tag.upper() == "&CONTROL"
            for group in self.groups
        ):
            raise ValueError("QePwInputFile groups must not duplicate &CONTROL")


@dataclass(frozen=True, slots=True)
class PwInputParser:
    """Parse a bounded, text-form ``pw.x`` input into ordered loose groups."""

    def parse(self, text: str) -> PwInput:
        """Parse namelists and recognized cards without interpreting values."""
        if type(text) is not str:
            raise TypeError("pw.x input text must be a string")
        if len(text.encode("utf-8")) > _MAX_INPUT_BYTES:
            raise QuantumEspressoInputError("pw.x input exceeds the byte limit")

        groups: list[PwInputGroup] = []
        current_kind: Literal["namelist", "card"] | None = None
        current_tag: str | None = None
        current_lines: list[str] = []

        def close_group() -> None:
            nonlocal current_kind, current_tag, current_lines
            if current_kind is None or current_tag is None:
                return
            groups.append(
                PwInputGroup(
                    kind=current_kind,
                    tag=current_tag,
                    lines=tuple(current_lines),
                )
            )
            current_kind = None
            current_tag = None
            current_lines = []

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            if current_kind == "namelist":
                if line == "/" or line.startswith("/ !"):
                    close_group()
                    continue
                if line.startswith("&"):
                    raise QuantumEspressoInputError(
                        f"nested namelist at line {line_number}"
                    )
                current_lines.append(line)
                continue
            if line.startswith("!"):
                if current_kind == "card":
                    current_lines.append(line)
                continue
            if line.startswith("&"):
                close_group()
                current_kind = "namelist"
                current_tag = line
                continue
            first_token = line.split(maxsplit=1)[0].upper()
            if first_token in _CARD_NAMES:
                close_group()
                current_kind = "card"
                current_tag = line
                continue
            if current_kind == "card":
                current_lines.append(line)
                continue
            raise QuantumEspressoInputError(
                f"content outside an input group at line {line_number}"
            )

        if current_kind == "namelist":
            raise QuantumEspressoInputError("unterminated pw.x namelist")
        close_group()
        if not groups:
            raise QuantumEspressoInputError("pw.x input contains no groups")
        return PwInput(groups=tuple(groups))


@dataclass(frozen=True, slots=True)
class PwInputWriter:
    """Render a :class:`PwInput` deterministically without filesystem effects."""

    def render(self, input_file: PwInput | QePwInputFile) -> str:
        """Return normalized ``pw.x`` text ending in one newline."""
        if type(input_file) is PwInput:
            groups = input_file.groups
        elif type(input_file) is QePwInputFile:
            groups = (
                PwInputGroup(
                    kind="namelist",
                    tag="&CONTROL",
                    lines=_render_control_lines(input_file.control_block),
                ),
                *input_file.groups,
            )
        else:
            raise TypeError("input_file must be a PwInput or QePwInputFile")
        output: list[str] = []
        for group in groups:
            output.append(group.tag)
            indentation = "    " if group.kind == "namelist" else " "
            output.extend(f"{indentation}{line}" for line in group.lines)
            if group.kind == "namelist":
                output.append("/")
        return "\n".join(output) + "\n"


def _render_control_lines(control_block: ControlBlock) -> tuple[str, ...]:
    lines = [f"calculation = '{control_block.calculation_type.value}'"]
    for name, value in (
        ("prefix", control_block.prefix),
        ("pseudo_dir", control_block.pseudo_dir),
        ("outdir", control_block.outdir),
    ):
        if value is not None:
            lines.append(f"{name} = '{value}'")
    return tuple(lines)
