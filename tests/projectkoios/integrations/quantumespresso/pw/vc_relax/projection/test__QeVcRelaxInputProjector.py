from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
    QeCellCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.options import (
    QeIonicRelaxationOptions,
    QeLatticeVectorRelaxationOptions,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.projection import (  # noqa: E501
    QeRelaxationInputProjection,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.projection import (  # noqa: E501
    QeVcRelaxInputProjector,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationScope,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)


class QeVcRelaxInputProjectorTest(unittest.TestCase):
    def test_renders_variable_cell_input_from_shared_components(self) -> None:
        projection = QeVcRelaxInputProjector(_configuration()).project(
            silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL)
        )

        self.assertEqual(type(projection), QeRelaxationInputProjection)
        self.assertEqual(type(projection.ionic_options), QeIonicRelaxationOptions)
        self.assertEqual(
            type(projection.lattice_vector_options),
            QeLatticeVectorRelaxationOptions,
        )
        assert projection.lattice_vector_options is not None
        self.assertIs(
            projection.lattice_vector_options.dynamics,
            QeCellDynamics.BFGS,
        )
        self.assertIs(
            projection.lattice_vector_options.degrees_of_freedom,
            QeCellDegreesOfFreedom.ALL,
        )
        self.assertEqual(projection.lattice_vector_options.target_pressure_kbar, 0.0)
        self.assertEqual(
            projection.lattice_vector_options.pressure_tolerance_kbar,
            0.5,
        )
        self.assertEqual(type(projection.cell_card), QeCellCard)
        text = projection.rendered_inputs[0].text
        self.assertIn("calculation = 'vc-relax'", text)
        self.assertIn("tstress = .true.", text)
        self.assertIn("&CELL", text)
        self.assertIn("cell_dynamics = 'bfgs'", text)
        self.assertIn("cell_dofree = 'all'", text)
        self.assertIn("press = 0.0000000000", text)
        self.assertIn("press_conv_thr = 0.5000000000", text)

    def test_accepts_both_maintained_damped_optimizer_pairs(self) -> None:
        for cell_dynamics in (
            QeCellDynamics.DAMPED_PARRINELLO_RAHMAN,
            QeCellDynamics.DAMPED_WENTZCOVITCH,
        ):
            with self.subTest(cell_dynamics=cell_dynamics.value):
                projection = QeVcRelaxInputProjector(
                    _configuration(
                        ion_dynamics=QeIonDynamics.DAMP,
                        cell_dynamics=cell_dynamics,
                    )
                ).project(
                    silicon_relaxation_request(
                        PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                    )
                )

                self.assertIn(
                    f"cell_dynamics = '{cell_dynamics.value}'",
                    projection.rendered_inputs[0].text,
                )
                self.assertIn(
                    "ion_dynamics = 'damp'",
                    projection.rendered_inputs[0].text,
                )

    def test_rejects_fire_for_variable_cell_relaxation(self) -> None:
        configuration = _configuration(ion_dynamics=QeIonDynamics.FIRE)

        with self.assertRaisesRegex(ValueError, "invalid for vc-relax"):
            QeVcRelaxInputProjector(configuration).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                )
            )

    def test_rejects_incompatible_ion_and_cell_algorithms(self) -> None:
        configuration = _configuration(
            ion_dynamics=QeIonDynamics.DAMP,
            cell_dynamics=QeCellDynamics.BFGS,
        )

        with self.assertRaisesRegex(ValueError, "incompatible"):
            QeVcRelaxInputProjector(configuration).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                )
            )

    def test_rejects_documented_but_unimplemented_cell_algorithm(self) -> None:
        configuration = _configuration(cell_dynamics=QeCellDynamics.STEEPEST_DESCENT)

        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            QeVcRelaxInputProjector(configuration).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                )
            )


def _configuration(
    *,
    ion_dynamics: QeIonDynamics = QeIonDynamics.BFGS,
    cell_dynamics: QeCellDynamics = QeCellDynamics.BFGS,
) -> QeVcRelaxProjectionConfiguration:
    return QeVcRelaxProjectionConfiguration(
        species=(QeAtomicSpecies("Si", 28.086, "Si.test.UPF"),),
        ion_dynamics=ion_dynamics,
        charge_density_cutoff_ratio=8.0,
        electronic_tolerance_ry=1.0e-8,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        coordinate_precision=8,
        cell_dynamics=cell_dynamics,
        cell_degrees_of_freedom=QeCellDegreesOfFreedom.ALL,
    )
