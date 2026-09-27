from __future__ import annotations

import inspect
import unittest

from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationIntegration,
)


class PwDftRelaxationIntegrationTest(unittest.TestCase):
    def test_simulation_owned_contract_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(PwDftRelaxationIntegration))
        self.assertEqual(
            PwDftRelaxationIntegration.__abstractmethods__,
            frozenset({"description", "project"}),
        )


if __name__ == "__main__":
    unittest.main()
