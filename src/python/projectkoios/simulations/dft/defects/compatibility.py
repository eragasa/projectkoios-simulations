"""Mechanical plane-wave DFT compatibility records for defect energetics."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.defects import (
    DefectEnergyCompatibility,
    DefectEnergyEvidence,
)


@dataclass(frozen=True, slots=True)
class PwDftDefectCompatibilityAction:
    """Build a positive record only for already matched DFT model identities."""

    def qualify(
        self,
        *,
        qualification_id: str,
        evidence: tuple[DefectEnergyEvidence, ...],
        explanation: str,
    ) -> DefectEnergyCompatibility:
        """Return mechanical compatibility without scientific acceptance."""
        if (
            type(qualification_id) is not str
            or not qualification_id
            or qualification_id != qualification_id.strip()
        ):
            raise ValueError("qualification_id must be nonempty and stripped")
        if type(evidence) is not tuple or not evidence:
            raise ValueError("evidence must be a nonempty tuple")
        if any(type(value) is not DefectEnergyEvidence for value in evidence):
            raise TypeError("evidence must contain DefectEnergyEvidence values")
        if any(value.method_id != "plane-wave-dft" for value in evidence):
            raise ValueError("compatibility requires plane-wave-dft evidence")
        if len({value.model_id for value in evidence}) != 1:
            raise ValueError("DFT evidence model identities must match exactly")
        if any(
            not value.final_single_point or not value.completed or not value.converged
            for value in evidence
        ):
            raise ValueError(
                "DFT compatibility requires converged, completed final SCF evidence"
            )
        if any(value.qualification_id != qualification_id for value in evidence):
            raise ValueError("DFT evidence qualification identities must match")
        return DefectEnergyCompatibility(
            qualification_id=qualification_id,
            evidence_ids=tuple(value.energy_id for value in evidence),
            method_id="plane-wave-dft",
            model_id=evidence[0].model_id,
            compatible=True,
            explanation=explanation,
            compared_fields=(
                "method_id",
                "model_id",
                "qualification_id",
                "final_single_point",
                "completed",
                "converged",
            ),
            permitted_differences=(),
            limitations=(
                "cutoff, k-point, occupation, calculator-version, and exact "
                "pseudopotential comparisons require richer evidence records",
            ),
        )
