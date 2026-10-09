"""Pure convergence replay action."""

from __future__ import annotations

from typing import ClassVar

from projectkoios.simulations.workflows.pw_dft_scf.convergence.assessment import (
    EnergyGridConvergenceAssessmentRequest,
    EnergyGridConvergenceAssessor,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.controller import (
    ExtendPwDftScfConvergence,
    PwDftScfConvergenceAccepted,
    PwDftScfConvergenceController,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.error import (
    PwDftScfConvergenceReplayError,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.identity import (
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.request import (
    PwDftScfConvergenceReplayRequest,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.result import (
    PwDftScfConvergenceReplayResult,
)


class PwDftScfConvergenceReplayActionizer:
    """Execute one cohesive pure action without choosing or running a runtime."""

    action_identity: ClassVar[str] = PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID
    action_version: ClassVar[str] = PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION

    def action(
        self,
        *,
        request: PwDftScfConvergenceReplayRequest,
    ) -> PwDftScfConvergenceReplayResult:
        """Require evidence to reproduce one extension followed by acceptance."""
        if type(request) is not PwDftScfConvergenceReplayRequest:
            raise TypeError("request must be PwDftScfConvergenceReplayRequest")
        evidence = request.evidence
        assessor = EnergyGridConvergenceAssessor()
        controller = PwDftScfConvergenceController()
        initial_assessment = assessor.assess(
            EnergyGridConvergenceAssessmentRequest(
                observations=evidence.initial_observations,
                policy=evidence.policy,
            )
        )
        initial_decision = controller.decide(initial_assessment)
        if type(initial_decision) is not ExtendPwDftScfConvergence:
            raise PwDftScfConvergenceReplayError(
                "initial observations do not reproduce one grid extension"
            )
        requested = set(initial_decision.coordinates)
        retained = {
            observation.coordinate for observation in evidence.extension_observations
        }
        if requested != retained:
            raise PwDftScfConvergenceReplayError(
                "extension observations do not match the requested coordinates"
            )
        observations = evidence.initial_observations + evidence.extension_observations
        final_assessment = assessor.assess(
            EnergyGridConvergenceAssessmentRequest(
                observations=observations,
                policy=evidence.policy,
            )
        )
        terminal_outcome = controller.decide(final_assessment)
        if type(terminal_outcome) is not PwDftScfConvergenceAccepted:
            raise PwDftScfConvergenceReplayError(
                "complete observations do not reproduce policy acceptance"
            )
        return PwDftScfConvergenceReplayResult(
            evidence_id=evidence.evidence_id,
            integration_id=evidence.integration_id,
            observation_count=len(observations),
            initial_assessment=initial_assessment,
            initial_extension=initial_decision,
            final_assessment=final_assessment,
            terminal_outcome=terminal_outcome,
            source_evidence_reference=evidence.source_evidence_reference,
        )
