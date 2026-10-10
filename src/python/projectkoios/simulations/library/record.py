"""Exact simulation-record identities and closed provenance contracts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SIMULATION_ID = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z][A-Za-z0-9-]*)+")
_OPERATION_ID = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)+(?:-[a-z0-9]+)*")
_VERSION = re.compile(r"[1-9][0-9]*(?:\.[0-9]+)*")


class SimulationRepresentation(StrEnum):
    """Name every canonical simulation specification representation."""

    PW_DFT_SCF = "pw-dft-scf"
    PW_DFT_RELAXATION = "pw-dft-relaxation"


@dataclass(frozen=True, slots=True)
class SimulationRecordReference:
    """Identify exact canonical specification bytes without provenance expansion."""

    simulation_id: str
    representation: SimulationRepresentation
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        _validate_record_identity(
            self.simulation_id,
            self.representation,
            self.schema_version,
            self.byte_size,
            self.sha256,
        )


@dataclass(frozen=True, slots=True)
class AuthoredSimulationProvenance:
    """Identify a reviewed locally authored canonical specification."""

    source: str
    author: str
    result_sha256: str

    def __post_init__(self) -> None:
        _nonempty(self.source, "source")
        _nonempty(self.author, "author")
        _sha256(self.result_sha256, "result_sha256")


@dataclass(frozen=True, slots=True)
class TransferredSimulationProvenance:
    """Retain exact upstream and local identities for transferred specifications."""

    source: str
    revision: str
    record_path: str
    source_sha256: str
    result_sha256: str

    def __post_init__(self) -> None:
        _nonempty(self.source, "source")
        _nonempty(self.revision, "revision")
        _relative_path(self.record_path)
        _sha256(self.source_sha256, "source_sha256")
        _sha256(self.result_sha256, "result_sha256")


@dataclass(frozen=True, slots=True)
class DerivedSimulationProvenance:
    """Identify deterministic recipe derivation from exact parent specifications."""

    operation_id: str
    operation_version: str
    parents: tuple[SimulationRecordReference, ...]
    parameters_json: str
    parameters_sha256: str
    result_sha256: str

    def __post_init__(self) -> None:
        if type(self.operation_id) is not str or not _OPERATION_ID.fullmatch(
            self.operation_id
        ):
            raise ValueError("operation_id must be a qualified stable identifier")
        if type(self.operation_version) is not str or not _VERSION.fullmatch(
            self.operation_version
        ):
            raise ValueError("operation_version must be numeric dot-separated text")
        if type(self.parents) is not tuple or not self.parents:
            raise ValueError("parents must be a nonempty tuple")
        if any(type(value) is not SimulationRecordReference for value in self.parents):
            raise TypeError("parents must contain SimulationRecordReference values")
        if len(self.parents) != len(set(self.parents)):
            raise ValueError("parents must be unique")

        # Recipe parameters are retained as their own canonical document. This
        # lets auditors distinguish a scientific edit from provenance metadata.
        _canonical_json(self.parameters_json, "parameters_json")
        _sha256(self.parameters_sha256, "parameters_sha256")
        if (
            hashlib.sha256(self.parameters_json.encode("utf-8")).hexdigest()
            != self.parameters_sha256
        ):
            raise ValueError("parameters_sha256 must match parameters_json")
        _sha256(self.result_sha256, "result_sha256")


SimulationProvenance = (
    AuthoredSimulationProvenance
    | TransferredSimulationProvenance
    | DerivedSimulationProvenance
)


@dataclass(frozen=True, slots=True)
class SimulationRecord:
    """Catalog one immutable canonical simulation specification."""

    simulation_id: str
    representation: SimulationRepresentation
    schema_version: int
    byte_size: int
    sha256: str
    provenance: SimulationProvenance

    def __post_init__(self) -> None:
        _validate_record_identity(
            self.simulation_id,
            self.representation,
            self.schema_version,
            self.byte_size,
            self.sha256,
        )
        if type(self.provenance) not in {
            AuthoredSimulationProvenance,
            TransferredSimulationProvenance,
            DerivedSimulationProvenance,
        }:
            raise TypeError(
                "provenance must use the closed simulation provenance union"
            )
        # The record digest always identifies the local canonical bytes; source
        # digests may differ after an explicitly documented transfer operation.
        if self.sha256 != self.provenance.result_sha256:
            raise ValueError("record sha256 must equal provenance result_sha256")

    @property
    def reference(self) -> SimulationRecordReference:
        """Return the exact dependency identity without provenance expansion."""
        return SimulationRecordReference(
            simulation_id=self.simulation_id,
            representation=self.representation,
            schema_version=self.schema_version,
            byte_size=self.byte_size,
            sha256=self.sha256,
        )


def canonical_derivation_parameters(parameters: dict[str, object]) -> tuple[str, str]:
    """Return finite canonical derivation JSON and its SHA-256."""
    if type(parameters) is not dict:
        raise TypeError("parameters must be a dictionary")
    try:
        text = (
            json.dumps(
                parameters,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )
    except (TypeError, ValueError) as error:
        raise ValueError("parameters must contain finite JSON values") from error
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_record_identity(
    simulation_id: str,
    representation: SimulationRepresentation,
    schema_version: int,
    byte_size: int,
    sha256: str,
) -> None:
    if type(simulation_id) is not str or not _SIMULATION_ID.fullmatch(simulation_id):
        raise ValueError("simulation_id must be a qualified stable identifier")
    if type(representation) is not SimulationRepresentation:
        raise TypeError("representation must be a SimulationRepresentation")
    if type(schema_version) is not int or schema_version != 1:
        raise ValueError("schema_version must be one")
    if type(byte_size) is not int or byte_size <= 0:
        raise ValueError("byte_size must be positive")
    _sha256(sha256, "sha256")


def _nonempty(value: str, label: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be nonempty and stripped")


def _sha256(value: str, label: str) -> None:
    if type(value) is not str or not _SHA256.fullmatch(value):
        raise ValueError(f"{label} must be lowercase SHA-256 text")


def _relative_path(value: str) -> None:
    _nonempty(value, "record_path")
    if value.startswith("/") or "\\" in value:
        raise ValueError("record_path must be a portable relative path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("record_path must be normalized")


def _canonical_json(value: str, label: str) -> None:
    _nonempty(value, label)
    try:
        parsed = json.loads(value, parse_constant=_reject_nonfinite)
        canonical = (
            json.dumps(
                parsed,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} must be finite canonical JSON") from error
    if canonical != value:
        raise ValueError(f"{label} must be finite canonical JSON")


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON constant is forbidden: {value}")
