from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialFile,
)


class PseudopotentialFileTest(unittest.TestCase):
    def test_binds_metadata_to_exact_file_identity(self) -> None:
        pseudopotential = _pseudopotential()
        pseudopotential_file = PseudopotentialFile(
            pseudopotential=pseudopotential,
            filename="Si.pseudo",
            sha256="a" * 64,
            byte_size=225602,
        )

        self.assertIs(pseudopotential_file.pseudopotential, pseudopotential)
        self.assertEqual(pseudopotential_file.symbol, "Si")
        self.assertEqual(pseudopotential_file.filename, "Si.pseudo")

    def test_rejects_path_as_filename(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a basename"):
            PseudopotentialFile(
                pseudopotential=_pseudopotential(),
                filename="pseudo/Si.pseudo",
                sha256="a" * 64,
                byte_size=225602,
            )


def _pseudopotential() -> Pseudopotential:
    return Pseudopotential(
        symbol="Si",
        exchange_correlation="PBE",
        formalism="norm-conserving",
        relativistic_treatment="scalar-relativistic",
        valence_electrons=4,
    )


if __name__ == "__main__":
    unittest.main()
