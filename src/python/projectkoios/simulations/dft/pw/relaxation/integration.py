"""Calculator-selectable input integration for structural relaxation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.capabilities import (
    PwDftRelaxationBackendDescription,
    PwDftRelaxationImplementationStatus,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.structure import StructureResolution


class PwDftRelaxationIntegration(ABC):
    """Project common relaxation intent into one backend's native input model."""

    __slots__ = ()

    @property
    @abstractmethod
    def description(self) -> PwDftRelaxationBackendDescription:
        """Return reviewed backend capability and input-model metadata."""
        raise NotImplementedError

    @property
    def integration_id(self) -> CalculatorIntegrationId:
        """Return the stable identity from the reviewed backend description."""
        return self.description.integration_id

    @abstractmethod
    def project(
        self,
        request: PwDftRelaxationRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Project common intent into exact calculator-input identity."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class PwDftRelaxationIntegrationRegistry:
    """Resolve only installed, implemented integrations by stable identity."""

    integrations: tuple[PwDftRelaxationIntegration, ...]

    def __post_init__(self) -> None:
        if not self.integrations:
            raise ValueError("integration registry must not be empty")
        if any(
            not isinstance(item, PwDftRelaxationIntegration)
            for item in self.integrations
        ):
            raise TypeError(
                "registry values must inherit from PwDftRelaxationIntegration"
            )
        selections = tuple(
            (item.integration_id, scope)
            for item in self.integrations
            for scope in item.description.supported_scopes
        )
        if len(selections) != len(set(selections)):
            raise ValueError("integration and scope selections must be unique")
        if any(
            item.description.status
            is not (PwDftRelaxationImplementationStatus.INPUT_PROJECTION_IMPLEMENTED)
            for item in self.integrations
        ):
            raise ValueError("registry may contain only implemented integrations")

    def resolve(
        self,
        integration_id: CalculatorIntegrationId,
        scope: PwDftRelaxationScope,
    ) -> PwDftRelaxationIntegration:
        """Return the integration selected by backend identity and scope."""
        if type(integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if type(scope) is not PwDftRelaxationScope:
            raise TypeError("scope must be a PwDftRelaxationScope")
        for integration in self.integrations:
            if (
                integration.integration_id == integration_id
                and scope in integration.description.supported_scopes
            ):
                return integration
        raise KeyError(
            "unknown relaxation integration and scope: "
            f"{integration_id.value}/{scope.value}"
        )


@dataclass(frozen=True, slots=True)
class PwDftRelaxationInputWrapper:
    """Select one registered backend without interpreting native declarations."""

    registry: PwDftRelaxationIntegrationRegistry

    def __post_init__(self) -> None:
        if type(self.registry) is not PwDftRelaxationIntegrationRegistry:
            raise TypeError("registry must be a PwDftRelaxationIntegrationRegistry")

    def project(
        self,
        *,
        integration_id: CalculatorIntegrationId,
        request: PwDftRelaxationRequest,
        structure: StructureResolution,
    ) -> CalculatorInputRecord:
        """Select the integration and return its exact prepared inputs."""
        # Backend selection uses specification scope; occurrence identity has no
        # authority to alter scientific degrees of freedom.
        return self.registry.resolve(
            integration_id,
            request.specification.scope,
        ).project(request, structure)
