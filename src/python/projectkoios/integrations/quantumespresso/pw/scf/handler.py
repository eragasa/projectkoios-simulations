"""Concrete Quantum ESPRESSO handler for the common SCF lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.execution import (
    QeSimulationExecutor,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    integration as qe_integration,
)
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.dft.pseudopotential.library import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.base import PwDftScfEvent
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskCompleted,
    PwDftScfTaskFailed,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.dft.pw.scf.handler import (
    PwDftScfActionHandler,
    PwDftScfHandlerTask,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
)


@dataclass(frozen=True, slots=True)
class QePwDftScfTask(PwDftScfHandlerTask):
    """Bind one QE simulation and operator resources to workflow identities."""

    prepared_input: CalculatorInputRecord
    pseudopotentials: tuple[PseudopotentialFile, ...]
    pseudopotential_library: PseudopotentialLibrary
    executable: Path
    working_directory: Path
    timeout_seconds: float | None = None
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        super(QePwDftScfTask, self).__post_init__()
        if type(self.prepared_input) is not CalculatorInputRecord:
            raise TypeError("prepared_input must be a CalculatorInputRecord")
        if type(self.pseudopotentials) is not tuple or not self.pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        if any(
            not isinstance(item, PseudopotentialFile) for item in self.pseudopotentials
        ):
            raise TypeError("pseudopotentials must contain PseudopotentialFile values")
        if type(self.pseudopotential_library) is not PseudopotentialLibrary:
            raise TypeError("pseudopotential_library must be a PseudopotentialLibrary")
        if not isinstance(self.executable, Path) or not self.executable.is_absolute():
            raise ValueError("executable must be an absolute Path")
        if not isinstance(self.working_directory, Path):
            raise TypeError("working_directory must be a Path")
        if not self.working_directory.is_dir() or self.working_directory.is_symlink():
            raise ValueError(
                "working_directory must be an existing nonsymlink directory"
            )
        if self.timeout_seconds is not None and (
            type(self.timeout_seconds) is not float or self.timeout_seconds <= 0.0
        ):
            raise ValueError("timeout_seconds must be a positive float or None")
        if type(self.execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a bool")
        if Path(self.output_artifact_id).name in {
            artifact.filename for artifact in self.prepared_input.artifacts
        }:
            raise ValueError("output artifact must differ from prepared input files")


@dataclass(frozen=True, slots=True)
class QePwDftScfActionHandler(PwDftScfActionHandler):
    """Compose QE staging/execution and common retained-data extraction."""

    integration: qe_integration.QePwDftScfIntegration
    tasks: tuple[QePwDftScfTask, ...]
    executor: QeSimulationExecutor = QeSimulationExecutor()

    def __post_init__(self) -> None:
        if type(self.integration) is not qe_integration.QePwDftScfIntegration:
            raise TypeError("integration must be a QePwDftScfIntegration")
        if type(self.tasks) is not tuple or not self.tasks:
            raise ValueError("tasks must be a nonempty tuple")
        if any(type(task) is not QePwDftScfTask for task in self.tasks):
            raise TypeError("tasks must contain QePwDftScfTask values")
        if type(self.executor) is not QeSimulationExecutor:
            raise TypeError("executor must be a QeSimulationExecutor")
        if len({task.evaluation_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task evaluation identifiers must be unique")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task identifiers must be unique")
        for task in self.tasks:
            self._validate_artifact_location(task)

    def register(self, action: RegisterPwDftScfTask) -> PwDftScfEvent:
        """Return the declared task identity for one QE evaluation."""
        task = self._task_for_evaluation(action.evaluation_id)
        return PwDftScfTaskRegistered(
            evaluation_id=task.evaluation_id,
            task_id=task.task_id,
        )

    def submit(self, action: SubmitPwDftScfTask) -> tuple[PwDftScfEvent, ...]:
        """Stage and execute one QE task, returning recorded terminal events."""
        task = self._task_for_id(action.task_id)
        if not task.execution_authorized:
            raise PermissionError("Quantum ESPRESSO execution is not authorized")
        submitted = PwDftScfTaskSubmitted(task_id=task.task_id)
        try:
            self.executor.execute(
                prepared_input=task.prepared_input,
                pseudopotentials=task.pseudopotentials,
                pseudopotential_library=task.pseudopotential_library,
                executable=task.executable,
                working_directory=task.working_directory,
                output_filename=Path(task.output_artifact_id).name,
                timeout_seconds=task.timeout_seconds,
                execution_authorized=task.execution_authorized,
            )
        except CalculatorExecutionError as error:
            return (
                submitted,
                PwDftScfTaskFailed(
                    task_id=task.task_id,
                    code=f"calculator-{error.record.status.value}",
                    message=str(error),
                ),
            )
        return (
            submitted,
            PwDftScfTaskCompleted(
                task_id=task.task_id,
                output_artifact_id=task.output_artifact_id,
            ),
        )

    def analyze(self, action: AnalyzePwDftScfOutput) -> PwDftScfEvent:
        """Normalize correlated retained QE evidence or return failure evidence."""
        task = self._task_for_id(action.task_id)
        if action.output_artifact_id != task.output_artifact_id:
            raise ValueError("QE output artifact does not match the task declaration")
        try:
            observation = self.integration.analyze(task.output_artifact_id)
        except (OSError, UnicodeError, ValueError) as error:
            return PwDftScfTaskFailed(
                task_id=task.task_id,
                code="output-analysis-failed",
                message=str(error) or type(error).__name__,
            )
        return PwDftScfOutputAnalyzed(
            task_id=task.task_id,
            observation=observation,
        )

    def _task_for_evaluation(self, evaluation_id: str) -> QePwDftScfTask:
        for task in self.tasks:
            if task.evaluation_id == evaluation_id:
                return task
        raise KeyError(f"unknown QE SCF evaluation: {evaluation_id}")

    def _task_for_id(self, task_id: str) -> QePwDftScfTask:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"unknown QE SCF task: {task_id}")

    def _validate_artifact_location(self, task: QePwDftScfTask) -> None:
        artifact_id = Path(task.output_artifact_id)
        if artifact_id.is_absolute():
            raise ValueError("QE output artifact identifier must be relative")
        root = self.integration.artifact_root.resolve()
        artifact_path = (root / artifact_id).resolve()
        if not artifact_path.is_relative_to(root):
            raise ValueError("QE output artifact must remain inside artifact_root")
        if artifact_path.parent != task.working_directory.resolve():
            raise ValueError(
                "QE output artifact parent must equal the working directory"
            )
