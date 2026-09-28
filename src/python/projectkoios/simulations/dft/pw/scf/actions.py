"""Calculator-neutral actions emitted by plane-wave DFT SCF workflows."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfAction,
    _validate_identifier,
    _validate_nonempty_text,
)


@dataclass(frozen=True, slots=True)
class RegisterPwDftScfTask(PwDftScfAction):
    """Request task registration for one retained SCF evaluation."""

    evaluation_id: str

    def __post_init__(self) -> None:
        _validate_identifier(self.evaluation_id, "evaluation_id")


@dataclass(frozen=True, slots=True)
class SubmitPwDftScfTask(PwDftScfAction):
    """Request execution of one opaque registered task identity."""

    task_id: str

    def __post_init__(self) -> None:
        _validate_nonempty_text(self.task_id, "task_id")


@dataclass(frozen=True, slots=True)
class AnalyzePwDftScfOutput(PwDftScfAction):
    """Request analysis of one calculator-native output artifact."""

    task_id: str
    output_artifact_id: str

    def __post_init__(self) -> None:
        _validate_nonempty_text(self.task_id, "task_id")
        _validate_nonempty_text(self.output_artifact_id, "output_artifact_id")
