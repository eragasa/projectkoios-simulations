"""Native ``&CELL`` values consumed by variable-cell ``pw.x`` modes."""

from __future__ import annotations

from enum import StrEnum


class QeCellDynamics(StrEnum):
    """Represent documented ``&CELL.cell_dynamics`` values."""

    NONE = "none"
    STEEPEST_DESCENT = "sd"
    DAMPED_PARRINELLO_RAHMAN = "damp-pr"
    DAMPED_WENTZCOVITCH = "damp-w"
    BFGS = "bfgs"

    @property
    def implemented(self) -> bool:
        """Return whether QE 7.5 implements the documented value."""
        return self is not QeCellDynamics.STEEPEST_DESCENT

    def require_implemented(self) -> None:
        """Reject values documented but not implemented by QE 7.5."""
        if not self.implemented:
            raise NotImplementedError(
                f"cell_dynamics={self.value!r} is not implemented by QE 7.5"
            )


class QeCellDegreesOfFreedom(StrEnum):
    """Represent documented base values of ``&CELL.cell_dofree``."""

    ALL = "all"
    IBRAV = "ibrav"
    A = "a"
    B = "b"
    C = "c"
    FIX_A = "fixa"
    FIX_B = "fixb"
    FIX_C = "fixc"
    X = "x"
    Y = "y"
    Z = "z"
    XY = "xy"
    XZ = "xz"
    YZ = "yz"
    XYZ = "xyz"
    SHAPE = "shape"
    VOLUME = "volume"
    TWO_DIMENSIONAL_XY = "2Dxy"
    TWO_DIMENSIONAL_SHAPE = "2Dshape"
    EPITAXIAL_AB = "epitaxial_ab"
    EPITAXIAL_AC = "epitaxial_ac"
    EPITAXIAL_BC = "epitaxial_bc"
