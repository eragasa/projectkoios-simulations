"""Standard cells and declared Appendix-A case validation.

This module implements the direct-cell and reciprocal-angle mathematics in
Appendix A. It validates a declared case; it does not classify or infer
symmetry, centering, or a Bravais lattice from an atomic structure.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.simulations.dft.pw.bands import BandVector3
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010._linear_algebra import (
    _angle_degrees,
    _determinant,
    _reciprocal_vectors,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.model import (
    SetyawanCurtaroloAppendixACase,
    SetyawanCurtaroloBravaisLattice,
)
from projectkoios.simulations.dft.pw.simulation import PwMatrix3

_METRIC_TOLERANCE = 1.0e-10
_ANGLE_TOLERANCE_DEGREES = 1.0e-8


@dataclass(frozen=True, slots=True)
class SetyawanCurtaroloLattice(DataObject):
    """Retain declared conventional metrics for one Appendix-A case.

    Angles follow the crystallographic convention: ``alpha`` is between the
    second and third vectors, ``beta`` between the first and third, and
    ``gamma`` between the first and second. For RHL the paper defines a
    primitive rhombohedral lattice directly, so all three lengths and angles
    must be equal.

    This record validates a declared case but deliberately does not infer
    crystal symmetry or standardize an arbitrary structure.
    """

    appendix_a_case: SetyawanCurtaroloAppendixACase
    a_angstrom: float
    b_angstrom: float
    c_angstrom: float
    alpha_degrees: float = 90.0
    beta_degrees: float = 90.0
    gamma_degrees: float = 90.0

    def __post_init__(self) -> None:
        if type(self.appendix_a_case) is not SetyawanCurtaroloAppendixACase:
            raise TypeError("appendix_a_case must be a SetyawanCurtaroloAppendixACase")
        for label, value in (
            ("a_angstrom", self.a_angstrom),
            ("b_angstrom", self.b_angstrom),
            ("c_angstrom", self.c_angstrom),
        ):
            if type(value) is not float or not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{label} must be positive and finite")
        for label, value in (
            ("alpha_degrees", self.alpha_degrees),
            ("beta_degrees", self.beta_degrees),
            ("gamma_degrees", self.gamma_degrees),
        ):
            if (
                type(value) is not float
                or not math.isfinite(value)
                or not 0.0 < value < 180.0
            ):
                raise ValueError(f"{label} must be finite and between 0 and 180")
        self._validate_declared_appendix_a_case()
        if abs(_determinant(self.standard_primitive_lattice_vectors_angstrom)) <= 0.0:
            raise ValueError("standard primitive lattice must have nonzero volume")

    @property
    def bravais_lattice(self) -> SetyawanCurtaroloBravaisLattice:
        """Return the declared case's unique Bravais-lattice identity."""
        for bravais_lattice in SetyawanCurtaroloBravaisLattice:
            if self.appendix_a_case in _appendix_a_cases_for_bravais_lattice(
                bravais_lattice
            ):
                return bravais_lattice
        raise AssertionError(f"unmapped Appendix-A case: {self.appendix_a_case.value}")

    @property
    def standard_conventional_lattice_vectors_angstrom(self) -> PwMatrix3:
        """Return the paper's source-ordered conventional direct lattice."""
        a = self.a_angstrom
        b = self.b_angstrom
        c = self.c_angstrom
        alpha = math.radians(self.alpha_degrees)
        appendix_a_case = self.appendix_a_case
        if appendix_a_case is SetyawanCurtaroloAppendixACase.hex:
            return (
                (a / 2.0, -a * math.sqrt(3.0) / 2.0, 0.0),
                (a / 2.0, a * math.sqrt(3.0) / 2.0, 0.0),
                (0.0, 0.0, c),
            )
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.rhl1,
            SetyawanCurtaroloAppendixACase.rhl2,
        }:
            return self.standard_primitive_lattice_vectors_angstrom
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.mcl,
            SetyawanCurtaroloAppendixACase.mclc1,
            SetyawanCurtaroloAppendixACase.mclc2,
            SetyawanCurtaroloAppendixACase.mclc3,
            SetyawanCurtaroloAppendixACase.mclc4,
            SetyawanCurtaroloAppendixACase.mclc5,
        }:
            return (
                (a, 0.0, 0.0),
                (0.0, b, 0.0),
                (0.0, c * math.cos(alpha), c * math.sin(alpha)),
            )
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.tri1a,
            SetyawanCurtaroloAppendixACase.tri1b,
            SetyawanCurtaroloAppendixACase.tri2a,
            SetyawanCurtaroloAppendixACase.tri2b,
        }:
            return _triclinic_lattice(self)
        return ((a, 0.0, 0.0), (0.0, b, 0.0), (0.0, 0.0, c))

    @property
    def standard_primitive_lattice_vectors_angstrom(self) -> PwMatrix3:
        """Return the paper's source-ordered primitive direct lattice."""
        a = self.a_angstrom
        b = self.b_angstrom
        c = self.c_angstrom
        alpha = math.radians(self.alpha_degrees)
        appendix_a_case = self.appendix_a_case

        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.cub,
            SetyawanCurtaroloAppendixACase.tet,
            SetyawanCurtaroloAppendixACase.orc,
        }:
            return ((a, 0.0, 0.0), (0.0, b, 0.0), (0.0, 0.0, c))
        if appendix_a_case is SetyawanCurtaroloAppendixACase.fcc or appendix_a_case in {
            SetyawanCurtaroloAppendixACase.orcf1,
            SetyawanCurtaroloAppendixACase.orcf2,
            SetyawanCurtaroloAppendixACase.orcf3,
        }:
            return (
                (0.0, b / 2.0, c / 2.0),
                (a / 2.0, 0.0, c / 2.0),
                (a / 2.0, b / 2.0, 0.0),
            )
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.bcc,
            SetyawanCurtaroloAppendixACase.bct1,
            SetyawanCurtaroloAppendixACase.bct2,
            SetyawanCurtaroloAppendixACase.orci,
        }:
            return (
                (-a / 2.0, b / 2.0, c / 2.0),
                (a / 2.0, -b / 2.0, c / 2.0),
                (a / 2.0, b / 2.0, -c / 2.0),
            )
        if appendix_a_case is SetyawanCurtaroloAppendixACase.orcc:
            return (
                (a / 2.0, -b / 2.0, 0.0),
                (a / 2.0, b / 2.0, 0.0),
                (0.0, 0.0, c),
            )
        if appendix_a_case is SetyawanCurtaroloAppendixACase.hex:
            return (
                (a / 2.0, -a * math.sqrt(3.0) / 2.0, 0.0),
                (a / 2.0, a * math.sqrt(3.0) / 2.0, 0.0),
                (0.0, 0.0, c),
            )
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.rhl1,
            SetyawanCurtaroloAppendixACase.rhl2,
        }:
            half_alpha = alpha / 2.0
            cos_half = math.cos(half_alpha)
            cos_alpha = math.cos(alpha)
            z_square = 1.0 - cos_alpha**2 / cos_half**2
            if z_square <= 0.0:
                raise ValueError("rhombohedral metrics do not define a real cell")
            return (
                (a * cos_half, -a * math.sin(half_alpha), 0.0),
                (a * cos_half, a * math.sin(half_alpha), 0.0),
                (a * cos_alpha / cos_half, 0.0, a * math.sqrt(z_square)),
            )
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mcl:
            return (
                (a, 0.0, 0.0),
                (0.0, b, 0.0),
                (0.0, c * math.cos(alpha), c * math.sin(alpha)),
            )
        if appendix_a_case in {
            SetyawanCurtaroloAppendixACase.mclc1,
            SetyawanCurtaroloAppendixACase.mclc2,
            SetyawanCurtaroloAppendixACase.mclc3,
            SetyawanCurtaroloAppendixACase.mclc4,
            SetyawanCurtaroloAppendixACase.mclc5,
        }:
            return (
                (a / 2.0, b / 2.0, 0.0),
                (-a / 2.0, b / 2.0, 0.0),
                (0.0, c * math.cos(alpha), c * math.sin(alpha)),
            )
        return _triclinic_lattice(self)

    @property
    def reciprocal_angles_degrees(self) -> BandVector3:
        """Return ``(k_alpha, k_beta, k_gamma)`` for the primitive lattice."""
        b1, b2, b3 = _reciprocal_vectors(
            self.standard_primitive_lattice_vectors_angstrom
        )
        return (
            _angle_degrees(b2, b3),
            _angle_degrees(b1, b3),
            _angle_degrees(b1, b2),
        )

    def _validate_declared_appendix_a_case(self) -> None:
        appendix_a_case = self.appendix_a_case
        a = self.a_angstrom
        b = self.b_angstrom
        c = self.c_angstrom
        alpha = self.alpha_degrees
        beta = self.beta_degrees
        gamma = self.gamma_degrees

        cubic = {
            SetyawanCurtaroloAppendixACase.cub,
            SetyawanCurtaroloAppendixACase.fcc,
            SetyawanCurtaroloAppendixACase.bcc,
        }
        tetragonal = {
            SetyawanCurtaroloAppendixACase.tet,
            SetyawanCurtaroloAppendixACase.bct1,
            SetyawanCurtaroloAppendixACase.bct2,
        }
        orthorhombic = {
            SetyawanCurtaroloAppendixACase.orc,
            SetyawanCurtaroloAppendixACase.orcf1,
            SetyawanCurtaroloAppendixACase.orcf2,
            SetyawanCurtaroloAppendixACase.orcf3,
            SetyawanCurtaroloAppendixACase.orci,
            SetyawanCurtaroloAppendixACase.orcc,
        }
        monoclinic = {
            SetyawanCurtaroloAppendixACase.mcl,
            SetyawanCurtaroloAppendixACase.mclc1,
            SetyawanCurtaroloAppendixACase.mclc2,
            SetyawanCurtaroloAppendixACase.mclc3,
            SetyawanCurtaroloAppendixACase.mclc4,
            SetyawanCurtaroloAppendixACase.mclc5,
        }
        triclinic = {
            SetyawanCurtaroloAppendixACase.tri1a,
            SetyawanCurtaroloAppendixACase.tri1b,
            SetyawanCurtaroloAppendixACase.tri2a,
            SetyawanCurtaroloAppendixACase.tri2b,
        }

        if appendix_a_case in cubic:
            _require_close(a, b, "cubic a and b")
            _require_close(a, c, "cubic a and c")
            _require_right_angles(alpha, beta, gamma)
        elif appendix_a_case in tetragonal:
            _require_close(a, b, "tetragonal a and b")
            _require_right_angles(alpha, beta, gamma)
            if appendix_a_case is SetyawanCurtaroloAppendixACase.bct1 and not c < a:
                raise ValueError("BCT1 requires c < a")
            if appendix_a_case is SetyawanCurtaroloAppendixACase.bct2 and not c > a:
                raise ValueError("BCT2 requires c > a")
        elif appendix_a_case in orthorhombic:
            _require_right_angles(alpha, beta, gamma)
            if appendix_a_case is SetyawanCurtaroloAppendixACase.orcc:
                if not a < b:
                    raise ValueError("ORCC requires a < b")
            elif not a < b < c:
                raise ValueError(f"{appendix_a_case.value} requires a < b < c")
            if appendix_a_case in {
                SetyawanCurtaroloAppendixACase.orcf1,
                SetyawanCurtaroloAppendixACase.orcf2,
                SetyawanCurtaroloAppendixACase.orcf3,
            }:
                discriminator = 1.0 - a**2 / b**2 - a**2 / c**2
                _require_sign_for_appendix_a_case(
                    discriminator,
                    appendix_a_case,
                    SetyawanCurtaroloAppendixACase.orcf1,
                    SetyawanCurtaroloAppendixACase.orcf2,
                    SetyawanCurtaroloAppendixACase.orcf3,
                    "ORCF discriminator",
                )
        elif appendix_a_case is SetyawanCurtaroloAppendixACase.hex:
            _require_close(a, b, "hexagonal a and b")
            _require_angle(alpha, 90.0, "hexagonal alpha")
            _require_angle(beta, 90.0, "hexagonal beta")
            _require_angle(gamma, 120.0, "hexagonal gamma")
        elif appendix_a_case in {
            SetyawanCurtaroloAppendixACase.rhl1,
            SetyawanCurtaroloAppendixACase.rhl2,
        }:
            _require_close(a, b, "rhombohedral a and b")
            _require_close(a, c, "rhombohedral a and c")
            _require_angle(alpha, beta, "rhombohedral alpha and beta")
            _require_angle(alpha, gamma, "rhombohedral alpha and gamma")
            if (
                appendix_a_case is SetyawanCurtaroloAppendixACase.rhl1
                and not alpha < 90.0
            ):
                raise ValueError("RHL1 requires alpha < 90 degrees")
            if (
                appendix_a_case is SetyawanCurtaroloAppendixACase.rhl2
                and not alpha > 90.0
            ):
                raise ValueError("RHL2 requires alpha > 90 degrees")
        elif appendix_a_case in monoclinic:
            if not a <= c or not b <= c:
                raise ValueError(f"{appendix_a_case.value} requires a, b <= c")
            if not alpha < 90.0:
                raise ValueError(f"{appendix_a_case.value} requires alpha < 90 degrees")
            _require_angle(beta, 90.0, "monoclinic beta")
            _require_angle(gamma, 90.0, "monoclinic gamma")
            if appendix_a_case is not SetyawanCurtaroloAppendixACase.mcl:
                reciprocal_gamma = self.reciprocal_angles_degrees[2]
                q = b * math.cos(math.radians(alpha)) / c
                q += b**2 * math.sin(math.radians(alpha)) ** 2 / a**2
                self._validate_mclc_appendix_a_case(reciprocal_gamma, q)
        elif appendix_a_case in triclinic:
            self._validate_triclinic_appendix_a_case()
        else:  # pragma: no cover - exhaustive defensive guard
            raise ValueError(f"unsupported Appendix-A case: {appendix_a_case}")

    def _validate_mclc_appendix_a_case(
        self,
        reciprocal_gamma: float,
        q: float,
    ) -> None:
        appendix_a_case = self.appendix_a_case
        gamma_is_right = math.isclose(
            reciprocal_gamma,
            90.0,
            rel_tol=0.0,
            abs_tol=_ANGLE_TOLERANCE_DEGREES,
        )
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc1:
            if not reciprocal_gamma > 90.0 + _ANGLE_TOLERANCE_DEGREES:
                raise ValueError("MCLC1 requires reciprocal gamma > 90 degrees")
            return
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc2:
            if not gamma_is_right:
                raise ValueError("MCLC2 requires reciprocal gamma = 90 degrees")
            return
        if not reciprocal_gamma < 90.0 - _ANGLE_TOLERANCE_DEGREES:
            raise ValueError("MCLC3-5 require reciprocal gamma < 90 degrees")
        q_is_one = math.isclose(q, 1.0, rel_tol=0.0, abs_tol=_METRIC_TOLERANCE)
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc3 and not (
            q < 1.0 and not q_is_one
        ):
            raise ValueError("MCLC3 requires its metric discriminator < 1")
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc4 and not q_is_one:
            raise ValueError("MCLC4 requires its metric discriminator = 1")
        if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc5 and not (
            q > 1.0 and not q_is_one
        ):
            raise ValueError("MCLC5 requires its metric discriminator > 1")

    def _validate_triclinic_appendix_a_case(self) -> None:
        kalpha, kbeta, kgamma = self.reciprocal_angles_degrees
        appendix_a_case = self.appendix_a_case
        a_side = appendix_a_case in {
            SetyawanCurtaroloAppendixACase.tri1a,
            SetyawanCurtaroloAppendixACase.tri2a,
        }
        two = appendix_a_case in {
            SetyawanCurtaroloAppendixACase.tri2a,
            SetyawanCurtaroloAppendixACase.tri2b,
        }
        if a_side:
            if not (
                kalpha > 90.0 + _ANGLE_TOLERANCE_DEGREES
                and kbeta > 90.0 + _ANGLE_TOLERANCE_DEGREES
            ):
                raise ValueError("TRI-a requires reciprocal alpha and beta > 90")
        elif not (
            kalpha < 90.0 - _ANGLE_TOLERANCE_DEGREES
            and kbeta < 90.0 - _ANGLE_TOLERANCE_DEGREES
        ):
            raise ValueError("TRI-b requires reciprocal alpha and beta < 90")
        gamma_is_right = math.isclose(
            kgamma,
            90.0,
            rel_tol=0.0,
            abs_tol=_ANGLE_TOLERANCE_DEGREES,
        )
        if two and not gamma_is_right:
            raise ValueError("TRI2 requires reciprocal gamma = 90 degrees")
        if not two:
            if a_side and not kgamma > 90.0 + _ANGLE_TOLERANCE_DEGREES:
                raise ValueError("TRI1a requires reciprocal gamma > 90")
            if not a_side and not kgamma < 90.0 - _ANGLE_TOLERANCE_DEGREES:
                raise ValueError("TRI1b requires reciprocal gamma < 90")


