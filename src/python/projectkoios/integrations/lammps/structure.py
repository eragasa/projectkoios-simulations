from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Literal

from projectkoios.integrations.lammps.provenance import (
    PypospackLammpsProvenance,
)

Vector3 = tuple[float, float, float]
Matrix3 = tuple[Vector3, Vector3, Vector3]
AtomStyle = Literal["atomic", "charge"]
_SYMBOL = re.compile(r"[A-Z][a-z]{0,2}")
_MAX_ATOMS = 10_000_000
_MAX_SERIALIZED_BYTES = 1_000_000_000


@dataclass(frozen=True, slots=True)
class LammpsAtom:
    symbol: str
    fractional_position: Vector3
    charge: float | None = None

    def __post_init__(self) -> None:
        if _SYMBOL.fullmatch(self.symbol) is None:
            raise ValueError("atom symbol is invalid")
        _finite_vector(self.fractional_position, "fractional_position")
        if self.charge is not None and not math.isfinite(self.charge):
            raise ValueError("atom charge must be finite")


@dataclass(frozen=True, slots=True)
class LammpsSimulationCell:
    scale: float
    lattice: Matrix3
    atoms: tuple[LammpsAtom, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise ValueError("cell scale must be finite and positive")
        if len(self.lattice) != 3:
            raise ValueError("cell lattice must contain three vectors")
        for vector in self.lattice:
            _finite_vector(vector, "lattice vector")
        if not self.atoms or len(self.atoms) > _MAX_ATOMS:
            raise ValueError("cell atom count is outside the serialization bound")


@dataclass(frozen=True, slots=True)
class LammpsDataArtifact:
    atom_style: AtomStyle
    species_order: tuple[str, ...]
    source: PypospackLammpsProvenance
    utf8_text: str
    sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.atom_style not in {"atomic", "charge"}:
            raise ValueError("LAMMPS atom style is unsupported")
        _validate_species_order_value(self.species_order)
        if not isinstance(self.source, PypospackLammpsProvenance):
            raise TypeError("source must be verified PyPosPack LAMMPS provenance")
        if not self.utf8_text.endswith("\n"):
            raise ValueError("LAMMPS data serialization must end with a newline")
        encoded = self.utf8_text.encode("utf-8")
        if len(encoded) > _MAX_SERIALIZED_BYTES:
            raise ValueError("LAMMPS data serialization exceeds the byte bound")
        digest = hashlib.sha256(encoded).hexdigest()
        object.__setattr__(self, "sha256", digest)

    def to_dict(self, *, include_text: bool = False) -> dict[str, object]:
        result: dict[str, object] = {
            "contract": "projectkoios.integrations.lammps-data",
            "contract_version": "0.1.0",
            "atom_style": self.atom_style,
            "species_order": list(self.species_order),
            "source": self.source.to_dict(),
            "sha256": self.sha256,
            "byte_size": len(self.utf8_text.encode("utf-8")),
            "calculator_execution_authorized": False,
            "scientific_validation_claimed": False,
        }
        if include_text:
            result["utf8_text"] = self.utf8_text
        return result


def render_lammps_data(
    *,
    cell: LammpsSimulationCell,
    species_order: tuple[str, ...],
    atom_style: AtomStyle,
    source: PypospackLammpsProvenance,
) -> LammpsDataArtifact:
    """Render deterministic data-file text without filesystem or execution effects.

    The retained source emits tilt factors while omitting corresponding terms from
    its coordinate transformation. This reconstruction therefore accepts only
    diagonal cells until a separately reviewed triclinic convention is adopted.
    """
    _validate_species_order(species_order, cell)
    if atom_style not in {"atomic", "charge"}:
        raise ValueError("LAMMPS atom style is unsupported")
    if atom_style == "charge" and any(atom.charge is None for atom in cell.atoms):
        raise ValueError("charge style requires an explicit charge for every atom")

    lattice = cell.lattice
    off_diagonal = (
        lattice[0][1],
        lattice[0][2],
        lattice[1][0],
        lattice[1][2],
        lattice[2][0],
        lattice[2][1],
    )
    if any(value != 0.0 for value in off_diagonal):
        raise ValueError(
            "off-diagonal cells are unsupported because the retained source has "
            "an inconsistent triclinic coordinate transformation"
        )
    bounds = tuple(lattice[index][index] * cell.scale for index in range(3))
    if any(
        not math.isfinite(value) or value <= 0 or float(f"{value:.4f}") <= 0
        for value in bounds
    ):
        raise ValueError(
            "LAMMPS cell bounds must be finite and positive at serialization precision"
        )

    lines = [
        f"# {list(species_order)!r}",
        "",
        f"{len(cell.atoms)} atoms",
        f"{len(species_order)} atom types",
        "",
        f"{0.0:10.4f} {bounds[0]:10.4f} xlo xhi",
        f"{0.0:10.4f} {bounds[1]:10.4f} ylo yhi",
        f"{0.0:10.4f} {bounds[2]:10.4f} zlo zhi",
        "",
        f"{0.0:10.4f} {0.0:10.4f} {0.0:10.4f} xy xz yz",
        "",
        "Atoms",
        "",
    ]
    atom_id = 1
    for atom_type, symbol in enumerate(species_order, 1):
        for atom in cell.atoms:
            if atom.symbol != symbol:
                continue
            coordinates = tuple(
                bounds[index] * atom.fractional_position[index] for index in range(3)
            )
            if any(not math.isfinite(value) for value in coordinates):
                raise ValueError("LAMMPS atom coordinates must be finite")
            if atom_style == "atomic":
                lines.append(
                    f"{atom_id} {atom_type} "
                    f"{coordinates[0]:10.4f} {coordinates[1]:10.4f} "
                    f"{coordinates[2]:10.4f}"
                )
            else:
                if atom.charge is None:
                    raise AssertionError("validated charge unexpectedly absent")
                lines.append(
                    f"{atom_id} {atom_type} {atom.charge:10.4f} "
                    f"{coordinates[0]:10.4f} {coordinates[1]:10.4f} "
                    f"{coordinates[2]:10.4f}"
                )
            atom_id += 1
    return LammpsDataArtifact(
        atom_style=atom_style,
        species_order=species_order,
        source=source,
        utf8_text="\n".join(lines) + "\n",
    )


def _validate_species_order(
    species_order: tuple[str, ...], cell: LammpsSimulationCell
) -> None:
    _validate_species_order_value(species_order)
    atom_symbols = {atom.symbol for atom in cell.atoms}
    if set(species_order) != atom_symbols:
        raise ValueError("species order must exactly cover the cell atom symbols")


def _validate_species_order_value(species_order: tuple[str, ...]) -> None:
    if not species_order or len(species_order) != len(set(species_order)):
        raise ValueError("species order must be nonempty and unique")
    if any(_SYMBOL.fullmatch(symbol) is None for symbol in species_order):
        raise ValueError("species order contains an invalid symbol")


def _finite_vector(value: tuple[float, ...], label: str) -> None:
    if len(value) != 3 or not all(math.isfinite(item) for item in value):
        raise ValueError(f"{label} must contain three finite values")
