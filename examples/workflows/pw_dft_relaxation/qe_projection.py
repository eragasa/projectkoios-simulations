"""Compose a relaxation campaign without granting calculator execution.

This compact example replaces the misleading historical
`execute_relaxation.py` path. Callers provide public neutral contracts and an
installed projection integration, and receive a non-authorizing handoff.
"""

from __future__ import annotations

from projectkoios.simulations.dft.pw.relaxation.integration import (
    PwDftRelaxationIntegrationRegistry,
)
from projectkoios.simulations.workflows.pw_dft_relaxation.composition import (
    PwDftRelaxationCampaign,
    PwDftRelaxationComposer,
    PwDftRelaxationCompositionResult,
)


def compose(
    campaign: PwDftRelaxationCampaign,
    registry: PwDftRelaxationIntegrationRegistry,
) -> PwDftRelaxationCompositionResult:
    """Project inputs and return an external-authority-required handoff."""
    return PwDftRelaxationComposer(registry).compose(campaign)
