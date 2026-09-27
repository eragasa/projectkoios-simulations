from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    integration as qe_integration,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfIntegrationRegistry,
)

pytestmark = pytest.mark.integration


class QePwDftScfIntegrationTest(unittest.TestCase):
    def test_qe_resolves_by_its_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory)
            qe = qe_integration.QePwDftScfIntegration(
                artifact_root=artifact_root,
                projection_configuration=qe_configuration.QeScfProjectionConfiguration(
                    species=(
                        qe_configuration.QeScfSpeciesConfiguration(
                            symbol="Si",
                            mass_amu=28.086,
                            pseudopotential_filename="Si.upf",
                        ),
                    )
                ),
            )
            registry = PwDftScfIntegrationRegistry(integrations=(qe,))

            resolved_qe = registry.resolve(
                CalculatorIntegrationId(value="quantum-espresso")
            )

        self.assertIs(resolved_qe, qe)


if __name__ == "__main__":
    unittest.main()
