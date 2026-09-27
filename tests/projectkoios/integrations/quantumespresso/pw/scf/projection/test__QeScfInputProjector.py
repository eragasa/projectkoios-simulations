from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from tests.projectkoios.simulations.dft.pw.scf.support import (
    silicon_scf_request,
)


class QeScfInputProjectorTest(unittest.TestCase):
    def test_projects_common_sampling_and_structure_into_pw_input(self) -> None:
        projection = qe_projection.QeScfInputProjector(
            configuration=_configuration()
        ).project(silicon_scf_request())

        self.assertEqual(
            projection.integration_id,
            qe_projection.QE_SCF_INTEGRATION_ID,
        )
        self.assertEqual(
            projection.required_external_inputs,
            ("Si.pbe-n-rrkjus_psl.1.0.0.UPF",),
        )
        self.assertEqual(projection.rendered_inputs[0].filename, "pw.in")
        text = projection.rendered_inputs[0].text
        self.assertIn("ibrav = 0,", text)
        self.assertIn("K_POINTS automatic\n 8 8 8 0 0 0", text)
        self.assertIn("CELL_PARAMETERS (angstrom)", text)
        self.assertIn("ATOMIC_POSITIONS (crystal)", text)
        self.assertIn("ecutwfc = 29.3994577405,", text)


def _configuration() -> qe_configuration.QeScfProjectionConfiguration:
    return qe_configuration.QeScfProjectionConfiguration(
        species=(
            qe_configuration.QeScfSpeciesConfiguration(
                symbol="Si",
                mass_amu=28.086,
                pseudopotential_filename="Si.pbe-n-rrkjus_psl.1.0.0.UPF",
            ),
        )
    )


if __name__ == "__main__":
    unittest.main()
