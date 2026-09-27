from __future__ import annotations

import hashlib
import unittest

from projectkoios.integrations.lammps import (
    inspect_lammps_data_structure,
)
from projectkoios.integrations.lammps.models import SourceFileEvidence


def evidence_for(text: str) -> SourceFileEvidence:
    payload = text.encode("utf-8")
    return SourceFileEvidence(
        "structure_db/unit.structure",
        hashlib.sha256(payload).hexdigest(),
        len(payload),
    )


class InspectLammpsDataStructureTest(unittest.TestCase):
    def test_inspects_a_charge_style_orthogonal_structure(self) -> None:
        text = """# ['Mg', 'O']

2 atoms
2 atom types

0.0 4.0 xlo xhi
0.0 5.0 ylo yhi
0.0 6.0 zlo zhi
0.0 0.0 0.0 xy xz yz

Atoms

1 1 2.0 0.0 0.0 0.0
2 2 -2.0 2.0 2.5 3.0
"""

        observation = inspect_lammps_data_structure(
            name="unit",
            evidence=evidence_for(text),
            text=text,
        )

        self.assertEqual(observation.species_order, ("Mg", "O"))
        self.assertEqual(observation.atom_count, 2)
        self.assertEqual(observation.atom_type_count, 2)
        self.assertEqual(observation.atom_style, "charge")
        self.assertEqual(
            observation.bounds,
            ((0.0, 4.0), (0.0, 5.0), (0.0, 6.0)),
        )
        self.assertEqual(observation.tilt_factors, (0.0, 0.0, 0.0))
        self.assertFalse(observation.to_dict()["calculator_execution_authorized"])

    def test_rejects_incomplete_atom_identifiers(self) -> None:
        text = """# ['Mg']
2 atoms
1 atom types
0.0 4.0 xlo xhi
0.0 4.0 ylo yhi
0.0 4.0 zlo zhi
0.0 0.0 0.0 xy xz yz
Atoms
1 1 0.0 0.0 0.0
3 1 1.0 1.0 1.0
"""

        with self.assertRaisesRegex(ValueError, "identifiers are incomplete"):
            inspect_lammps_data_structure(
                name="unit", evidence=evidence_for(text), text=text
            )

    def test_rejects_structure_text_that_does_not_match_its_evidence(self) -> None:
        text = "# ['Mg']\n"
        altered_evidence = evidence_for(text.replace("Mg", "Si"))

        with self.assertRaisesRegex(ValueError, "hash does not match"):
            inspect_lammps_data_structure(
                name="unit", evidence=altered_evidence, text=text
            )


if __name__ == "__main__":
    unittest.main()
