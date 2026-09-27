"""Immutable file identities for a staged Quantum ESPRESSO simulation."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    QePwInputFile,
)


@dataclass(frozen=True, slots=True)
class QuantumEspressoSimulation:
    """Bundle one ``pw.x`` input with exact external pseudopotential identities."""

    input_file: QePwInputFile
    pseudopotentials: tuple[QePseudopotentialFile, ...]
    input_filename: str = "pw.in"
    output_filename: str = "pw.out"

    def __post_init__(self) -> None:
        if type(self.input_file) is not QePwInputFile:
            raise TypeError("input_file must be a QePwInputFile")
        if type(self.pseudopotentials) is not tuple:
            raise TypeError("pseudopotentials must be a tuple")
        if not self.pseudopotentials:
            raise ValueError("simulation must identify at least one pseudopotential")
        if any(
            type(pseudopotential) is not QePseudopotentialFile
            for pseudopotential in self.pseudopotentials
        ):
            raise TypeError(
                "pseudopotentials must contain QePseudopotentialFile values"
            )
        symbols = tuple(item.symbol for item in self.pseudopotentials)
        filenames = tuple(item.filename for item in self.pseudopotentials)
        if len(set(symbols)) != len(symbols):
            raise ValueError("pseudopotential symbols must be unique")
        if len(set(filenames)) != len(filenames):
            raise ValueError("pseudopotential filenames must be unique")
        _validate_basename(self.input_filename, "input filename")
        _validate_basename(self.output_filename, "output filename")
        if self.input_filename == self.output_filename:
            raise ValueError("input and output filenames must differ")


def _validate_basename(value: str, label: str) -> None:
    if not value or value in {".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"{label} must be a basename")
