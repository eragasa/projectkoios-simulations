"""Concrete VASP action handler for the calculator-neutral SCF lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.vasp.pw_dft_scf.integration import (
    VaspScfIntegration,
)
from projectkoios.integrations.vasp.pw_dft_scf.output_analysis import (
    VaspScfArtifactError,
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
    CalculatorExecutionRequest,
    CalculatorExecutor,
)


@dataclass(frozen=True, slots=True)
class VaspPwDftScfTask(PwDftScfHandlerTask):
    """Bind one pre-staged VASP execution request to workflow identities."""

    execution_request: CalculatorExecutionRequest

    def __post_init__(self) -> None:
        super(VaspPwDftScfTask, self).__post_init__()
        if type(self.execution_request) is not CalculatorExecutionRequest:
            raise TypeError("execution_request must be a CalculatorExecutionRequest")


@dataclass(frozen=True, slots=True)
class VaspPwDftScfActionHandler(PwDftScfActionHandler):
    """Compose VASP evidence analysis with bounded no-shell process execution."""

    integration: VaspScfIntegration
    tasks: tuple[VaspPwDftScfTask, ...]
    executor: CalculatorExecutor = CalculatorExecutor()

    def __post_init__(self) -> None:
        if type(self.integration) is not VaspScfIntegration:
            raise TypeError("integration must be a VaspScfIntegration")
        if type(self.tasks) is not tuple or not self.tasks:
            raise ValueError("tasks must be a nonempty tuple")
        if any(type(task) is not VaspPwDftScfTask for task in self.tasks):
            raise TypeError("tasks must contain VaspPwDftScfTask values")
        if type(self.executor) is not CalculatorExecutor:
            raise TypeError("executor must be a CalculatorExecutor")
        evaluation_ids = tuple(task.evaluation_id for task in self.tasks)
        task_ids = tuple(task.task_id for task in self.tasks)
        if len(set(evaluation_ids)) != len(evaluation_ids):
            raise ValueError("task evaluation identifiers must be unique")
        if len(set(task_ids)) != len(task_ids):
            raise ValueError("task identifiers must be unique")
        for task in self.tasks:
            self._validate_artifact_location(task)

    def register(self, action: RegisterPwDftScfTask) -> PwDftScfEvent:
        """Return the task identity declared for one pre-staged evaluation."""
        task = self._task_for_evaluation(action.evaluation_id)
        return PwDftScfTaskRegistered(
            evaluation_id=task.evaluation_id,
            task_id=task.task_id,
        )

    def submit(self, action: SubmitPwDftScfTask) -> tuple[PwDftScfEvent, ...]:
        """Execute one explicitly authorized, pre-staged VASP task."""
        task = self._task_for_id(action.task_id)
        if not task.execution_request.execution_authorized:
            raise PermissionError("VASP calculator execution is not authorized")
        submitted = PwDftScfTaskSubmitted(task_id=task.task_id)
        try:
            self.executor.action(request=task.execution_request)
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
        """Normalize the correlated retained OUTCAR or return failure evidence."""
        task = self._task_for_id(action.task_id)
        if action.output_artifact_id != task.output_artifact_id:
            raise ValueError("VASP output artifact does not match the task declaration")
        try:
            observation = self.integration.analyze(task.output_artifact_id)
        except VaspScfArtifactError as error:
            return PwDftScfTaskFailed(
                task_id=task.task_id,
                code=error.code,
                message=str(error),
            )
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

    def _task_for_evaluation(self, evaluation_id: str) -> VaspPwDftScfTask:
        for task in self.tasks:
            if task.evaluation_id == evaluation_id:
                return task
        raise KeyError(f"unknown VASP SCF evaluation: {evaluation_id}")

    def _task_for_id(self, task_id: str) -> VaspPwDftScfTask:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"unknown VASP SCF task: {task_id}")

    def _validate_artifact_location(self, task: VaspPwDftScfTask) -> None:
        artifact_id = Path(task.output_artifact_id)
        if artifact_id.is_absolute():
            raise ValueError("VASP output artifact identifier must be relative")
        root = self.integration.artifact_root.resolve()
        artifact_path = (root / artifact_id).resolve()
        if not artifact_path.is_relative_to(root):
            raise ValueError("VASP output artifact must remain inside artifact_root")
        if artifact_path.parent != task.execution_request.working_directory.resolve():
            raise ValueError(
                "VASP output artifact parent must equal the execution directory"
            )
