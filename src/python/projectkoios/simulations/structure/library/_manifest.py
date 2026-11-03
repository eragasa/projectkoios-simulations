"""Bounded strict TOML loading for exact structure libraries."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from projectkoios.simulations.structure.library._records import (
    _DEFAULT_MAXIMUM_MANIFEST_BYTES,
    _DEFAULT_MAXIMUM_RECORD_BYTES,
    DerivedStructureProvenance,
    ObservedStructureProvenance,
    ObservedStructureScope,
    StructureLibraryEntry,
    StructureManifestError,
    StructureProvenanceReference,
    StructureRecord,
    StructureRecordReference,
    StructureRepresentation,
    TransferredStructureProvenance,
)
from projectkoios.simulations.structure.library._repository import StructureLibrary


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
