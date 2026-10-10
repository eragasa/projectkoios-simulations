from __future__ import annotations

import unittest
from dataclasses import replace

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
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import QeIonDynamics
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
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationInputWrapper,
    PwDftRelaxationIntegrationRegistry,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)
from tests.projectkoios.simulations.dft.pw.support import silicon_structure_resolution


class QeRelaxInputProjectorTest(unittest.TestCase):
    def test_renders_fixed_cell_input_from_shared_components(self) -> None:
        projection = QeRelaxInputProjector(_configuration()).project(
            silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS),
            silicon_structure_resolution(),
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
        self.assertIn("calculation = 'relax'", text)
        self.assertNotIn("&CELL", text)
        self.assertIn("K_POINTS automatic\n 4 4 4 0 0 0", text)
        self.assertEqual(projection.required_external_inputs, ("Si.test.UPF",))

    def test_translates_charge_and_constrained_collinear_spin(self) -> None:
        request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
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
                            filename="Si.test.UPF",
                            sha256="1" * 64,
                            byte_size=100,
                        ),
                    ),
                ),
            ),
        )

        text = (
            QeRelaxInputProjector(_configuration())
            .project(request, silicon_structure_resolution())
            .rendered_inputs[0]
            .text
        )
        self.assertIn("tot_charge = -1", text)
        self.assertIn("nspin = 2", text)
        self.assertIn("tot_magnetization = 1", text)

    def test_rejects_unsupported_spin_orbit_treatment(self) -> None:
        request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
        request = replace(
            request,
            specification=replace(
                request.specification,
                simulation=replace(
                    request.specification.simulation,
                    spin=DftSpinTreatment(
                        mode=DftSpinMode.SPIN_ORBIT,
                        spin_quantization_axis=(0.0, 0.0, 1.0),
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(NotImplementedError, "only unpolarized"):
            QeRelaxInputProjector(_configuration()).project(
                request,
                silicon_structure_resolution(),
            )

    def test_generic_wrapper_selects_fixed_cell_integration(self) -> None:
        integration = QePwRelaxIntegration(_configuration())
        wrapper = PwDftRelaxationInputWrapper(
            registry=PwDftRelaxationIntegrationRegistry(integrations=(integration,))
        )
        projection = wrapper.project(
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            request=silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS),
            structure=silicon_structure_resolution(),
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
            structure=silicon_structure_resolution(),
        )
        variable = wrapper.project(
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            request=silicon_relaxation_request(
                PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
            ),
            structure=silicon_structure_resolution(),
        )
        self.assertIn("calculation = 'relax'", fixed.rendered_inputs[0].text)
        self.assertIn("calculation = 'vc-relax'", variable.rendered_inputs[0].text)

    def test_rejects_variable_cell_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "atomic-positions-only"):
            QeRelaxInputProjector(_configuration()).project(
                silicon_relaxation_request(
                    PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                ),
                silicon_structure_resolution(),
            )


def _configuration() -> QeRelaxProjectionConfiguration:
    return QeRelaxProjectionConfiguration(
        species=(QeAtomicSpecies("Si", 28.086, "Si.test.UPF"),),
        ion_dynamics=QeIonDynamics.BFGS,
        charge_density_cutoff_ratio=8.0,
        electronic_tolerance_ry=1.0e-8,
        electronic_atol_ry=1.0e-15,
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
        electronic_atol_ry=1.0e-15,
        prefix="system",
        pseudo_dir="./",
        outdir="./tmp/",
        input_filename="pw.in",
        coordinate_precision=8,
        cell_dynamics=QeCellDynamics.BFGS,
        cell_degrees_of_freedom=QeCellDegreesOfFreedom.ALL,
    )


if __name__ == "__main__":
    unittest.main()
