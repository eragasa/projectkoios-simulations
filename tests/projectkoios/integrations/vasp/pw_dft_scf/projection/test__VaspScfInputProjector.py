from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import VaspScfInputProjector
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftOccupationMethod,
    DftOccupationPolicy,
    DftSpinMode,
    DftSpinTreatment,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from tests.projectkoios.simulations.dft.pw.scf.support import silicon_scf_request
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution


class VaspScfInputProjectorTest(unittest.TestCase):
    def test_reproduces_maintained_silicon_text_inputs(self) -> None:
        projection = VaspScfInputProjector(
            VaspScfProjectionConfiguration(
                system_label="Silicon SCF",
                poscar_comment="Silicon primitive cell",
            )
        ).project(_vasp_request(), silicon_structure_resolution())

        rendered = {
            item.filename: item.content.decode("ascii") for item in projection.artifacts
        }
        self.assertEqual(tuple(rendered), ("INCAR", "KPOINTS", "POSCAR"))
        self.assertIn("ENCUT = 400", rendered["INCAR"])
        self.assertIn("ISMEAR = 0", rendered["INCAR"])
        self.assertIn("8 8 8", rendered["KPOINTS"])
        self.assertIn("Direct", rendered["POSCAR"])

    def test_translates_charge_and_constrained_collinear_spin(self) -> None:
        request = _vasp_request()
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
                        initial_site_magnetic_moments_mu_b=(0.5, 0.5),
                    ),
                    pseudopotentials=(
                        PseudopotentialFile(
                            pseudopotential=Pseudopotential(
                                symbol="Si",
                                exchange_correlation="PBE",
                                formalism="PAW",
                                relativistic_treatment="scalar-relativistic",
                                valence_electrons=4,
                            ),
                            artifact_format=PseudopotentialArtifactFormat.VASP_POTCAR,
                            artifact_format_version=None,
                            filename="Si.POTCAR",
                            sha256="1" * 64,
                            byte_size=100,
                        ),
                    ),
                ),
            ),
        )

        projection = VaspScfInputProjector(VaspScfProjectionConfiguration()).project(
            request, silicon_structure_resolution()
        )
        incar = projection.artifacts[0].content.decode("ascii")

        self.assertIn("ISPIN = 2", incar)
        self.assertIn("NUPDOWN = 1", incar)
        self.assertIn("MAGMOM = 0.5 0.5", incar)
        self.assertIn("NELECT = 9", incar)

    def test_rejects_unsupported_noncollinear_spin(self) -> None:
        request = _vasp_request()
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
                    spin=DftSpinTreatment(mode=DftSpinMode.NONCOLLINEAR),
                ),
            ),
        )

        with self.assertRaisesRegex(NotImplementedError, "only unpolarized"):
            VaspScfInputProjector(VaspScfProjectionConfiguration()).project(
                request,
                silicon_structure_resolution(),
            )


def _vasp_request() -> PwDftScfRequest:
    request = silicon_scf_request()
    return replace(
        request,
        specification=replace(
            request.specification,
            simulation_id="Si.PrimitiveUnitCell.VASP.SCF",
            simulation=replace(
                request.specification.simulation,
                pseudopotentials=(
                    PseudopotentialFile(
                        pseudopotential=Pseudopotential(
                            symbol="Si",
                            exchange_correlation="PBE",
                            formalism="PAW",
                            relativistic_treatment="scalar-relativistic",
                            valence_electrons=4,
                        ),
                        artifact_format=PseudopotentialArtifactFormat.VASP_POTCAR,
                        artifact_format_version=None,
                        filename="Si.POTCAR",
                        sha256="1" * 64,
                        byte_size=100,
                    ),
                ),
            ),
            occupation=DftOccupationPolicy(
                method=DftOccupationMethod.GAUSSIAN,
                smearing_width_ev=0.05,
            ),
            electronic_convergence=PwDftElectronicConvergencePolicy(
                energy_tolerance_ev=1.0e-6,
                maximum_electronic_iterations=60,
            ),
        ),
    )


if __name__ == "__main__":
    unittest.main()
