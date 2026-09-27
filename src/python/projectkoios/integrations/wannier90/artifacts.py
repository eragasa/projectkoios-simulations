"""Caller-supplied Wannier90 artifact authentication and typed parsing."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from physkit.units.quantities import ModelSystemUnit, PhysicalUnit, Unitless

from ._parsing import BoundedParser
from .hamiltonian_blocks import (
    Wannier90HamiltonianBlockData,
    Wannier90HamiltonianBlockParser,
)
from .interface_data import (
    Wannier90EigenvalueData,
    Wannier90EigenvalueParser,
    Wannier90NeighborOverlapData,
    Wannier90NeighborOverlapParser,
    Wannier90ProjectionData,
    Wannier90ProjectionParser,
)
from .localization import Wannier90LocalizationData, Wannier90LocalizationParser
from .neighbor_lists import Wannier90NeighborListData, Wannier90NeighborListParser
from .unitary_matrices import Wannier90UnitaryMatrixData, Wannier90UnitaryMatrixParser


@dataclass(frozen=True, slots=True)
class Wannier90NativeArtifactIdentity:
    """Identify one native artifact by logical name, byte count, and SHA-256."""

    name: str
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        """Require a basename-like name, nonnegative size, and lowercase digest."""
        if type(self.name) is not str or not self.name:
            raise ValueError("name must be a nonempty built-in str")
        if "/" in self.name or "\\" in self.name or self.name in {".", ".."}:
            raise ValueError("name must not contain a path")
        if type(self.byte_count) is not int or self.byte_count < 0:
            raise ValueError("byte_count must be a nonnegative built-in int")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.sha256)
        ):
            raise ValueError("sha256 must be lowercase SHA-256 hexadecimal")


@dataclass(frozen=True, slots=True)
class Wannier90NativeArtifact:
    """Retain one explicitly named caller-supplied native byte payload."""

    name: str
    payload: bytes

    def __post_init__(self) -> None:
        """Require a basename-like name and immutable bytes; empty files are valid."""
        if type(self.name) is not str or not self.name:
            raise ValueError("name must be a nonempty built-in str")
        if "/" in self.name or "\\" in self.name or self.name in {".", ".."}:
            raise ValueError("name must not contain a path")
        if type(self.payload) is not bytes:
            raise TypeError("payload must be built-in bytes")

    @property
    def identity(self) -> Wannier90NativeArtifactIdentity:
        """Return the byte count and SHA-256 identity derived from the payload."""
        return Wannier90NativeArtifactIdentity(
            self.name,
            len(self.payload),
            hashlib.sha256(self.payload).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class Wannier90NativeArtifactCorrelationResult:
    """Retain one exact expected-to-observed native artifact correlation."""

    expected_identities: tuple[Wannier90NativeArtifactIdentity, ...]
    observed_identities: tuple[Wannier90NativeArtifactIdentity, ...]

    def __post_init__(self) -> None:
        """Require equal, uniquely named, nonempty identity inventories."""
        for name, identities in (
            ("expected_identities", self.expected_identities),
            ("observed_identities", self.observed_identities),
        ):
            if (
                not isinstance(identities, tuple)
                or not identities
                or any(
                    type(identity) is not Wannier90NativeArtifactIdentity
                    for identity in identities
                )
            ):
                raise TypeError(f"{name} must be a nonempty typed tuple")
            artifact_names = tuple(identity.name for identity in identities)
            if len(set(artifact_names)) != len(artifact_names):
                raise ValueError(f"{name} must use unique artifact names")
        if self.expected_identities != self.observed_identities:
            raise ValueError("native artifact identities do not agree exactly")


class Wannier90NativeArtifactCorrelator:
    """Authenticate a complete caller-supplied artifact inventory by size and hash."""

    __slots__ = ()

    def execute(
        self,
        expected_identities: tuple[Wannier90NativeArtifactIdentity, ...],
        artifacts: tuple[Wannier90NativeArtifact, ...],
    ) -> Wannier90NativeArtifactCorrelationResult:
        """Return exact correlation in expected order or reject any inventory defect."""
        if (
            not isinstance(expected_identities, tuple)
            or not expected_identities
            or any(
                type(identity) is not Wannier90NativeArtifactIdentity
                for identity in expected_identities
            )
        ):
            raise TypeError("expected_identities must be a nonempty typed tuple")
        if (
            not isinstance(artifacts, tuple)
            or not artifacts
            or any(
                type(artifact) is not Wannier90NativeArtifact for artifact in artifacts
            )
        ):
            raise TypeError("artifacts must be a nonempty typed tuple")
        expected_names = tuple(identity.name for identity in expected_identities)
        supplied_names = tuple(artifact.name for artifact in artifacts)
        if len(set(expected_names)) != len(expected_names):
            raise ValueError("expected artifact names must be unique")
        if len(set(supplied_names)) != len(supplied_names):
            raise ValueError("supplied artifact names must be unique")
        if set(supplied_names) != set(expected_names):
            raise ValueError("supplied artifact name inventory does not agree")
        by_name = {artifact.name: artifact for artifact in artifacts}
        observed = tuple(by_name[name].identity for name in expected_names)
        return Wannier90NativeArtifactCorrelationResult(expected_identities, observed)


@dataclass(frozen=True, slots=True)
class Wannier90ParsedNativeArtifactSet:
    """Retain parsed records for the seven supported scientific text artifacts."""

    eigenvalues: Wannier90EigenvalueData
    projections: Wannier90ProjectionData
    neighbor_overlaps: Wannier90NeighborOverlapData
    neighbor_list: Wannier90NeighborListData
    localization: Wannier90LocalizationData
    unitary_matrices: Wannier90UnitaryMatrixData
    hamiltonian_blocks: Wannier90HamiltonianBlockData

    def __post_init__(self) -> None:
        """Require every parsed value to use its exact public record type."""
        expected = (
            (self.eigenvalues, Wannier90EigenvalueData),
            (self.projections, Wannier90ProjectionData),
            (self.neighbor_overlaps, Wannier90NeighborOverlapData),
            (self.neighbor_list, Wannier90NeighborListData),
            (self.localization, Wannier90LocalizationData),
            (self.unitary_matrices, Wannier90UnitaryMatrixData),
            (self.hamiltonian_blocks, Wannier90HamiltonianBlockData),
        )
        if any(type(value) is not kind for value, kind in expected):
            raise TypeError("every parsed artifact must use its exact public record")
        kpoint_counts = (
            self.eigenvalues.kpoint_count,
            self.projections.kpoint_count,
            self.neighbor_overlaps.kpoint_count,
            self.neighbor_list.kpoint_count,
            self.unitary_matrices.kpoint_count,
        )
        if len(set(kpoint_counts)) != 1:
            raise ValueError("parsed native artifacts must agree on k-point count")
        band_counts = (
            self.eigenvalues.band_count,
            self.projections.band_count,
            self.neighbor_overlaps.band_count,
        )
        if len(set(band_counts)) != 1:
            raise ValueError("parsed native artifacts must agree on band count")
        wannier_counts = (
            self.localization.wannier_count,
            self.unitary_matrices.wannier_count,
            self.hamiltonian_blocks.wannier_count,
        )
        if len(set(wannier_counts)) != 1:
            raise ValueError("parsed native artifacts must agree on Wannier count")
        if self.neighbor_list.neighbor_count != self.neighbor_overlaps.neighbor_count:
            raise ValueError("nnkp and mmn neighbor counts do not agree")
        if self.neighbor_list.records != self.neighbor_overlaps.normalized_records:
            raise ValueError("nnkp and mmn ordered neighbor inventories do not agree")


class Wannier90NativeArtifactSetParser(BoundedParser):
    """Parse supported scientific files from one authenticated named artifact set."""

    __slots__ = ()

    def execute(
        self,
        seed_name: str,
        artifacts: tuple[Wannier90NativeArtifact, ...],
        energy_unit: ModelSystemUnit,
        length_unit: ModelSystemUnit,
    ) -> Wannier90ParsedNativeArtifactSet:
        """Parse ``eig``, ``amn``, ``mmn``, ``nnkp``, ``wout``, ``u.mat``, and HR."""
        if type(seed_name) is not str or not seed_name:
            raise ValueError("seed_name must be a nonempty built-in str")
        if not isinstance(energy_unit, PhysicalUnit | Unitless):
            raise TypeError("energy_unit must be PhysicalUnit or Unitless")
        if not isinstance(length_unit, PhysicalUnit | Unitless):
            raise TypeError("length_unit must be PhysicalUnit or Unitless")
        if (
            not isinstance(artifacts, tuple)
            or not artifacts
            or any(
                type(artifact) is not Wannier90NativeArtifact for artifact in artifacts
            )
        ):
            raise TypeError("artifacts must be a nonempty typed tuple")
        by_name = {artifact.name: artifact.payload for artifact in artifacts}
        if len(by_name) != len(artifacts):
            raise ValueError("artifact names must be unique")

        def payload(name: str) -> bytes:
            try:
                return by_name[name]
            except KeyError as error:
                raise ValueError(
                    f"required native artifact is absent: {name}"
                ) from error

        return Wannier90ParsedNativeArtifactSet(
            Wannier90EigenvalueParser(self.limits).execute(
                payload(f"{seed_name}.eig"), energy_unit
            ),
            Wannier90ProjectionParser(self.limits).execute(payload(f"{seed_name}.amn")),
            Wannier90NeighborOverlapParser(self.limits).execute(
                payload(f"{seed_name}.mmn")
            ),
            Wannier90NeighborListParser(self.limits).execute(
                payload(f"{seed_name}.nnkp")
            ),
            Wannier90LocalizationParser(self.limits).execute(
                payload(f"{seed_name}.wout"), length_unit
            ),
            Wannier90UnitaryMatrixParser(self.limits).execute(
                payload(f"{seed_name}_u.mat")
            ),
            Wannier90HamiltonianBlockParser(self.limits).execute(
                payload(f"{seed_name}_hr.dat"), energy_unit
            ),
        )
