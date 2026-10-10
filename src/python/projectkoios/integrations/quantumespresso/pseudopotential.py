"""Quantum ESPRESSO specializations of calculator-neutral pseudopotentials."""

from __future__ import annotations

from dataclasses import dataclass, field

from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)


@dataclass(frozen=True, slots=True)
class QePseudopotential(Pseudopotential):
    """Represent metadata specific to a Quantum ESPRESSO UPF pseudopotential."""

    upf_version: str

    def __post_init__(self) -> None:
        Pseudopotential.__post_init__(self)
        if type(self.upf_version) is not str:
            raise TypeError("upf_version must be a string")
        if not self.upf_version or self.upf_version != self.upf_version.strip():
            raise ValueError("upf_version must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class QePseudopotentialFile(PseudopotentialFile):
    """Bind a Quantum ESPRESSO pseudopotential to exact UPF file identity."""

    pseudopotential: QePseudopotential
    artifact_format: PseudopotentialArtifactFormat = field(
        init=False,
        default=PseudopotentialArtifactFormat.UPF,
    )
    artifact_format_version: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "artifact_format_version",
            self.pseudopotential.upf_version,
        )
        PseudopotentialFile.__post_init__(self)
        if type(self.pseudopotential) is not QePseudopotential:
            raise TypeError("pseudopotential must be a QePseudopotential")
        if self.artifact_format is not PseudopotentialArtifactFormat.UPF:
            raise ValueError("QE pseudopotential files must use UPF format")
        if self.artifact_format_version != self.pseudopotential.upf_version:
            raise ValueError(
                "UPF artifact format version must match pseudopotential metadata"
            )
