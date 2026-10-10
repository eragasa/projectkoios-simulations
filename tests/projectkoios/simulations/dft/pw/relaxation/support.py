from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import Unitless, VectorQuantity
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorInputArtifact,
    CalculatorInputRecord,
)
from projectkoios.simulations.dft.electronic import (
    DftOccupationMethod,
    DftOccupationPolicy,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftCellRelaxationMode,
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationDegreesOfFreedom,
    PwDftRelaxationInitialization,
    PwDftRelaxationScope,
)
from projectkoios.simulations.dft.pw.relaxation.observation import (
    PwDftRelaxationNativeArtifact,
    PwDftRelaxationObservation,
)
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.dft.pw.relaxation.result import PwDftRelaxationResult
from projectkoios.simulations.dft.pw.relaxation.specification import (
    PwDftRelaxationSpecification,
)
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from projectkoios.simulations.evidence import (
    EvidenceArtifactReference,
    EvidenceNormalizationRecord,
    SimulationEvidenceRecord,
)
from projectkoios.simulations.library import simulation_source_reference
from projectkoios.simulations.structure import StructureResolution
from tests.projectkoios.simulations.dft.pw.support import (
    pbe_exchange_correlation,
    silicon_structure_resolution,
)


def silicon_relaxation_request(
    scope: PwDftRelaxationScope,
) -> PwDftRelaxationRequest:
    variable_cell = scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
    structure = silicon_structure_resolution()
    return PwDftRelaxationRequest(
        evaluation_id="silicon-relaxation-test",
        specification=PwDftRelaxationSpecification(
            simulation_id=(
                "Si.PrimitiveUnitCell.QE.VcRelax"
                if variable_cell
                else "Si.PrimitiveUnitCell.QE.Relax"
            ),
            simulation=PwDftSimulation(
                structure=structure.record,
                exchange_correlation=pbe_exchange_correlation(),
            ),
            kpoint_sampling=PwDftKPointSamplingPolicy(
                mesh=(4, 4, 4),
                shift=(0, 0, 0),
                use_spatial_symmetry=True,
                use_time_reversal=True,
            ),
            wavefunction_cutoff_ev=300.0,
            occupation=DftOccupationPolicy(method=DftOccupationMethod.FIXED),
            electronic_convergence=PwDftElectronicConvergencePolicy(
                energy_tolerance_ev=1.3605693122994e-7,
                maximum_electronic_iterations=100,
            ),
            initialization=(
                PwDftRelaxationInitialization.FROM_EXACT_STARTING_STRUCTURE
            ),
            degrees_of_freedom=PwDftRelaxationDegreesOfFreedom(
                relax_atomic_positions=True,
                cell_mode=(
                    PwDftCellRelaxationMode.UNRESTRICTED_VECTORS
                    if variable_cell
                    else PwDftCellRelaxationMode.FIXED
                ),
            ),
            ionic_convergence=PwDftRelaxationConvergencePolicy(
                maximum_ionic_steps=7,
                total_energy_tolerance_ev=0.001,
                force_tolerance_ev_per_angstrom=0.01,
                target_pressure_kbar=0.0 if variable_cell else None,
                pressure_tolerance_kbar=0.5 if variable_cell else None,
            ),
        ),
    )


def completed_relaxation_result(
    scope: PwDftRelaxationScope,
) -> PwDftRelaxationResult:
    request = silicon_relaxation_request(scope)
    variable_cell = scope is PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL
    starting_structure = silicon_structure_resolution()
    integration_id = CalculatorIntegrationId("quantum-espresso")
    input_content = b"relaxation input\n"
    input_record = CalculatorInputRecord(
        input_id="silicon-relaxation-input",
        schema_version=1,
        source=simulation_source_reference(request.specification),
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
    starting = starting_structure.unit_cell
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
        starting_structure=starting_structure,
        calculator_input=input_record,
        observation=PwDftRelaxationObservation(
            final_unit_cell=final_cell,
            ionic_step_count=6,
            completed=True,
            ionic_converged=True,
            cell_converged=True if variable_cell else None,
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
    # The exact starting structure is now part of result correlation. The root
    # argument is retained only by the test helper's callers and grants no I/O.
    del root
    return result.starting_structure


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
            byte_size=20,
            sha256="3" * 64,
        ),
        provider_completed=True,
        calculation_converged=calculation_converged,
        native_artifacts=(
            EvidenceArtifactReference(
                artifact_id="stdout",
                role="stdout",
                media_type="text/plain",
                byte_size=100,
                sha256="2" * 64,
            ),
        ),
        normalization=EvidenceNormalizationRecord(
            operation_id="test.normalize",
            operation_version="1",
            source_artifact_ids=("stdout",),
            output_representation=result.observation_representation,
            output_schema_version=result.observation_schema_version,
            output_byte_size=result.observation_byte_size,
            output_sha256=result.observation_sha256,
        ),
    )
