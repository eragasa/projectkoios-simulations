from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (  # noqa: E501
    QeControlCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.control import (  # noqa: E501
    calculation as calculation_module,
)

QeCalculationCard = calculation_module.QeCalculationCard
QeCalculationEnum = calculation_module.QeCalculationEnum


class QeCalculationCardTest(unittest.TestCase):
    def test_defaults_to_scf(self) -> None:
        card = QeCalculationCard()

        self.assertIsInstance(card, QeControlCard)
        self.assertIs(card.calculation, QeCalculationEnum.scf)
        self.assertEqual(card.lines, ("calculation = 'scf'",))
        self.assertEqual(card.tag, "&CONTROL")

    def test_renders_every_documented_calculation_value(self) -> None:
        expected = {
            QeCalculationEnum.scf: "scf",
            QeCalculationEnum.nscf: "nscf",
            QeCalculationEnum.bands: "bands",
            QeCalculationEnum.relax: "relax",
            QeCalculationEnum.md: "md",
            QeCalculationEnum.vc_relax: "vc-relax",
            QeCalculationEnum.vc_md: "vc-md",
        }
        for calculation, rendered in expected.items():
            with self.subTest(calculation=calculation):
                card = QeCalculationCard(calculation)
                self.assertEqual(
                    card.lines,
                    (f"calculation = '{rendered}'",),
                )

    def test_rejects_untyped_values(self) -> None:
        with self.assertRaisesRegex(TypeError, "QeCalculationEnum"):
            QeCalculationCard("scf")  # type: ignore[arg-type]

    def test_is_immutable_and_slotted(self) -> None:
        card = QeCalculationCard()

        self.assertFalse(hasattr(card, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            card.calculation = QeCalculationEnum.nscf  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
