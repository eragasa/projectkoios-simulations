from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pw.settings import CalculationType


class CalculationTypeTest(unittest.TestCase):
    def test_values_match_quantum_espresso_control_syntax(self) -> None:
        self.assertEqual(
            tuple(member.value for member in CalculationType),
            (
                "scf",
                "nscf",
                "bands",
                "relax",
                "md",
                "vc-relax",
                "vc-md",
            ),
        )


if __name__ == "__main__":
    unittest.main()
