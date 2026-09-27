"""Calculator-neutral events accepted by plane-wave DFT SCF workflows."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfEvent,
    PwDftScfObservation,
)


@dataclass(frozen=True, slots=True)
class PwDftScfTaskRegistered(PwDftScfEvent):
    """Report the task identity allocated for an SCF evaluation."""

    evaluation_id: str
    task_id: str


@dataclass(frozen=True, slots=True)
class PwDftScfTaskSubmitted(PwDftScfEvent):
    """Report acceptance of one SCF task by an external executor."""

    task_id: str


@dataclass(frozen=True, slots=True)
class PwDftScfTaskCompleted(PwDftScfEvent):
    """Report terminal calculator output availability for one task."""

    task_id: str
    output_artifact_id: str


@dataclass(frozen=True, slots=True)
class PwDftScfOutputAnalyzed(PwDftScfEvent):
    """Report one normalized observation derived from native output."""

    task_id: str
    observation: PwDftScfObservation


@dataclass(frozen=True, slots=True)
class PwDftScfTaskFailed(PwDftScfEvent):
    """Report a terminal external failure for one correlated task."""

    task_id: str
    code: str
    message: str
