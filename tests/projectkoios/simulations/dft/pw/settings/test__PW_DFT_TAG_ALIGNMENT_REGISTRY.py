from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pw.settings import (
    PW_DFT_TAG_ALIGNMENT_REGISTRY,
    AlignmentKind,
    PwDftTag,
)


class PwDftTagAlignmentRegistryTest(unittest.TestCase):
    def test_contains_one_alignment_for_every_semantic_tag(self) -> None:
        tags = tuple(alignment.tag for alignment in PW_DFT_TAG_ALIGNMENT_REGISTRY)

        self.assertEqual(len(tags), len(set(tags)))
        self.assertEqual(set(tags), set(PwDftTag))

    def test_records_conditional_vasp_calculation_projection(self) -> None:
        alignment = next(
            item
            for item in PW_DFT_TAG_ALIGNMENT_REGISTRY
            if item.tag is PwDftTag.calculation_type
        )

        self.assertIs(alignment.qe_alignment, AlignmentKind.exact)
        self.assertIs(alignment.vasp_alignment, AlignmentKind.conditional)
        self.assertIn("INCAR.IBRION", alignment.vasp_fields)
        self.assertIn("KPOINTS", alignment.vasp_fields)
        self.assertIn("run-state", alignment.vasp_fields)


if __name__ == "__main__":
    unittest.main()
