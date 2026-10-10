from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    UnitCell,
    UnitCellJsonCodec,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationRequest,
    PwDftRelaxationSampling,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.observation import (
    PwDftRelaxationNativeArtifact,
    PwDftRelaxationObservation,
)
from projectkoios.simulations.dft.pw.relaxation.result import PwDftRelaxationResult
from projectkoios.simulations.dft.pw.settings import (
    CalculationType,
    PwDftSettings,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from projectkoios.simulations.evidence import (
    EvidenceArtifactReference,
    EvidenceNormalizationRecord,
    SimulationEvidenceRecord,
)
from projectkoios.simulations.structure import (
    StructureRecord,
    StructureRepresentation,
    StructureResolution,
    TransferredStructureProvenance,
)


def silicon_relaxation_request(
    scope: PwDftRelaxationScope,
) -> PwDftRelaxationRequest:
    calculation = {
        PwDftRelaxationScope.ATOMIC_POSITIONS: CalculationType.relax,
        PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL: CalculationType.vc_relax,
    }[scope]
    variable_cell = scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
    return PwDftRelaxationRequest(
        evaluation_id="silicon-relaxation-test",
        simulation=PwDftSimulation(
            unit_cell=UnitCell(
                direct_lattice=DirectLattice3D(
                    a1=np.array([0.5, 0.5, 0.0]),
                    a2=np.array([0.0, 0.5, 0.5]),
                    a3=np.array([0.5, 0.0, 0.5]),
                ),
                lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
                atomic_basis=AtomicBasis(
                    atoms=(
                        _silicon_atom((0.0, 0.0, 0.0)),
                        _silicon_atom((0.25, 0.25, 0.25)),
                    )
                ),
            ),
            settings=PwDftSettings(calculation_type=calculation),
        ),
        scope=scope,
        sampling=PwDftRelaxationSampling(
            kpoint_mesh=(4, 4, 4),
            kpoint_shift=(0, 0, 0),
            wavefunction_cutoff_ev=300.0,
        ),
        convergence=PwDftRelaxationConvergencePolicy(
            maximum_ionic_steps=7,
            total_energy_tolerance_ev=0.001,
            force_tolerance_ev_per_angstrom=0.01,
            target_pressure_kbar=0.0 if variable_cell else None,
            pressure_tolerance_kbar=0.5 if variable_cell else None,
        ),
    )


def completed_relaxation_result(
    scope: PwDftRelaxationScope,
) -> PwDftRelaxationResult:
    request = silicon_relaxation_request(scope)
    integration_id = CalculatorIntegrationId("quantum-espresso")
    input_content = b"relaxation input\n"
    input_record = CalculatorInputRecord(
        input_id="silicon-relaxation-input",
        schema_version=1,
        source=CalculatorInputSourceReference(
            simulation_id="silicon-relaxation",
            representation="projectkoios.pw-dft-relaxation+json",
            schema_version=1,
            byte_size=10,
            sha256="1" * 64,
        ),
        integration_id=integration_id,
        calculator_name="Quantum ESPRESSO",
        calculator_version_constraint="7.4",
        representation="quantum-espresso-pw-input",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename="pw.in",
                media_type="text/plain",
                content=input_content,
                byte_size=len(input_content),
                sha256=hashlib.sha256(input_content).hexdigest(),
            ),
        ),
        external_requirements=(),
        mappings=(),
        preparation_operation="test.render",
        preparation_version="1",
    )
    starting = request.simulation.unit_cell
    first, second = starting.atomic_basis.atoms
    final_cell = UnitCell(
        direct_lattice=starting.direct_lattice,
        lattice_parameter=starting.lattice_parameter,
        atomic_basis=AtomicBasis(
            atoms=(
                Atom(
                    first.symbol,
                    VectorQuantity(np.array((0.01, 0.0, 0.0)), Unitless()),
                ),
                Atom(
                    second.symbol,
                    VectorQuantity(np.array((0.26, 0.25, 0.25)), Unitless()),
                ),
            )
        ),
    )
    return PwDftRelaxationResult(
        evaluation_id=request.evaluation_id,
        task_id="task-1",
        request=request,
        calculator_input=input_record,
        observation=PwDftRelaxationObservation(
            final_unit_cell=final_cell,
            ionic_step_count=6,
            completed=True,
            ionic_converged=True,
            cell_converged=(
                True
                if scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
                else None
            ),
            final_total_energy_ev=-10.0,
            maximum_force_ev_per_angstrom=0.005,
            pressure_kbar=0.1,
            total_magnetization_electrons=0.0,
            program_version="7.4",
            native_artifacts=(
                PwDftRelaxationNativeArtifact(
                    integration_id=integration_id,
                    artifact_id="stdout",
                    sha256="2" * 64,
                    byte_size=100,
                ),
            ),
        ),
    )


def starting_structure_resolution(
    result: PwDftRelaxationResult,
    root: Path,
) -> StructureResolution:
    content = (
        UnitCellJsonCodec()
        .dumps(
            result.request.simulation.unit_cell,
            structure_id="Si.StartingUnitCell",
        )
        .encode()
    )
    sha256 = hashlib.sha256(content).hexdigest()
    path = root / "starting.json"
    path.write_bytes(content)
    record = StructureRecord(
        structure_id="Si.StartingUnitCell",
        representation=StructureRepresentation.unit_cell,
        schema_version=1,
        sha256=sha256,
        byte_size=len(content),
        provenance=TransferredStructureProvenance(
            source="https://example.invalid/structures",
            revision="snapshot-1",
            record_path="source/starting.json",
            source_sha256=sha256,
            result_sha256=sha256,
        ),
    )
    return StructureResolution(
        record=record,
        path=path.resolve(),
        unit_cell=result.request.simulation.unit_cell,
    )


def matching_relaxation_evidence(
    result: PwDftRelaxationResult,
    *,
    calculation_converged: bool = True,
) -> SimulationEvidenceRecord:
    integration_id = result.calculator_input.integration_id
    return SimulationEvidenceRecord(
        evidence_id="silicon-relaxation-evidence",
        schema_version=1,
        evaluation_id=result.evaluation_id,
        task_id=result.task_id,
        simulation=result.calculator_input.source,
        calculator_input_sha256=result.calculator_input.sha256,
        integration_id=integration_id,
        calculator_name=result.calculator_input.calculator_name,
        calculator_version="7.4",
        execution=EvidenceArtifactReference(
            artifact_id="execution",
            role="execution-record",
            media_type="application/json",
            byte_size=50,
            sha256="3" * 64,
        ),
        native_artifacts=(
            EvidenceArtifactReference(
                artifact_id="stdout",
                role="standard-output",
                media_type="text/plain",
                byte_size=100,
                sha256="2" * 64,
            ),
        ),
        normalization=EvidenceNormalizationRecord(
            operation_id="test.normalize-relaxation",
            operation_version="1",
            source_artifact_ids=("stdout",),
            output_representation=result.observation_representation,
            output_schema_version=result.observation_schema_version,
            output_byte_size=result.observation_byte_size,
            output_sha256=result.observation_sha256,
        ),
        provider_completed=True,
        calculation_converged=calculation_converged,
    )


def _silicon_atom(position: tuple[float, float, float]) -> Atom:
    return Atom(
        symbol="Si",
        position_fractional=VectorQuantity(np.array(position), Unitless()),
    )
