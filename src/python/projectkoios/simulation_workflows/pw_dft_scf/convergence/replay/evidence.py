"""Provider-normalized evidence admitted to convergence replay."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulation_workflows.pw_dft_scf.convergence.base import (
    PwDftScfEnergyObservation,
)
from projectkoios.simulation_workflows.pw_dft_scf.convergence.policy import (
    PwDftScfConvergencePolicy,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObject


@dataclass(frozen=True, slots=True)
class PwDftScfConvergenceReplayEvidence(PwDftScfObject):
    """Carry provider-normalized observations without copying native artifacts."""

    evidence_id: str
    integration_id: CalculatorIntegrationId
    policy: PwDftScfConvergencePolicy
    initial_observations: tuple[PwDftScfEnergyObservation, ...]
    extension_observations: tuple[PwDftScfEnergyObservation, ...]
    source_evidence_reference: str

    def __post_init__(self) -> None:
        for label, value in (
            ("evidence_id", self.evidence_id),
            ("source_evidence_reference", self.source_evidence_reference),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if type(self.policy) is not PwDftScfConvergencePolicy:
            raise TypeError("policy must be a PwDftScfConvergencePolicy")
        _validate_observations(self.initial_observations, "initial_observations")
        _validate_observations(self.extension_observations, "extension_observations")
        initial_coordinates = {
            observation.coordinate for observation in self.initial_observations
        }
        extension_coordinates = {
            observation.coordinate for observation in self.extension_observations
        }
        if initial_coordinates & extension_coordinates:
            raise ValueError("initial and extension coordinates must be disjoint")


def _validate_observations(
    observations: tuple[PwDftScfEnergyObservation, ...],
    label: str,
) -> None:
    if type(observations) is not tuple or not observations:
        raise ValueError(f"{label} must be a nonempty tuple")
    if any(type(item) is not PwDftScfEnergyObservation for item in observations):
        raise TypeError(f"{label} must contain PwDftScfEnergyObservation values")
    coordinates = tuple(item.coordinate for item in observations)
    if len(coordinates) != len(set(coordinates)):
        raise ValueError(f"{label} coordinates must be unique")
