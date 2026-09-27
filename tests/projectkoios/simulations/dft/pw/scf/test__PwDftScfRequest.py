from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfSampling,
)
from tests.projectkoios.simulations.dft.pw.scf.support import (
    silicon_scf_request,
)


class PwDftScfRequestTest(unittest.TestCase):
    def test_represents_calculator_neutral_sampling(self) -> None:
        request = silicon_scf_request()

        self.assertEqual(request.sampling.kpoint_mesh, (8, 8, 8))
        self.assertEqual(request.sampling.wavefunction_cutoff_ev, 400.0)

    def test_rejects_nonpositive_cutoff(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive finite"):
            replace(
                silicon_scf_request().sampling,
                wavefunction_cutoff_ev=0.0,
            )

    def test_sampling_type_is_nominal(self) -> None:
        self.assertIs(type(silicon_scf_request().sampling), PwDftScfSampling)


if __name__ == "__main__":
    unittest.main()
