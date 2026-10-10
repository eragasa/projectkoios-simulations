from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftSpinMode,
    DftSpinTreatment,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
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

    def test_translates_charge_and_constrained_collinear_spin(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            simulation=replace(
                request.simulation,
                charge=DftChargeState(delta_n_electrons=1, charge_state=-1),
                spin=DftSpinTreatment(
                    mode=DftSpinMode.COLLINEAR,
                    spin_channel_electron_difference=1,
                    constrain_spin_channel_difference=True,
                ),
                pseudopotentials=(
                    PseudopotentialFile(
                        pseudopotential=Pseudopotential(
                            symbol="Si",
                            exchange_correlation="PBE",
                            formalism="ultrasoft",
                            relativistic_treatment="scalar-relativistic",
                            valence_electrons=4,
                        ),
                        artifact_format=PseudopotentialArtifactFormat.UPF,
                        artifact_format_version="2.0.1",
                        filename="Si.pbe-n-rrkjus_psl.1.0.0.UPF",
                        sha256="1" * 64,
                        byte_size=100,
                    ),
                ),
            ),
        )

        text = (
            qe_projection.QeScfInputProjector(configuration=_configuration())
            .project(request)
            .rendered_inputs[0]
            .text
        )

        self.assertIn("tot_charge = -1,", text)
        self.assertIn("nspin = 2,", text)
        self.assertIn("tot_magnetization = 1,", text)

    def test_rejects_unsupported_noncollinear_spin(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            simulation=replace(
                request.simulation,
                spin=DftSpinTreatment(
                    mode=DftSpinMode.NONCOLLINEAR,
                    initial_site_magnetic_moment_vectors_mu_b=(
                        (1.0, 0.0, 0.0),
                        (0.0, 1.0, 0.0),
                    ),
                ),
            ),
        )

        with self.assertRaisesRegex(NotImplementedError, "only unpolarized"):
            qe_projection.QeScfInputProjector(configuration=_configuration()).project(
                request
            )


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
