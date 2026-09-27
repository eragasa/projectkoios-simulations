from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PW_CARD_NAMES,
    PW_INPUT_DOCUMENTATION_URL,
    PW_INPUT_DOCUMENTATION_VERSION,
    PW_NAMELIST_NAMES,
    PwInputParser,
    QuantumEspressoInputError,
)

PW_INPUT = """&CONTROL
  calculation = 'scf'
  prefix = 'si'
/
&SYSTEM
  ibrav = 2
  nat = 2
  ntyp = 1
  ecutwfc = 40.0
/
&ELECTRONS
  conv_thr = 1.0d-10
/
ATOMIC_SPECIES
  Si 28.0855 Si.upf
ATOMIC_POSITIONS alat
  Si 0.00 0.00 0.00
  Si 0.25 0.25 0.25
K_POINTS automatic
  6 6 6 1 1 1
"""


class PwInputParserTest(unittest.TestCase):
    def test_parse_preserves_ordered_namelists_and_cards(self) -> None:
        parsed = PwInputParser().parse(PW_INPUT)

        self.assertEqual(
            tuple(group.tag for group in parsed.groups),
            (
                "&CONTROL",
                "&SYSTEM",
                "&ELECTRONS",
                "ATOMIC_SPECIES",
                "ATOMIC_POSITIONS alat",
                "K_POINTS automatic",
            ),
        )
        self.assertEqual(parsed.groups[1].kind, "namelist")
        self.assertEqual(parsed.groups[3].kind, "card")
        self.assertEqual(parsed.groups[3].lines, ("Si 28.0855 Si.upf",))
        self.assertEqual(parsed.groups[-1].lines, ("6 6 6 1 1 1",))

    def test_documented_group_inventory_is_complete_for_pw_7_5(self) -> None:
        self.assertEqual(
            PW_INPUT_DOCUMENTATION_URL,
            "https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1",
        )
        self.assertEqual(PW_INPUT_DOCUMENTATION_VERSION, "7.5")
        self.assertEqual(
            PW_NAMELIST_NAMES,
            (
                "&CONTROL",
                "&SYSTEM",
                "&ELECTRONS",
                "&IONS",
                "&CELL",
                "&FCP",
                "&RISM",
            ),
        )
        self.assertEqual(
            PW_CARD_NAMES,
            (
                "ATOMIC_SPECIES",
                "ATOMIC_POSITIONS",
                "K_POINTS",
                "CELL_PARAMETERS",
                "OCCUPATIONS",
                "CONSTRAINTS",
                "ATOMIC_VELOCITIES",
                "ATOMIC_FORCES",
                "ADDITIONAL_K_POINTS",
                "SOLVENTS",
                "HUBBARD",
            ),
        )

    def test_parse_rejects_unterminated_namelist(self) -> None:
        with self.assertRaisesRegex(
            QuantumEspressoInputError, "unterminated pw.x namelist"
        ):
            PwInputParser().parse("&CONTROL\n calculation = 'scf'\n")

    def test_parse_rejects_content_outside_a_group(self) -> None:
        with self.assertRaisesRegex(
            QuantumEspressoInputError, "content outside an input group"
        ):
            PwInputParser().parse("calculation = 'scf'\n")


if __name__ == "__main__":
    unittest.main()
