"""Immutable VASP automatic KPOINTS mesh records and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VaspKpointCentering(StrEnum):
    """Select an official automatic-mesh centering mode."""

    gamma = "Gamma"
    monkhorst_pack = "Monkhorst-Pack"


@dataclass(frozen=True, slots=True)
class VaspAutomaticKpointMesh:
    """Represent one automatic three-dimensional VASP k-point mesh."""

    mesh: tuple[int, int, int]
    shift: tuple[int, int, int]
    centering: VaspKpointCentering = VaspKpointCentering.gamma
    comment: str = "Automatic mesh"

    def __post_init__(self) -> None:
        if len(self.mesh) != 3 or any(
            type(value) is not int or value <= 0 for value in self.mesh
        ):
            raise ValueError("KPOINTS mesh must contain three positive integers")
        if len(self.shift) != 3 or any(
            type(value) is not int or value not in {0, 1} for value in self.shift
        ):
            raise ValueError("KPOINTS shift must contain three zero-or-one integers")
        if type(self.centering) is not VaspKpointCentering:
            raise TypeError("centering must be a VaspKpointCentering")
        if not self.comment or self.comment != self.comment.strip():
            raise ValueError("KPOINTS comment must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class VaspKpointsWriter:
    """Render one deterministic automatic-mesh KPOINTS file."""

    def render(self, model: VaspAutomaticKpointMesh) -> str:
        """Return official automatic-mesh syntax with an explicit shift."""
        if type(model) is not VaspAutomaticKpointMesh:
            raise TypeError("model must be a VaspAutomaticKpointMesh")
        mesh = " ".join(str(value) for value in model.mesh)
        shift = " ".join(str(value) for value in model.shift)
        return f"{model.comment}\n0\n{model.centering.value}\n{mesh}\n{shift}\n"
