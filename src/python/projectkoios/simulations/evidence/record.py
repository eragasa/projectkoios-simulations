"""Immutable correlation records for simulation execution evidence."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import ClassVar

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import CalculatorInputSourceReference
from projectkoios.simulations.evidence.artifact import EvidenceArtifactReference

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class EvidenceNormalizationRecord:
    """Identify one source-controlled normalization of native artifacts."""

    operation_id: str
    operation_version: str
    source_artifact_ids: tuple[str, ...]
    output_representation: str
    output_schema_version: int
    output_byte_size: int
    output_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("operation_id", self.operation_id),
            ("operation_version", self.operation_version),
            ("output_representation", self.output_representation),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.source_artifact_ids) is not tuple or not self.source_artifact_ids:
            raise ValueError("source_artifact_ids must be a nonempty tuple")
        if any(
            type(value) is not str or not value or value != value.strip()
            for value in self.source_artifact_ids
        ):
            raise ValueError("source_artifact_ids must be nonempty and stripped")
        if len(self.source_artifact_ids) != len(set(self.source_artifact_ids)):
            raise ValueError("source_artifact_ids must be unique")
        if type(self.output_schema_version) is not int or (
            self.output_schema_version <= 0
        ):
            raise ValueError("output_schema_version must be positive")
        if type(self.output_byte_size) is not int or self.output_byte_size <= 0:
            raise ValueError("output_byte_size must be positive")
        if type(self.output_sha256) is not str or not _SHA256.fullmatch(
            self.output_sha256
        ):
            raise ValueError("output_sha256 must be lowercase hexadecimal")


@dataclass(frozen=True, slots=True)
class SimulationEvidenceRecord:
    """Correlate exact specification, inputs, execution, artifacts, and observation."""

    representation: ClassVar[str] = "projectkoios.simulation-evidence+json"

    evidence_id: str
    schema_version: int
    evaluation_id: str
    task_id: str
    simulation: CalculatorInputSourceReference
    calculator_input_sha256: str
    integration_id: CalculatorIntegrationId
    calculator_name: str
    calculator_version: str
    execution: EvidenceArtifactReference
    native_artifacts: tuple[EvidenceArtifactReference, ...]
    normalization: EvidenceNormalizationRecord
    provider_completed: bool
    calculation_converged: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("evidence_id", self.evidence_id),
            ("evaluation_id", self.evaluation_id),
            ("task_id", self.task_id),
            ("calculator_name", self.calculator_name),
            ("calculator_version", self.calculator_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be one")
        if type(self.simulation) is not CalculatorInputSourceReference:
            raise TypeError("simulation must be CalculatorInputSourceReference")
        if type(self.calculator_input_sha256) is not str or not _SHA256.fullmatch(
            self.calculator_input_sha256
        ):
            raise ValueError("calculator_input_sha256 must be lowercase hexadecimal")
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be CalculatorIntegrationId")
        if type(self.execution) is not EvidenceArtifactReference:
            raise TypeError("execution must be EvidenceArtifactReference")
        if self.execution.role != "execution-record":
            raise ValueError("execution artifact must have role execution-record")
        if type(self.native_artifacts) is not tuple or not self.native_artifacts:
            raise ValueError("native_artifacts must be a nonempty tuple")
        if any(
            type(value) is not EvidenceArtifactReference
            for value in self.native_artifacts
        ):
            raise TypeError(
                "native_artifacts must contain EvidenceArtifactReference values"
            )
        artifact_ids = tuple(value.artifact_id for value in self.native_artifacts)
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("native artifact identities must be unique")
        if type(self.normalization) is not EvidenceNormalizationRecord:
            raise TypeError("normalization must be EvidenceNormalizationRecord")
        if self.normalization.source_artifact_ids != artifact_ids:
            raise ValueError(
                "normalization sources must exactly match native artifact order"
            )
        if (
            type(self.provider_completed) is not bool
            or type(self.calculation_converged) is not bool
        ):
            raise TypeError(
                "provider_completed and calculation_converged must be booleans"
            )

    @property
    def canonical_bytes(self) -> bytes:
        """Return the versioned canonical JSON identity of this evidence record."""
        payload = {
            "calculation_converged": self.calculation_converged,
            "calculator_input_sha256": self.calculator_input_sha256,
            "calculator_name": self.calculator_name,
            "calculator_version": self.calculator_version,
            "evaluation_id": self.evaluation_id,
            "evidence_id": self.evidence_id,
            "execution": {
                "artifact_id": self.execution.artifact_id,
                "byte_size": self.execution.byte_size,
                "media_type": self.execution.media_type,
                "role": self.execution.role,
                "sha256": self.execution.sha256,
            },
            "integration_id": self.integration_id.value,
            "native_artifacts": [
                {
                    "artifact_id": artifact.artifact_id,
                    "byte_size": artifact.byte_size,
                    "media_type": artifact.media_type,
                    "role": artifact.role,
                    "sha256": artifact.sha256,
                }
                for artifact in self.native_artifacts
            ],
            "normalization": {
                "operation_id": self.normalization.operation_id,
                "operation_version": self.normalization.operation_version,
                "output_byte_size": self.normalization.output_byte_size,
                "output_representation": self.normalization.output_representation,
                "output_schema_version": self.normalization.output_schema_version,
                "output_sha256": self.normalization.output_sha256,
                "source_artifact_ids": list(self.normalization.source_artifact_ids),
            },
            "provider_completed": self.provider_completed,
            "representation": self.representation,
            "schema_version": self.schema_version,
            "simulation": {
                "byte_size": self.simulation.byte_size,
                "representation": self.simulation.representation,
                "schema_version": self.simulation.schema_version,
                "sha256": self.simulation.sha256,
                "simulation_id": self.simulation.simulation_id,
            },
            "task_id": self.task_id,
        }
        return (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    @property
    def byte_size(self) -> int:
        """Return the canonical evidence-record byte size."""
        return len(self.canonical_bytes)

    @property
    def sha256(self) -> str:
        """Return the canonical evidence-record SHA-256."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()
