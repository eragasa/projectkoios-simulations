"""Immutable identities, provenance, entries, and resolutions for structures."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from projectkoios.physkit.periodic.unit_cell import (
    ConventionalUnitCell,
    PrimitiveUnitCell,
    UnitCell,
)

_STRUCTURE_ID = re.compile(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z][A-Za-z0-9-]*)+")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SUPPORTED_STRUCTURE_SCHEMA = 1
_DEFAULT_MAXIMUM_MANIFEST_BYTES = 100_000
_DEFAULT_MAXIMUM_RECORD_BYTES = 1_000_000


class StructureNotFoundError(LookupError):
    """Report an unavailable exact structure record or stable identifier."""


class StructureIntegrityError(ValueError):
    """Report structure bytes that violate a declared exact identity or schema."""


class StructureConflictError(ValueError):
    """Report a stable identifier that does not select one unique record."""


class StructureManifestError(ValueError):
    """Report an invalid structure-library manifest."""


class StructureRepresentation(StrEnum):
    """Classify the unit-cell representation declared by one exact record."""

    primitive = "primitive"
    conventional = "conventional"
    unit_cell = "unit-cell"


@dataclass(frozen=True, slots=True)
class StructureRecordReference:
    """Reference one exact parent structure without embedding its catalog."""

    structure_id: str
    representation: StructureRepresentation
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if type(self.structure_id) is not str or not _STRUCTURE_ID.fullmatch(
            self.structure_id
        ):
            raise ValueError("structure_id must be a qualified stable identifier")
        if type(self.representation) is not StructureRepresentation:
            raise TypeError("representation must be a StructureRepresentation")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be one")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("SHA-256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class StructureProvenanceReference:
    """Reference exact simulation or evidence content without importing its owner."""

    stable_id: str
    representation: str
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("stable_id", self.stable_id),
            ("representation", self.representation),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.schema_version) is not int or self.schema_version <= 0:
            raise ValueError("schema_version must be positive")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be positive")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("SHA-256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class TransferredStructureProvenance:
    """Identify bytes retained from one immutable source record or snapshot."""

    source: str
    revision: str
    record_path: str
    source_sha256: str
    result_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("provenance source", self.source),
            ("provenance revision", self.revision),
            ("provenance record_path", self.record_path),
        ):
            if type(value) is not str:
                raise TypeError(f"{label} must be a string")
            if not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        parts = self.record_path.split("/")
        if (
            self.record_path.startswith("/")
            or "\\" in self.record_path
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise ValueError(
                "provenance record_path must be a normalized relative POSIX path"
            )
        for label, value in (
            ("source_sha256", self.source_sha256),
            ("result_sha256", self.result_sha256),
        ):
            if type(value) is not str or not _SHA256.fullmatch(value):
                raise ValueError(f"{label} must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class DerivedStructureProvenance:
    """Identify a deterministic structure derivation and its exact parents."""

    operation_id: str
    operation_version: str
    parents: tuple[StructureRecordReference, ...]
    parameters_json: str
    parameters_sha256: str
    result_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("operation_id", self.operation_id),
            ("operation_version", self.operation_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.parents) is not tuple or not self.parents:
            raise ValueError("parents must be a nonempty tuple")
        if any(type(value) is not StructureRecordReference for value in self.parents):
            raise TypeError("parents must contain StructureRecordReference values")
        if len(self.parents) != len(set(self.parents)):
            raise ValueError("parents must be unique")
        if type(self.parameters_json) is not str or not self.parameters_json:
            raise ValueError("parameters_json must be nonempty")
        try:
            parameters = json.loads(self.parameters_json)
        except json.JSONDecodeError as error:
            raise ValueError("parameters_json must be valid JSON") from error
        try:
            canonical = (
                json.dumps(
                    parameters,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
        except ValueError as error:
            raise ValueError("parameters_json values must be finite") from error
        if self.parameters_json != canonical:
            raise ValueError("parameters_json must be canonical JSON with one newline")
        if self.parameters_sha256 != hashlib.sha256(canonical.encode()).hexdigest():
            raise ValueError("parameters_sha256 must match parameters_json")
        if type(self.result_sha256) is not str or not _SHA256.fullmatch(
            self.result_sha256
        ):
            raise ValueError("result_sha256 must be lowercase hexadecimal")


class ObservedStructureScope(StrEnum):
    """Classify geometry degrees of freedom represented by observed provenance."""

    atomic_positions = "atomic-positions"
    atomic_positions_and_cell = "atomic-positions-and-cell"


@dataclass(frozen=True, slots=True)
class ObservedStructureProvenance:
    """Correlate a published structure with relaxation specification and evidence."""

    starting_structure: StructureRecordReference
    relaxation_calculation: StructureProvenanceReference
    relaxation_evidence: StructureProvenanceReference
    scope: ObservedStructureScope
    publication_operation: str
    publication_version: str
    result_sha256: str

    def __post_init__(self) -> None:
        if type(self.starting_structure) is not StructureRecordReference:
            raise TypeError("starting_structure must be a StructureRecordReference")
        if type(self.relaxation_calculation) is not StructureProvenanceReference:
            raise TypeError(
                "relaxation_calculation must be a StructureProvenanceReference"
            )
        if type(self.relaxation_evidence) is not StructureProvenanceReference:
            raise TypeError(
                "relaxation_evidence must be a StructureProvenanceReference"
            )
        if type(self.scope) is not ObservedStructureScope:
            raise TypeError("scope must be an ObservedStructureScope")
        for label, value in (
            ("publication_operation", self.publication_operation),
            ("publication_version", self.publication_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.result_sha256) is not str or not _SHA256.fullmatch(
            self.result_sha256
        ):
            raise ValueError("result_sha256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class StructureRecord:
    """Bind stable structure and schema identities to exact transferred bytes."""

    structure_id: str
    representation: StructureRepresentation
    schema_version: int
    sha256: str
    byte_size: int
    provenance: (
        TransferredStructureProvenance
        | DerivedStructureProvenance
        | ObservedStructureProvenance
    )

    def __post_init__(self) -> None:
        if type(self.structure_id) is not str or not _STRUCTURE_ID.fullmatch(
            self.structure_id
        ):
            raise ValueError("structure_id must be a qualified stable identifier")
        if type(self.representation) is not StructureRepresentation:
            raise TypeError(
                "structure representation must be a StructureRepresentation"
            )
        if type(self.schema_version) is not int:
            raise TypeError("structure schema_version must be an integer")
        if self.schema_version != _SUPPORTED_STRUCTURE_SCHEMA:
            raise ValueError("structure schema_version must be 1")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("structure SHA-256 must be lowercase hexadecimal")
        if type(self.byte_size) is not int:
            raise TypeError("structure byte_size must be an integer")
        if self.byte_size <= 0:
            raise ValueError("structure byte_size must be positive")
        if type(self.provenance) not in {
            TransferredStructureProvenance,
            DerivedStructureProvenance,
            ObservedStructureProvenance,
        }:
            raise TypeError("structure provenance must be a supported exact variant")
        if self.sha256 != self.provenance.result_sha256:
            raise ValueError(
                "structure SHA-256 must equal the provenance result SHA-256"
            )


@dataclass(frozen=True, slots=True)
class StructureLibraryEntry:
    """Bind one exact structure record to a relative library path."""

    record: StructureRecord
    relative_path: str

    def __post_init__(self) -> None:
        if type(self.record) is not StructureRecord:
            raise TypeError("library entry record must be a StructureRecord")
        if type(self.relative_path) is not str:
            raise TypeError("library entry relative_path must be a string")
        if not self.relative_path or self.relative_path != self.relative_path.strip():
            raise ValueError(
                "library entry relative_path must be nonempty and stripped"
            )
        parts = self.relative_path.split("/")
        if (
            self.relative_path.startswith("/")
            or "\\" in self.relative_path
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise ValueError(
                "library entry relative_path must be a normalized relative POSIX path"
            )
        if not self.relative_path.endswith(".json"):
            raise ValueError("library entry relative_path must end with .json")


@dataclass(frozen=True, slots=True)
class StructureResolution:
    """Return the exact record, verified path, and decoded neutral unit cell."""

    record: StructureRecord
    path: Path
    unit_cell: UnitCell

    def __post_init__(self) -> None:
        if type(self.record) is not StructureRecord:
            raise TypeError("resolution record must be a StructureRecord")
        if not isinstance(self.path, Path):
            raise TypeError("resolution path must be a Path")
        if not isinstance(self.unit_cell, UnitCell):
            raise TypeError("resolution unit_cell must inherit from UnitCell")
        expected_type: type[UnitCell] = {
            StructureRepresentation.primitive: PrimitiveUnitCell,
            StructureRepresentation.conventional: ConventionalUnitCell,
            StructureRepresentation.unit_cell: UnitCell,
        }[self.record.representation]
        if type(self.unit_cell) is not expected_type:
            raise TypeError(
                "resolution unit_cell exact type must match the record representation"
            )
