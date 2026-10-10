from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import projection as qe_projection
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftOccupationMethod,
    DftOccupationPolicy,
    DftSpinMode,
    DftSpinTreatment,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from tests.projectkoios.simulations.dft.pw.scf.support import silicon_scf_request
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution


class QeScfInputProjectorTest(unittest.TestCase):
    def test_projects_common_sampling_and_structure_into_pw_input(self) -> None:
        projection = qe_projection.QeScfInputProjector(
            configuration=_configuration()
        ).project(silicon_scf_request(), silicon_structure_resolution())

        self.assertEqual(
            projection.integration_id,
            qe_projection.QE_SCF_INTEGRATION_ID,
        )
        self.assertEqual(
            tuple(item.filename for item in projection.external_requirements),
            ("Si.pbe-n-rrkjus_psl.1.0.0.UPF",),
        )
        self.assertEqual(projection.artifacts[0].filename, "pw.in")
        self.assertEqual(projection.source.simulation_id, "Si.PrimitiveUnitCell.QE.SCF")
        text = projection.artifacts[0].content.decode("ascii")
        self.assertIn("ibrav = 0,", text)
        self.assertIn("K_POINTS automatic\n 8 8 8 0 0 0", text)
        self.assertIn("CELL_PARAMETERS (angstrom)", text)
        self.assertIn("ATOMIC_POSITIONS (crystal)", text)
        self.assertIn("ecutwfc = 29.3994577405,", text)

    def test_translates_charge_and_constrained_collinear_spin(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
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
            ),
        )

        text = (
            qe_projection.QeScfInputProjector(configuration=_configuration())
            .project(request, silicon_structure_resolution())
            .artifacts[0]
            .content.decode("ascii")
        )

        self.assertIn("tot_charge = -1,", text)
        self.assertIn("nspin = 2,", text)
        self.assertIn("tot_magnetization = 1,", text)

    def test_translates_gaussian_smearing_and_species_initial_magnetization(
        self,
    ) -> None:
        request = silicon_scf_request()
        pseudopotential = PseudopotentialFile(
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
        )
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
                    spin=DftSpinTreatment(
                        mode=DftSpinMode.COLLINEAR,
                        initial_site_magnetic_moments_mu_b=(1.0, 1.0),
                    ),
                    pseudopotentials=(pseudopotential,),
                ),
                occupation=DftOccupationPolicy(
                    method=DftOccupationMethod.GAUSSIAN,
                    smearing_width_ev=0.13605693122994,
                ),
            ),
        )

        text = (
            qe_projection.QeScfInputProjector(configuration=_configuration())
            .project(request, silicon_structure_resolution())
            .artifacts[0]
            .content.decode("ascii")
        )

        self.assertIn("occupations = 'smearing',", text)
        self.assertIn("smearing = 'gaussian',", text)
        self.assertIn("degauss = 1.0000000000e-02,", text)
        self.assertIn("nspin = 2,", text)
        self.assertIn("starting_magnetization(1) = 0.2500000000,", text)
        self.assertIn("electron_maxstep = 100", text)

    def test_rejects_site_moments_that_one_qe_species_cannot_represent(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
                    spin=DftSpinTreatment(
                        mode=DftSpinMode.COLLINEAR,
                        initial_site_magnetic_moments_mu_b=(1.0, 0.0),
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
            ),
        )

        with self.assertRaisesRegex(NotImplementedError, "different site moments"):
            qe_projection.QeScfInputProjector(configuration=_configuration()).project(
                request,
                silicon_structure_resolution(),
            )

    def test_uses_configured_native_ry_comparison_tolerance(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            specification=replace(
                request.specification,
                electronic_convergence=replace(
                    request.specification.electronic_convergence,
                    # Perturb the neutral threshold by about 3.7e-13 Ry: large
                    # enough to fail the strict profile but fit the wider one.
                    energy_tolerance_ev=(
                        request.specification.electronic_convergence.energy_tolerance_ev
                        + 5.0e-12
                    ),
                ),
            ),
        )

        with self.assertRaisesRegex(ValueError, "electronic tolerance"):
            qe_projection.QeScfInputProjector(
                configuration=replace(_configuration(), electronic_atol_ry=1.0e-15)
            ).project(request, silicon_structure_resolution())

        qe_projection.QeScfInputProjector(
            configuration=replace(_configuration(), electronic_atol_ry=1.0e-12)
        ).project(request, silicon_structure_resolution())

    def test_rejects_negative_native_ry_comparison_tolerance(self) -> None:
        with self.assertRaisesRegex(ValueError, "electronic_atol_ry"):
            replace(_configuration(), electronic_atol_ry=-1.0)

    def test_rejects_native_file_layout_not_supported_by_executor(self) -> None:
        with self.assertRaisesRegex(NotImplementedError, "pseudo_dir"):
            replace(_configuration(), pseudo_dir="./pseudo/")
        with self.assertRaisesRegex(NotImplementedError, "outdir"):
            replace(_configuration(), outdir="./scratch/")

    def test_rejects_unsupported_noncollinear_spin(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
                    spin=DftSpinTreatment(
                        mode=DftSpinMode.NONCOLLINEAR,
                        initial_site_magnetic_moment_vectors_mu_b=(
                            (1.0, 0.0, 0.0),
                            (0.0, 1.0, 0.0),
                        ),
                    ),
                ),
            ),
        )

        with self.assertRaisesRegex(NotImplementedError, "only unpolarized"):
            qe_projection.QeScfInputProjector(configuration=_configuration()).project(
                request,
                silicon_structure_resolution(),
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
