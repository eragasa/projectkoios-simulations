"""Native ``&IONS`` values consumed by ``pw.x`` calculation modes."""

from __future__ import annotations

from enum import StrEnum


class QeIonDynamics(StrEnum):
    """Represent maintained ``&IONS.ion_dynamics`` values."""

    BFGS = "bfgs"
    DAMP = "damp"
    FIRE = "fire"
