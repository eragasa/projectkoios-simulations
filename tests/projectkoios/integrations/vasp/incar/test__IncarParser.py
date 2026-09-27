from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.incar import (
    INCAR_DOCUMENTATION_URL,
    INCAR_TAG_DOCUMENTATION_URL,
    IncarParser,
    IncarSyntaxError,
)

INCAR_TEXT = """SYSTEM = Si convergence
ISMEAR = -1 ; SIGMA = 0.05 ! broadening
MAGMOM = 0 0 1.0 \\
         0 0 -1.0 \\
         6*0
WANNIER90_WIN = "
Begin Projections
Si:sp3
End Projections
"
KERNEL_TRUNCATION/LTRUNCATE = T
PLUGINS {
  STRUCTURE = T
  NEIGHBOR_CUTOFF = 5.0
}
"""


class IncarParserTest(unittest.TestCase):
    def test_parse_supports_generic_official_incar_syntax(self) -> None:
        input_file = IncarParser().parse(INCAR_TEXT)

        self.assertEqual(
            tuple(assignment.tag for assignment in input_file.assignments),
            (
                "SYSTEM",
                "ISMEAR",
                "SIGMA",
                "MAGMOM",
                "WANNIER90_WIN",
                "KERNEL_TRUNCATION/LTRUNCATE",
                "PLUGINS/STRUCTURE",
                "PLUGINS/NEIGHBOR_CUTOFF",
            ),
        )
        self.assertEqual(input_file.assignments[3].value, "0 0 1.0 0 0 -1.0 6*0")
        self.assertEqual(
            input_file.assignments[4].value,
            '"\nBegin Projections\nSi:sp3\nEnd Projections\n"',
        )

    def test_records_official_documentation_authorities(self) -> None:
        self.assertEqual(INCAR_DOCUMENTATION_URL, "https://vasp.at/wiki/INCAR")
        self.assertEqual(
            INCAR_TAG_DOCUMENTATION_URL,
            "https://vasp.at/wiki/Category:INCAR_tag",
        )

    def test_ignores_non_statement_section_labels(self) -> None:
        input_file = IncarParser().parse("electronic optimization\nENCUT = 400 # eV\n")

        self.assertEqual(len(input_file.assignments), 1)
        self.assertEqual(input_file.assignments[0].tag, "ENCUT")
        self.assertEqual(input_file.assignments[0].value, "400")

    def test_rejects_unterminated_nested_block(self) -> None:
        with self.assertRaisesRegex(IncarSyntaxError, "unterminated nested-tag block"):
            IncarParser().parse("PLUGINS {\n STRUCTURE = T\n")

    def test_rejects_non_ascii_text(self) -> None:
        with self.assertRaisesRegex(IncarSyntaxError, "plain ASCII"):
            IncarParser().parse("SYSTEM = silicón\n")


if __name__ == "__main__":
    unittest.main()
