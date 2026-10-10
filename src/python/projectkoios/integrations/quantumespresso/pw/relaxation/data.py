"""Unified immutable data facade for QE structural relaxation output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from projectkoios.integrations.quantumespresso.outputs.pw_stderr import (
    QePwStderrFileResult,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFileResult,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwCapturedStreamData,
    QePwDataSources,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (
    QeQexsdFinalStructure,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.trajectory import (
    QeRelaxationTrajectory,
    QeRelaxationTrajectoryStep,
)
from projectkoios.physkit.mechanics.stress import (
    StressSignConvention,
    StressTensor,
)
from projectkoios.physkit.periodic.unit_cell import UnitCell
from projectkoios.physkit.units import (
    MODEL_SYSTEM_UNIT_CONVERTER,
    MatrixQuantity,
    PhysicalUnit,
    ScalarQuantity,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.observation import (
    PwDftRelaxationNativeArtifact,
    PwDftRelaxationObservation,
)
from projectkoios.simulations.execution import CalculatorExecutionRecord
from projectkoios.simulations.structure import StructureResolution

_QE_INTEGRATION_ID = CalculatorIntegrationId("quantum-espresso")

QeQexsdRelaxationData = QeQexsdData


@dataclass(frozen=True, slots=True)
class QeRelaxationConsistency:
    """Report mechanical agreement without deciding scientific acceptance."""

    stdout_job_completed: bool
    qexsd_present: bool
    qexsd_exit_status: int | None
    terminal_status_matches: bool | None
    atom_count_matches: bool | None

    def __post_init__(self) -> None:
        if type(self.stdout_job_completed) is not bool:
            raise TypeError("stdout_job_completed must be a boolean")
        if type(self.qexsd_present) is not bool:
            raise TypeError("qexsd_present must be a boolean")
        if self.qexsd_present is not (self.qexsd_exit_status is not None):
            raise ValueError("qexsd presence and exit status must agree")
        if self.qexsd_exit_status is not None and (
            type(self.qexsd_exit_status) is not int
            or not 0 <= self.qexsd_exit_status <= 255
        ):
            raise ValueError("qexsd_exit_status must be in 0..255 or None")
        for label, value in (
            ("terminal_status_matches", self.terminal_status_matches),
            ("atom_count_matches", self.atom_count_matches),
        ):
            if value is not None and type(value) is not bool:
                raise TypeError(f"{label} must be a boolean or None")
        if not self.qexsd_present and (
            self.terminal_status_matches is not None
            or self.atom_count_matches is not None
        ):
            raise ValueError("QEXSD comparisons require QEXSD data")

    @classmethod
    def compare(
        cls,
        stdout: QePwStdoutFileResult,
        qexsd: QeQexsdRelaxationData | None,
    ) -> QeRelaxationConsistency:
        """Compare only unambiguous native identity and terminal observations."""
        if type(stdout) is not QePwStdoutFileResult:
            raise TypeError("stdout must be QePwStdoutFileResult")
        if qexsd is None:
            return cls(
                stdout_job_completed=stdout.job_completed,
                qexsd_present=False,
                qexsd_exit_status=None,
                terminal_status_matches=None,
                atom_count_matches=None,
            )
        if type(qexsd) is not QeQexsdRelaxationData:
            raise TypeError("qexsd must be QeQexsdRelaxationData or None")
        document_atom_count = getattr(qexsd.document, "declared_atom_count", None)
        atom_count_matches = (
            stdout.atom_count == document_atom_count
            if stdout.atom_count is not None and type(document_atom_count) is int
            else None
        )
        return cls(
            stdout_job_completed=stdout.job_completed,
            qexsd_present=True,
            qexsd_exit_status=qexsd.final_structure.exit_status,
            terminal_status_matches=(
                stdout.job_completed == (qexsd.final_structure.exit_status == 0)
            ),
            atom_count_matches=atom_count_matches,
        )


@dataclass(frozen=True, slots=True)
class QeRelaxData:
    """Facade all retained native and interpreted QE relaxation data."""

    calculation: Literal["relax", "vc-relax"]
    sources: QePwDataSources
    stdout_trajectory: QeRelaxationTrajectory
    consistency: QeRelaxationConsistency

    def __post_init__(self) -> None:
        if self.calculation not in {"relax", "vc-relax"}:
            raise ValueError("calculation must be relax or vc-relax")
        if type(self.sources) is not QePwDataSources:
            raise TypeError("sources must be QePwDataSources")
        if type(self.stdout_trajectory) is not QeRelaxationTrajectory:
            raise TypeError("stdout_trajectory must be QeRelaxationTrajectory")
        if self.stdout_trajectory.calculation != self.calculation:
            raise ValueError("trajectory calculation disagrees with facade calculation")
        if self.stdout_trajectory.summary != self.streams.stdout:
            raise ValueError("trajectory summary must equal the captured stdout result")
        if self.sources.qexsd is not None and (
            type(self.sources.qexsd) is not QeQexsdRelaxationData
        ):
            raise TypeError("qexsd must be QeQexsdRelaxationData or None")
        if type(self.consistency) is not QeRelaxationConsistency:
            raise TypeError("consistency must be QeRelaxationConsistency")
        expected_consistency = QeRelaxationConsistency.compare(
            self.streams.stdout,
            self.qexsd,
        )
        if self.consistency != expected_consistency:
            raise ValueError("consistency does not describe the retained sources")
        if self.sources.execution is not None and (
            type(self.sources.execution) is not CalculatorExecutionRecord
        ):
            raise TypeError(
                "relaxation execution must be CalculatorExecutionRecord or None"
            )

    @property
    def streams(self) -> QePwCapturedStreamData:
        return self.sources.streams

    @property
    def qexsd(self) -> QeQexsdRelaxationData | None:
        return self.sources.qexsd

    @property
    def execution(self) -> CalculatorExecutionRecord | None:
        execution = self.sources.execution
        assert execution is None or type(execution) is CalculatorExecutionRecord
        return execution

    @property
    def stdout(self) -> QePwStdoutFileResult:
        """Expose parsed stdout observations directly from the facade."""
        return self.streams.stdout

    @property
    def stderr(self) -> QePwStderrFileResult:
        """Expose parsed stderr observations directly from the facade."""
        return self.streams.stderr

    @property
    def stdout_artifact(self) -> QePwNativeArtifact:
        """Expose the exact stdout identity."""
        return self.streams.stdout_artifact

    @property
    def stderr_artifact(self) -> QePwNativeArtifact:
        """Expose the exact stderr identity."""
        return self.streams.stderr_artifact

    @property
    def trajectory(self) -> QeRelaxationTrajectory:
        """Expose the stdout-observed trajectory with its source semantics intact."""
        return self.stdout_trajectory

    @property
    def steps(self) -> tuple[QeRelaxationTrajectoryStep, ...]:
        """Expose source-ordered stdout trajectory steps."""
        return self.stdout_trajectory.steps

    @property
    def final_structure(self) -> QeQexsdFinalStructure | None:
        """Expose the interpreted final QEXSD structure when available."""
        return self.qexsd.final_structure if self.qexsd is not None else None

    @property
    def job_completed(self) -> bool:
        """Expose the native stdout terminal marker observation."""
        return self.stdout.job_completed

    @property
    def scf_converged(self) -> bool:
        """Expose the native stdout SCF convergence observation."""
        return self.stdout.scf_converged

    @property
    def optimizer_converged(self) -> bool:
        """Expose the native stdout optimizer convergence observation."""
        return self.stdout.geometry_optimization_converged

    def normalize(
        self,
        starting_structure: StructureResolution,
    ) -> PwDftRelaxationObservation:
        """Normalize terminal QE values without deciding scientific acceptance."""
        if type(starting_structure) is not StructureResolution:
            raise TypeError("starting_structure must be a StructureResolution")
        final_structure = self.final_structure
        if final_structure is None:
            raise ValueError(
                "normalized relaxation observation requires QEXSD structure"
            )
        stdout = self.stdout
        if stdout.total_energy_ry is None:
            raise ValueError("normalized relaxation observation requires total energy")
        if stdout.bfgs_step_count is None:
            raise ValueError(
                "normalized relaxation observation requires BFGS step count"
            )
        native_stress = (
            stdout.optimizer_stress_ry_per_bohr_cubed
            if stdout.optimizer_stress_ry_per_bohr_cubed is not None
            else stdout.stress_ry_per_bohr_cubed
        )
        stress_tensor = None
        if native_stress is not None:
            stress_tensor = (
                StressTensor(
                    components=MatrixQuantity(
                        np.asarray(native_stress, dtype=np.float64),
                        PhysicalUnit("rydberg / bohr ** 3"),
                    ),
                    sign_convention=StressSignConvention.COMPRESSION_POSITIVE,
                )
                .to_si()
                .to_sign_convention(StressSignConvention.TENSION_POSITIVE)
            )
        maximum_force_ry_per_bohr = (
            stdout.optimizer_maximum_atomic_force_ry_per_bohr
            if stdout.optimizer_maximum_atomic_force_ry_per_bohr is not None
            else stdout.maximum_atomic_force_ry_per_bohr
        )
        pressure_kbar = (
            MODEL_SYSTEM_UNIT_CONVERTER.convert_scalar(
                stress_tensor.hydrostatic_pressure,
                PhysicalUnit("kilobar"),
            ).magnitude
            if stress_tensor is not None
            else (
                stdout.optimizer_pressure_kbar
                if stdout.optimizer_pressure_kbar is not None
                else stdout.pressure_kbar
            )
        )
        observed_unit_cell = final_structure.unit_cell
        starting_unit_cell = starting_structure.unit_cell
        starting_symbols = tuple(
            atom.symbol for atom in starting_unit_cell.atomic_basis.atoms
        )
        observed_symbols = tuple(
            atom.symbol for atom in observed_unit_cell.atomic_basis.atoms
        )
        if starting_symbols != observed_symbols:
            raise ValueError("QEXSD final structure composition or order changed")
        final_unit_cell = (
            UnitCell(
                direct_lattice=starting_unit_cell.direct_lattice,
                lattice_parameter=starting_unit_cell.lattice_parameter,
                atomic_basis=observed_unit_cell.atomic_basis,
            )
            if self.calculation == "relax"
            else observed_unit_cell
        )
        artifacts = [
            _normalized_artifact(self.stdout_artifact),
            _normalized_artifact(self.stderr_artifact),
        ]
        if self.qexsd is not None:
            artifacts.append(
                PwDftRelaxationNativeArtifact(
                    integration_id=_QE_INTEGRATION_ID,
                    artifact_id=final_structure.source_path,
                    sha256=final_structure.source_sha256,
                    byte_size=final_structure.source_byte_count,
                )
            )
        return PwDftRelaxationObservation(
            final_unit_cell=final_unit_cell,
            ionic_step_count=stdout.bfgs_step_count,
            completed=stdout.job_completed,
            ionic_converged=stdout.geometry_optimization_converged,
            cell_converged=(
                stdout.geometry_optimization_converged
                if self.calculation == "vc-relax"
                else None
            ),
            final_total_energy_ev=_convert_scalar(
                stdout.total_energy_ry,
                "rydberg",
                "electron_volt",
            ),
            maximum_force_ev_per_angstrom=(
                _convert_scalar(
                    maximum_force_ry_per_bohr,
                    "rydberg / bohr",
                    "electron_volt / angstrom",
                )
                if maximum_force_ry_per_bohr is not None
                else None
            ),
            pressure_kbar=pressure_kbar,
            stress_tensor=stress_tensor,
            total_magnetization_electrons=(
                stdout.total_magnetization_bohr_magneton_per_cell
            ),
            program_version=stdout.program_version,
            native_artifacts=tuple(artifacts),
        )


def _convert_scalar(value: float, source: str, target: str) -> float:
    return MODEL_SYSTEM_UNIT_CONVERTER.convert_scalar(
        ScalarQuantity(value, PhysicalUnit(source)),
        PhysicalUnit(target),
    ).magnitude


def _normalized_artifact(artifact: QePwNativeArtifact) -> PwDftRelaxationNativeArtifact:
    return PwDftRelaxationNativeArtifact(
        integration_id=_QE_INTEGRATION_ID,
        artifact_id=artifact.relative_path,
        sha256=artifact.sha256,
        byte_size=artifact.byte_size,
    )


def assemble_qe_relax_data(
    *,
    calculation: Literal["relax", "vc-relax"],
    streams: QePwCapturedStreamData,
    stdout_trajectory: QeRelaxationTrajectory,
    qexsd_document: object | None,
    execution: CalculatorExecutionRecord | None,
) -> QeRelaxData:
    """Assemble one facade from independently extracted native sources."""
    qexsd = (
        QeQexsdData.from_document(qexsd_document)
        if qexsd_document is not None
        else None
    )
    return QeRelaxData(
        calculation=calculation,
        sources=QePwDataSources(
            streams=streams,
            qexsd=qexsd,
            execution=execution,
        ),
        stdout_trajectory=stdout_trajectory,
        consistency=QeRelaxationConsistency.compare(streams.stdout, qexsd),
    )
