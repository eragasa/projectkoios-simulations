from __future__ import annotations

import unittest

import numpy as np

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.pw.bands import (
    BandDiagramBranch,
    BandDiagramData,
    BandPath,
    BandPathBranch,
    BandPathCoordinateSystem,
    BandPathVertex,
    PwDftBandsSimulation,
)
from tests.projectkoios.simulations.dft.pw.support import (
    resolved_pw_dft_simulation,
)


class BandDiagramDataTest(unittest.TestCase):
    def test_bands_simulation_requires_resolved_structure_state(self) -> None:
        path = _path()
        bands = _calculation(path)
        with self.assertRaisesRegex(TypeError, "ResolvedPwDftSimulation"):
            PwDftBandsSimulation(
                simulation=bands.simulation.simulation,  # type: ignore[arg-type]
                path=path,
            )

    def test_retains_branches_and_explicit_energy_reference(self) -> None:
        path = _path()
        data = BandDiagramData(
            calculation=_calculation(path),
            sampled_kpoints_reciprocal_fractional=(
                (0.5, 0.5, 0.5),
                (0.0, 0.0, 0.0),
            ),
            path_coordinate=(0.0, 1.0),
            path_coordinate_label="test distance",
            branches=(
                BandDiagramBranch(
                    start_index=0,
                    stop_index=2,
                    tick_indices=(0, 1),
                    tick_labels=("L", "G"),
                ),
            ),
            energies_ev=(((-2.0, 1.0), (-1.0, 2.0)),),
            occupations=(((1.0, 0.0), (1.0, 0.0)),),
            reference_energy_ev=1.0,
            reference_label="explicit reference",
        )

        self.assertEqual(data.spin_count, 1)
        self.assertEqual(data.kpoint_count, 2)
        self.assertEqual(data.band_count, 2)
        self.assertEqual(data.shifted_energies_ev[0][0], (-3.0, 0.0))
        self.assertIs(data.path, path)


def _path() -> BandPath:
    return BandPath(
        branches=(
            BandPathBranch(
                vertices=(
                    BandPathVertex("L", (0.5, 0.5, 0.5)),
                    BandPathVertex("G", (0.0, 0.0, 0.0)),
                )
            ),
        ),
        coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
        convention="test path",
    )


def _calculation(path: BandPath) -> PwDftBandsSimulation:
    unit_cell = UnitCell(
        direct_lattice=DirectLattice3D(
            a1=np.array([1.0, 0.0, 0.0]),
            a2=np.array([0.0, 1.0, 0.0]),
            a3=np.array([0.0, 0.0, 1.0]),
        ),
        lattice_parameter=ScalarQuantity(1.0, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            atoms=(
                Atom(
                    symbol="Si",
                    position_fractional=VectorQuantity(np.zeros(3), Unitless()),
                ),
            )
        ),
    )
    return PwDftBandsSimulation(
        simulation=resolved_pw_dft_simulation(unit_cell),
        path=path,
    )


if __name__ == "__main__":
    unittest.main()
