"""Select Appendix-A cases within caller-declared Bravais lattices."""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.lattice import (
    SetyawanCurtaroloLattice,
    _appendix_a_cases_for_bravais_lattice,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.model import (
    SetyawanCurtaroloBravaisLattice,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SetyawanCurtaroloAppendixACaseSelectionRequest(DataObject):
    """Request Appendix-A case selection within one declared Bravais lattice."""

    bravais_lattice: SetyawanCurtaroloBravaisLattice
    a_angstrom: float
    b_angstrom: float
    c_angstrom: float
    alpha_degrees: float = 90.0
    beta_degrees: float = 90.0
    gamma_degrees: float = 90.0

    def __post_init__(self) -> None:
        if type(self.bravais_lattice) is not SetyawanCurtaroloBravaisLattice:
            raise TypeError("bravais_lattice must be a SetyawanCurtaroloBravaisLattice")
        for label, value in (
            ("a_angstrom", self.a_angstrom),
            ("b_angstrom", self.b_angstrom),
            ("c_angstrom", self.c_angstrom),
        ):
            if type(value) is not float:
                raise TypeError(f"{label} must be a built-in float")
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")
        for label, value in (
            ("alpha_degrees", self.alpha_degrees),
            ("beta_degrees", self.beta_degrees),
            ("gamma_degrees", self.gamma_degrees),
        ):
            if type(value) is not float:
                raise TypeError(f"{label} must be a built-in float")
            if not math.isfinite(value) or not 0.0 < value < 180.0:
                raise ValueError(f"{label} must be finite and between 0 and 180")


@dataclass(frozen=True, slots=True, kw_only=True)
class SetyawanCurtaroloAppendixACaseSelectionResult(ResultsObject):
    """Correlate one selection request with its selected Appendix-A case."""

    request: SetyawanCurtaroloAppendixACaseSelectionRequest
    lattice: SetyawanCurtaroloLattice

    def __post_init__(self) -> None:
        if type(self.request) is not SetyawanCurtaroloAppendixACaseSelectionRequest:
            raise TypeError(
                "request must be a SetyawanCurtaroloAppendixACaseSelectionRequest"
            )
        if type(self.lattice) is not SetyawanCurtaroloLattice:
            raise TypeError("lattice must be a SetyawanCurtaroloLattice")
        if self.lattice.bravais_lattice is not self.request.bravais_lattice:
            raise ValueError(
                "selected Appendix-A case must match the requested Bravais lattice"
            )
        for field_name in (
            "a_angstrom",
            "b_angstrom",
            "c_angstrom",
            "alpha_degrees",
            "beta_degrees",
            "gamma_degrees",
        ):
            if getattr(self.lattice, field_name) != getattr(self.request, field_name):
                raise ValueError(
                    "selected Appendix-A case metrics must exactly match the request"
                )


class SetyawanCurtaroloAppendixACaseSelector(
    DataObjectActionizer[
        SetyawanCurtaroloAppendixACaseSelectionRequest,
        SetyawanCurtaroloAppendixACaseSelectionResult,
    ]
):
    """Select the unique Appendix-A case matching declared metric data."""

    __slots__ = ()

    def action(
        self,
        *,
        request: SetyawanCurtaroloAppendixACaseSelectionRequest,
    ) -> SetyawanCurtaroloAppendixACaseSelectionResult:
        """Return the correlated unique selection or reject the declaration."""
        if type(request) is not SetyawanCurtaroloAppendixACaseSelectionRequest:
            raise TypeError(
                "request must be a SetyawanCurtaroloAppendixACaseSelectionRequest"
            )
        matches: list[SetyawanCurtaroloLattice] = []
        failures: list[str] = []
        for appendix_a_case in _appendix_a_cases_for_bravais_lattice(
            request.bravais_lattice
        ):
            try:
                matches.append(
                    SetyawanCurtaroloLattice(
                        appendix_a_case=appendix_a_case,
                        a_angstrom=request.a_angstrom,
                        b_angstrom=request.b_angstrom,
                        c_angstrom=request.c_angstrom,
                        alpha_degrees=request.alpha_degrees,
                        beta_degrees=request.beta_degrees,
                        gamma_degrees=request.gamma_degrees,
                    )
                )
            except ValueError as error:
                failures.append(f"{appendix_a_case.value}: {error}")
        if len(matches) == 1:
            return SetyawanCurtaroloAppendixACaseSelectionResult(
                request=request,
                lattice=matches[0],
            )
        if not matches:
            detail = "; ".join(failures)
            raise ValueError(
                "metrics do not select a "
                f"{request.bravais_lattice.value} Appendix-A case: {detail}"
            )
        names = ", ".join(match.appendix_a_case.value for match in matches)
        raise ValueError(
            "metrics ambiguously select "
            f"{request.bravais_lattice.value} Appendix-A cases: {names}"
        )
