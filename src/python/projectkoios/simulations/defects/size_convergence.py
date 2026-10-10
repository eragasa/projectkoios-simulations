"""Method-neutral matched finite-supercell defect-energy differences."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.simulations.defects.compatibility import DefectEnergyCompatibility
from projectkoios.simulations.defects.energy import (
    DefectEnergyEvidence,
    DefectEnergyRole,
)
from projectkoios.simulations.defects.formation_energy import ElementCountDelta


@dataclass(frozen=True, slots=True)
class DefectSupercellEnergyPair:
    """Bind matched pristine and defect energies for one supercell size."""

    pristine: DefectEnergyEvidence
    defect: DefectEnergyEvidence
    atom_count_deltas: tuple[ElementCountDelta, ...]

    def __post_init__(self) -> None:
        if type(self.pristine) is not DefectEnergyEvidence:
            raise TypeError("pristine must be DefectEnergyEvidence")
        if self.pristine.role is not DefectEnergyRole.PRISTINE:
            raise ValueError("pristine evidence must have the pristine role")
        if type(self.defect) is not DefectEnergyEvidence:
            raise TypeError("defect must be DefectEnergyEvidence")
        if self.defect.role not in {
            DefectEnergyRole.DEFECT,
            DefectEnergyRole.IDEAL_DEFECT,
            DefectEnergyRole.ION_RELAXED_DEFECT,
            DefectEnergyRole.FULLY_RELAXED_DEFECT,
        }:
            raise ValueError("defect evidence must have a defect role")
        if type(self.atom_count_deltas) is not tuple or not self.atom_count_deltas:
            raise ValueError("atom_count_deltas must be a nonempty tuple")
        if any(
            type(value) is not ElementCountDelta for value in self.atom_count_deltas
        ):
            raise TypeError("atom_count_deltas must contain ElementCountDelta values")


@dataclass(frozen=True, slots=True)
class MatchedSizeConvergenceRequest:
    """Declare two composition-matched supercell energy pairs."""

    smaller: DefectSupercellEnergyPair
    larger: DefectSupercellEnergyPair
    compatibility: DefectEnergyCompatibility

    def __post_init__(self) -> None:
        if type(self.smaller) is not DefectSupercellEnergyPair:
            raise TypeError("smaller must be DefectSupercellEnergyPair")
        if type(self.larger) is not DefectSupercellEnergyPair:
            raise TypeError("larger must be DefectSupercellEnergyPair")
        if self.smaller.atom_count_deltas != self.larger.atom_count_deltas:
            raise ValueError(
                "size-convergence pairs must have identical composition deltas"
            )
        if self.smaller.pristine.atom_count >= self.larger.pristine.atom_count:
            raise ValueError("smaller pair must have fewer pristine atoms than larger")
        if type(self.compatibility) is not DefectEnergyCompatibility:
            raise TypeError("compatibility must be DefectEnergyCompatibility")


@dataclass(frozen=True, slots=True)
class MatchedSizeConvergenceResult:
    """Retain the matched energy change from smaller to larger supercell."""

    smaller_atom_count: int
    larger_atom_count: int
    smaller_defect_minus_pristine_ev: float
    larger_defect_minus_pristine_ev: float
    larger_minus_smaller_ev: float
    compatibility_qualification_id: str

    def __post_init__(self) -> None:
        if (
            type(self.smaller_atom_count) is not int
            or type(self.larger_atom_count) is not int
            or self.smaller_atom_count <= 0
            or self.larger_atom_count <= self.smaller_atom_count
        ):
            raise ValueError(
                "size-convergence atom counts must be positive and increasing"
            )
        if any(
            type(value) is not float or not math.isfinite(value)
            for value in (
                self.smaller_defect_minus_pristine_ev,
                self.larger_defect_minus_pristine_ev,
                self.larger_minus_smaller_ev,
            )
        ):
            raise ValueError("size-convergence energies must be finite floats")
        expected = (
            self.larger_defect_minus_pristine_ev - self.smaller_defect_minus_pristine_ev
        )
        if not math.isclose(
            self.larger_minus_smaller_ev,
            expected,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("larger_minus_smaller_ev must equal retained pair terms")
        if (
            type(self.compatibility_qualification_id) is not str
            or not self.compatibility_qualification_id
        ):
            raise ValueError("compatibility_qualification_id must be nonempty")


@dataclass(frozen=True, slots=True)
class MatchedSizeConvergenceAction:
    """Evaluate matched finite-supercell energy differences."""

    def evaluate(
        self, request: MatchedSizeConvergenceRequest
    ) -> MatchedSizeConvergenceResult:
        """Return a chemical-potential-cancelling matched difference."""
        if type(request) is not MatchedSizeConvergenceRequest:
            raise TypeError("request must be MatchedSizeConvergenceRequest")
        evidence = (
            request.smaller.defect,
            request.smaller.pristine,
            request.larger.defect,
            request.larger.pristine,
        )
        request.compatibility.require(evidence)
        smaller = request.smaller.defect.energy_ev - request.smaller.pristine.energy_ev
        larger = request.larger.defect.energy_ev - request.larger.pristine.energy_ev
        return MatchedSizeConvergenceResult(
            smaller_atom_count=request.smaller.pristine.atom_count,
            larger_atom_count=request.larger.pristine.atom_count,
            smaller_defect_minus_pristine_ev=smaller,
            larger_defect_minus_pristine_ev=larger,
            larger_minus_smaller_ev=larger - smaller,
            compatibility_qualification_id=request.compatibility.qualification_id,
        )
