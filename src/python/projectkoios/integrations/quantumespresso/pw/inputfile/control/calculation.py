"""Typed Quantum ESPRESSO ``calculation`` selection."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import StrEnum

from projectkoios.integrations.quantumespresso.pw.inputfile.base import (
    QeControlCard,
)


class QeCalculationEnum(StrEnum):
    """Represent documented values of the QE ``calculation`` variable."""

    scf = "scf"
    nscf = "nscf"
    bands = "bands"
    relax = "relax"
    md = "md"
    vc_relax = "vc-relax"
    vc_md = "vc-md"


class QeCalculationCard(QeControlCard):
    """Represent one typed ``calculation`` assignment in ``&CONTROL``."""

    __slots__ = ("calculation",)

    calculation: QeCalculationEnum

    def __init__(
        self,
        calculation: QeCalculationEnum = QeCalculationEnum.scf,
    ) -> None:
        if type(calculation) is not QeCalculationEnum:
            raise TypeError("calculation must be a QeCalculationEnum")
        QeControlCard.__init__(
            self,
            lines=(f"calculation = '{calculation.value}'",),
        )
        object.__setattr__(self, "calculation", calculation)

    def __setattr__(self, name: str, value: object) -> None:
        raise FrozenInstanceError(f"cannot assign to field {name!r}")
