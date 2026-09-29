from __future__ import annotations

import unittest

import numpy as np

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.pw.settings import (
    CalculationType,
    PwDftSettings,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation


class PwDftSimulationTest(unittest.TestCase):
    def test_retains_the_exact_unit_cell(self) -> None:
        unit_cell = UnitCell(
            direct_lattice=DirectLattice3D(
                a1=np.array([1.0, 0.0, 0.0]),
                a2=np.array([0.0, 1.0, 0.0]),
                a3=np.array([0.0, 0.0, 1.0]),
            ),
            lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
            atomic_basis=AtomicBasis(
                atoms=(
                    Atom(
                        symbol="Si",
                        position_fractional=VectorQuantity(np.zeros(3), Unitless()),
                    ),
                )
            ),
        )

        settings = PwDftSettings(calculation_type=CalculationType.scf)
        simulation = PwDftSimulation(unit_cell=unit_cell, settings=settings)

        self.assertIs(simulation.unit_cell, unit_cell)
        self.assertIs(simulation.settings, settings)
        self.assertEqual(
            simulation.lattice_vectors_angstrom,
            (
                (5.43, 0.0, 0.0),
                (0.0, 5.43, 0.0),
                (0.0, 0.0, 5.43),
            ),
        )
        self.assertEqual(
            simulation.fractional_sites,
            (("Si", (0.0, 0.0, 0.0)),),
        )


if __name__ == "__main__":
    unittest.main()
