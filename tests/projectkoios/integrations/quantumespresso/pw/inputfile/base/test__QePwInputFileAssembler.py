from __future__ import annotations

import unittest

import numpy as np

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (  # noqa: E501
    QePwInputFileAssembler,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PwInputGroup,
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


class QePwInputFileAssemblerTest(unittest.TestCase):
    def test_generates_structure_cards_from_the_shared_unit_cell(self) -> None:
        unit_cell = _unit_cell()

        input_file = QePwInputFileAssembler().assemble(
            unit_cell,
            groups=(
                PwInputGroup(
                    kind="namelist",
                    tag="&SYSTEM",
                    lines=("ibrav = 0", "nat = 1", "ntyp = 1"),
                ),
                PwInputGroup(
                    kind="card",
                    tag="K_POINTS gamma",
                    lines=(),
                ),
            ),
            calculation_type=CalculationType.scf,
            cell_parameters_unit="angstrom",
            atomic_positions_unit="crystal",
            coordinate_precision=16,
            card_order=(
                "ATOMIC_SPECIES",
                "ATOMIC_POSITIONS",
                "K_POINTS",
                "CELL_PARAMETERS",
            ),
        )

        self.assertIs(input_file.unit_cell, unit_cell)
        cards = {
            group.tag.split(maxsplit=1)[0]: group
            for group in input_file.groups
            if group.kind == "card"
        }
        self.assertEqual(
            cards["ATOMIC_POSITIONS"].lines,
            ("Si 0.0000000000000000 0.0000000000000000 0.0000000000000000",),
        )
        self.assertEqual(
            cards["ATOMIC_POSITIONS"].tag,
            "ATOMIC_POSITIONS (crystal)",
        )
        self.assertEqual(
            cards["CELL_PARAMETERS"].tag,
            "CELL_PARAMETERS (angstrom)",
        )
        self.assertEqual(
            cards["CELL_PARAMETERS"].lines,
            (
                "5.4299999999999997 0.0000000000000000 0.0000000000000000",
                "0.0000000000000000 5.4299999999999997 0.0000000000000000",
                "0.0000000000000000 0.0000000000000000 5.4299999999999997",
            ),
        )

    def test_writes_the_columns_of_H_as_cell_parameter_vectors(self) -> None:
        input_file = QePwInputFileAssembler().assemble(
            _skewed_unit_cell(),
            groups=(),
            calculation_type=CalculationType.scf,
            cell_parameters_unit="angstrom",
            atomic_positions_unit="crystal",
            coordinate_precision=2,
            card_order=("CELL_PARAMETERS", "ATOMIC_POSITIONS"),
        )

        cell_parameters = next(
            group
            for group in input_file.groups
            if group.tag.startswith("CELL_PARAMETERS")
        )
        self.assertEqual(
            cell_parameters.lines,
            (
                "2.00 0.00 0.00",
                "0.40 4.00 0.00",
                "0.60 0.80 6.00",
            ),
        )

    def test_rejects_caller_supplied_structure_cards(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not duplicate"):
            QePwInputFileAssembler().assemble(
                _unit_cell(),
                groups=(
                    PwInputGroup(
                        kind="card",
                        tag="ATOMIC_POSITIONS crystal",
                        lines=("Si 0 0 0",),
                    ),
                ),
                calculation_type=CalculationType.scf,
                cell_parameters_unit="angstrom",
                atomic_positions_unit="crystal",
                coordinate_precision=16,
                card_order=(
                    "ATOMIC_SPECIES",
                    "ATOMIC_POSITIONS",
                    "K_POINTS",
                    "CELL_PARAMETERS",
                ),
            )


def _skewed_unit_cell() -> UnitCell:
    return UnitCell(
        direct_lattice=DirectLattice3D(
            a1=np.array([1.0, 0.0, 0.0]),
            a2=np.array([0.2, 2.0, 0.0]),
            a3=np.array([0.3, 0.4, 3.0]),
        ),
        lattice_parameter=ScalarQuantity(2.0, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            atoms=(
                Atom(
                    symbol="Si",
                    position_fractional=VectorQuantity(np.zeros(3), Unitless()),
                ),
            )
        ),
    )


def _unit_cell() -> UnitCell:
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
