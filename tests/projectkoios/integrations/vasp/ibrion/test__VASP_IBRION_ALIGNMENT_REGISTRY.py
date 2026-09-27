from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.ibrion import (
    VASP_IBRION_ALIGNMENT_REGISTRY,
    VASP_NEB_ALIGNMENT,
    VaspIbrion,
)
from projectkoios.simulations.dft.pw.settings import AlignmentKind


class VaspIbrionAlignmentRegistryTest(unittest.TestCase):
    def test_covers_every_officially_listed_ibrion_value_once(self) -> None:
        indexed = tuple(item.ibrion for item in VASP_IBRION_ALIGNMENT_REGISTRY)

        self.assertEqual(len(indexed), len(set(indexed)))
        self.assertEqual(set(indexed), set(VaspIbrion))
        self.assertEqual(
            {item.value for item in VaspIbrion},
            {-1, 0, 1, 2, 3, 5, 6, 7, 8, 11, 12, 40, 44},
        )

    def test_does_not_claim_qe_has_a_conjugate_gradient_ionic_mode(self) -> None:
        alignment = _alignment(VaspIbrion.conjugate_gradient)

        self.assertFalse(alignment.algorithm_equivalent)
        self.assertNotIn("ion_dynamics='cg'", alignment.qe_fields)
        self.assertIn("does not document ion_dynamics='cg'", alignment.qualification)

    def test_distinguishes_finite_difference_and_dfpt_phonons(self) -> None:
        finite_difference = _alignment(VaspIbrion.finite_differences_with_symmetry)
        perturbation_theory = _alignment(VaspIbrion.perturbation_theory_with_symmetry)

        self.assertEqual(finite_difference.qe_executable, "ph.x")
        self.assertFalse(finite_difference.algorithm_equivalent)
        self.assertIs(finite_difference.alignment, AlignmentKind.approximate)
        self.assertEqual(perturbation_theory.qe_executable, "ph.x")
        self.assertTrue(perturbation_theory.algorithm_equivalent)
        self.assertIs(perturbation_theory.alignment, AlignmentKind.conditional)

    def test_does_not_misidentify_ibrion_44_as_neb(self) -> None:
        dimer = _alignment(VaspIbrion.improved_dimer_method)

        self.assertIsNone(dimer.qe_executable)
        self.assertFalse(dimer.algorithm_equivalent)
        self.assertIn("not NEB", dimer.qualification)
        self.assertEqual(VASP_NEB_ALIGNMENT.qe_executable, "neb.x")
        self.assertIn("IMAGES", VASP_NEB_ALIGNMENT.vasp_fields)
        self.assertIn("SPRING", VASP_NEB_ALIGNMENT.vasp_fields)
        self.assertIn("IBRION=44", VASP_NEB_ALIGNMENT.qualification)


def _alignment(ibrion: VaspIbrion):
    return next(
        item for item in VASP_IBRION_ALIGNMENT_REGISTRY if item.ibrion is ibrion
    )


if __name__ == "__main__":
    unittest.main()
