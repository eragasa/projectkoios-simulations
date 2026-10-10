from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftCellRelaxationMode,
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationDegreesOfFreedom,
    PwDftRelaxationInitialization,
    PwDftRelaxationScope,
)
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request,
)


class PwDftRelaxationRequestTest(unittest.TestCase):
    def test_represents_version_one_relaxation_controls(self) -> None:
        degrees_of_freedom = PwDftRelaxationDegreesOfFreedom(
            relax_atomic_positions=True,
            cell_mode=PwDftCellRelaxationMode.SELECTED_COMPONENTS,
            selected_strain_components=(True, True, True, False, False, False),
        )

        self.assertEqual(
            PwDftRelaxationInitialization.FROM_EXACT_STARTING_STRUCTURE.value,
            "from-exact-starting-structure",
        )
        self.assertEqual(
            degrees_of_freedom.selected_strain_components,
            (True, True, True, False, False, False),
        )

    def test_rejects_empty_selected_cell_components(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonempty six-boolean"):
            PwDftRelaxationDegreesOfFreedom(
                relax_atomic_positions=True,
                cell_mode=PwDftCellRelaxationMode.SELECTED_COMPONENTS,
                selected_strain_components=(False, False, False, False, False, False),
            )

    def test_accepts_explicit_fixed_and_variable_cell_policies(self) -> None:
        fixed = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
        variable = silicon_relaxation_request(
            PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
        )

        self.assertIsNone(fixed.specification.ionic_convergence.target_pressure_kbar)
        self.assertEqual(
            variable.specification.ionic_convergence.target_pressure_kbar,
            0.0,
        )

    def test_stage_identity_is_owned_by_the_relaxation_specification(self) -> None:
        request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)

        self.assertEqual(
            request.specification.scope,
            PwDftRelaxationScope.ATOMIC_POSITIONS,
        )
        self.assertFalse(hasattr(request.specification.simulation, "settings"))

    def test_rejects_pressure_controls_for_fixed_cell(self) -> None:
        request = silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
        policy = PwDftRelaxationConvergencePolicy(
            maximum_ionic_steps=7,
            total_energy_tolerance_ev=0.001,
            force_tolerance_ev_per_angstrom=0.01,
            target_pressure_kbar=0.0,
            pressure_tolerance_kbar=0.5,
        )

        with self.assertRaisesRegex(ValueError, "must not declare pressure"):
            replace(
                request.specification,
                ionic_convergence=policy,
            )


if __name__ == "__main__":
    unittest.main()
