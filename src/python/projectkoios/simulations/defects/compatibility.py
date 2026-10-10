"""Mechanical compatibility qualification for defect-energy evidence."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.defects.energy import DefectEnergyEvidence


@dataclass(frozen=True, slots=True)
class DefectEnergyCompatibility:
    """Retain an explicit mechanical compatibility determination."""

    qualification_id: str
    evidence_ids: tuple[str, ...]
    method_id: str
    model_id: str
    compatible: bool
    explanation: str
    compared_fields: tuple[str, ...]
    permitted_differences: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        for label, value in (
            ("qualification_id", self.qualification_id),
            ("method_id", self.method_id),
            ("model_id", self.model_id),
            ("explanation", self.explanation),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if type(self.evidence_ids) is not tuple or not self.evidence_ids:
            raise ValueError("evidence_ids must be a nonempty tuple")
        if any(
            type(value) is not str or not value or value != value.strip()
            for value in self.evidence_ids
        ):
            raise ValueError("evidence_ids must contain nonempty stripped strings")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")
        if type(self.compatible) is not bool:
            raise TypeError("compatible must be a bool")
        if type(self.compared_fields) is not tuple or not self.compared_fields:
            raise ValueError("compared_fields must be a nonempty tuple")
        for label, values in (
            ("compared_fields", self.compared_fields),
            ("permitted_differences", self.permitted_differences),
            ("limitations", self.limitations),
        ):
            if type(values) is not tuple or any(
                type(value) is not str or not value or value != value.strip()
                for value in values
            ):
                raise ValueError(f"{label} must contain nonempty stripped strings")
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")

    def require(self, evidence: tuple[DefectEnergyEvidence, ...]) -> None:
        """Reject evidence that does not match this explicit qualification."""
        if type(evidence) is not tuple or not evidence:
            raise ValueError("evidence must be a nonempty tuple")
        if any(type(value) is not DefectEnergyEvidence for value in evidence):
            raise TypeError("evidence must contain DefectEnergyEvidence values")
        if not self.compatible:
            raise ValueError("defect-energy compatibility qualification is negative")
        if tuple(value.energy_id for value in evidence) != self.evidence_ids:
            raise ValueError("evidence identities do not match compatibility record")
        if any(value.method_id != self.method_id for value in evidence):
            raise ValueError("evidence method does not match compatibility record")
        if any(value.model_id != self.model_id for value in evidence):
            raise ValueError("evidence model does not match compatibility record")
        if any(value.qualification_id != self.qualification_id for value in evidence):
            raise ValueError(
                "evidence qualification does not match compatibility record"
            )
        if any(
            not value.final_single_point or not value.completed or not value.converged
            for value in evidence
        ):
            raise ValueError(
                "compatible defect energies require converged, completed final "
                "single points"
            )
