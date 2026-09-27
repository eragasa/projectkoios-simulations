"""Calculator-neutral actions emitted by plane-wave DFT SCF workflows."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.dft.pw.scf.base import PwDftScfAction


@dataclass(frozen=True, slots=True)
class RegisterPwDftScfTask(PwDftScfAction):
    """Request task registration for one retained SCF evaluation."""

    evaluation_id: str


@dataclass(frozen=True, slots=True)
class SubmitPwDftScfTask(PwDftScfAction):
    """Request execution of one opaque registered task identity."""

    task_id: str


@dataclass(frozen=True, slots=True)
class AnalyzePwDftScfOutput(PwDftScfAction):
    """Request analysis of one calculator-native output artifact."""

    task_id: str
    output_artifact_id: str
