"""Atomic authentication and parsing of native Wannier90 provider bytes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from projectkoios.integrations.quantumespresso.pw2wannier90.provider import (
    QeWannier90ProviderArtifact,
    QeWannier90ProviderArtifactRole,
)
from projectkoios.integrations.wannier90._parsing import (
    DEFAULT_LIMITS,
    Wannier90ParserLimits,
)
from projectkoios.integrations.wannier90.disentanglement_matrices import (
    Wannier90DisentanglementMatrixData,
    Wannier90DisentanglementMatrixParser,
)
from projectkoios.integrations.wannier90.hamiltonian_blocks import (
    Wannier90HamiltonianBlockData,
    Wannier90HamiltonianBlockParser,
)
from projectkoios.integrations.wannier90.interface_data import (
    Wannier90EigenvalueData,
    Wannier90EigenvalueParser,
)
from projectkoios.integrations.wannier90.nnkp import (
    Wannier90NnkpData,
    Wannier90NnkpParser,
)
from projectkoios.integrations.wannier90.unitary_matrices import (
    Wannier90UnitaryMatrixData,
    Wannier90UnitaryMatrixParser,
)
from projectkoios.physkit.units.quantities import ModelSystemUnit


@dataclass(frozen=True, slots=True, init=False)
class QeWannier90AuthenticatedData[DataT]:
    """Pair parsed data with the exact manifest binding authenticated before parse."""

    artifact: QeWannier90ProviderArtifact
    data: DataT

    def __init__(self) -> None:
        raise TypeError(
            "QeWannier90AuthenticatedData must be created by an authenticated parser"
        )

    @classmethod
    def _from_authenticated(
        cls, artifact: QeWannier90ProviderArtifact, data: DataT
    ) -> Self:
        if type(artifact) is not QeWannier90ProviderArtifact:
            raise TypeError("artifact must be a QeWannier90ProviderArtifact")
        if data is None:
            raise TypeError("data must be a parsed native record")
        instance = object.__new__(cls)
        object.__setattr__(instance, "artifact", artifact)
        object.__setattr__(instance, "data", data)
        return instance


@dataclass(frozen=True, slots=True)
class QeWannier90AuthenticatedParser:
    """Authenticate exact bytes and parse those same bytes without a path race."""

    limits: Wannier90ParserLimits = DEFAULT_LIMITS

    def __post_init__(self) -> None:
        if type(self.limits) is not Wannier90ParserLimits:
            raise TypeError("limits must be Wannier90ParserLimits")

    def parse_nnkp(
        self, artifact: QeWannier90ProviderArtifact, payload: bytes
    ) -> QeWannier90AuthenticatedData[Wannier90NnkpData]:
        self._authenticate(
            artifact, payload, QeWannier90ProviderArtifactRole.neighbor_interface
        )
        return QeWannier90AuthenticatedData._from_authenticated(
            artifact, Wannier90NnkpParser(self.limits).execute(payload)
        )

    def parse_eigenvalues(
        self,
        artifact: QeWannier90ProviderArtifact,
        payload: bytes,
        energy_unit: ModelSystemUnit,
    ) -> QeWannier90AuthenticatedData[Wannier90EigenvalueData]:
        self._authenticate(
            artifact, payload, QeWannier90ProviderArtifactRole.eigenvalues
        )
        return QeWannier90AuthenticatedData._from_authenticated(
            artifact,
            Wannier90EigenvalueParser(self.limits).execute(payload, energy_unit),
        )

    def parse_gauge_matrix(
        self, artifact: QeWannier90ProviderArtifact, payload: bytes
    ) -> QeWannier90AuthenticatedData[Wannier90UnitaryMatrixData]:
        self._authenticate(
            artifact, payload, QeWannier90ProviderArtifactRole.gauge_matrix
        )
        return QeWannier90AuthenticatedData._from_authenticated(
            artifact, Wannier90UnitaryMatrixParser(self.limits).execute(payload)
        )

    def parse_disentanglement_matrix(
        self, artifact: QeWannier90ProviderArtifact, payload: bytes
    ) -> QeWannier90AuthenticatedData[Wannier90DisentanglementMatrixData]:
        self._authenticate(
            artifact,
            payload,
            QeWannier90ProviderArtifactRole.disentanglement_matrix,
        )
        return QeWannier90AuthenticatedData._from_authenticated(
            artifact,
            Wannier90DisentanglementMatrixParser(self.limits).execute(payload),
        )

    def parse_hamiltonian(
        self,
        artifact: QeWannier90ProviderArtifact,
        payload: bytes,
        energy_unit: ModelSystemUnit,
    ) -> QeWannier90AuthenticatedData[Wannier90HamiltonianBlockData]:
        self._authenticate(
            artifact, payload, QeWannier90ProviderArtifactRole.hamiltonian
        )
        return QeWannier90AuthenticatedData._from_authenticated(
            artifact,
            Wannier90HamiltonianBlockParser(self.limits).execute(payload, energy_unit),
        )

    @staticmethod
    def _authenticate(
        artifact: QeWannier90ProviderArtifact,
        payload: bytes,
        expected_role: QeWannier90ProviderArtifactRole,
    ) -> None:
        if type(artifact) is not QeWannier90ProviderArtifact:
            raise TypeError("artifact must be a QeWannier90ProviderArtifact")
        if artifact.role is not expected_role:
            raise ValueError(f"artifact role must be {expected_role.value}")
        artifact.authenticate(payload)


__all__ = [
    "QeWannier90AuthenticatedData",
    "QeWannier90AuthenticatedParser",
]
