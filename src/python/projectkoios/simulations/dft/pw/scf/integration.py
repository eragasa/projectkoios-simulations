"""Nominal calculator-integration contract and source-controlled registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.scf.base import PwDftScfObservation
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from projectkoios.simulations.structure import StructureResolution


class PwDftScfIntegration(ABC):
    """Project and analyze one calculator backend without owning workflow state."""

    __slots__ = ()

    @property
    @abstractmethod
    def integration_id(self) -> CalculatorIntegrationId:
        """Return the stable source-controlled backend identity."""
        raise NotImplementedError

    @abstractmethod
    def project(
        self,
        request: PwDftScfRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Prepare exact, content-addressed calculator inputs."""
        raise NotImplementedError

    @abstractmethod
    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        """Derive a normalized observation from retained native evidence."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class PwDftScfIntegrationRegistry:
    """Resolve only explicitly installed integration instances by stable identity."""

    integrations: tuple[PwDftScfIntegration, ...]

    def __post_init__(self) -> None:
        if not self.integrations:
            raise ValueError("integration registry must not be empty")
        if any(not isinstance(item, PwDftScfIntegration) for item in self.integrations):
            raise TypeError("registry values must inherit from PwDftScfIntegration")
        identities = tuple(item.integration_id for item in self.integrations)
        if len(identities) != len(set(identities)):
            raise ValueError("integration identities must be unique")

    def resolve(self, integration_id: CalculatorIntegrationId) -> PwDftScfIntegration:
        """Return one installed integration or reject the unknown identifier."""
        for integration in self.integrations:
            if integration.integration_id == integration_id:
                return integration
        raise KeyError(f"unknown SCF integration: {integration_id.value}")
