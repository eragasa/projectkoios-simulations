from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.nscf.configuration import (  # noqa: E501
    QeNscfKPoint,
    QeNscfOccupations,
    QeNscfProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.nscf.projection import (  # noqa: E501
    QeNscfInputProjector,
)
from projectkoios.simulations.dft.pw.settings import (
    CalculationType,
    PwDftSettings,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from tests.projectkoios.simulations.dft.pw.scf.support import (
    silicon_scf_request,
)


class QeNscfInputProjectorTest(unittest.TestCase):
    def test_projects_explicit_kpoint_order_and_saved_state_identity(self) -> None:
        projection = QeNscfInputProjector(_configuration()).project(_simulation())

        self.assertEqual(projection.band_count, 8)
        self.assertEqual(projection.kpoint_count, 2)
        self.assertEqual(projection.parent_saved_state_manifest_sha256, "a" * 64)
        self.assertEqual(
            projection.required_pseudopotential_filenames,
            ("Si.pbe-n-rrkjus_psl.1.0.0.UPF",),
        )
        text = projection.rendered_input.text
        self.assertIn("calculation = 'nscf'", text)
        self.assertIn("nbnd = 8", text)
        self.assertIn("occupations = 'fixed'", text)
        self.assertIn("nosym = .true.", text)
        self.assertIn("noinv = .true.", text)
        self.assertIn(
            "K_POINTS crystal\n"
            " 2\n"
            " 0.000000000000 0.000000000000 0.000000000000 0.500000000000\n"
            " 0.500000000000 0.000000000000 0.000000000000 0.500000000000",
            text,
        )

    def test_rejects_unsupported_occupation_projection(self) -> None:
        configuration = replace(
            _configuration(),
            occupations=QeNscfOccupations.smearing,
        )

        with self.assertRaisesRegex(NotImplementedError, "smearing"):
            QeNscfInputProjector(configuration).project(_simulation())

    def test_configuration_rejects_reducible_kpoint_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires symmetry"):
            replace(_configuration(), disable_symmetry=False)

    def test_configuration_rejects_non_normalized_weights(self) -> None:
        with self.assertRaisesRegex(ValueError, "weights must sum to one"):
            replace(
                _configuration(),
                kpoints=(
                    QeNscfKPoint((0.0, 0.0, 0.0), 0.4),
                    QeNscfKPoint((0.5, 0.0, 0.0), 0.4),
                ),
            )


def _configuration() -> QeNscfProjectionConfiguration:
    return QeNscfProjectionConfiguration(
        species=(
            QeAtomicSpecies(
                symbol="Si",
                mass_amu=28.086,
                pseudopotential_filename="Si.pbe-n-rrkjus_psl.1.0.0.UPF",
            ),
        ),
        kpoints=(
            QeNscfKPoint((0.0, 0.0, 0.0), 0.5),
            QeNscfKPoint((0.5, 0.0, 0.0), 0.5),
        ),
        band_count=8,
        wavefunction_cutoff_ry=40.0,
        charge_density_cutoff_ry=320.0,
        electronic_tolerance_ry=1.0e-8,
        occupations=QeNscfOccupations.fixed,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        parent_saved_state_manifest_sha256="a" * 64,
    )


def _simulation() -> PwDftSimulation:
    source = silicon_scf_request().simulation
    return PwDftSimulation(
        unit_cell=source.unit_cell,
        settings=PwDftSettings(calculation_type=CalculationType.nscf),
    )


if __name__ == "__main__":
    unittest.main()
