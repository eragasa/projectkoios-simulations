"""Render unit-aware shared unit cells as deterministic VASP POSCAR files."""

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from projectkoios.physkit.periodic.unit_cell import Atom, UnitCell
from projectkoios.physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit

POSCAR_DOCUMENTATION_URL = "https://vasp.at/wiki/POSCAR"
_ANGSTROM = PhysicalUnit("angstrom")


@dataclass(frozen=True, slots=True)
class UnitCellModel:
    """Bind a shared unit cell to the POSCAR representation boundary."""

    unit_cell: UnitCell

    def __post_init__(self) -> None:
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("unit_cell must be a UnitCell")


@dataclass(frozen=True, slots=True)
class PoscarModel:
    """Represent one POSCAR comment and its unit-cell model."""

    comment: str
    unit_cell_model: UnitCellModel

    def __post_init__(self) -> None:
        if type(self.comment) is not str:
            raise TypeError("POSCAR comment must be a string")
        if not self.comment or self.comment != self.comment.strip():
            raise ValueError("POSCAR comment must be nonempty and stripped")
        if "\n" in self.comment or "\r" in self.comment:
            raise ValueError("POSCAR comment must not contain line terminators")
        if type(self.unit_cell_model) is not UnitCellModel:
            raise TypeError("unit_cell_model must be a UnitCellModel")

    def write(self, writer: PoscarWriter, destination: Path) -> None:
        """Delegate this model's filesystem serialization to a POSCAR writer."""
        if type(writer) is not PoscarWriter:
            raise TypeError("writer must be a PoscarWriter")
        writer.write(self, destination)


@dataclass(frozen=True, slots=True)
class PoscarWriter:
    """Render or atomically write one deterministic VASP 5 POSCAR."""

    def render(self, model: PoscarModel) -> str:
        """Render lattice vectors in Å and sites in fractional coordinates."""
        if type(model) is not PoscarModel:
            raise TypeError("model must be a PoscarModel")
        unit_cell = model.unit_cell_model.unit_cell
        conversion_factor = MODEL_SYSTEM_UNIT_CONVERTER.conversion_factor(
            unit_cell.H.unit,
            _ANGSTROM,
        )
        lattice_matrix = unit_cell.H.magnitude * conversion_factor
        lattice_vectors = tuple(lattice_matrix[:, index] for index in range(3))
        symbols = tuple(
            dict.fromkeys(atom.symbol for atom in unit_cell.atomic_basis.atoms)
        )
        grouped_atoms = tuple(
            tuple(
                atom for atom in unit_cell.atomic_basis.atoms if atom.symbol == symbol
            )
            for symbol in symbols
        )

        lines = [model.comment, "1.0"]
        lines.extend(_format_vector(vector) for vector in lattice_vectors)
        lines.append(" ".join(symbols))
        lines.append(" ".join(str(len(atoms)) for atoms in grouped_atoms))
        lines.append("Direct")
        for atoms in grouped_atoms:
            lines.extend(_format_atom(atom) for atom in atoms)
        return "\n".join(lines) + "\n"

    def write(self, model: PoscarModel, destination: Path) -> None:
        """Atomically write one rendered POSCAR without following a file symlink."""
        if not isinstance(destination, Path):
            raise TypeError("destination must be a Path")
        if destination.is_symlink():
            raise ValueError("POSCAR destination must not be a symbolic link")
        if not destination.parent.is_dir():
            raise ValueError("POSCAR destination parent must be an existing directory")
        payload = self.render(model).encode("ascii")
        mode = (
            stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o644
        )
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as temporary:
                temporary_name = temporary.name
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_name, mode)
            os.replace(temporary_name, destination)
        finally:
            if temporary_name is not None and os.path.exists(temporary_name):
                os.unlink(temporary_name)


def _format_vector(vector: NDArray[np.float64]) -> str:
    first, second, third = vector
    return f"{float(first):.16f} {float(second):.16f} {float(third):.16f}"


def _format_atom(atom: Atom) -> str:
    first, second, third = atom.position_fractional.magnitude
    return f"{float(first):.16f} {float(second):.16f} {float(third):.16f}"
