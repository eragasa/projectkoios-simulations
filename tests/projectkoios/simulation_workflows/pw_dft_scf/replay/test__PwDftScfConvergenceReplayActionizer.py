from __future__ import annotations

import unittest

import pytest

from projectkoios.simulation_workflows.pw_dft_scf.convergence.base import (
    PwDftScfConvergenceCoordinate,
    PwDftScfEnergyObservation,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.policy import (
    PwDftScfConvergencePolicy,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.action import (
    PwDftScfConvergenceReplayActionizer,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.error import (
    PwDftScfConvergenceReplayError,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.evidence import (
    PwDftScfConvergenceReplayEvidence,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.identity import (
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.request import (
    PwDftScfConvergenceReplayRequest,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId

_MESH_COMPONENTS = {4: 0.0, 6: 0.0100, 8: 0.0200, 10: 0.0205, 12: 0.0207}
_CUTOFF_COMPONENTS = {
    300.0: 0.0,
    350.0: 0.0100,
    400.0: 0.0200,
    450.0: 0.0204,
    500.0: 0.0206,
}
_INITIAL_COORDINATES = tuple(
    (mesh, cutoff) for mesh in (4, 6, 8) for cutoff in (300.0, 350.0, 400.0)
)
_EXTENSION_COORDINATES = tuple(
    (mesh, cutoff)
    for mesh in (4, 6, 8, 10, 12)
    for cutoff in (300.0, 350.0, 400.0, 450.0, 500.0)
    if (mesh, cutoff) not in _INITIAL_COORDINATES
)


class PwDftScfConvergenceReplayActionizerTest(unittest.TestCase):
    def test_typed_action_has_exact_identity(self) -> None:
        evidence = _evidence()
        request = PwDftScfConvergenceReplayRequest(evidence=evidence)

        action_result = PwDftScfConvergenceReplayActionizer().action(request=request)

        self.assertEqual(
            request.action_identity,
            PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
        )
        self.assertEqual(
            request.action_version,
            PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
        )
        self.assertEqual(action_result.action_identity, request.action_identity)
        self.assertEqual(action_result.action_version, request.action_version)

    @pytest.mark.adversarial
    def test_actionizer_rejects_an_untyped_evidence_argument(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "request must be PwDftScfConvergenceReplayRequest",
        ):
            PwDftScfConvergenceReplayActionizer().action(
                request=_evidence(),  # type: ignore[arg-type]
            )

    @pytest.mark.property
    def test_replays_extension_then_acceptance_deterministically(self) -> None:
        actionizer = PwDftScfConvergenceReplayActionizer()
        forward = actionizer.action(
            request=PwDftScfConvergenceReplayRequest(evidence=_evidence())
        )
        reversed_order = actionizer.action(
            request=PwDftScfConvergenceReplayRequest(evidence=_evidence(reverse=True))
        )

        self.assertEqual(forward.observation_count, 25)
        self.assertEqual(
            set(forward.initial_extension.coordinates),
            set(reversed_order.initial_extension.coordinates),
        )
        self.assertEqual(forward.final_assessment, reversed_order.final_assessment)
        self.assertTrue(forward.final_assessment.converged)

    @pytest.mark.adversarial
    def test_rejects_extension_that_does_not_match_policy_request(self) -> None:
        evidence = _evidence()
        incomplete = PwDftScfConvergenceReplayEvidence(
            evidence_id=evidence.evidence_id,
            integration_id=evidence.integration_id,
            policy=evidence.policy,
            initial_observations=evidence.initial_observations,
            extension_observations=evidence.extension_observations[:-1],
            source_evidence_reference=evidence.source_evidence_reference,
        )

        with self.assertRaisesRegex(
            PwDftScfConvergenceReplayError,
            "do not match",
        ):
            PwDftScfConvergenceReplayActionizer().action(
                request=PwDftScfConvergenceReplayRequest(evidence=incomplete)
            )

    @pytest.mark.adversarial
    def test_rejects_overlapping_initial_and_extension_coordinates(self) -> None:
        evidence = _evidence()
        with self.assertRaisesRegex(ValueError, "must be disjoint"):
            PwDftScfConvergenceReplayEvidence(
                evidence_id=evidence.evidence_id,
                integration_id=evidence.integration_id,
                policy=evidence.policy,
                initial_observations=evidence.initial_observations,
                extension_observations=(evidence.initial_observations[0],),
                source_evidence_reference=evidence.source_evidence_reference,
            )


def _evidence(*, reverse: bool = False) -> PwDftScfConvergenceReplayEvidence:
    initial = _observations(_INITIAL_COORDINATES)
    extension = _observations(_EXTENSION_COORDINATES)
    if reverse:
        initial = tuple(reversed(initial))
        extension = tuple(reversed(extension))
    return PwDftScfConvergenceReplayEvidence(
        evidence_id="synthetic-qe-grid-replay",
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        policy=PwDftScfConvergencePolicy(
            tolerance_mev_per_atom=1.0,
            required_consecutive_deltas=2,
            mesh_increment=2,
            cutoff_increment_ev=50.0,
            extension_steps=2,
            maximum_mesh_density=12,
            maximum_cutoff_ev=500.0,
            maximum_grid_points=25,
        ),
        initial_observations=initial,
        extension_observations=extension,
        source_evidence_reference="provider-evidence:synthetic-software-verification",
    )


def _observations(
    coordinates: tuple[tuple[int, float], ...],
) -> tuple[PwDftScfEnergyObservation, ...]:
    return tuple(
        PwDftScfEnergyObservation(
            coordinate=PwDftScfConvergenceCoordinate(mesh, cutoff),
            total_energy_ev_per_atom=(
                -5.0 - _MESH_COMPONENTS[mesh] - _CUTOFF_COMPONENTS[cutoff]
            ),
        )
        for mesh, cutoff in coordinates
    )


if __name__ == "__main__":
    unittest.main()
