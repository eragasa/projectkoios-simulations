"""Immutable VASP automatic KPOINTS mesh records and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from projectkoios.simulations.dft.pw.bands import (
    BandPath,
    BandPathCoordinateSystem,
    PwDftBandsSimulation,
)


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
class VaspLineModeKpoints:
    """Project one cell-bound simulation into VASP line-mode sampling."""

    calculation: PwDftBandsSimulation
    points_per_segment: int
    comment: str = "Band path"

    def __post_init__(self) -> None:
        if type(self.calculation) is not PwDftBandsSimulation:
            raise TypeError("calculation must be a PwDftBandsSimulation")
        if (
            self.path.coordinate_system
            is not BandPathCoordinateSystem.reciprocal_fractional
        ):
            raise ValueError("VASP line mode supports reciprocal-fractional paths only")
        if type(self.points_per_segment) is not int or self.points_per_segment < 2:
            raise ValueError("points_per_segment must be at least two")
        if (
            type(self.comment) is not str
            or not self.comment
            or self.comment != self.comment.strip()
            or "\n" in self.comment
            or "\r" in self.comment
        ):
            raise ValueError("KPOINTS comment must be one nonempty stripped line")

    @property
    def path(self) -> BandPath:
        """Return the path bound to the projected simulation."""
        return self.calculation.path


@dataclass(frozen=True, slots=True)
class VaspKpointsWriter:
    """Render deterministic automatic-mesh or line-mode KPOINTS files."""

    def render(self, model: VaspAutomaticKpointMesh | VaspLineModeKpoints) -> str:
        """Return official syntax for one supported KPOINTS representation."""
        if type(model) is VaspAutomaticKpointMesh:
            mesh = " ".join(str(value) for value in model.mesh)
            shift = " ".join(str(value) for value in model.shift)
            return f"{model.comment}\n0\n{model.centering.value}\n{mesh}\n{shift}\n"
        if type(model) is not VaspLineModeKpoints:
            raise TypeError("model must be a supported VASP KPOINTS record")
        coordinate_label = {
            BandPathCoordinateSystem.reciprocal_fractional: "Reciprocal",
        }[model.path.coordinate_system]
        lines = [
            model.comment,
            str(model.points_per_segment),
            "Line-mode",
            coordinate_label,
        ]
        for branch in model.path.branches:
            for start, stop in zip(
                branch.vertices,
                branch.vertices[1:],
                strict=False,
            ):
                lines.extend(
                    (
                        _format_path_vertex(start.coordinates, start.label),
                        _format_path_vertex(stop.coordinates, stop.label),
                        "",
                    )
                )
        return "\n".join(lines) + "\n"


def _format_path_vertex(
    coordinates: tuple[float, float, float],
    label: str,
) -> str:
    rendered = " ".join(f"{value:.10f}" for value in coordinates)
    return f"{rendered} ! {label}"
