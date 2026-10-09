"""Typed convergence replay result."""

from __future__ import annotations

from dataclasses import dataclass, field

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObject
from projectkoios.simulations.workflows.pw_dft_scf.convergence.base import (
    PwDftScfConvergenceAssessment,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.controller import (
    ExtendPwDftScfConvergence,
    PwDftScfConvergenceAccepted,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.identity import (
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
)


@dataclass(frozen=True, slots=True)
class PwDftScfConvergenceReplayResult(PwDftScfObject):
    """Record the result of the stable convergence-replay action."""

    evidence_id: str
    integration_id: CalculatorIntegrationId
    observation_count: int
    initial_assessment: PwDftScfConvergenceAssessment
    initial_extension: ExtendPwDftScfConvergence
    final_assessment: PwDftScfConvergenceAssessment
    terminal_outcome: PwDftScfConvergenceAccepted
    source_evidence_reference: str
    action_identity: str = field(
        init=False,
        default=PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    )
    action_version: str = field(
        init=False,
        default=PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
    )

    def __post_init__(self) -> None:
        if type(self.evidence_id) is not str or not self.evidence_id:
            raise ValueError("evidence_id must be nonempty")
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if type(self.observation_count) is not int or self.observation_count <= 0:
            raise ValueError("observation_count must be positive")
        if type(self.initial_assessment) is not PwDftScfConvergenceAssessment:
            raise TypeError(
                "initial_assessment must be a PwDftScfConvergenceAssessment"
            )
        if type(self.initial_extension) is not ExtendPwDftScfConvergence:
            raise TypeError("initial_extension must be ExtendPwDftScfConvergence")
        if type(self.final_assessment) is not PwDftScfConvergenceAssessment:
            raise TypeError("final_assessment must be a PwDftScfConvergenceAssessment")
        if type(self.terminal_outcome) is not PwDftScfConvergenceAccepted:
            raise TypeError("terminal_outcome must be PwDftScfConvergenceAccepted")
        if self.terminal_outcome.assessment != self.final_assessment:
            raise ValueError("terminal outcome must retain the final assessment")
        if (
            type(self.source_evidence_reference) is not str
            or not self.source_evidence_reference
            or self.source_evidence_reference != self.source_evidence_reference.strip()
        ):
            raise ValueError("source_evidence_reference must be nonempty and stripped")
