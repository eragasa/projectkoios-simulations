"""Typed adaptation of final Wannier90 localization observations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

import numpy as np
from physkit.units.quantities import (
    MatrixQuantity,
    ModelSystemUnit,
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)


@dataclass(frozen=True, slots=True, eq=False)
class Wannier90LocalizationData:
    """Retain final native centers, spreads, spread decomposition, and iteration."""

    centers: MatrixQuantity
    spreads: VectorQuantity
    omega_invariant: ScalarQuantity
    omega_diagonal: ScalarQuantity
    omega_off_diagonal: ScalarQuantity
    omega_total: ScalarQuantity
    maximum_converged_iteration: int

    def __post_init__(self) -> None:
        """Validate center/spread dimensions and the native spread decomposition."""
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
        squared_unit = self.spreads.unit
        for name, value in (
            ("omega_invariant", self.omega_invariant),
            ("omega_diagonal", self.omega_diagonal),
            ("omega_off_diagonal", self.omega_off_diagonal),
            ("omega_total", self.omega_total),
        ):
            if type(value) is not ScalarQuantity:
                raise TypeError(f"{name} must be ScalarQuantity")
            if value.unit != squared_unit:
                raise ValueError(f"{name} must use the spread unit")
            if value.magnitude < 0.0:
                raise ValueError(f"{name} must be nonnegative")
        if np.any(self.spreads.magnitude < 0.0):
            raise ValueError("spreads must be nonnegative")
        if type(self.maximum_converged_iteration) is not int:
            raise TypeError("maximum_converged_iteration must be a built-in int")
        if self.maximum_converged_iteration < 0:
            raise ValueError("maximum_converged_iteration must be nonnegative")

    @property
    def wannier_count(self) -> int:
        """Return the number of final localized functions."""
        return int(self.spreads.magnitude.size)


class Wannier90LocalizationParser:
    """Parse final localization observations from one UTF-8 ``.wout`` payload."""

    __slots__ = ()

    _CENTER_PATTERN = re.compile(
        r"WF centre and spread\s+\d+\s+\(\s*"
        r"([-+0-9.Ee]+),\s*([-+0-9.Ee]+),\s*([-+0-9.Ee]+)\s*\)\s*"
        r"([-+0-9.Ee]+)"
    )
    _ITERATION_PATTERN = re.compile(r"^\s*(\d+)\s+[-+0-9.Ee]+.*<-- CONV$", re.M)

    def execute(
        self, payload: bytes, length_unit: ModelSystemUnit
    ) -> Wannier90LocalizationData:
        """Return the final-state observations and maximum converged iteration."""
        if type(payload) is not bytes:
            raise TypeError("payload must be bytes")
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("wout payload must be valid UTF-8") from error
        final_index = text.rfind("Final State")
        if final_index < 0:
            raise ValueError("wout payload lacks a Final State")
        final_text = text[final_index:]
        center_matches = self._CENTER_PATTERN.findall(final_text)
        if not center_matches:
            raise ValueError("wout final state lacks centers and spreads")
        centers = np.asarray(
            [[float(value) for value in match[:3]] for match in center_matches],
            dtype=np.float64,
        )
        spreads = np.asarray(
            [float(match[3]) for match in center_matches], dtype=np.float64
        )
        squared_unit: ModelSystemUnit = (
            Unitless()
            if isinstance(length_unit, Unitless)
            else PhysicalUnit(f"({cast(PhysicalUnit, length_unit).expression}) ** 2")
        )
        omega_values: list[float] = []
        for label in ("Omega I", "Omega D", "Omega OD", "Omega Total"):
            match = re.search(rf"{label}\s+=\s+([-+0-9.Ee]+)", final_text)
            if match is None:
                raise ValueError(f"wout final state lacks {label}")
            omega_values.append(float(match.group(1)))
        iterations = [
            int(match.group(1)) for match in self._ITERATION_PATTERN.finditer(text)
        ]
        if not iterations:
            raise ValueError("wout payload lacks converged iteration records")
        return Wannier90LocalizationData(
            MatrixQuantity(centers, length_unit),
            VectorQuantity(spreads, squared_unit),
            ScalarQuantity(omega_values[0], squared_unit),
            ScalarQuantity(omega_values[1], squared_unit),
            ScalarQuantity(omega_values[2], squared_unit),
            ScalarQuantity(omega_values[3], squared_unit),
            max(iterations),
        )
