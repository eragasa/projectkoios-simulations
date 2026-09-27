"""Shared bounded primitives for caller-supplied Wannier90 text."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_FORTRAN_REAL = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?$")


@dataclass(frozen=True, slots=True)
class Wannier90ParserLimits:
    """Bound parser work before allocation.

    ``maximum_records`` bounds scalar or complex numeric records after dimensions
    are multiplied. ``maximum_dimension`` bounds every individual declared or
    inferred dimension. These limits are software resource guards, not scientific
    acceptance criteria.
    """

    maximum_payload_bytes: int = 64 * 1024 * 1024
    maximum_dimension: int = 1_000_000
    maximum_records: int = 10_000_000

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_payload_bytes", self.maximum_payload_bytes),
            ("maximum_dimension", self.maximum_dimension),
            ("maximum_records", self.maximum_records),
        ):
            if type(value) is not int:
                raise TypeError(f"{name} must be a built-in int")
            if value <= 0:
                raise ValueError(f"{name} must be positive")


DEFAULT_LIMITS = Wannier90ParserLimits()


def decode_text(payload: bytes, label: str, limits: Wannier90ParserLimits) -> str:
    """Validate byte size and decode one UTF-8 payload with normalized newlines."""
    if type(payload) is not bytes:
        raise TypeError("payload must be bytes")
    if len(payload) > limits.maximum_payload_bytes:
        raise ValueError(
            f"{label} payload exceeds maximum_payload_bytes "
            f"({limits.maximum_payload_bytes})"
        )
    try:
        return payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} payload must be valid UTF-8") from error


def parse_fortran_real(token: str, label: str) -> float:
    """Parse one finite Fortran real using E/e or D/d exponent syntax."""
    if _FORTRAN_REAL.fullmatch(token) is None:
        raise ValueError(f"{label} must be a finite Fortran real")
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite Fortran real")
    return value


def positive_dimension(value: int, name: str, limits: Wannier90ParserLimits) -> int:
    """Validate one positive declared or inferred dimension."""
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    if value > limits.maximum_dimension:
        raise ValueError(
            f"{name} exceeds maximum_dimension ({limits.maximum_dimension})"
        )
    return value


def checked_product(
    factors: tuple[int, ...], label: str, limits: Wannier90ParserLimits
) -> int:
    """Multiply positive dimensions without crossing the configured record bound."""
    product = 1
    for factor in factors:
        if factor <= 0:
            raise ValueError(f"{label} dimensions must be positive")
        if product > limits.maximum_records // factor:
            raise ValueError(
                f"{label} record count exceeds maximum_records "
                f"({limits.maximum_records})"
            )
        product *= factor
    return product


class BoundedParser:
    """Store immutable limits for a concrete parser."""

    __slots__ = ("_limits",)

    def __init__(self, limits: Wannier90ParserLimits = DEFAULT_LIMITS) -> None:
        if type(limits) is not Wannier90ParserLimits:
            raise TypeError("limits must be Wannier90ParserLimits")
        self._limits = limits

    @property
    def limits(self) -> Wannier90ParserLimits:
        """Return the configured resource limits."""
        return self._limits
