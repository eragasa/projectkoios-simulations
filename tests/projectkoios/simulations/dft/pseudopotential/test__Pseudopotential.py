from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pseudopotential import Pseudopotential


class PseudopotentialTest(unittest.TestCase):
    def test_constructs_calculator_neutral_metadata(self) -> None:
        pseudopotential = Pseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="norm-conserving",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
        )

        self.assertEqual(pseudopotential.symbol, "Si")
        self.assertEqual(pseudopotential.exchange_correlation, "PBE")
        self.assertEqual(pseudopotential.valence_electrons, 4)

    def test_rejects_non_element_symbol(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be an element symbol"):
            Pseudopotential(
                symbol="silicon",
                exchange_correlation="PBE",
                formalism="norm-conserving",
                relativistic_treatment="scalar-relativistic",
                valence_electrons=4,
            )


if __name__ == "__main__":
    unittest.main()
