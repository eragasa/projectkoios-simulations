from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from tests.projectkoios.simulations.dft.pw.scf.support import silicon_scf_request


class PwDftScfRequestTest(unittest.TestCase):
    def test_separates_occurrence_from_reusable_specification(self) -> None:
        request = silicon_scf_request()

        self.assertEqual(request.evaluation_id, "silicon-scf")
        self.assertEqual(request.specification.kpoint_sampling.mesh, (8, 8, 8))
        self.assertEqual(request.specification.wavefunction_cutoff_ev, 400.0)
        self.assertIs(type(request.specification), PwDftScfSpecification)

    def test_rejects_nonpositive_cutoff(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive and finite"):
            replace(
                silicon_scf_request().specification,
                wavefunction_cutoff_ev=0.0,
            )

    def test_rejects_unqualified_simulation_identifier(self) -> None:
        with self.assertRaisesRegex(ValueError, "qualified stable"):
            replace(
                silicon_scf_request().specification,
                simulation_id="local",
            )


if __name__ == "__main__":
    unittest.main()
