"""Exact structure-library resolution and byte verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from projectkoios.physkit.periodic.unit_cell import (
    ConventionalUnitCell,
    PrimitiveUnitCell,
    UnitCell,
    UnitCellJsonCodec,
    UnitCellSerializationError,
)
from projectkoios.simulations.structure.library._records import (
    _DEFAULT_MAXIMUM_RECORD_BYTES,
    _STRUCTURE_ID,
    StructureConflictError,
    StructureIntegrityError,
    StructureLibraryEntry,
    StructureNotFoundError,
    StructureRecord,
    StructureRepresentation,
    StructureResolution,
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
