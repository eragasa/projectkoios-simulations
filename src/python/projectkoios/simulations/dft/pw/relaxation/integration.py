"""Calculator-selectable input integration for structural relaxation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationRequest,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.capabilities import (
    PwDftRelaxationBackendDescription,
    PwDftRelaxationImplementationStatus,
)


@dataclass(frozen=True, slots=True)
class PwDftRelaxationRenderedInput:
    """Represent one deterministic calculator-native input file."""

    filename: str
    text: str

    def __post_init__(self) -> None:
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("filename must be a basename")
        if type(self.text) is not str:
            raise TypeError("text must be a string")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationInputProjection:
    """Return native files and unresolved external input names."""

    integration_id: CalculatorIntegrationId
    rendered_inputs: tuple[PwDftRelaxationRenderedInput, ...]
    required_external_inputs: tuple[str, ...]
    qualification: str

    def __post_init__(self) -> None:
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if not self.rendered_inputs or any(
            type(item) is not PwDftRelaxationRenderedInput
            for item in self.rendered_inputs
        ):
            raise TypeError(
                "rendered_inputs must contain PwDftRelaxationRenderedInput values"
            )
        filenames = tuple(item.filename for item in self.rendered_inputs)
        if len(filenames) != len(set(filenames)):
            raise ValueError("rendered input filenames must be unique")
        if type(self.required_external_inputs) is not tuple or any(
            type(filename) is not str
            or not filename
            or filename in {".", ".."}
            or "/" in filename
            or "\\" in filename
            for filename in self.required_external_inputs
        ):
            raise ValueError("required_external_inputs must contain basenames")
        if (
            type(self.qualification) is not str
            or not self.qualification
            or self.qualification != self.qualification.strip()
        ):
            raise ValueError("qualification must be nonempty and stripped")


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
        self, request: PwDftRelaxationRequest
    ) -> PwDftRelaxationInputProjection:
        """Project common intent into deterministic calculator-native inputs."""
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
    ) -> PwDftRelaxationInputProjection:
        """Select the integration and return its native input projection."""
        return self.registry.resolve(integration_id, request.scope).project(request)
