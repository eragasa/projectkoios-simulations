"""Exact prepared calculator-input values and records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from projectkoios.simulations.calculator import CalculatorIntegrationId

__all__ = (
    "CalculatorExternalInputRequirement",
    "CalculatorInputArtifact",
    "CalculatorInputMapping",
    "CalculatorInputRecord",
    "CalculatorInputSourceReference",
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_ROLE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class CalculatorInputArtifact:
    """Retain one exact rendered calculator input file.

    Parameters
    ----------
    role
        Lowercase semantic role slug unique within the prepared input.
    filename
        Portable destination basename.
    media_type
        Nonempty media type describing the retained bytes.
    content
        Exact immutable rendered file bytes.
    byte_size
        Positive byte count equal to ``len(content)``.
    sha256
        Lowercase SHA-256 digest of ``content``.
    """

    role: str
    filename: str
    media_type: str
    content: bytes
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        if type(self.role) is not str or not _ROLE.fullmatch(self.role):
            raise ValueError("calculator input artifact role must be a lowercase slug")
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("calculator input artifact filename must be a basename")
        if (
            type(self.media_type) is not str
            or not self.media_type
            or self.media_type != self.media_type.strip()
        ):
            raise ValueError("calculator input artifact media_type must be nonempty")
        if type(self.content) is not bytes:
            raise TypeError("calculator input artifact content must be bytes")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("calculator input artifact byte_size must be positive")
        if self.byte_size != len(self.content):
            raise ValueError("calculator input artifact byte_size must match content")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError(
                "calculator input artifact SHA-256 must be lowercase hexadecimal"
            )
        if hashlib.sha256(self.content).hexdigest() != self.sha256:
            raise ValueError("calculator input artifact SHA-256 must match content")


@dataclass(frozen=True, slots=True)
class CalculatorExternalInputRequirement:
    """Require one exact external input without resolving a local path.

    Parameters
    ----------
    role
        Lowercase semantic role slug.
    stable_id
        Stable scientific or repository identity for the required file.
    filename
        Required deployment basename.
    format
        Nonempty source-format description.
    byte_size
        Positive expected file size in bytes.
    sha256
        Lowercase expected SHA-256 digest.
    provenance
        Nonempty provenance statement for the selected requirement.
    element_symbol
        Optional chemical element symbol when the file is element-specific.
    """

    role: str
    stable_id: str
    filename: str
    format: str
    byte_size: int
    sha256: str
    provenance: str
    element_symbol: str | None = None

    def __post_init__(self) -> None:
        if type(self.role) is not str or not _ROLE.fullmatch(self.role):
            raise ValueError("external input role must be a lowercase slug")
        for label, value in (
            ("stable_id", self.stable_id),
            ("format", self.format),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(
                    f"external input {label} must be nonempty and stripped"
                )
        if (
            type(self.filename) is not str
            or not self.filename
            or self.filename in {".", ".."}
            or "/" in self.filename
            or "\\" in self.filename
        ):
            raise ValueError("external input filename must be a basename")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("external input byte_size must be positive")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("external input SHA-256 must be lowercase hexadecimal")
        if (
            type(self.provenance) is not str
            or not self.provenance
            or self.provenance != self.provenance.strip()
        ):
            raise ValueError("external input provenance must be nonempty and stripped")
        if self.element_symbol is not None and (
            type(self.element_symbol) is not str
            or not re.fullmatch(r"[A-Z][a-z]?", self.element_symbol)
        ):
            raise ValueError("element_symbol must be an element symbol or None")


@dataclass(frozen=True, slots=True)
class CalculatorInputSourceReference:
    """Identify the exact simulation specification translated into inputs.

    Parameters
    ----------
    simulation_id
        Stable identity of the source simulation specification.
    representation
        Explicit source representation identifier.
    schema_version
        Positive source representation schema version.
    byte_size
        Positive byte count of the canonical source representation.
    sha256
        Lowercase SHA-256 digest of the canonical source representation.
    """

    simulation_id: str
    representation: str
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("simulation_id", self.simulation_id),
            ("representation", self.representation),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.schema_version) is not int or self.schema_version <= 0:
            raise ValueError("schema_version must be a positive integer")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("byte_size must be a positive integer")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("SHA-256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class CalculatorInputMapping:
    """Correlate neutral intent with exact calculator-native encoding.

    Parameters
    ----------
    neutral_field
        Stable neutral-model field name.
    neutral_value
        Exact represented neutral value.
    native_fields
        Nonempty ordered calculator-native destination fields.
    native_values
        Ordered native values corresponding one-to-one with ``native_fields``.
    effect
        Lowercase slug classifying the mapping effect.
    qualification
        Nonempty statement qualifying the mapping convention.
    """

    neutral_field: str
    neutral_value: str
    native_fields: tuple[str, ...]
    native_values: tuple[str, ...]
    effect: str
    qualification: str

    def __post_init__(self) -> None:
        if (
            type(self.neutral_field) is not str
            or not self.neutral_field
            or self.neutral_field != self.neutral_field.strip()
        ):
            raise ValueError("neutral_field must be nonempty and stripped")
        if type(self.neutral_value) is not str or not self.neutral_value:
            raise ValueError("neutral_value must be nonempty")
        if type(self.native_fields) is not tuple or not self.native_fields:
            raise ValueError("native_fields must be a nonempty tuple")
        if type(self.native_values) is not tuple or len(self.native_values) != len(
            self.native_fields
        ):
            raise ValueError(
                "native_values must correspond one-to-one to native_fields"
            )
        if any(
            type(value) is not str or not value or value != value.strip()
            for value in (*self.native_fields, *self.native_values)
        ):
            raise ValueError("native fields and values must be nonempty and stripped")
        if type(self.effect) is not str or not _SLUG.fullmatch(self.effect):
            raise ValueError("mapping effect must be a lowercase slug")
        if (
            type(self.qualification) is not str
            or not self.qualification
            or self.qualification != self.qualification.strip()
        ):
            raise ValueError("mapping qualification must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class CalculatorInputRecord:
    """Retain exact rendered inputs without granting calculator authority.

    Parameters
    ----------
    input_id
        Stable identity of the complete prepared-input record.
    schema_version
        Positive prepared-record schema version.
    source
        Exact source simulation reference.
    integration_id
        Stable outward calculator-integration identity.
    calculator_name
        Nonempty calculator name.
    calculator_version_constraint
        Declared compatible calculator-version range or constraint.
    representation
        Explicit calculator-native input representation.
    artifacts
        Nonempty exact rendered input artifacts.
    external_requirements
        Exact external file requirements resolved only at deployment.
    mappings
        Neutral-to-native mapping observations.
    preparation_operation
        Stable identity of the preparation operation.
    preparation_version
        Exact preparation implementation version.

    Notes
    -----
    The record contains no executable path or execution-authorization field.
    """

    input_id: str
    schema_version: int
    source: CalculatorInputSourceReference
    integration_id: CalculatorIntegrationId
    calculator_name: str
    calculator_version_constraint: str
    representation: str
    artifacts: tuple[CalculatorInputArtifact, ...]
    external_requirements: tuple[CalculatorExternalInputRequirement, ...]
    mappings: tuple[CalculatorInputMapping, ...]
    preparation_operation: str
    preparation_version: str

    def __post_init__(self) -> None:
        for label, value in (
            ("input_id", self.input_id),
            ("calculator_name", self.calculator_name),
            ("calculator_version_constraint", self.calculator_version_constraint),
            ("representation", self.representation),
            ("preparation_operation", self.preparation_operation),
            ("preparation_version", self.preparation_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.schema_version) is not int or self.schema_version <= 0:
            raise ValueError("schema_version must be a positive integer")
        if type(self.source) is not CalculatorInputSourceReference:
            raise TypeError("source must be a CalculatorInputSourceReference")
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if type(self.artifacts) is not tuple or not self.artifacts:
            raise ValueError("artifacts must be a nonempty tuple")
        if any(type(value) is not CalculatorInputArtifact for value in self.artifacts):
            raise TypeError("artifacts must contain CalculatorInputArtifact values")
        if len({value.filename for value in self.artifacts}) != len(self.artifacts):
            raise ValueError("calculator input artifact filenames must be unique")
        if len({value.role for value in self.artifacts}) != len(self.artifacts):
            raise ValueError("calculator input artifact roles must be unique")
        if type(self.external_requirements) is not tuple or any(
            type(value) is not CalculatorExternalInputRequirement
            for value in self.external_requirements
        ):
            raise TypeError(
                "external_requirements must contain "
                "CalculatorExternalInputRequirement values"
            )
        external_identities = tuple(
            (value.role, value.stable_id) for value in self.external_requirements
        )
        if len(external_identities) != len(set(external_identities)):
            raise ValueError("external input requirement identities must be unique")
        external_filenames = tuple(
            value.filename for value in self.external_requirements
        )
        if len(external_filenames) != len(set(external_filenames)):
            raise ValueError("external input requirement filenames must be unique")
        if type(self.mappings) is not tuple or any(
            type(value) is not CalculatorInputMapping for value in self.mappings
        ):
            raise TypeError("mappings must contain CalculatorInputMapping values")
        if len({value.neutral_field for value in self.mappings}) != len(self.mappings):
            raise ValueError("neutral input mapping fields must be unique")

    @property
    def canonical_bytes(self) -> bytes:
        """Return the versioned canonical JSON identity of this input record."""
        payload = {
            "artifacts": [
                {
                    "byte_size": artifact.byte_size,
                    "filename": artifact.filename,
                    "media_type": artifact.media_type,
                    "role": artifact.role,
                    "sha256": artifact.sha256,
                }
                for artifact in self.artifacts
            ],
            "calculator_name": self.calculator_name,
            "calculator_version_constraint": self.calculator_version_constraint,
            "external_requirements": [
                {
                    "byte_size": requirement.byte_size,
                    "filename": requirement.filename,
                    "element_symbol": requirement.element_symbol,
                    "format": requirement.format,
                    "provenance": requirement.provenance,
                    "role": requirement.role,
                    "sha256": requirement.sha256,
                    "stable_id": requirement.stable_id,
                }
                for requirement in self.external_requirements
            ],
            "input_id": self.input_id,
            "integration_id": self.integration_id.value,
            "mappings": [
                {
                    "effect": mapping.effect,
                    "native_fields": list(mapping.native_fields),
                    "native_values": list(mapping.native_values),
                    "neutral_field": mapping.neutral_field,
                    "neutral_value": mapping.neutral_value,
                    "qualification": mapping.qualification,
                }
                for mapping in self.mappings
            ],
            "preparation_operation": self.preparation_operation,
            "preparation_version": self.preparation_version,
            "representation": self.representation,
            "schema_version": self.schema_version,
            "source": {
                "byte_size": self.source.byte_size,
                "representation": self.source.representation,
                "schema_version": self.source.schema_version,
                "sha256": self.source.sha256,
                "simulation_id": self.source.simulation_id,
            },
        }
        return (
            json.dumps(
                payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
            )
            + "\n"
        ).encode("utf-8")

    @property
    def byte_size(self) -> int:
        """Return the canonical record byte size."""
        return len(self.canonical_bytes)

    @property
    def sha256(self) -> str:
        """Return the canonical record SHA-256."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()
