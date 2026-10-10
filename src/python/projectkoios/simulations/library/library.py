"""Strict manifest-backed resolution of exact simulation specifications."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.dft.pw.relaxation.specification import (
    PwDftRelaxationSpecification,
)
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.library.codec import (
    SimulationJsonCodec,
    SimulationSerializationError,
    SimulationSpecification,
)
from projectkoios.simulations.library.record import (
    AuthoredSimulationProvenance,
    DerivedSimulationProvenance,
    SimulationRecord,
    SimulationRecordReference,
    SimulationRepresentation,
    TransferredSimulationProvenance,
)
from projectkoios.simulations.structure import (
    StructureConflictError,
    StructureIntegrityError,
    StructureLibrary,
    StructureNotFoundError,
    StructureResolution,
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_DEFAULT_MAXIMUM_MANIFEST_BYTES = 100_000
_DEFAULT_MAXIMUM_RECORD_BYTES = 1_000_000


class SimulationNotFoundError(LookupError):
    """Report an undeclared or unavailable exact simulation specification."""


class SimulationConflictError(ValueError):
    """Report a stable simulation identifier with multiple exact records."""


class SimulationIntegrityError(ValueError):
    """Report bytes that violate a declared simulation record identity."""


class SimulationDependencyError(ValueError):
    """Report an unavailable or mismatched exact scientific dependency."""


class SimulationManifestError(ValueError):
    """Report an invalid or unauthenticated simulation-library manifest."""


@dataclass(frozen=True, slots=True)
class SimulationLibraryEntry:
    """Bind one exact simulation record to a normalized library-relative path."""

    record: SimulationRecord
    relative_path: str

    def __post_init__(self) -> None:
        if type(self.record) is not SimulationRecord:
            raise TypeError("record must be a SimulationRecord")
        if type(self.relative_path) is not str:
            raise TypeError("relative_path must be a string")
        if (
            not self.relative_path
            or self.relative_path != self.relative_path.strip()
            or self.relative_path.startswith("/")
            or "\\" in self.relative_path
            or any(
                component in {"", ".", ".."}
                for component in self.relative_path.split("/")
            )
        ):
            raise ValueError("relative_path must be a normalized relative POSIX path")
        if not self.relative_path.endswith(".json"):
            raise ValueError("relative_path must end with .json")


@dataclass(frozen=True, slots=True)
class SimulationResolution:
    """Return verified specification bytes and exact resolved dependencies."""

    record: SimulationRecord
    path: Path
    specification: SimulationSpecification
    structure: StructureResolution
    pseudopotentials: tuple[PseudopotentialFile, ...]

    def __post_init__(self) -> None:
        if type(self.record) is not SimulationRecord:
            raise TypeError("record must be a SimulationRecord")
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            raise TypeError("path must be an absolute Path")
        expected_type: (
            type[PwDftScfSpecification] | type[PwDftRelaxationSpecification]
        ) = {
            SimulationRepresentation.PW_DFT_SCF: PwDftScfSpecification,
            SimulationRepresentation.PW_DFT_RELAXATION: (PwDftRelaxationSpecification),
        }[self.record.representation]
        if type(self.specification) is not expected_type:
            raise TypeError("specification type must match the record representation")
        if self.specification.simulation_id != self.record.simulation_id:
            raise ValueError("specification simulation_id must match the record")
        if type(self.structure) is not StructureResolution:
            raise TypeError("structure must be a StructureResolution")
        if self.structure.record != self.specification.simulation.structure:
            raise ValueError("resolved structure must match the specification")
        if type(self.pseudopotentials) is not tuple or any(
            type(item) is not PseudopotentialFile for item in self.pseudopotentials
        ):
            raise TypeError(
                "pseudopotentials must contain exact PseudopotentialFile values"
            )
        if self.pseudopotentials != self.specification.simulation.pseudopotentials:
            raise ValueError(
                "resolved pseudopotentials must match the specification order"
            )


@dataclass(frozen=True, slots=True)
class SimulationLibrary:
    """Resolve immutable simulation specifications from one explicit catalog."""

    root: Path
    entries: tuple[SimulationLibraryEntry, ...]
    maximum_record_bytes: int = _DEFAULT_MAXIMUM_RECORD_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path):
            raise TypeError("root must be a Path")
        if not self.root.is_absolute() or ".." in self.root.parts:
            raise ValueError("root must be absolute without parent traversal")
        if self.root.is_symlink() or not self.root.is_dir():
            raise ValueError("root must be an existing nonsymlink directory")
        if type(self.entries) is not tuple:
            raise TypeError("entries must be a tuple")
        if any(type(entry) is not SimulationLibraryEntry for entry in self.entries):
            raise TypeError("entries must contain SimulationLibraryEntry values")
        if type(self.maximum_record_bytes) is not int:
            raise TypeError("maximum_record_bytes must be an integer")
        if self.maximum_record_bytes <= 0:
            raise ValueError("maximum_record_bytes must be positive")
        if any(
            entry.record.byte_size > self.maximum_record_bytes for entry in self.entries
        ):
            raise ValueError("simulation record exceeds maximum_record_bytes")
        records = tuple(entry.record for entry in self.entries)
        if len(records) != len(set(records)):
            raise ValueError("simulation record identities must be unique")
        paths = tuple(entry.relative_path for entry in self.entries)
        if len(paths) != len(set(paths)):
            raise ValueError("simulation relative paths must be unique")

    def records(self, simulation_id: str | None = None) -> tuple[SimulationRecord, ...]:
        """Return records in manifest order, optionally filtered by stable ID."""
        if simulation_id is None:
            return tuple(entry.record for entry in self.entries)
        # SimulationRecord performs the authoritative syntax validation without
        # duplicating its private identifier expression here.
        matches = tuple(
            entry.record
            for entry in self.entries
            if entry.record.simulation_id == simulation_id
        )
        if matches:
            return matches
        if type(simulation_id) is not str:
            raise TypeError("simulation_id must be a string")
        try:
            SimulationRecordReference(
                simulation_id=simulation_id,
                representation=SimulationRepresentation.PW_DFT_SCF,
                schema_version=1,
                byte_size=1,
                sha256="0" * 64,
            )
        except ValueError as error:
            raise ValueError(
                "simulation_id must be a qualified stable identifier"
            ) from error
        return ()

    def require_unique(self, simulation_id: str) -> SimulationRecord:
        """Return one record or fail closed on absence or historical ambiguity."""
        matches = self.records(simulation_id)
        if not matches:
            raise SimulationNotFoundError(
                f"simulation identifier is not declared in the library: {simulation_id}"
            )
        if len(matches) != 1:
            raise SimulationConflictError(
                "simulation identifier resolves to multiple exact records; "
                f"select one SimulationRecord explicitly: {simulation_id}"
            )
        return matches[0]

    def resolve_unique(
        self,
        simulation_id: str,
        *,
        structure_library: StructureLibrary,
    ) -> SimulationResolution:
        """Resolve the sole exact record for one stable identifier."""
        return self.resolve(
            self.require_unique(simulation_id),
            structure_library=structure_library,
        )

    def resolve(
        self,
        required: SimulationRecord,
        *,
        structure_library: StructureLibrary,
    ) -> SimulationResolution:
        """Verify, decode, and resolve exact calculator-neutral dependencies."""
        if type(required) is not SimulationRecord:
            raise TypeError("required must be a SimulationRecord")
        if type(structure_library) is not StructureLibrary:
            raise TypeError("structure_library must be a StructureLibrary")
        matches = tuple(entry for entry in self.entries if entry.record == required)
        if not matches:
            raise SimulationNotFoundError(
                "exact simulation record is not declared in the library: "
                f"{required.simulation_id}/{required.sha256}"
            )
        entry = matches[0]
        if self.root.is_symlink() or not self.root.is_dir():
            raise SimulationNotFoundError(
                f"simulation library root is unavailable: {self.root}"
            )
        root = self.root.resolve(strict=True)
        path = root
        for component in entry.relative_path.split("/"):
            path /= component
            if path.is_symlink():
                raise SimulationNotFoundError(
                    f"declared simulation record is unavailable: {path}"
                )
        if not path.is_file():
            raise SimulationNotFoundError(
                f"declared simulation record is unavailable: {path}"
            )
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise SimulationIntegrityError(
                f"declared simulation record escapes the library root: {path}"
            )
        observed_size = resolved.stat().st_size
        if observed_size > self.maximum_record_bytes:
            raise SimulationIntegrityError(
                "simulation record exceeds maximum_record_bytes: "
                f"{observed_size} > {self.maximum_record_bytes}: {resolved}"
            )
        if observed_size != required.byte_size:
            raise SimulationIntegrityError(
                "simulation byte-size mismatch: "
                f"expected {required.byte_size}, observed {observed_size}: {resolved}"
            )
        with resolved.open("rb") as stream:
            content = stream.read(self.maximum_record_bytes + 1)
        if len(content) > self.maximum_record_bytes:
            raise SimulationIntegrityError(
                "simulation record exceeds maximum_record_bytes while reading: "
                f"{resolved}"
            )
        if len(content) != observed_size:
            raise SimulationIntegrityError(
                f"simulation record changed while being read: {resolved}"
            )
        observed_sha256 = hashlib.sha256(content).hexdigest()
        if observed_sha256 != required.sha256:
            raise SimulationIntegrityError(
                "simulation SHA-256 mismatch: "
                f"expected {required.sha256}, observed {observed_sha256}: {resolved}"
            )
        try:
            specification = SimulationJsonCodec().loads(content)
        except SimulationSerializationError as error:
            raise SimulationIntegrityError(
                f"simulation record failed schema validation: {resolved}"
            ) from error
        expected_type: (
            type[PwDftScfSpecification] | type[PwDftRelaxationSpecification]
        ) = {
            SimulationRepresentation.PW_DFT_SCF: PwDftScfSpecification,
            SimulationRepresentation.PW_DFT_RELAXATION: (PwDftRelaxationSpecification),
        }[required.representation]
        if type(specification) is not expected_type:
            raise SimulationIntegrityError(
                "decoded simulation representation does not match the record: "
                f"{required.representation.value}: {resolved}"
            )
        if specification.simulation_id != required.simulation_id:
            raise SimulationIntegrityError(
                "decoded simulation_id does not match the record: "
                f"{required.simulation_id}: {resolved}"
            )
        try:
            structure = structure_library.resolve(specification.simulation.structure)
        except (
            StructureNotFoundError,
            StructureConflictError,
            StructureIntegrityError,
        ) as error:
            raise SimulationDependencyError(
                "simulation dependency resolution failed for "
                f"{required.simulation_id}: {error}"
            ) from error
        return SimulationResolution(
            record=required,
            path=resolved,
            specification=specification,
            structure=structure,
            pseudopotentials=specification.simulation.pseudopotentials,
        )


@dataclass(frozen=True, slots=True)
class SimulationLibraryManifestLoader:
    """Authenticate and load one bounded strict TOML simulation manifest."""

    manifest_path: Path
    expected_sha256: str
    expected_byte_size: int
    maximum_manifest_bytes: int = _DEFAULT_MAXIMUM_MANIFEST_BYTES
    maximum_record_bytes: int = _DEFAULT_MAXIMUM_RECORD_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.manifest_path, Path):
            raise TypeError("manifest_path must be a Path")
        if not self.manifest_path.is_absolute() or ".." in self.manifest_path.parts:
            raise ValueError("manifest_path must be absolute without parent traversal")
        if self.manifest_path.is_symlink() or not self.manifest_path.is_file():
            raise ValueError("manifest_path must be a regular nonsymlink file")
        if type(self.expected_sha256) is not str or not _SHA256.fullmatch(
            self.expected_sha256
        ):
            raise ValueError("expected_sha256 must be lowercase SHA-256 text")
        if type(self.expected_byte_size) is not int or self.expected_byte_size <= 0:
            raise ValueError("expected_byte_size must be positive")
        for label, value in (
            ("maximum_manifest_bytes", self.maximum_manifest_bytes),
            ("maximum_record_bytes", self.maximum_record_bytes),
        ):
            if type(value) is not int:
                raise TypeError(f"{label} must be an integer")
            if value <= 0:
                raise ValueError(f"{label} must be positive")

    def load(self) -> SimulationLibrary:
        """Authenticate and parse strict schema version one without resolution."""
        if self.manifest_path.is_symlink() or not self.manifest_path.is_file():
            raise SimulationManifestError(
                "simulation manifest is unavailable or is a symlink"
            )
        observed_size = self.manifest_path.stat().st_size
        if observed_size > self.maximum_manifest_bytes:
            raise SimulationManifestError("simulation manifest exceeds the byte limit")
        if observed_size != self.expected_byte_size:
            raise SimulationManifestError("simulation manifest byte-size mismatch")
        with self.manifest_path.open("rb") as stream:
            content = stream.read(self.maximum_manifest_bytes + 1)
        if len(content) > self.maximum_manifest_bytes:
            raise SimulationManifestError("simulation manifest exceeds the byte limit")
        if len(content) != observed_size:
            raise SimulationManifestError("simulation manifest changed while reading")
        if hashlib.sha256(content).hexdigest() != self.expected_sha256:
            raise SimulationManifestError("simulation manifest SHA-256 mismatch")
        try:
            payload = tomllib.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
            raise SimulationManifestError(
                "simulation manifest is not valid UTF-8 TOML"
            ) from error
        if set(payload) != {"schema_version", "records"}:
            raise SimulationManifestError("simulation manifest keys are invalid")
        if type(payload.get("schema_version")) is not int or (
            payload["schema_version"] != 1
        ):
            raise SimulationManifestError("unsupported simulation manifest schema")
        raw_records = payload.get("records")
        if not isinstance(raw_records, list) or not raw_records:
            raise SimulationManifestError("manifest records must be a nonempty array")
        entries: list[SimulationLibraryEntry] = []
        for index, raw_record in enumerate(raw_records):
            entries.append(self._entry(raw_record, index))
        try:
            return SimulationLibrary(
                root=self.manifest_path.parent.resolve(strict=True),
                entries=tuple(entries),
                maximum_record_bytes=self.maximum_record_bytes,
            )
        except (TypeError, ValueError) as error:
            raise SimulationManifestError(
                "manifest records do not form a valid simulation library"
            ) from error

    @staticmethod
    def _entry(raw_value: object, index: int) -> SimulationLibraryEntry:
        label = f"records[{index}]"
        if not isinstance(raw_value, dict):
            raise SimulationManifestError(f"{label} must be a table")
        raw = cast(dict[str, Any], raw_value)
        expected_keys = {
            "simulation_id",
            "representation",
            "schema_version",
            "byte_size",
            "sha256",
            "relative_path",
            "provenance",
        }
        if set(raw) != expected_keys:
            raise SimulationManifestError(f"{label} keys are invalid")
        provenance_value = raw.get("provenance")
        if not isinstance(provenance_value, dict):
            raise SimulationManifestError(f"{label}.provenance must be a table")
        provenance_raw = cast(dict[str, Any], provenance_value)
        kind = provenance_raw.get("kind")
        expected_by_kind = {
            "authored": {"kind", "source", "author", "result_sha256"},
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
        }
        if type(kind) is not str or kind not in expected_by_kind:
            raise SimulationManifestError(f"{label}.provenance.kind is unsupported")
        if set(provenance_raw) != expected_by_kind[kind]:
            raise SimulationManifestError(f"{label}.provenance keys are invalid")
        for key, expected_type in (
            ("simulation_id", str),
            ("representation", str),
            ("schema_version", int),
            ("byte_size", int),
            ("sha256", str),
            ("relative_path", str),
        ):
            if type(raw.get(key)) is not expected_type:
                raise SimulationManifestError(
                    f"{label}.{key} must be a {expected_type.__name__}"
                )
        try:
            provenance: (
                AuthoredSimulationProvenance
                | TransferredSimulationProvenance
                | DerivedSimulationProvenance
            )
            if kind == "authored":
                provenance = AuthoredSimulationProvenance(
                    source=cast(str, provenance_raw["source"]),
                    author=cast(str, provenance_raw["author"]),
                    result_sha256=cast(str, provenance_raw["result_sha256"]),
                )
            elif kind == "transferred":
                provenance = TransferredSimulationProvenance(
                    source=cast(str, provenance_raw["source"]),
                    revision=cast(str, provenance_raw["revision"]),
                    record_path=cast(str, provenance_raw["record_path"]),
                    source_sha256=cast(str, provenance_raw["source_sha256"]),
                    result_sha256=cast(str, provenance_raw["result_sha256"]),
                )
            else:
                parents_value = provenance_raw.get("parents")
                if not isinstance(parents_value, list) or not parents_value:
                    raise SimulationManifestError(
                        f"{label}.provenance.parents must be a nonempty array"
                    )
                parents = tuple(
                    SimulationLibraryManifestLoader._parent(value, label, offset)
                    for offset, value in enumerate(parents_value)
                )
                provenance = DerivedSimulationProvenance(
                    operation_id=cast(str, provenance_raw["operation_id"]),
                    operation_version=cast(str, provenance_raw["operation_version"]),
                    parents=parents,
                    parameters_json=cast(str, provenance_raw["parameters_json"]),
                    parameters_sha256=cast(str, provenance_raw["parameters_sha256"]),
                    result_sha256=cast(str, provenance_raw["result_sha256"]),
                )
            return SimulationLibraryEntry(
                record=SimulationRecord(
                    simulation_id=cast(str, raw["simulation_id"]),
                    representation=SimulationRepresentation(
                        cast(str, raw["representation"])
                    ),
                    schema_version=cast(int, raw["schema_version"]),
                    byte_size=cast(int, raw["byte_size"]),
                    sha256=cast(str, raw["sha256"]),
                    provenance=provenance,
                ),
                relative_path=cast(str, raw["relative_path"]),
            )
        except SimulationManifestError:
            raise
        except (KeyError, TypeError, ValueError) as error:
            raise SimulationManifestError(f"{label} is invalid: {error}") from error

    @staticmethod
    def _parent(raw_value: object, label: str, index: int) -> SimulationRecordReference:
        if not isinstance(raw_value, dict):
            raise SimulationManifestError(
                f"{label}.provenance.parents[{index}] must be a table"
            )
        raw = cast(dict[str, Any], raw_value)
        expected_keys = {
            "simulation_id",
            "representation",
            "schema_version",
            "byte_size",
            "sha256",
        }
        if set(raw) != expected_keys:
            raise SimulationManifestError(
                f"{label}.provenance.parents[{index}] keys are invalid"
            )
        try:
            return SimulationRecordReference(
                simulation_id=cast(str, raw["simulation_id"]),
                representation=SimulationRepresentation(
                    cast(str, raw["representation"])
                ),
                schema_version=cast(int, raw["schema_version"]),
                byte_size=cast(int, raw["byte_size"]),
                sha256=cast(str, raw["sha256"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise SimulationManifestError(
                f"{label}.provenance.parents[{index}] is invalid: {error}"
            ) from error
