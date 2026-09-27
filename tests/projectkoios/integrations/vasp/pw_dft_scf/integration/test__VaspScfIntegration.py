from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.integration import (
    VaspScfIntegration,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfIntegrationRegistry,
)

pytestmark = pytest.mark.integration


class VaspScfIntegrationTest(unittest.TestCase):
    def test_is_resolved_by_the_common_source_controlled_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            integration = VaspScfIntegration(
                Path(temporary_directory),
                VaspScfProjectionConfiguration(),
            )
            registry = PwDftScfIntegrationRegistry((integration,))

            resolved = registry.resolve(CalculatorIntegrationId("vasp"))

        self.assertIs(resolved, integration)


if __name__ == "__main__":
    unittest.main()
