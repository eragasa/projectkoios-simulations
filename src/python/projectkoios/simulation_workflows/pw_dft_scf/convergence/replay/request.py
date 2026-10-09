"""Typed convergence replay request."""

from __future__ import annotations

from dataclasses import dataclass, field

from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.evidence import (
    PwDftScfConvergenceReplayEvidence,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.replay.identity import (
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
)
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObject


@dataclass(frozen=True, slots=True, kw_only=True)
class PwDftScfConvergenceReplayRequest(PwDftScfObject):
    """Bind normalized evidence to one stable, runtime-neutral pure action."""

    evidence: PwDftScfConvergenceReplayEvidence
    action_identity: str = field(
        init=False,
        default=PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_ID,
    )
    action_version: str = field(
        init=False,
        default=PW_DFT_SCF_CONVERGENCE_REPLAY_ACTION_VERSION,
    )

    def __post_init__(self) -> None:
        if type(self.evidence) is not PwDftScfConvergenceReplayEvidence:
            raise TypeError("evidence must be PwDftScfConvergenceReplayEvidence")
