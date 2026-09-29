from __future__ import annotations

import unittest

import numpy as np

from projectkoios.integrations.vasp.kpoints import (
    VaspAutomaticKpointMesh,
    VaspKpointsWriter,
    VaspLineModeKpoints,
)
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.pw.bands import (
    BandPath,
    BandPathBranch,
    BandPathCoordinateSystem,
    BandPathVertex,
    PwDftBandsSimulation,
)
from projectkoios.simulations.dft.pw.settings import CalculationType, PwDftSettings
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010 import (
    SetyawanCurtaroloAppendixACase,
    SetyawanCurtaroloLattice,
    SetyawanCurtaroloPathBinder,
    SetyawanCurtaroloPathBindingRequest,
    SetyawanCurtaroloPathDefinition,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation


class VaspKpointsWriterTest(unittest.TestCase):
    def test_renders_deterministic_gamma_centered_mesh(self) -> None:
        rendered = VaspKpointsWriter().render(
            VaspAutomaticKpointMesh((8, 8, 8), (0, 0, 0))
        )

        self.assertEqual(rendered, "Automatic mesh\n0\nGamma\n8 8 8\n0 0 0\n")

    def test_renders_basis_transformed_setyawan_curtarolo_fcc_path(self) -> None:
        placeholder_path = BandPath(
            branches=(
                BandPathBranch(
                    vertices=(
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("X", (0.5, 0.0, 0.0)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="test placeholder",
        )
        simulation = _calculation(
            placeholder_path,
            canonical_basis=True,
        ).simulation
        definition = SetyawanCurtaroloPathDefinition(
            SetyawanCurtaroloLattice(
                appendix_a_case=SetyawanCurtaroloAppendixACase.fcc,
                a_angstrom=5.4,
                b_angstrom=5.4,
                c_angstrom=5.4,
            )
        )
        calculation = (
            SetyawanCurtaroloPathBinder()
            .action(
                request=SetyawanCurtaroloPathBindingRequest(
                    definition=definition,
                    simulation=simulation,
                )
            )
            .calculation
        )

        rendered = VaspKpointsWriter().render(
            VaspLineModeKpoints(calculation=calculation, points_per_segment=20)
        )

        self.assertIn("basis-transformed", calculation.path.convention)
        self.assertIn(
            "0.0000000000 0.0000000000 0.0000000000 ! Γ\n"
            "0.5000000000 0.5000000000 0.0000000000 ! X\n",
            rendered,
        )
        self.assertTrue(
            rendered.endswith(
                "0.6250000000 0.6250000000 0.2500000000 ! U\n"
                "0.5000000000 0.5000000000 0.0000000000 ! X\n\n"
            )
        )

    def test_renders_source_ordered_line_mode_branches(self) -> None:
        path = BandPath(
            branches=(
                BandPathBranch(
                    vertices=(
                        BandPathVertex("L", (0.5, 0.5, 0.5)),
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("X", (0.0, 0.5, 0.5)),
                    )
                ),
                BandPathBranch(
                    vertices=(
                        BandPathVertex("K", (0.375, 0.75, 0.375)),
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="VASP fcc Si example",
        )

        rendered = VaspKpointsWriter().render(
            VaspLineModeKpoints(calculation=_calculation(path), points_per_segment=20)
        )

        self.assertEqual(
            rendered,
            "Band path\n"
            "20\n"
            "Line-mode\n"
            "Reciprocal\n"
            "0.5000000000 0.5000000000 0.5000000000 ! L\n"
            "0.0000000000 0.0000000000 0.0000000000 ! G\n"
            "\n"
            "0.0000000000 0.0000000000 0.0000000000 ! G\n"
            "0.0000000000 0.5000000000 0.5000000000 ! X\n"
            "\n"
            "0.3750000000 0.7500000000 0.3750000000 ! K\n"
            "0.0000000000 0.0000000000 0.0000000000 ! G\n"
            "\n",
        )


def _calculation(
    path: BandPath,
    *,
    canonical_basis: bool = False,
) -> PwDftBandsSimulation:
    vectors = (
        (
            np.array([0.5, 0.5, 0.0]),
            np.array([0.0, 0.5, 0.5]),
            np.array([0.5, 0.0, 0.5]),
        )
        if canonical_basis
        else (
            np.array([0.5, 0.0, 0.5]),
            np.array([0.5, 0.5, 0.0]),
            np.array([0.0, 0.5, 0.5]),
        )
    )
    cell = UnitCell(
        direct_lattice=DirectLattice3D(
            a1=vectors[0],
            a2=vectors[1],
            a3=vectors[2],
        ),
        lattice_parameter=ScalarQuantity(5.4, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            (
                Atom("Si", VectorQuantity(np.zeros(3), Unitless())),
                Atom("Si", VectorQuantity(np.full(3, 0.25), Unitless())),
            )
        ),
    )
    return PwDftBandsSimulation(
        PwDftSimulation(cell, PwDftSettings(CalculationType.bands)),
        path,
    )


if __name__ == "__main__":
    unittest.main()
