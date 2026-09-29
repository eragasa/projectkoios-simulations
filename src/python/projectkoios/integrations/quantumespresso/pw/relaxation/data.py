"""Unified immutable data facade for QE structural relaxation output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
from projectkoios.simulations.execution import CalculatorExecutionRecord

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
