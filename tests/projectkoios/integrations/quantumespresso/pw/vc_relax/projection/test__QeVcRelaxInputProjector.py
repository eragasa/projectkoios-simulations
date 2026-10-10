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
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationScope,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution


class QeVcRelaxInputProjectorTest(unittest.TestCase):
    def test_renders_variable_cell_input_from_shared_components(self) -> None:
        projection = QeVcRelaxInputProjector(_configuration()).project(
            silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL),
            silicon_structure_resolution(),
        )

        self.assertEqual(type(projection), CalculatorInputRecord)
        text = _text(projection)
        self.assertIn("calculation = 'vc-relax'", text)
        self.assertIn("tstress = .true.", text)
        self.assertIn("&CELL", text)
        self.assertIn("cell_dynamics = 'bfgs'", text)
        self.assertIn("cell_dofree = 'all'", text)
        self.assertIn("press = 0.0000000000", text)
        self.assertIn("press_conv_thr = 0.5000000000", text)
        pressure_mapping = next(
            item
            for item in projection.mappings
            if item.neutral_field == "pressure_control"
        )
        self.assertEqual(
            pressure_mapping.native_fields,
            ("CELL.press", "CELL.press_conv_thr"),
        )

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
                    ),
                    silicon_structure_resolution(),
                )

                self.assertIn(
                    f"cell_dynamics = '{cell_dynamics.value}'",
                    _text(projection),
                )
                self.assertIn(
                    "ion_dynamics = 'damp'",
                    _text(projection),
                )

    def test_rejects_fire_for_variable_cell_relaxation(self) -> None:
        configuration = _configuration(ion_dynamics=QeIonDynamics.FIRE)

        with self.assertRaisesRegex(ValueError, "invalid for vc-relax"):
            QeVcRelaxInputProjector(configuration).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                ),
                silicon_structure_resolution(),
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
                ),
                silicon_structure_resolution(),
            )

    def test_rejects_documented_but_unimplemented_cell_algorithm(self) -> None:
        configuration = _configuration(cell_dynamics=QeCellDynamics.STEEPEST_DESCENT)

        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            QeVcRelaxInputProjector(configuration).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                ),
                silicon_structure_resolution(),
            )


def _text(prepared_input: CalculatorInputRecord) -> str:
    return prepared_input.artifacts[0].content.decode("ascii")


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
        electronic_atol_ry=1.0e-15,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        coordinate_precision=8,
        cell_dynamics=cell_dynamics,
        cell_degrees_of_freedom=QeCellDegreesOfFreedom.ALL,
    )
