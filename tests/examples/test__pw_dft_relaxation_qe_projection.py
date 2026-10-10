from __future__ import annotations

import unittest

from examples.workflows.pw_dft_relaxation.qe_projection import compose
from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import QeIonDynamics
from projectkoios.integrations.quantumespresso.pw.relax.configuration import (
    QeRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.relax.integration import (
    QePwRelaxIntegration,
)
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationIntegrationRegistry,
)
from projectkoios.simulations.workflows.pw_dft_relaxation.composition import (
    PwDftRelaxationCampaign,
)
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution
from tests.projectkoios.simulations.workflows.support import silicon_relaxation_request


class QuantumEspressoRelaxationCompositionTest(unittest.TestCase):
    def test_composes_real_projection_but_exposes_no_execution_authority(self) -> None:
        integration = QePwRelaxIntegration(
            QeRelaxProjectionConfiguration(
                species=(QeAtomicSpecies("Si", 28.086, "Si.test.UPF"),),
                ion_dynamics=QeIonDynamics.BFGS,
                charge_density_cutoff_ratio=8.0,
                electronic_tolerance_ry=1.0e-8,
                electronic_atol_ry=1.0e-15,
                prefix="system",
                pseudo_dir="./",
                outdir="./tmp/",
                input_filename="pw.in",
                coordinate_precision=8,
            )
        )
        campaign = PwDftRelaxationCampaign(
            campaign_id="silicon-relaxation",
            integration_id=integration.integration_id,
            request=silicon_relaxation_request(),
            structure=silicon_structure_resolution(),
        )

        result = compose(
            campaign,
            PwDftRelaxationIntegrationRegistry((integration,)),
        )

        self.assertEqual(result.prepared_input.artifacts[0].filename, "pw.in")
        self.assertIn(
            "calculation = 'relax'",
            result.prepared_input.artifacts[0].content.decode("ascii"),
        )
        self.assertEqual(
            result.execution_handoff.authority_requirement,
            "separate-explicit-external-authority-required",
        )
        self.assertFalse(hasattr(result.execution_handoff, "execute"))


if __name__ == "__main__":
    unittest.main()
