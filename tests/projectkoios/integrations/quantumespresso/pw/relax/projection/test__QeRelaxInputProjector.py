from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeAtomicPositionsCard,
    QeAtomicSpecies,
    QeAtomicSpeciesCard,
    QeCellParametersCard,
    QeControlCard,
    QeElectronsCard,
    QeIonsCard,
    QeKpointsCard,
    QeSystemCard,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)
from projectkoios.integrations.quantumespresso.pw.relax.configuration import (  # noqa: E501
    QeRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.relax.integration import (  # noqa: E501
    QePwRelaxIntegration,
)
from projectkoios.integrations.quantumespresso.pw.relax.projection import (  # noqa: E501
    QeRelaxInputProjector,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.options import (
    QeIonicRelaxationOptions,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.projection import (  # noqa: E501
    QeRelaxationInputProjection,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.configuration import (  # noqa: E501
    QeVcRelaxProjectionConfiguration,
)
from projectkoios.integrations.quantumespresso.pw.vc_relax.integration import (  # noqa: E501
    QePwVcRelaxIntegration,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationInputWrapper,
    PwDftRelaxationIntegrationRegistry,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)


class QeRelaxInputProjectorTest(unittest.TestCase):
    def test_renders_fixed_cell_input_from_shared_components(self) -> None:
        projection = QeRelaxInputProjector(_configuration()).project(
            silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
        )

        self.assertEqual(type(projection), QeRelaxationInputProjection)
        self.assertEqual(type(projection.ionic_options), QeIonicRelaxationOptions)
        self.assertIs(projection.ionic_options.dynamics, QeIonDynamics.BFGS)
        self.assertEqual(projection.ionic_options.maximum_steps, 7)
        self.assertIsNone(projection.lattice_vector_options)
        self.assertEqual(type(projection.control_card), QeControlCard)
        self.assertEqual(type(projection.system_card), QeSystemCard)
        self.assertEqual(type(projection.electrons_card), QeElectronsCard)
        self.assertEqual(type(projection.ions_card), QeIonsCard)
        self.assertIsNone(projection.cell_card)
        self.assertEqual(type(projection.atomic_species_card), QeAtomicSpeciesCard)
        self.assertEqual(type(projection.kpoints_card), QeKpointsCard)
        self.assertEqual(type(projection.cell_parameters_card), QeCellParametersCard)
        self.assertEqual(type(projection.atomic_positions_card), QeAtomicPositionsCard)
        text = projection.rendered_inputs[0].text
        self.assertIn("&CONTROL", text)
        self.assertIn("calculation = 'relax'", text)
        self.assertIn("&IONS", text)
        self.assertIn("ion_dynamics = 'bfgs'", text)
        self.assertNotIn("&CELL", text)
        self.assertIn("CELL_PARAMETERS (angstrom)", text)
        self.assertIn("ATOMIC_POSITIONS (crystal)", text)
        self.assertIn("K_POINTS automatic\n 4 4 4 0 0 0", text)
        self.assertEqual(projection.required_external_inputs, ("Si.test.UPF",))

    def test_generic_wrapper_selects_fixed_cell_integration(self) -> None:
        integration = QePwRelaxIntegration(_configuration())
        wrapper = PwDftRelaxationInputWrapper(
            registry=PwDftRelaxationIntegrationRegistry(integrations=(integration,))
        )

        projection = wrapper.project(
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            request=silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS),
        )

        self.assertEqual(projection.integration_id.value, "quantum-espresso")

    def test_generic_wrapper_selects_mode_by_scope(self) -> None:
        wrapper = PwDftRelaxationInputWrapper(
            registry=PwDftRelaxationIntegrationRegistry(
                integrations=(
                    QePwRelaxIntegration(_configuration()),
                    QePwVcRelaxIntegration(_vc_configuration()),
                )
            )
        )

        fixed = wrapper.project(
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            request=silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS),
        )
        variable = wrapper.project(
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            request=silicon_relaxation_request(
                PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
            ),
        )

        self.assertIn("calculation = 'relax'", fixed.rendered_inputs[0].text)
        self.assertIn("calculation = 'vc-relax'", variable.rendered_inputs[0].text)

    def test_rejects_variable_cell_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "atomic-positions-only"):
            QeRelaxInputProjector(_configuration()).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                )
            )


def _configuration() -> QeRelaxProjectionConfiguration:
    return QeRelaxProjectionConfiguration(
        species=(QeAtomicSpecies("Si", 28.086, "Si.test.UPF"),),
        ion_dynamics=QeIonDynamics.BFGS,
        charge_density_cutoff_ratio=8.0,
        electronic_tolerance_ry=1.0e-8,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        coordinate_precision=8,
    )


def _vc_configuration() -> QeVcRelaxProjectionConfiguration:
    return QeVcRelaxProjectionConfiguration(
        species=(QeAtomicSpecies("Si", 28.086, "Si.test.UPF"),),
        ion_dynamics=QeIonDynamics.BFGS,
        charge_density_cutoff_ratio=8.0,
        electronic_tolerance_ry=1.0e-8,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        coordinate_precision=8,
        cell_dynamics=QeCellDynamics.BFGS,
        cell_degrees_of_freedom=QeCellDegreesOfFreedom.ALL,
    )
