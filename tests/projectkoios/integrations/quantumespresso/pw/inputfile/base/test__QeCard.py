from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAdditionalKpointsCard,
    QeAtomicForcesCard,
    QeAtomicPositionsCard,
    QeAtomicSpeciesCard,
    QeAtomicVelocitiesCard,
    QeCard,
    QeCellCard,
    QeCellParametersCard,
    QeConstraintsCard,
    QeControlCard,
    QeElectronsCard,
    QeFcpCard,
    QeHubbardCard,
    QeIonsCard,
    QeKpointsCard,
    QeOccupationsCard,
    QeRismCard,
    QeSolventsCard,
    QeSystemCard,
)


class QeCardTest(unittest.TestCase):
    def test_defines_all_documented_namelists(self) -> None:
        cases = (
            (QeControlCard, "&CONTROL"),
            (QeSystemCard, "&SYSTEM"),
            (QeElectronsCard, "&ELECTRONS"),
            (QeIonsCard, "&IONS"),
            (QeCellCard, "&CELL"),
            (QeFcpCard, "&FCP"),
            (QeRismCard, "&RISM"),
        )
        for card_type, tag in cases:
            with self.subTest(card_type=card_type.__name__):
                card = card_type(lines=())
                self.assertIsInstance(card, QeCard)
                self.assertEqual(card.kind, "namelist")
                self.assertEqual(card.tag, tag)

    def test_defines_all_documented_data_cards(self) -> None:
        cases = (
            (QeAtomicSpeciesCard, "ATOMIC_SPECIES"),
            (QeAtomicPositionsCard, "ATOMIC_POSITIONS"),
            (QeKpointsCard, "K_POINTS"),
            (QeAdditionalKpointsCard, "ADDITIONAL_K_POINTS"),
            (QeCellParametersCard, "CELL_PARAMETERS"),
            (QeOccupationsCard, "OCCUPATIONS"),
            (QeConstraintsCard, "CONSTRAINTS"),
            (QeAtomicVelocitiesCard, "ATOMIC_VELOCITIES"),
            (QeAtomicForcesCard, "ATOMIC_FORCES"),
            (QeSolventsCard, "SOLVENTS"),
            (QeHubbardCard, "HUBBARD"),
        )
        for card_type, tag in cases:
            with self.subTest(card_type=card_type.__name__):
                card = card_type(lines=())
                self.assertIsInstance(card, QeCard)
                self.assertEqual(card.kind, "card")
                self.assertEqual(card.tag, tag)

    def test_marks_only_maintained_components_as_implemented(self) -> None:
        supported = (
            QeControlCard,
            QeSystemCard,
            QeElectronsCard,
            QeIonsCard,
            QeCellCard,
            QeAtomicSpeciesCard,
            QeAtomicPositionsCard,
            QeKpointsCard,
            QeCellParametersCard,
        )
        unsupported = (
            QeFcpCard,
            QeRismCard,
            QeAdditionalKpointsCard,
            QeOccupationsCard,
            QeConstraintsCard,
            QeAtomicVelocitiesCard,
            QeAtomicForcesCard,
            QeSolventsCard,
            QeHubbardCard,
        )

        for card_type in supported:
            with self.subTest(card_type=card_type.__name__):
                self.assertTrue(card_type(lines=()).implemented)
        for card_type in unsupported:
            with self.subTest(card_type=card_type.__name__):
                card = card_type(lines=())
                self.assertFalse(card.implemented)
                with self.assertRaisesRegex(NotImplementedError, "not implemented"):
                    card.to_input_group()

    def test_renders_a_data_card_option(self) -> None:
        card = QeAtomicPositionsCard(
            lines=("Si 0.00 0.00 0.00",),
            option="(crystal)",
        )

        self.assertEqual(card.tag, "ATOMIC_POSITIONS (crystal)")
        group = card.to_input_group()
        self.assertEqual(group.kind, "card")
        self.assertEqual(group.tag, "ATOMIC_POSITIONS (crystal)")
        self.assertEqual(group.lines, card.lines)

    def test_is_immutable(self) -> None:
        card = QeSystemCard(lines=("ibrav = 0,",))

        self.assertFalse(hasattr(card, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            card.lines = ()  # type: ignore[misc]

    def test_rejects_direct_base_instantiation(self) -> None:
        with self.assertRaisesRegex(TypeError, "nominal base"):
            QeCard(lines=())

    def test_rejects_options_on_namelists(self) -> None:
        with self.assertRaisesRegex(ValueError, "namelists"):
            QeSystemCard(lines=(), option="invalid")

    def test_rejects_nonlexical_lines(self) -> None:
        with self.assertRaisesRegex(ValueError, "stripped"):
            QeAtomicSpeciesCard(lines=(" Si 28.086 Si.UPF",))
        with self.assertRaisesRegex(TypeError, "contain strings"):
            QeAtomicSpeciesCard(lines=(1,))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
