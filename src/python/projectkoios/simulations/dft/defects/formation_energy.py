"""Plane-wave DFT qualification wrapper for neutral defect formation energy."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.simulations.defects import (
    NeutralDefectFormationEnergyAction,
    NeutralDefectFormationEnergyRequest,
    NeutralDefectFormationEnergyResult,
)


@dataclass(frozen=True, slots=True)
class PwDftNeutralDefectFormationEnergyAction:
    """Require plane-wave DFT evidence, then delegate neutral arithmetic."""

    def evaluate(
        self, request: NeutralDefectFormationEnergyRequest
    ) -> NeutralDefectFormationEnergyResult:
        """Evaluate a DFT-qualified neutral formation energy."""
        if type(request) is not NeutralDefectFormationEnergyRequest:
            raise TypeError("request must be NeutralDefectFormationEnergyRequest")
        evidence = (
            request.defect,
            request.pristine,
            *(value.evidence for value in request.chemical_potentials),
        )
        if any(value.method_id != "plane-wave-dft" for value in evidence):
            raise ValueError("DFT formation energy requires plane-wave-dft evidence")
        return NeutralDefectFormationEnergyAction().evaluate(request)
