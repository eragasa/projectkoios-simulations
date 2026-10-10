from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.simulations.dft.pseudopotential import (
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)


class QePseudopotentialFileTest(unittest.TestCase):
    def test_inherits_calculator_neutral_file_identity(self) -> None:
        pseudopotential = QePseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ONCVPSP",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
            upf_version="2.0.1",
        )
        pseudopotential_file = QePseudopotentialFile(
            pseudopotential=pseudopotential,
            filename="Si.upf",
            sha256="39822757f53f36e3bf3bfb779356152a8d3f21199c7db9dd5a931e5d18c45282",
            byte_size=225602,
        )

        self.assertIsInstance(pseudopotential_file, PseudopotentialFile)
        self.assertIs(pseudopotential_file.pseudopotential, pseudopotential)
        self.assertEqual(pseudopotential_file.symbol, "Si")
        self.assertIs(
            pseudopotential_file.artifact_format,
            PseudopotentialArtifactFormat.UPF,
        )
        self.assertEqual(pseudopotential_file.artifact_format_version, "2.0.1")


if __name__ == "__main__":
    unittest.main()
