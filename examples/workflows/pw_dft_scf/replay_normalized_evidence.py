"""Compose provider-normalized QE evidence with application replay policy.

The provider owner retains native artifacts and parsing. This example accepts
only the explicit application evidence contract; it neither discovers provider
corpora nor invokes Quantum ESPRESSO.
"""

from __future__ import annotations

from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.action import (
    PwDftScfConvergenceReplayActionizer,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.evidence import (
    PwDftScfConvergenceReplayEvidence,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.request import (
    PwDftScfConvergenceReplayRequest,
)
from projectkoios.simulations.workflows.pw_dft_scf.convergence.replay.result import (
    PwDftScfConvergenceReplayResult,
)


def replay(
    evidence: PwDftScfConvergenceReplayEvidence,
) -> PwDftScfConvergenceReplayResult:
    """Replay one already-normalized evidence declaration deterministically."""
    return PwDftScfConvergenceReplayActionizer().action(
        request=PwDftScfConvergenceReplayRequest(evidence=evidence)
    )
