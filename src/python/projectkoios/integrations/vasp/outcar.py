"""Bounded extraction of maintained VASP OUTCAR SCF observations."""

from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_OUTCAR_BYTES = 100_000_000
_VERSION = re.compile(r"^\s*vasp\.([^\s]+)", re.MULTILINE)
_NKPTS = re.compile(r"\bNKPTS\s*=\s*(\d+)")
_NIONS = re.compile(r"\bNIONS\s*=\s*(\d+)")
_ENCUT = re.compile(r"\bENCUT\s*=\s*([-+0-9.Ee]+)\s+eV")
_ITERATION = re.compile(
    r"^\s*-+\s*Iteration\s+\d+\(\s*(\d+)\)",
    re.MULTILINE,
)
_TOTEN = re.compile(r"free\s+energy\s+TOTEN\s*=\s*([-+0-9.Ee]+)\s+eV")


class VaspOutcarError(ValueError):
    """Report missing, malformed, or unsupported bounded OUTCAR evidence."""


@dataclass(frozen=True, slots=True)
class VaspOutcar:
    """Preserve calculator-native SCF observations extracted from OUTCAR."""

    program_version: str
    atom_count: int
    irreducible_kpoint_count: int
    wavefunction_cutoff_ev: float
    electronic_iteration_count: int
    total_energy_toten_ev: float
    electronic_converged: bool
    completed: bool


@dataclass(frozen=True, slots=True)
class VaspOutcarParser:
    """Extract a bounded static-SCF observation without parsing arbitrary XML."""

    def parse(self, text: str) -> VaspOutcar:
        """Return the last total energy and completion evidence from OUTCAR text."""
        if type(text) is not str:
            raise TypeError("OUTCAR text must be a string")
        if len(text.encode("utf-8")) > _MAX_OUTCAR_BYTES:
            raise VaspOutcarError("OUTCAR text exceeds the byte limit")
        version = _required_match(_VERSION, text, "program version")
        atom_count = int(_required_match(_NIONS, text, "atom count"))
        kpoint_count = int(_required_match(_NKPTS, text, "k-point count"))
        cutoff = float(_required_match(_ENCUT, text, "ENCUT"))
        iterations = tuple(int(value) for value in _ITERATION.findall(text))
        energies = tuple(float(value) for value in _TOTEN.findall(text))
        if not iterations:
            raise VaspOutcarError("OUTCAR contains no electronic iterations")
        if not energies:
            raise VaspOutcarError("OUTCAR contains no TOTEN observation")
        return VaspOutcar(
            program_version=version,
            atom_count=atom_count,
            irreducible_kpoint_count=kpoint_count,
            wavefunction_cutoff_ev=cutoff,
            electronic_iteration_count=len(iterations),
            total_energy_toten_ev=energies[-1],
            electronic_converged=("aborting loop because EDIFF is reached" in text),
            completed=("General timing and accounting" in text),
        )


def _required_match(pattern: re.Pattern[str], text: str, label: str) -> str:
    match = pattern.search(text)
    if match is None:
        raise VaspOutcarError(f"OUTCAR contains no {label}")
    return match.group(1)
