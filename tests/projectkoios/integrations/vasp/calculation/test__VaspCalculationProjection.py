from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.calculation import (
    VaspCalculationProjection,
)
from projectkoios.integrations.vasp.incar import IncarFile
from projectkoios.simulations.dft.pw.settings import AlignmentKind


class VaspCalculationProjectionTest(unittest.TestCase):
    def test_completeness_describes_only_open_calculation_mode_inputs(self) -> None:
        complete = VaspCalculationProjection(
            input_file=IncarFile(assignments=()),
            alignment=AlignmentKind.conditional,
            required_inputs=(),
            qualification="Other calculator inputs remain independently required.",
        )
        incomplete = VaspCalculationProjection(
            input_file=IncarFile(assignments=()),
            alignment=AlignmentKind.conditional,
            required_inputs=("self-consistent CHGCAR",),
            qualification="Prior run state is required.",
        )

        self.assertTrue(complete.is_complete)
        self.assertFalse(incomplete.is_complete)


if __name__ == "__main__":
    unittest.main()
