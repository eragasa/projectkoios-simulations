from __future__ import annotations

import unittest

import numpy as np

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    ControlBlock,
    PwInputGroup,
    PwInputWriter,
    QePwInputFile,
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


class QePwInputFileTest(unittest.TestCase):
    def test_writer_emits_the_typed_control_block_first(self) -> None:
        unit_cell = _si_unit_cell()
        input_file = QePwInputFile(
            control_block=ControlBlock(calculation_type=CalculationType.bands),
            unit_cell=unit_cell,
            groups=(
                PwInputGroup(
                    kind="namelist",
                    tag="&SYSTEM",
                    lines=("ibrav = 0", "nat = 1", "ntyp = 1"),
                ),
            ),
        )

        rendered = PwInputWriter().render(input_file)

        self.assertIs(input_file.unit_cell, unit_cell)
        self.assertEqual(
            rendered,
            "&CONTROL\n"
            "    calculation = 'bands'\n"
            "/\n"
            "&SYSTEM\n"
            "    ibrav = 0\n"
            "    nat = 1\n"
            "    ntyp = 1\n"
            "/\n",
        )

    def test_rejects_a_duplicate_lexical_control_group(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not duplicate &CONTROL"):
            QePwInputFile(
                control_block=ControlBlock(calculation_type=CalculationType.scf),
                unit_cell=_si_unit_cell(),
                groups=(
                    PwInputGroup(
                        kind="namelist",
                        tag="&CONTROL",
                        lines=("prefix = 'si'",),
                    ),
                ),
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


if __name__ == "__main__":
    unittest.main()
