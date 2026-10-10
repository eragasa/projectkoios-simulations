from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.calculation import (
    VaspCalculationProjection,
    VaspCalculationProjector,
)
from projectkoios.simulations.dft.pw.settings import AlignmentKind, CalculationType


class VaspCalculationProjectorTest(unittest.TestCase):
    def test_projects_static_scf_controls(self) -> None:
        projection = VaspCalculationProjector().project(CalculationType.scf)

        self.assertEqual(_assignments(projection), (("IBRION", "-1"), ("NSW", "0")))
        self.assertIs(projection.alignment, AlignmentKind.conditional)
        self.assertTrue(projection.is_complete)

    def test_projects_nscf_without_concealing_required_chgcar(self) -> None:
        projection = VaspCalculationProjector().project(CalculationType.nscf)

        self.assertEqual(
            _assignments(projection),
            (("IBRION", "-1"), ("NSW", "0"), ("ICHARG", "11")),
        )
        self.assertEqual(projection.required_inputs, ("self-consistent CHGCAR",))
        self.assertFalse(projection.is_complete)

    def test_projects_bands_with_run_state_and_kpoint_requirements(self) -> None:
        projection = VaspCalculationProjector().project(CalculationType.bands)

        self.assertEqual(
            projection.required_inputs,
            ("self-consistent CHGCAR", "band-path KPOINTS"),
        )
        self.assertFalse(projection.is_complete)

    def test_projects_relaxation_without_inventing_step_budget(self) -> None:
        expected = {
            CalculationType.relax: (("IBRION", "2"), ("ISIF", "2")),
            CalculationType.vc_relax: (("IBRION", "2"), ("ISIF", "3")),
        }
        for calculation_type, assignments in expected.items():
            with self.subTest(calculation_type=calculation_type):
                projection = VaspCalculationProjector().project(calculation_type)
                self.assertEqual(_assignments(projection), assignments)
                self.assertIs(projection.alignment, AlignmentKind.approximate)
                self.assertEqual(projection.required_inputs, ("INCAR.NSW",))

    def test_projects_md_without_inventing_dynamics_policy(self) -> None:
        expected = {
            CalculationType.md: (("IBRION", "0"),),
            CalculationType.vc_md: (("IBRION", "0"), ("ISIF", "3")),
        }
        for calculation_type, assignments in expected.items():
            with self.subTest(calculation_type=calculation_type):
                projection = VaspCalculationProjector().project(calculation_type)
                self.assertEqual(_assignments(projection), assignments)
                self.assertIs(projection.alignment, AlignmentKind.conditional)
                self.assertIn("INCAR.NSW", projection.required_inputs)
                self.assertIn("INCAR.POTIM", projection.required_inputs)


def _assignments(
    projection: VaspCalculationProjection,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (assignment.tag, assignment.value)
        for assignment in projection.input_file.assignments
    )


if __name__ == "__main__":
    unittest.main()
