from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicSpecies,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
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

        text = projection.rendered_inputs[0].text
        self.assertIn("calculation = 'vc-relax'", text)
        self.assertIn("tstress = .true.", text)
        self.assertIn("&CELL", text)
        self.assertIn("cell_dynamics = 'bfgs'", text)
        self.assertIn("cell_dofree = 'all'", text)
        self.assertIn("press = 0.0000000000", text)
        self.assertIn("press_conv_thr = 0.5000000000", text)

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
