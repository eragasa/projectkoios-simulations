"""Calculator-neutral exact structure library and manifest contracts."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from projectkoios.physkit.periodic.unit_cell import (
    ConventionalUnitCell,
    PrimitiveUnitCell,
    UnitCell,
    UnitCellJsonCodec,
    UnitCellSerializationError,
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


@dataclass(frozen=True, slots=True)
class StructureLibrary:
    """Resolve manifest-declared structures by exact identity and provenance."""

    root: Path
    entries: tuple[StructureLibraryEntry, ...]
    maximum_record_bytes: int = _DEFAULT_MAXIMUM_RECORD_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("structure library root must be a Path")
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError(
                "structure library root must be absolute without parent traversal"
            )
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError(
                "structure library root must be an existing nonsymlink directory"
            )
        if type(self.entries) is not tuple:
            raise TypeError("structure library entries must be a tuple")
        if any(type(entry) is not StructureLibraryEntry for entry in self.entries):
            raise TypeError(
                "structure library entries must contain StructureLibraryEntry values"
            )
        if type(self.maximum_record_bytes) is not int:
            raise TypeError("maximum_record_bytes must be an integer")
        if self.maximum_record_bytes <= 0:
            raise ValueError("maximum_record_bytes must be positive")
        if any(
            entry.record.byte_size > self.maximum_record_bytes for entry in self.entries
        ):
            raise ValueError("structure record byte_size exceeds maximum_record_bytes")
        records = tuple(entry.record for entry in self.entries)
        if len(records) != len(set(records)):
            raise ValueError("structure library record identities must be unique")
        paths = tuple(entry.relative_path for entry in self.entries)
        if len(paths) != len(set(paths)):
            raise ValueError("structure library relative paths must be unique")
        provenances = tuple(entry.record.provenance for entry in self.entries)
        if len(provenances) != len(set(provenances)):
            raise ValueError("structure library provenances must be unique")

    def records(self, structure_id: str | None = None) -> tuple[StructureRecord, ...]:
        """Return declared records in manifest order, optionally filtered by ID."""
        if structure_id is None:
            return tuple(entry.record for entry in self.entries)
        if type(structure_id) is not str or not _STRUCTURE_ID.fullmatch(structure_id):
            raise ValueError("structure_id must be a qualified stable identifier")
        return tuple(
            entry.record
            for entry in self.entries
            if entry.record.structure_id == structure_id
        )

    def require_unique(self, structure_id: str) -> StructureRecord:
        """Return the sole record for an ID or fail closed on absence or ambiguity."""
        matches = self.records(structure_id)
        if not matches:
            raise StructureNotFoundError(
                f"structure identifier is not declared in the library: {structure_id}"
            )
        if len(matches) != 1:
            raise StructureConflictError(
                "structure identifier resolves to multiple exact records; "
                f"select one StructureRecord explicitly: {structure_id}"
            )
        return matches[0]

    def resolve_unique(self, structure_id: str) -> StructureResolution:
        """Resolve the sole exact record declared for one stable identifier."""
        return self.resolve(self.require_unique(structure_id))

    def resolve(self, required: StructureRecord) -> StructureResolution:
        """Verify and decode one explicitly selected exact structure record."""
        if type(required) is not StructureRecord:
            raise TypeError("required must be a StructureRecord")
        matches = tuple(entry for entry in self.entries if entry.record == required)
        if not matches:
            raise StructureNotFoundError(
                "exact structure record is not declared in the library: "
                f"{required.structure_id}/{required.sha256}"
            )
        entry = matches[0]
        root = self.root.resolve(strict=True)
        path = root
        for component in entry.relative_path.split("/"):
            path /= component
            if path.is_symlink():
                raise StructureNotFoundError(
                    f"declared structure record is unavailable: {path}"
                )
        if not path.is_file():
            raise StructureNotFoundError(
                f"declared structure record is unavailable: {path}"
            )
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise StructureIntegrityError(
                f"declared structure record escapes the library root: {path}"
            )
        content = resolved.read_bytes()
        if len(content) > self.maximum_record_bytes:
            raise StructureIntegrityError(
                "structure record exceeds maximum_record_bytes: "
                f"{len(content)} > {self.maximum_record_bytes}: {resolved}"
            )
        if len(content) != required.byte_size:
            raise StructureIntegrityError(
                "structure byte-size mismatch: "
                f"expected {required.byte_size}, observed {len(content)}: {resolved}"
            )
        observed_sha256 = hashlib.sha256(content).hexdigest()
        if observed_sha256 != required.sha256:
            raise StructureIntegrityError(
                "structure SHA-256 mismatch: "
                f"expected {required.sha256}, observed {observed_sha256}: {resolved}"
            )
        try:
            text = content.decode("utf-8")
            unit_cell = UnitCellJsonCodec().loads(
                text,
                expected_structure_id=required.structure_id,
            )
        except (UnicodeDecodeError, UnitCellSerializationError) as error:
            raise StructureIntegrityError(
                f"structure record failed schema validation: {resolved}"
            ) from error
        expected_type: type[UnitCell] = {
            StructureRepresentation.primitive: PrimitiveUnitCell,
            StructureRepresentation.conventional: ConventionalUnitCell,
            StructureRepresentation.unit_cell: UnitCell,
        }[required.representation]
        if type(unit_cell) is not expected_type:
            raise StructureIntegrityError(
                "decoded unit-cell representation does not match the record: "
                f"{required.representation.value}: {resolved}"
            )
        return StructureResolution(
            record=required,
            path=resolved,
            unit_cell=unit_cell,
        )


@dataclass(frozen=True, slots=True)
class StructureLibraryManifestLoader:
    """Load one bounded strict TOML manifest into an exact structure library."""

    manifest_path: Path
    maximum_manifest_bytes: int = _DEFAULT_MAXIMUM_MANIFEST_BYTES
    maximum_record_bytes: int = _DEFAULT_MAXIMUM_RECORD_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_path, Path):
            raise TypeError("manifest_path must be a Path")
        if not self.manifest_path.is_absolute() or ".." in self.manifest_path.parts:
            raise ValueError("manifest_path must be absolute without parent traversal")
        if self.manifest_path.is_symlink() or not self.manifest_path.is_file():
            raise ValueError("manifest_path must be a regular nonsymlink file")
        for label, value in (
            ("maximum_manifest_bytes", self.maximum_manifest_bytes),
            ("maximum_record_bytes", self.maximum_record_bytes),
        ):
            if type(value) is not int:
                raise TypeError(f"{label} must be an integer")
            if value <= 0:
                raise ValueError(f"{label} must be positive")

    def load(self) -> StructureLibrary:
        """Parse strict schema version one without selecting a scientific record."""
        content = self.manifest_path.read_bytes()
        if len(content) > self.maximum_manifest_bytes:
            raise StructureManifestError("structure manifest exceeds the byte limit")
        try:
            payload = tomllib.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise StructureManifestError(
                "structure manifest is not valid UTF-8 TOML"
            ) from error
        expected_manifest_keys = {"schema_version", "records"}
        observed_manifest_keys = set(payload)
        if observed_manifest_keys != expected_manifest_keys:
            raise StructureManifestError(
                "manifest keys are invalid; "
                f"missing={sorted(expected_manifest_keys - observed_manifest_keys)}, "
                f"unexpected={sorted(observed_manifest_keys - expected_manifest_keys)}"
            )
        if payload.get("schema_version") != 1:
            raise StructureManifestError("unsupported structure manifest schema")
        raw_records = payload.get("records")
        if not isinstance(raw_records, list) or not raw_records:
            raise StructureManifestError("manifest records must be a nonempty array")

        entries: list[StructureLibraryEntry] = []
        expected_record_keys = {
            "structure_id",
            "representation",
            "schema_version",
            "sha256",
            "byte_size",
            "relative_path",
            "provenance",
        }
        reference_keys = {
            "structure_id",
            "representation",
            "schema_version",
            "byte_size",
            "sha256",
        }
        associated_reference_keys = {
            "stable_id",
            "representation",
            "schema_version",
            "byte_size",
            "sha256",
        }
        provenance_keys_by_kind = {
            "transferred": {
                "kind",
                "source",
                "revision",
                "record_path",
                "source_sha256",
                "result_sha256",
            },
            "derived": {
                "kind",
                "operation_id",
                "operation_version",
                "parents",
                "parameters_json",
                "parameters_sha256",
                "result_sha256",
            },
            "observed": {
                "kind",
                "starting_structure",
                "relaxation_calculation",
                "relaxation_evidence",
                "scope",
                "publication_operation",
                "publication_version",
                "result_sha256",
            },
        }
        for index, value in enumerate(raw_records):
            record_path = f"records[{index}]"
            if not isinstance(value, dict):
                raise StructureManifestError(f"{record_path} must be a table")
            observed_record_keys = set(value)
            if observed_record_keys != expected_record_keys:
                raise StructureManifestError(
                    f"{record_path} keys are invalid; "
                    f"missing={sorted(expected_record_keys - observed_record_keys)}, "
                    f"unexpected={sorted(observed_record_keys - expected_record_keys)}"
                )
            raw_provenance = value.get("provenance")
            if not isinstance(raw_provenance, dict):
                raise StructureManifestError(
                    f"{record_path}.provenance must be a table"
                )
            provenance_kind = raw_provenance.get("kind")
            if type(provenance_kind) is not str or (
                provenance_kind not in provenance_keys_by_kind
            ):
                raise StructureManifestError(
                    f"{record_path}.provenance.kind is unsupported"
                )
            expected_provenance_keys = provenance_keys_by_kind[provenance_kind]
            observed_provenance_keys = set(raw_provenance)
            if observed_provenance_keys != expected_provenance_keys:
                raise StructureManifestError(
                    f"{record_path}.provenance keys are invalid; "
                    "missing="
                    f"{sorted(expected_provenance_keys - observed_provenance_keys)}, "
                    "unexpected="
                    f"{sorted(observed_provenance_keys - expected_provenance_keys)}"
                )
            for mapping, key, expected_type in (
                (value, "structure_id", str),
                (value, "representation", str),
                (value, "schema_version", int),
                (value, "sha256", str),
                (value, "byte_size", int),
                (value, "relative_path", str),
            ):
                if type(mapping.get(key)) is not expected_type:
                    raise StructureManifestError(
                        f"{record_path}.{key} must be a {expected_type.__name__}"
                    )
            try:
                representation = StructureRepresentation(
                    cast(str, value["representation"])
                )
                provenance: (
                    TransferredStructureProvenance
                    | DerivedStructureProvenance
                    | ObservedStructureProvenance
                )
                if provenance_kind == "transferred":
                    provenance = TransferredStructureProvenance(
                        source=cast(str, raw_provenance["source"]),
                        revision=cast(str, raw_provenance["revision"]),
                        record_path=cast(str, raw_provenance["record_path"]),
                        source_sha256=cast(str, raw_provenance["source_sha256"]),
                        result_sha256=cast(str, raw_provenance["result_sha256"]),
                    )
                elif provenance_kind == "derived":
                    raw_parents = raw_provenance.get("parents")
                    if not isinstance(raw_parents, list) or not raw_parents:
                        raise StructureManifestError(
                            f"{record_path}.provenance.parents must be a nonempty array"
                        )
                    parents: list[StructureRecordReference] = []
                    for parent_index, raw_parent in enumerate(raw_parents):
                        if not isinstance(raw_parent, dict) or (
                            set(raw_parent) != reference_keys
                        ):
                            raise StructureManifestError(
                                f"{record_path}.provenance.parents[{parent_index}] "
                                "has invalid keys"
                            )
                        parents.append(
                            StructureRecordReference(
                                structure_id=cast(str, raw_parent["structure_id"]),
                                representation=StructureRepresentation(
                                    cast(str, raw_parent["representation"])
                                ),
                                schema_version=cast(int, raw_parent["schema_version"]),
                                byte_size=cast(int, raw_parent["byte_size"]),
                                sha256=cast(str, raw_parent["sha256"]),
                            )
                        )
                    provenance = DerivedStructureProvenance(
                        operation_id=cast(str, raw_provenance["operation_id"]),
                        operation_version=cast(
                            str, raw_provenance["operation_version"]
                        ),
                        parents=tuple(parents),
                        parameters_json=cast(str, raw_provenance["parameters_json"]),
                        parameters_sha256=cast(
                            str, raw_provenance["parameters_sha256"]
                        ),
                        result_sha256=cast(str, raw_provenance["result_sha256"]),
                    )
                else:
                    raw_starting = raw_provenance.get("starting_structure")
                    raw_calculation = raw_provenance.get("relaxation_calculation")
                    raw_evidence = raw_provenance.get("relaxation_evidence")
                    if not isinstance(raw_starting, dict) or (
                        set(raw_starting) != reference_keys
                    ):
                        raise StructureManifestError(
                            f"{record_path}.provenance.starting_structure has "
                            "invalid keys"
                        )
                    for label, associated in (
                        ("relaxation_calculation", raw_calculation),
                        ("relaxation_evidence", raw_evidence),
                    ):
                        if not isinstance(associated, dict) or (
                            set(associated) != associated_reference_keys
                        ):
                            raise StructureManifestError(
                                f"{record_path}.provenance.{label} has invalid keys"
                            )
                    assert isinstance(raw_calculation, dict)
                    assert isinstance(raw_evidence, dict)
                    provenance = ObservedStructureProvenance(
                        starting_structure=StructureRecordReference(
                            structure_id=cast(str, raw_starting["structure_id"]),
                            representation=StructureRepresentation(
                                cast(str, raw_starting["representation"])
                            ),
                            schema_version=cast(int, raw_starting["schema_version"]),
                            byte_size=cast(int, raw_starting["byte_size"]),
                            sha256=cast(str, raw_starting["sha256"]),
                        ),
                        relaxation_calculation=StructureProvenanceReference(
                            stable_id=cast(str, raw_calculation["stable_id"]),
                            representation=cast(str, raw_calculation["representation"]),
                            schema_version=cast(int, raw_calculation["schema_version"]),
                            byte_size=cast(int, raw_calculation["byte_size"]),
                            sha256=cast(str, raw_calculation["sha256"]),
                        ),
                        relaxation_evidence=StructureProvenanceReference(
                            stable_id=cast(str, raw_evidence["stable_id"]),
                            representation=cast(str, raw_evidence["representation"]),
                            schema_version=cast(int, raw_evidence["schema_version"]),
                            byte_size=cast(int, raw_evidence["byte_size"]),
                            sha256=cast(str, raw_evidence["sha256"]),
                        ),
                        scope=ObservedStructureScope(
                            cast(str, raw_provenance["scope"])
                        ),
                        publication_operation=cast(
                            str, raw_provenance["publication_operation"]
                        ),
                        publication_version=cast(
                            str, raw_provenance["publication_version"]
                        ),
                        result_sha256=cast(str, raw_provenance["result_sha256"]),
                    )
                entries.append(
                    StructureLibraryEntry(
                        record=StructureRecord(
                            structure_id=cast(str, value["structure_id"]),
                            representation=representation,
                            schema_version=cast(int, value["schema_version"]),
                            sha256=cast(str, value["sha256"]),
                            byte_size=cast(int, value["byte_size"]),
                            provenance=provenance,
                        ),
                        relative_path=cast(str, value["relative_path"]),
                    )
                )
            except StructureManifestError:
                raise
            except (KeyError, TypeError, ValueError) as error:
                raise StructureManifestError(
                    f"{record_path} is invalid: {error}"
                ) from error
        try:
            return StructureLibrary(
                root=self.manifest_path.parent.resolve(strict=True),
                entries=tuple(entries),
                maximum_record_bytes=self.maximum_record_bytes,
            )
        except (TypeError, ValueError) as error:
            raise StructureManifestError(
                "manifest records do not form a valid structure library"
            ) from error
