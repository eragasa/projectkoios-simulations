"""Project cell-bound band simulations into QE ``K_POINTS`` cards."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.base import QeKpointsCard
from projectkoios.simulations.dft.pw.bands import (
    BandDiagramBranch,
    BandPath,
    BandPathCoordinateSystem,
    PwDftBandsSimulation,
)


@dataclass(frozen=True, slots=True)
class QeBandsPathProjection:
    """Project one cell-bound simulation using QE interpolation semantics."""

    calculation: PwDftBandsSimulation
    points_per_segment: int
    precision: int = 10

    def __post_init__(self) -> None:
        if type(self.calculation) is not PwDftBandsSimulation:
            raise TypeError("calculation must be a PwDftBandsSimulation")
        if (
            self.path.coordinate_system
            is not BandPathCoordinateSystem.reciprocal_fractional
        ):
            raise ValueError("QE bands support reciprocal-fractional paths only")
        if type(self.points_per_segment) is not int or self.points_per_segment < 2:
            raise ValueError("points_per_segment must be at least two")
        if type(self.precision) is not int or self.precision <= 0:
            raise ValueError("precision must be positive")

    @property
    def path(self) -> BandPath:
        """Return the path bound to the projected simulation."""
        return self.calculation.path

    @property
    def expected_sample_count(self) -> int:
        return sum(
            (len(branch.vertices) - 1) * self.points_per_segment + 1
            for branch in self.path.branches
        )

    def to_kpoints_card(self) -> QeKpointsCard:
        """Render branch boundaries with one-point discontinuity segments."""
        point_lines: list[str] = []
        for branch in self.path.branches:
            for index, vertex in enumerate(branch.vertices):
                interpolation_count = (
                    self.points_per_segment if index < len(branch.vertices) - 1 else 1
                )
                coordinates = " ".join(
                    f"{value:.{self.precision}f}" for value in vertex.coordinates
                )
                point_lines.append(
                    f"{coordinates} {interpolation_count} ! {vertex.label}"
                )
        option = {
            BandPathCoordinateSystem.reciprocal_fractional: "crystal_b",
        }[self.path.coordinate_system]
        return QeKpointsCard(
            option=option,
            lines=(str(len(point_lines)), *point_lines),
        )

    def diagram_branches(self) -> tuple[BandDiagramBranch, ...]:
        """Return expected QEXSD row ranges and high-symmetry tick indices."""
        branches: list[BandDiagramBranch] = []
        start = 0
        for branch in self.path.branches:
            segment_count = len(branch.vertices) - 1
            stop = start + segment_count * self.points_per_segment + 1
            branches.append(
                BandDiagramBranch(
                    start_index=start,
                    stop_index=stop,
                    tick_indices=tuple(
                        start + index * self.points_per_segment
                        for index in range(segment_count + 1)
                    ),
                    tick_labels=tuple(vertex.label for vertex in branch.vertices),
                )
            )
            start = stop
        return tuple(branches)
