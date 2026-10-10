"""Pure publication of exact relaxed structures from correlated DFT evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from projectkoios.physkit.periodic.unit_cell import UnitCellJsonCodec
from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.result import PwDftRelaxationResult
from projectkoios.simulations.evidence import SimulationEvidenceRecord
from projectkoios.simulations.structure import (
    ObservedStructureProvenance,
    ObservedStructureScope,
    StructureProvenanceReference,
    StructureRecord,
    StructureRecordReference,
    StructureRepresentation,
    StructureResolution,
)


@dataclass(frozen=True, slots=True)
class PwDftRelaxedStructurePublicationRequest:
    """Request exact publication without granting calculator or storage authority."""

    structure_id: str
    starting_structure: StructureResolution
    relaxation_result: PwDftRelaxationResult
    evidence: SimulationEvidenceRecord

    def __post_init__(self) -> None:
        if type(self.structure_id) is not str or not self.structure_id.strip():
            raise ValueError("structure_id must be nonempty and stripped")
        if type(self.starting_structure) is not StructureResolution:
            raise TypeError("starting_structure must be a StructureResolution")
        if type(self.relaxation_result) is not PwDftRelaxationResult:
            raise TypeError("relaxation_result must be a PwDftRelaxationResult")
        if type(self.evidence) is not SimulationEvidenceRecord:
            raise TypeError("evidence must be a SimulationEvidenceRecord")


@dataclass(frozen=True, slots=True)
class PwDftRelaxedStructurePublication:
    """Return exact canonical bytes and their observed structure record."""

    record: StructureRecord
    content: bytes

    def __post_init__(self) -> None:
        if type(self.record) is not StructureRecord:
            raise TypeError("record must be a StructureRecord")
        if self.record.representation is not StructureRepresentation.unit_cell:
            raise ValueError("published relaxation record must use unit-cell")
        if type(self.record.provenance) is not ObservedStructureProvenance:
            raise TypeError("published relaxation provenance must be observed")
        if type(self.content) is not bytes or not self.content:
            raise ValueError("content must be nonempty bytes")
        if len(self.content) != self.record.byte_size:
            raise ValueError("content byte size must match the structure record")
        if hashlib.sha256(self.content).hexdigest() != self.record.sha256:
            raise ValueError("content SHA-256 must match the structure record")


class PwDftRelaxedStructurePublisher:
    """Publish canonical base-UnitCell bytes from mechanically qualified evidence."""

    __slots__ = ()

    operation_id = "projectkoios.simulations.pw-dft-relaxation.publish-structure"
    operation_version = "1"

    def action(
        self,
        request: PwDftRelaxedStructurePublicationRequest,
    ) -> PwDftRelaxedStructurePublication:
        """Return exact bytes after mechanical correlation; perform no I/O."""
        if type(request) is not PwDftRelaxedStructurePublicationRequest:
            raise TypeError("request must be a PwDftRelaxedStructurePublicationRequest")
        result = request.relaxation_result
        evidence = request.evidence
        source = result.calculator_input.source
        if evidence.evaluation_id != result.evaluation_id:
            raise ValueError("evidence evaluation must match the relaxation result")
        if evidence.task_id != result.task_id:
            raise ValueError("evidence task must match the relaxation result")
        if evidence.simulation != source:
            raise ValueError("evidence simulation must match the prepared-input source")
        if evidence.calculator_input_sha256 != result.calculator_input.sha256:
            raise ValueError("evidence must match the exact prepared-input record")
        if evidence.integration_id != result.calculator_input.integration_id:
            raise ValueError("evidence and prepared-input integrations must match")
        if evidence.calculator_name != result.calculator_input.calculator_name:
            raise ValueError("evidence and prepared-input calculator names must match")
        if not evidence.provider_completed or not evidence.calculation_converged:
            raise ValueError("evidence must report completed converged calculation")
        observation = result.observation
        if not observation.completed or not observation.ionic_converged:
            raise ValueError("relaxation observation must be completed and converged")
        if (
            result.request.scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
            and observation.cell_converged is not True
        ):
            raise ValueError("variable-cell observation must report cell convergence")
        if observation.program_version is not None and (
            observation.program_version != evidence.calculator_version
        ):
            raise ValueError("observation and evidence calculator versions must match")
        observed_artifacts = tuple(
            (artifact.artifact_id, artifact.byte_size, artifact.sha256)
            for artifact in observation.native_artifacts
        )
        evidence_artifacts = tuple(
            (artifact.artifact_id, artifact.byte_size, artifact.sha256)
            for artifact in evidence.native_artifacts
        )
        if observed_artifacts != evidence_artifacts:
            raise ValueError("observation and evidence native artifacts must match")
        normalization = evidence.normalization
        if (
            normalization.output_representation != result.observation_representation
            or normalization.output_schema_version != result.observation_schema_version
            or normalization.output_byte_size != result.observation_byte_size
            or normalization.output_sha256 != result.observation_sha256
        ):
            raise ValueError(
                "evidence normalization must match the exact relaxation observation"
            )

        codec = UnitCellJsonCodec()
        starting_record = request.starting_structure.record
        starting_content = codec.dumps(
            request.starting_structure.unit_cell,
            structure_id=starting_record.structure_id,
        ).encode("utf-8")
        if len(starting_content) != starting_record.byte_size or (
            hashlib.sha256(starting_content).hexdigest() != starting_record.sha256
        ):
            raise ValueError("starting structure bytes must match its exact record")
        simulation_starting_content = codec.dumps(
            result.request.simulation.unit_cell,
            structure_id=starting_record.structure_id,
        ).encode("utf-8")
        if simulation_starting_content != starting_content:
            raise ValueError(
                "relaxation simulation must use the exact starting structure"
            )

        content = codec.dumps(
            observation.final_unit_cell,
            structure_id=request.structure_id,
        ).encode("utf-8")
        result_sha256 = hashlib.sha256(content).hexdigest()
        scope = {
            PwDftRelaxationScope.ATOMIC_POSITIONS: (
                ObservedStructureScope.atomic_positions
            ),
            PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL: (
                ObservedStructureScope.atomic_positions_and_cell
            ),
        }[result.request.scope]
        provenance = ObservedStructureProvenance(
            starting_structure=StructureRecordReference(
                structure_id=starting_record.structure_id,
                representation=starting_record.representation,
                schema_version=starting_record.schema_version,
                byte_size=starting_record.byte_size,
                sha256=starting_record.sha256,
            ),
            relaxation_calculation=StructureProvenanceReference(
                stable_id=source.simulation_id,
                representation=source.representation,
                schema_version=source.schema_version,
                byte_size=source.byte_size,
                sha256=source.sha256,
            ),
            relaxation_evidence=StructureProvenanceReference(
                stable_id=evidence.evidence_id,
                representation=evidence.representation,
                schema_version=evidence.schema_version,
                byte_size=evidence.byte_size,
                sha256=evidence.sha256,
            ),
            scope=scope,
            publication_operation=self.operation_id,
            publication_version=self.operation_version,
            result_sha256=result_sha256,
        )
        record = StructureRecord(
            structure_id=request.structure_id,
            representation=StructureRepresentation.unit_cell,
            schema_version=1,
            sha256=result_sha256,
            byte_size=len(content),
            provenance=provenance,
        )
        return PwDftRelaxedStructurePublication(record=record, content=content)