def _appendix_a_cases_for_bravais_lattice(
    bravais_lattice: SetyawanCurtaroloBravaisLattice,
) -> tuple[SetyawanCurtaroloAppendixACase, ...]:
    appendix_a_case = SetyawanCurtaroloAppendixACase
    return {
        SetyawanCurtaroloBravaisLattice.cubic_primitive: (appendix_a_case.cub,),
        SetyawanCurtaroloBravaisLattice.cubic_face_centered: (appendix_a_case.fcc,),
        SetyawanCurtaroloBravaisLattice.cubic_body_centered: (appendix_a_case.bcc,),
        SetyawanCurtaroloBravaisLattice.tetragonal_primitive: (appendix_a_case.tet,),
        SetyawanCurtaroloBravaisLattice.tetragonal_body_centered: (
            appendix_a_case.bct1,
            appendix_a_case.bct2,
        ),
        SetyawanCurtaroloBravaisLattice.orthorhombic_primitive: (appendix_a_case.orc,),
        SetyawanCurtaroloBravaisLattice.orthorhombic_face_centered: (
            appendix_a_case.orcf1,
            appendix_a_case.orcf2,
            appendix_a_case.orcf3,
        ),
        SetyawanCurtaroloBravaisLattice.orthorhombic_body_centered: (
            appendix_a_case.orci,
        ),
        SetyawanCurtaroloBravaisLattice.orthorhombic_base_centered: (
            appendix_a_case.orcc,
        ),
        SetyawanCurtaroloBravaisLattice.hexagonal_primitive: (appendix_a_case.hex,),
        SetyawanCurtaroloBravaisLattice.rhombohedral: (
            appendix_a_case.rhl1,
            appendix_a_case.rhl2,
        ),
        SetyawanCurtaroloBravaisLattice.monoclinic_primitive: (appendix_a_case.mcl,),
        SetyawanCurtaroloBravaisLattice.monoclinic_base_centered: (
            appendix_a_case.mclc1,
            appendix_a_case.mclc2,
            appendix_a_case.mclc3,
            appendix_a_case.mclc4,
            appendix_a_case.mclc5,
        ),
        SetyawanCurtaroloBravaisLattice.triclinic_primitive: (
            appendix_a_case.tri1a,
            appendix_a_case.tri1b,
            appendix_a_case.tri2a,
            appendix_a_case.tri2b,
        ),
    }[bravais_lattice]


