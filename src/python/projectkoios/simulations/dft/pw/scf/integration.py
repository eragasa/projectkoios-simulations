"""Nominal calculator-integration contract and source-controlled registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfObservation,
    PwDftScfRequest,
)


@dataclass(frozen=True, slots=True)
class PwDftScfRenderedInput:
    """Represent one deterministic calculator text input file."""

    filename: str
    text: str

    def __post_init__(self) -> None:
        if (
            not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("rendered input filename must be a basename")
        if type(self.text) is not str:
            raise TypeError("rendered input text must be a string")


@dataclass(frozen=True, slots=True)
class PwDftScfInputProjection:
    """Return rendered files and exact unresolved external input names."""

    integration_id: CalculatorIntegrationId
    rendered_inputs: tuple[PwDftScfRenderedInput, ...]
    required_external_inputs: tuple[str, ...]
    qualification: str

    def __post_init__(self) -> None:
        filenames = tuple(item.filename for item in self.rendered_inputs)
        if len(filenames) != len(set(filenames)):
            raise ValueError("rendered input filenames must be unique")
        if any(
            not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            for filename in self.required_external_inputs
        ):
            raise ValueError("required external inputs must be basenames")
        if not self.qualification or self.qualification != self.qualification.strip():
            raise ValueError("qualification must be nonempty and stripped")


class PwDftScfIntegration(ABC):
    """Project and analyze one calculator backend without owning workflow state."""

    __slots__ = ()

    @property
    @abstractmethod
    def integration_id(self) -> CalculatorIntegrationId:
        """Return the stable source-controlled backend identity."""
        raise NotImplementedError

    @abstractmethod
    def project(self, request: PwDftScfRequest) -> PwDftScfInputProjection:
        """Project calculator-neutral intent into deterministic native inputs."""
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
