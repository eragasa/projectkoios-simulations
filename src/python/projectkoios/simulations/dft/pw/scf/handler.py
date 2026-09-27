"""Action-handler contract with calculator-neutral mock and replay implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfAction,
    PwDftScfEvent,
    PwDftScfObservation,
)
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskCompleted,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfIntegration,
)


class PwDftScfActionHandler(ABC):
    """Dispatch SCF actions to a concrete external-effect implementation."""

    __slots__ = ()

    def handle(self, action: PwDftScfAction) -> tuple[PwDftScfEvent, ...]:
        """Return correlated events without exposing implementation state."""
        if isinstance(action, RegisterPwDftScfTask):
            return (self.register(action),)
        if isinstance(action, SubmitPwDftScfTask):
            return self.submit(action)
        if isinstance(action, AnalyzePwDftScfOutput):
            return (self.analyze(action),)
        raise TypeError(f"unsupported SCF action: {type(action).__name__}")

    @abstractmethod
    def register(self, action: RegisterPwDftScfTask) -> PwDftScfEvent:
        """Register one retained evaluation and return its task event."""
        raise NotImplementedError

    @abstractmethod
    def submit(self, action: SubmitPwDftScfTask) -> tuple[PwDftScfEvent, ...]:
        """Submit or replay one task and return ordered lifecycle events."""
        raise NotImplementedError

    @abstractmethod
    def analyze(self, action: AnalyzePwDftScfOutput) -> PwDftScfEvent:
        """Analyze or replay one retained output and return its event."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class PwDftScfHandlerTask:
    """Carry correlation shared by every concrete SCF action handler."""

    evaluation_id: str
    task_id: str
    output_artifact_id: str

    def __post_init__(self) -> None:
        for label, value in (
            ("evaluation_id", self.evaluation_id),
            ("task_id", self.task_id),
            ("output_artifact_id", self.output_artifact_id),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class MockPwDftScfTask(PwDftScfHandlerTask):
    """Declare deterministic synthetic events for one mock SCF task."""

    observation: PwDftScfObservation

    def __post_init__(self) -> None:
        super(MockPwDftScfTask, self).__post_init__()
        if type(self.observation) is not PwDftScfObservation:
            raise TypeError("observation must be a PwDftScfObservation")


@dataclass(frozen=True, slots=True)
class MockPwDftScfActionHandler(PwDftScfActionHandler):
    """Return configured synthetic events without defining another workflow net."""

    tasks: tuple[MockPwDftScfTask, ...]

    def __post_init__(self) -> None:
        if type(self.tasks) is not tuple or not self.tasks:
            raise ValueError("tasks must be a nonempty tuple")
        if any(type(task) is not MockPwDftScfTask for task in self.tasks):
            raise TypeError("tasks must contain MockPwDftScfTask values")
        self._validate_unique_task_identities()

    def register(self, action: RegisterPwDftScfTask) -> PwDftScfEvent:
        """Return the configured synthetic task registration."""
        task = self._task_for_evaluation(action.evaluation_id)
        return PwDftScfTaskRegistered(
            evaluation_id=task.evaluation_id,
            task_id=task.task_id,
        )

    def submit(self, action: SubmitPwDftScfTask) -> tuple[PwDftScfEvent, ...]:
        """Return synthetic submission and completion events in causal order."""
        task = self._task_for_id(action.task_id)
        return (
            PwDftScfTaskSubmitted(task_id=task.task_id),
            PwDftScfTaskCompleted(
                task_id=task.task_id,
                output_artifact_id=task.output_artifact_id,
            ),
        )

    def analyze(self, action: AnalyzePwDftScfOutput) -> PwDftScfEvent:
        """Return the configured synthetic normalized observation."""
        task = self._task_for_id(action.task_id)
        if action.output_artifact_id != task.output_artifact_id:
            raise ValueError("mock output artifact does not match the task declaration")
        return PwDftScfOutputAnalyzed(
            task_id=task.task_id,
            observation=task.observation,
        )

    def _task_for_evaluation(self, evaluation_id: str) -> MockPwDftScfTask:
        for task in self.tasks:
            if task.evaluation_id == evaluation_id:
                return task
        raise KeyError(f"unknown mock SCF evaluation: {evaluation_id}")

    def _task_for_id(self, task_id: str) -> MockPwDftScfTask:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"unknown mock SCF task: {task_id}")

    def _validate_unique_task_identities(self) -> None:
        if len({task.evaluation_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task evaluation identifiers must be unique")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task identifiers must be unique")


@dataclass(frozen=True, slots=True)
class ReplayPwDftScfTask(PwDftScfHandlerTask):
    """Bind one evaluation to retained calculator output for deterministic replay."""


@dataclass(frozen=True, slots=True)
class ReplayPwDftScfActionHandler(PwDftScfActionHandler):
    """Replay retained evidence through one calculator integration without execution."""

    integration: PwDftScfIntegration
    tasks: tuple[ReplayPwDftScfTask, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.integration, PwDftScfIntegration):
            raise TypeError("integration must inherit from PwDftScfIntegration")
        if type(self.tasks) is not tuple or not self.tasks:
            raise ValueError("tasks must be a nonempty tuple")
        if any(type(task) is not ReplayPwDftScfTask for task in self.tasks):
            raise TypeError("tasks must contain ReplayPwDftScfTask values")
        self._validate_unique_task_identities()

    def register(self, action: RegisterPwDftScfTask) -> PwDftScfEvent:
        """Replay the retained task registration identity."""
        task = self._task_for_evaluation(action.evaluation_id)
        return PwDftScfTaskRegistered(
            evaluation_id=task.evaluation_id,
            task_id=task.task_id,
        )

    def submit(self, action: SubmitPwDftScfTask) -> tuple[PwDftScfEvent, ...]:
        """Replay submission and retained-output availability without execution."""
        task = self._task_for_id(action.task_id)
        return (
            PwDftScfTaskSubmitted(task_id=task.task_id),
            PwDftScfTaskCompleted(
                task_id=task.task_id,
                output_artifact_id=task.output_artifact_id,
            ),
        )

    def analyze(self, action: AnalyzePwDftScfOutput) -> PwDftScfEvent:
        """Analyze the declared retained artifact through the integration."""
        task = self._task_for_id(action.task_id)
        if action.output_artifact_id != task.output_artifact_id:
            raise ValueError(
                "replay output artifact does not match the task declaration"
            )
        observation = self.integration.analyze(task.output_artifact_id)
        return PwDftScfOutputAnalyzed(
            task_id=task.task_id,
            observation=observation,
        )

    def _task_for_evaluation(self, evaluation_id: str) -> ReplayPwDftScfTask:
        for task in self.tasks:
            if task.evaluation_id == evaluation_id:
                return task
        raise KeyError(f"unknown replay SCF evaluation: {evaluation_id}")

    def _task_for_id(self, task_id: str) -> ReplayPwDftScfTask:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KeyError(f"unknown replay SCF task: {task_id}")

    def _validate_unique_task_identities(self) -> None:
        if len({task.evaluation_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task evaluation identifiers must be unique")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("task identifiers must be unique")
