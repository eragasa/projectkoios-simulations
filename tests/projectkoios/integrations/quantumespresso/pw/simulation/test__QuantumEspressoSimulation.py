from __future__ import annotations

import unittest

import numpy as np

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
    QePwInputFile,
)
from projectkoios.integrations.quantumespresso.pw.simulation import (
    QuantumEspressoSimulation,
)
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
from projectkoios.simulations.dft.pw.settings import CalculationType


class QuantumEspressoSimulationTest(unittest.TestCase):
    def test_bundle_retains_input_and_exact_pseudopotential_identity(self) -> None:
        input_file = QePwInputFile(
            control_block=ControlBlock(calculation_type=CalculationType.scf),
            unit_cell=_si_unit_cell(),
            groups=(),
        )
        pseudopotential = QePseudopotentialFile(
            pseudopotential=_si_pseudopotential(),
            filename="Si.upf",
            sha256="39822757f53f36e3bf3bfb779356152a8d3f21199c7db9dd5a931e5d18c45282",
            byte_size=225602,
        )

        simulation = QuantumEspressoSimulation(
            input_file=input_file,
            pseudopotentials=(pseudopotential,),
        )

        self.assertIs(simulation.input_file, input_file)
        self.assertIs(simulation.pseudopotentials[0], pseudopotential)
        self.assertEqual(simulation.input_filename, "pw.in")
        self.assertEqual(simulation.output_filename, "pw.out")

    def test_bundle_rejects_duplicate_species(self) -> None:
        input_file = QePwInputFile(
            control_block=ControlBlock(calculation_type=CalculationType.scf),
            unit_cell=_si_unit_cell(),
            groups=(),
        )
        first = QePseudopotentialFile(
            pseudopotential=_si_pseudopotential(),
            filename="Si-a.upf",
            sha256="a" * 64,
            byte_size=1,
        )
        second = QePseudopotentialFile(
            pseudopotential=_si_pseudopotential(),
            filename="Si-b.upf",
            sha256="b" * 64,
            byte_size=1,
        )

        with self.assertRaisesRegex(ValueError, "symbols must be unique"):
            QuantumEspressoSimulation(
                input_file=input_file,
                pseudopotentials=(first, second),
            )


def _si_unit_cell() -> UnitCell:
    return UnitCell(
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


def _si_pseudopotential() -> QePseudopotential:
    return QePseudopotential(
        symbol="Si",
        exchange_correlation="PBE",
        formalism="ONCVPSP",
        relativistic_treatment="scalar-relativistic",
        valence_electrons=4,
        upf_version="2.0.1",
    )


if __name__ == "__main__":
    unittest.main()
