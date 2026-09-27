from __future__ import annotations

import inspect
import unittest

from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfIntegration,
)


class PwDftScfIntegrationTest(unittest.TestCase):
    def test_simulation_owned_contract_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(PwDftScfIntegration))
        self.assertEqual(
            PwDftScfIntegration.__abstractmethods__,
            frozenset({"analyze", "integration_id", "project"}),
        )


if __name__ == "__main__":
    unittest.main()
