"""Typed adaptation of reported Wannier90 localization observations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise
from typing import cast

import numpy as np
import numpy.typing as npt
from physkit.units.quantities import (
    MatrixQuantity,
    ModelSystemUnit,
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)

from ._parsing import BoundedParser, decode_text, parse_fortran_real

_REAL_TOKEN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90LocalizationData:
    """Retain final centers, spreads, standard Omega terms, and iterations."""

    centers: MatrixQuantity
    spreads: VectorQuantity
    omega_invariant: ScalarQuantity
    omega_diagonal: ScalarQuantity
    omega_off_diagonal: ScalarQuantity
    omega_total: ScalarQuantity
    source_length_unit_label: str
    reported_wannierisation_iterations: tuple[int, ...]
    last_reported_wannierisation_iteration: int

    def __post_init__(self) -> None:
        if type(self.centers) is not MatrixQuantity:
            raise TypeError("centers must be MatrixQuantity")
        if self.centers.magnitude.ndim != 2 or self.centers.magnitude.shape[1] != 3:
            raise ValueError("centers must have shape (wannier_count, 3)")
        if type(self.spreads) is not VectorQuantity:
            raise TypeError("spreads must be VectorQuantity")
        if self.spreads.magnitude.size != self.centers.magnitude.shape[0]:
            raise ValueError("one spread is required per center")
        expected_squared_unit: ModelSystemUnit = (
            Unitless()
            if isinstance(self.centers.unit, Unitless)
            else PhysicalUnit(
                f"({cast(PhysicalUnit, self.centers.unit).expression}) ** 2"
            )
        )
        if self.spreads.unit != expected_squared_unit:
            raise ValueError("spread unit must be the square of the center unit")
        for name, value in (
            ("omega_invariant", self.omega_invariant),
            ("omega_diagonal", self.omega_diagonal),
            ("omega_off_diagonal", self.omega_off_diagonal),
            ("omega_total", self.omega_total),
        ):
            if type(value) is not ScalarQuantity:
                raise TypeError(f"{name} must be ScalarQuantity")
            if value.unit != self.spreads.unit:
                raise ValueError(f"{name} must use the spread unit")
            if value.magnitude < 0.0:
                raise ValueError(f"{name} must be nonnegative")
        if np.any(self.spreads.magnitude < 0.0):
            raise ValueError("spreads must be nonnegative")
        if type(self.source_length_unit_label) is not str or not (
            self.source_length_unit_label
        ):
            raise ValueError("source_length_unit_label must be a nonempty str")
        iterations = self.reported_wannierisation_iterations
        if (
            not isinstance(iterations, tuple)
            or not iterations
            or any(type(value) is not int or value < 0 for value in iterations)
        ):
            raise ValueError("reported iterations must be a nonempty integer tuple")
        if any(first >= second for first, second in pairwise(iterations)):
            raise ValueError("reported iterations must be strictly increasing")
        if type(self.last_reported_wannierisation_iteration) is not int:
            raise TypeError("last reported iteration must be a built-in int")
        if self.last_reported_wannierisation_iteration != iterations[-1]:
            raise ValueError(
                "last reported iteration must equal the final inventory item"
            )

    @property
    def wannier_count(self) -> int:
        return int(self.spreads.magnitude.size)


class Wannier90LocalizationParser(BoundedParser):
    """Parse standard (non-selective) final localization data from ``.wout``."""

    _CENTER_PATTERN = re.compile(
        rf"WF centre and spread\s+(\d+)\s+\(\s*"
        rf"({_REAL_TOKEN}),\s*({_REAL_TOKEN}),\s*({_REAL_TOKEN})\s*\)\s*"
        rf"({_REAL_TOKEN})"
    )
    _ITERATION_PATTERN = re.compile(r"^\s*(\d+)\s+.*<-- CONV\s*$")
    _CYCLE_PATTERN = re.compile(r"^\s*Cycle:\s*(\d+)\s*$")
    _UNIT_PATTERN = re.compile(r"Length Unit\s*:\s*([A-Za-z]+)")
    _UNIT_EXPRESSIONS = {"Ang": "angstrom", "Bohr": "bohr"}

    def execute(
        self, payload: bytes, length_unit: ModelSystemUnit
    ) -> Wannier90LocalizationData:
        """Return reported final-state observations without a convergence claim."""
        text = decode_text(payload, "wout", self.limits)
        lines = text.splitlines()
        if len(lines) > self.limits.maximum_records:
            raise ValueError("wout line count exceeds maximum_records")
        unit_matches = self._UNIT_PATTERN.findall(text)
        if not unit_matches:
            raise ValueError("wout payload lacks a Length Unit label")
        if len(set(unit_matches)) != 1:
            raise ValueError("wout payload contains contradictory Length Unit labels")
        source_label = unit_matches[0]
        try:
            expected_unit = PhysicalUnit(self._UNIT_EXPRESSIONS[source_label])
        except KeyError as error:
            raise ValueError(
                f"unsupported wout Length Unit label: {source_label}"
            ) from error
        if length_unit != expected_unit:
            raise ValueError(
                "caller length_unit contradicts the wout Length Unit label"
            )

        final_positions = [
            index for index, line in enumerate(lines) if line.strip() == "Final State"
        ]
        if len(final_positions) != 1:
            raise ValueError("wout payload must contain exactly one Final State")
        final_index = final_positions[0]
        final_text = "\n".join(lines[final_index:])
        if re.search(r"Omega\s+(?:IOD(?:_C)?|Rest|Total_C)\b", final_text):
            raise ValueError("selective-localization Omega variants are unsupported")

        reported_iterations: list[int] = []
        current_wf_indices: list[int] | None = None
        expected_iteration: int | None = None
        for line in lines[:final_index]:
            stripped = line.strip()
            if stripped == "Initial State":
                current_wf_indices = []
                expected_iteration = 0
                continue
            cycle_match = self._CYCLE_PATTERN.match(line)
            if cycle_match is not None:
                current_wf_indices = []
                expected_iteration = int(cycle_match.group(1))
                continue
            center_match = self._CENTER_PATTERN.search(line)
            if center_match is not None and current_wf_indices is not None:
                current_wf_indices.append(int(center_match.group(1)))
                continue
            iteration_match = self._ITERATION_PATTERN.match(line)
            if iteration_match is None:
                continue
            iteration = int(iteration_match.group(1))
            if expected_iteration is None or iteration != expected_iteration:
                raise ValueError("wout iteration record lacks its matching state block")
            self._require_ordered_wf_indices(current_wf_indices, "iteration")
            reported_iterations.append(iteration)
            current_wf_indices = None
            expected_iteration = None
        if not reported_iterations:
            raise ValueError("wout payload lacks reported Wannierisation iterations")
        if any(first >= second for first, second in pairwise(reported_iterations)):
            raise ValueError("reported Wannierisation iterations are not ordered")

        center_matches = tuple(self._CENTER_PATTERN.finditer(final_text))
        if not center_matches:
            raise ValueError("wout final state lacks centers and spreads")
        final_wf_indices = [int(match.group(1)) for match in center_matches]
        self._require_ordered_wf_indices(final_wf_indices, "final state")
        if len(center_matches) > self.limits.maximum_dimension:
            raise ValueError("wannier_count exceeds maximum_dimension")
        centers: npt.NDArray[np.float64] = np.asarray(
            [
                [
                    parse_fortran_real(match.group(index), "WF center")
                    for index in (2, 3, 4)
                ]
                for match in center_matches
            ],
            dtype=np.float64,
        )
        spreads: npt.NDArray[np.float64] = np.asarray(
            [
                parse_fortran_real(match.group(5), "WF spread")
                for match in center_matches
            ],
            dtype=np.float64,
        )
        squared_unit = PhysicalUnit(f"({length_unit.expression}) ** 2")
        omega_values: list[float] = []
        for label in ("Omega I", "Omega D", "Omega OD", "Omega Total"):
            matches = re.findall(rf"{label}\s*=\s*({_REAL_TOKEN})", final_text)
            if len(matches) != 1:
                raise ValueError(f"wout final state must contain exactly one {label}")
            omega_values.append(parse_fortran_real(matches[0], label))
        return Wannier90LocalizationData(
            MatrixQuantity(centers, length_unit),
            VectorQuantity(spreads, squared_unit),
            ScalarQuantity(omega_values[0], squared_unit),
            ScalarQuantity(omega_values[1], squared_unit),
            ScalarQuantity(omega_values[2], squared_unit),
            ScalarQuantity(omega_values[3], squared_unit),
            source_label,
            tuple(reported_iterations),
            reported_iterations[-1],
        )

    @staticmethod
    def _require_ordered_wf_indices(indices: list[int] | None, label: str) -> None:
        if not indices:
            raise ValueError(f"wout {label} lacks WF centre and spread records")
        if indices != list(range(1, len(indices) + 1)):
            raise ValueError(
                f"wout {label} WF indices must be ordered, unique, and one-based"
            )