def _triclinic_lattice(lattice: SetyawanCurtaroloLattice) -> PwMatrix3:
    direct_lattice = DirectLattice3D.from_lattice_parameters(
        a=lattice.a_angstrom,
        b=lattice.b_angstrom,
        c=lattice.c_angstrom,
        alpha_degrees=lattice.alpha_degrees,
        beta_degrees=lattice.beta_degrees,
        gamma_degrees=lattice.gamma_degrees,
    )
    a1 = direct_lattice.a1
    a2 = direct_lattice.a2
    a3 = direct_lattice.a3
    return (
        (float(a1[0]), float(a1[1]), float(a1[2])),
        (float(a2[0]), float(a2[1]), float(a2[2])),
        (float(a3[0]), float(a3[1]), float(a3[2])),
    )


def _require_close(first: float, second: float, label: str) -> None:
    if not math.isclose(first, second, rel_tol=_METRIC_TOLERANCE, abs_tol=0.0):
        raise ValueError(f"{label} must be equal")


def _require_angle(actual: float, expected: float, label: str) -> None:
    if not math.isclose(
        actual,
        expected,
        rel_tol=0.0,
        abs_tol=_ANGLE_TOLERANCE_DEGREES,
    ):
        raise ValueError(f"{label} must equal {expected:g} degrees")


def _require_right_angles(alpha: float, beta: float, gamma: float) -> None:
    _require_angle(alpha, 90.0, "alpha")
    _require_angle(beta, 90.0, "beta")
    _require_angle(gamma, 90.0, "gamma")


def _require_sign_for_appendix_a_case(
    value: float,
    appendix_a_case: SetyawanCurtaroloAppendixACase,
    positive: SetyawanCurtaroloAppendixACase,
    negative: SetyawanCurtaroloAppendixACase,
    zero: SetyawanCurtaroloAppendixACase,
    label: str,
) -> None:
    is_zero = math.isclose(value, 0.0, rel_tol=0.0, abs_tol=_METRIC_TOLERANCE)
    if appendix_a_case is positive and not (value > 0.0 and not is_zero):
        raise ValueError(f"{positive.value} requires positive {label}")
    if appendix_a_case is negative and not (value < 0.0 and not is_zero):
        raise ValueError(f"{negative.value} requires negative {label}")
    if appendix_a_case is zero and not is_zero:
        raise ValueError(f"{zero.value} requires zero {label}")
