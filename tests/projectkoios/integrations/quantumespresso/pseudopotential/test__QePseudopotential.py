from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
)
from projectkoios.simulations.dft.pseudopotential import Pseudopotential


class QePseudopotentialTest(unittest.TestCase):
    def test_inherits_calculator_neutral_pseudopotential(self) -> None:
        pseudopotential = QePseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ONCVPSP",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
            upf_version="2.0.1",
        )

        self.assertIsInstance(pseudopotential, Pseudopotential)
        self.assertEqual(pseudopotential.upf_version, "2.0.1")


if __name__ == "__main__":
    unittest.main()
