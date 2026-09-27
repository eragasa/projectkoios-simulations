from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PW_CARD_NAMES,
    PW_NAMELIST_NAMES,
    PwInput,
    PwInputGroup,
    PwInputParser,
    PwInputWriter,
)

ALL_DOCUMENTED_GROUPS = """&CONTROL
 calculation = 'scf'
/
&SYSTEM
 ibrav = 0
 nat = 1
 ntyp = 1
 ecutwfc = 40.0
/
&ELECTRONS
 conv_thr = 1.0d-8
/
&IONS
 ion_dynamics = 'verlet'
/
&CELL
 cell_dynamics = 'none'
/
&FCP
 fcp_mu = 0.0
/
&RISM
 nsolv = 1
/
ATOMIC_SPECIES
 Si 28.0855 Si.upf
ATOMIC_POSITIONS alat
 Si 0.0 0.0 0.0
K_POINTS gamma
CELL_PARAMETERS alat
 1.0 0.0 0.0
 0.0 1.0 0.0
 0.0 0.0 1.0
OCCUPATIONS
 1.0
CONSTRAINTS
 0
ATOMIC_VELOCITIES
 Si 0.0 0.0 0.0
ATOMIC_FORCES
 Si 0.0 0.0 0.0
ADDITIONAL_K_POINTS crystal
 1
 0.0 0.0 0.0 1.0
SOLVENTS
 H2O 0.0334 water
HUBBARD atomic
 U Si-3p 4.0
"""


class PwInputWriterTest(unittest.TestCase):
    def test_render_is_deterministic_and_parser_stable(self) -> None:
        input_file = PwInput(
            groups=(
                PwInputGroup(
                    kind="namelist",
                    tag="&CONTROL",
                    lines=("calculation = 'scf'", "prefix = 'si'"),
                ),
                PwInputGroup(
                    kind="card",
                    tag="ATOMIC_SPECIES",
                    lines=("Si 28.0855 Si.upf",),
                ),
            )
        )

        rendered = PwInputWriter().render(input_file)

        self.assertEqual(
            rendered,
            "&CONTROL\n"
            "    calculation = 'scf'\n"
            "    prefix = 'si'\n"
            "/\n"
            "ATOMIC_SPECIES\n"
            " Si 28.0855 Si.upf\n",
        )
        self.assertEqual(PwInputParser().parse(rendered), input_file)

    def test_render_supports_every_documented_namelist_and_card(self) -> None:
        parser = PwInputParser()
        parsed = parser.parse(ALL_DOCUMENTED_GROUPS)

        rendered = PwInputWriter().render(parsed)
        reparsed = parser.parse(rendered)

        self.assertEqual(reparsed, parsed)
        self.assertEqual(
            tuple(group.tag for group in parsed.groups if group.kind == "namelist"),
            PW_NAMELIST_NAMES,
        )
        self.assertEqual(
            tuple(
                group.tag.split(maxsplit=1)[0]
                for group in parsed.groups
                if group.kind == "card"
            ),
            PW_CARD_NAMES,
        )

    def test_render_requires_exact_input_type(self) -> None:
        with self.assertRaisesRegex(TypeError, "input_file must be a PwInput"):
            PwInputWriter().render(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
