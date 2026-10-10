"""Immutable calculator-neutral plane-wave DFT SCF records."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

from projectkoios.simulations.calculator import CalculatorIntegrationId

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class PwDftScfObject:
    """Base nominal identity for plane-wave DFT SCF records."""

    __slots__ = ()


class PwDftScfAction(PwDftScfObject):
    """Base nominal identity for externally handled SCF actions."""

    __slots__ = ()


class PwDftScfEvent(PwDftScfObject):
    """Base nominal identity for externally observed SCF events."""

    __slots__ = ()


class PwDftScfWorkflowOutcome(PwDftScfObject):
    """Base nominal identity for every terminal SCF workflow outcome."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class PwDftScfRequestReference(PwDftScfObject):
    """Carry only an evaluation identity through a workflow marking."""

    evaluation_id: str

    def __post_init__(self) -> None:
        _validate_identifier(self.evaluation_id, "evaluation_id")


@dataclass(frozen=True, slots=True)
class PwDftScfNativeArtifact(PwDftScfObject):
    """Identify the retained calculator-native output underlying an observation."""

    integration_id: CalculatorIntegrationId
    artifact_id: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        if not self.artifact_id or self.artifact_id != self.artifact_id.strip():
            raise ValueError("artifact_id must be nonempty and stripped")
        if type(self.sha256) is not str or not _SHA256.fullmatch(self.sha256):
            raise ValueError("artifact SHA-256 must be lowercase hexadecimal")
        if type(self.byte_size) is not int or self.byte_size <= 0:
            raise ValueError("artifact byte_size must be a positive integer")


class PwDftScfDiagnosticSeverity(StrEnum):
    """Classify a normalized calculator diagnostic without changing run status."""

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PwDftScfDiagnostic(PwDftScfObject):
    """Preserve one structured diagnostic and its native evidence identity."""

    code: str
    severity: PwDftScfDiagnosticSeverity
    message: str
    native_artifact: PwDftScfNativeArtifact

    def __post_init__(self) -> None:
        _validate_identifier(self.code, "diagnostic code")
        if type(self.severity) is not PwDftScfDiagnosticSeverity:
            raise TypeError("severity must be a PwDftScfDiagnosticSeverity")
        if not self.message or self.message != self.message.strip():
            raise ValueError("diagnostic message must be nonempty and stripped")
        if type(self.native_artifact) is not PwDftScfNativeArtifact:
            raise TypeError("native_artifact must be a PwDftScfNativeArtifact")


@dataclass(frozen=True, slots=True)
class PwDftScfObservation(PwDftScfObject):
    """Preserve normalized SCF observations and their native evidence identity."""

    total_energy_ev: float
    atom_count: int
    electronic_iteration_count: int
    converged: bool
    completed: bool
    native_artifact: PwDftScfNativeArtifact
    program_version: str | None = None
    irreducible_kpoint_count: int | None = None
    wavefunction_cutoff_ev: float | None = None
    total_magnetization_electrons: float | None = None
    spin_up_electrons: float | None = None
    spin_down_electrons: float | None = None
    diagnostics: tuple[PwDftScfDiagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.total_energy_ev):
            raise ValueError("total energy must be finite")
        if type(self.atom_count) is not int or self.atom_count <= 0:
            raise ValueError("atom_count must be a positive integer")
        if (
            type(self.electronic_iteration_count) is not int
            or self.electronic_iteration_count < 0
        ):
            raise ValueError("electronic iteration count must be nonnegative")
        if type(self.converged) is not bool or type(self.completed) is not bool:
            raise TypeError("converged and completed must be booleans")
        if type(self.native_artifact) is not PwDftScfNativeArtifact:
            raise TypeError("native_artifact must be a PwDftScfNativeArtifact")
        if self.wavefunction_cutoff_ev is not None and (
            not math.isfinite(self.wavefunction_cutoff_ev)
            or self.wavefunction_cutoff_ev <= 0.0
        ):
            raise ValueError("observed wavefunction cutoff must be positive and finite")
        for label, value in (
            ("total_magnetization_electrons", self.total_magnetization_electrons),
            ("spin_up_electrons", self.spin_up_electrons),
            ("spin_down_electrons", self.spin_down_electrons),
        ):
            if value is not None and (
                type(value) is not float or not math.isfinite(value)
            ):
                raise ValueError(f"{label} must be a finite float when represented")
        if (self.spin_up_electrons is None) is not (self.spin_down_electrons is None):
            raise ValueError(
                "spin-channel electron populations must both be set or omitted"
            )
        if (
            self.spin_up_electrons is not None
            and self.spin_down_electrons is not None
            and (self.spin_up_electrons < 0.0 or self.spin_down_electrons < 0.0)
        ):
            raise ValueError("spin-channel electron populations must be nonnegative")
        if (
            self.total_magnetization_electrons is not None
            and self.spin_up_electrons is not None
            and self.spin_down_electrons is not None
            and not math.isclose(
                self.total_magnetization_electrons,
                self.spin_up_electrons - self.spin_down_electrons,
                rel_tol=0.0,
                abs_tol=1e-9,
            )
        ):
            raise ValueError(
                "total magnetization must equal spin-up minus spin-down electrons"
            )
        if type(self.diagnostics) is not tuple or any(
            type(diagnostic) is not PwDftScfDiagnostic
            for diagnostic in self.diagnostics
        ):
            raise TypeError("diagnostics must be a tuple of PwDftScfDiagnostic values")

    @property
    def total_energy_ev_per_atom(self) -> float:
        """Return the normalized total energy divided by atom count."""
        return self.total_energy_ev / self.atom_count


@dataclass(frozen=True, slots=True)
class PwDftScfResult(PwDftScfObject):
    """Bind one evaluation and task identity to its normalized observation."""

    evaluation_id: str
    task_id: str
    observation: PwDftScfObservation

    def __post_init__(self) -> None:
        _validate_identifier(self.evaluation_id, "evaluation_id")
        _validate_nonempty_text(self.task_id, "task_id")
        if type(self.observation) is not PwDftScfObservation:
            raise TypeError("observation must be a PwDftScfObservation")


@dataclass(frozen=True, slots=True)
class PwDftScfWorkflowStart(PwDftScfObject):
    """Authorize exactly one workflow start for a retained evaluation."""

    evaluation_id: str

    def __post_init__(self) -> None:
        _validate_identifier(self.evaluation_id, "evaluation_id")


@dataclass(frozen=True, slots=True)
class PwDftScfWorkflowSucceeded(PwDftScfWorkflowOutcome):
    """Terminate one workflow with its successful immutable result."""

    result: PwDftScfResult

    def __post_init__(self) -> None:
        if type(self.result) is not PwDftScfResult:
            raise TypeError("result must be a PwDftScfResult")


@dataclass(frozen=True, slots=True)
class PwDftScfWorkflowFailed(PwDftScfWorkflowOutcome):
    """Terminate one workflow with a structured failure code and explanation."""

    evaluation_id: str
    code: str
    message: str

    def __post_init__(self) -> None:
        _validate_identifier(self.evaluation_id, "evaluation_id")
        _validate_identifier(self.code, "failure code")
        _validate_nonempty_text(self.message, "failure message")


def _validate_identifier(value: str, label: str) -> None:
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase slug")


def _validate_nonempty_text(value: str, label: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be nonempty and stripped")
