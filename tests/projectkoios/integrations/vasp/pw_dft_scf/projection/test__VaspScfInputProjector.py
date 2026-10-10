from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

import pytest

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VaspScfInputProjector,
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

pytestmark = pytest.mark.integration

_INPUT_ROOT = Path(
    "examples/projectkoios/integrations/vasp/pw_dft_scf/Si/primitive/input"
)


class VaspScfInputProjectorTest(unittest.TestCase):
    def test_reproduces_maintained_silicon_text_inputs(self) -> None:
        projection = VaspScfInputProjector(
            VaspScfProjectionConfiguration(
                system_label="Silicon SCF",
                poscar_comment="Silicon primitive cell",
            )
        ).project(silicon_scf_request())
        rendered = {item.filename: item.text for item in projection.rendered_inputs}

        for filename in ("INCAR", "KPOINTS", "POSCAR"):
            with self.subTest(filename=filename):
                self.assertEqual(
                    rendered[filename],
                    (_INPUT_ROOT / filename).read_text(encoding="ascii"),
                )
        self.assertEqual(projection.required_external_inputs, ("POTCAR",))

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
        )

        projection = VaspScfInputProjector(VaspScfProjectionConfiguration()).project(
            request
        )
        incar = next(
            item.text for item in projection.rendered_inputs if item.filename == "INCAR"
        )

        self.assertIn("ISPIN = 2", incar)
        self.assertIn("NUPDOWN = 1", incar)
        self.assertIn("MAGMOM = 0.5 0.5", incar)
        self.assertIn("NELECT = 9", incar)

    def test_rejects_unsupported_noncollinear_spin(self) -> None:
        request = silicon_scf_request()
        request = replace(
            request,
            simulation=replace(
                request.simulation,
                spin=DftSpinTreatment(mode=DftSpinMode.NONCOLLINEAR),
            ),
        )

        with self.assertRaisesRegex(NotImplementedError, "only unpolarized"):
            VaspScfInputProjector(VaspScfProjectionConfiguration()).project(request)


if __name__ == "__main__":
    unittest.main()
