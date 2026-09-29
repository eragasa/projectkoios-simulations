"""Appendix-A special points and ordered path topology.

Functions remain in the paper's lattice order.  Parameter symbols are kept
beside the tables that use them so the implementation can be compared
directly with the cited equations rather than hidden behind a formula engine.
"""

import math

from projectkoios.simulations.dft.pw.bands import BandVector3
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.lattice import (
    SetyawanCurtaroloLattice,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010.model import (
    SetyawanCurtaroloAppendixACase,
)


def _path_data(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    appendix_a_case = lattice.appendix_a_case
    gamma = "Γ"
    p = _point

    if appendix_a_case is SetyawanCurtaroloAppendixACase.cub:
        return (
            {
                gamma: p(0, 0, 0),
                "X": p(0, 0.5, 0),
                "M": p(0.5, 0.5, 0),
                "R": p(0.5, 0.5, 0.5),
            },
            ((gamma, "X", "M", gamma, "R", "X"), ("M", "R")),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.fcc:
        return (
            {
                gamma: p(0, 0, 0),
                "K": p(3 / 8, 3 / 8, 3 / 4),
                "L": p(1 / 2, 1 / 2, 1 / 2),
                "U": p(5 / 8, 1 / 4, 5 / 8),
                "W": p(1 / 2, 1 / 4, 3 / 4),
                "X": p(1 / 2, 0, 1 / 2),
            },
            (
                (gamma, "X", "W", "K", gamma, "L", "U", "W", "L", "K"),
                ("U", "X"),
            ),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.bcc:
        return (
            {
                gamma: p(0, 0, 0),
                "H": p(1 / 2, -1 / 2, 1 / 2),
                "P": p(1 / 4, 1 / 4, 1 / 4),
                "N": p(0, 0, 1 / 2),
            },
            ((gamma, "H", "N", gamma, "P", "H"), ("P", "N")),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.tet:
        return (
            {
                gamma: p(0, 0, 0),
                "A": p(1 / 2, 1 / 2, 1 / 2),
                "M": p(1 / 2, 1 / 2, 0),
                "R": p(0, 1 / 2, 1 / 2),
                "X": p(0, 1 / 2, 0),
                "Z": p(0, 0, 1 / 2),
            },
            (
                (gamma, "X", "M", gamma, "Z", "R", "A", "Z"),
                ("X", "R"),
                ("M", "A"),
            ),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.bct1:
        eta = (1 + lattice.c_angstrom**2 / lattice.a_angstrom**2) / 4
        return (
            {
                gamma: p(0, 0, 0),
                "M": p(-1 / 2, 1 / 2, 1 / 2),
                "N": p(0, 1 / 2, 0),
                "P": p(1 / 4, 1 / 4, 1 / 4),
                "X": p(0, 0, 1 / 2),
                "Z": p(eta, eta, -eta),
                "Z₁": p(-eta, 1 - eta, eta),
            },
            (
                (gamma, "X", "M", gamma, "Z", "P", "N", "Z₁", "M"),
                ("X", "P"),
            ),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.bct2:
        eta = (1 + lattice.a_angstrom**2 / lattice.c_angstrom**2) / 4
        zeta = lattice.a_angstrom**2 / (2 * lattice.c_angstrom**2)
        return (
            {
                gamma: p(0, 0, 0),
                "N": p(0, 1 / 2, 0),
                "P": p(1 / 4, 1 / 4, 1 / 4),
                "Σ": p(-eta, eta, eta),
                "Σ₁": p(eta, 1 - eta, -eta),
                "X": p(0, 0, 1 / 2),
                "Y": p(-zeta, zeta, 1 / 2),
                "Y₁": p(1 / 2, 1 / 2, -zeta),
                "Z": p(1 / 2, 1 / 2, -1 / 2),
            },
            (
                (
                    gamma,
                    "X",
                    "Y",
                    "Σ",
                    gamma,
                    "Z",
                    "Σ₁",
                    "N",
                    "P",
                    "Y₁",
                    "Z",
                ),
                ("X", "P"),
            ),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.orc:
        return _orc_path()
    if appendix_a_case in {
        SetyawanCurtaroloAppendixACase.orcf1,
        SetyawanCurtaroloAppendixACase.orcf3,
    }:
        return _orcf13_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.orcf2:
        return _orcf2_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.orci:
        return _orci_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.orcc:
        return _orcc_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.hex:
        return (
            {
                gamma: p(0, 0, 0),
                "A": p(0, 0, 1 / 2),
                "H": p(1 / 3, 1 / 3, 1 / 2),
                "K": p(1 / 3, 1 / 3, 0),
                "L": p(1 / 2, 0, 1 / 2),
                "M": p(1 / 2, 0, 0),
            },
            (
                (gamma, "M", "K", gamma, "A", "L", "H", "A"),
                ("L", "M"),
                ("K", "H"),
            ),
        )
    if appendix_a_case is SetyawanCurtaroloAppendixACase.rhl1:
        return _rhl1_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.rhl2:
        return _rhl2_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.mcl:
        return _mcl_path(lattice)
    if appendix_a_case in {
        SetyawanCurtaroloAppendixACase.mclc1,
        SetyawanCurtaroloAppendixACase.mclc2,
    }:
        return _mclc12_path(lattice)
    if appendix_a_case in {
        SetyawanCurtaroloAppendixACase.mclc3,
        SetyawanCurtaroloAppendixACase.mclc4,
    }:
        return _mclc34_path(lattice)
    if appendix_a_case is SetyawanCurtaroloAppendixACase.mclc5:
        return _mclc5_path(lattice)
    if appendix_a_case in {
        SetyawanCurtaroloAppendixACase.tri1a,
        SetyawanCurtaroloAppendixACase.tri2a,
    }:
        points = {
            gamma: p(0, 0, 0),
            "L": p(1 / 2, 1 / 2, 0),
            "M": p(0, 1 / 2, 1 / 2),
            "N": p(1 / 2, 0, 1 / 2),
            "R": p(1 / 2, 1 / 2, 1 / 2),
            "X": p(1 / 2, 0, 0),
            "Y": p(0, 1 / 2, 0),
            "Z": p(0, 0, 1 / 2),
        }
    else:
        points = {
            gamma: p(0, 0, 0),
            "L": p(1 / 2, -1 / 2, 0),
            "M": p(0, 0, 1 / 2),
            "N": p(-1 / 2, -1 / 2, 1 / 2),
            "R": p(0, -1 / 2, 1 / 2),
            "X": p(0, -1 / 2, 0),
            "Y": p(1 / 2, 0, 0),
            "Z": p(-1 / 2, 0, 1 / 2),
        }
    return (
        points,
        (("X", gamma, "Y"), ("L", gamma, "Z"), ("N", gamma, "M"), ("R", gamma)),
    )


def _orc_path() -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "R": p(1 / 2, 1 / 2, 1 / 2),
            "S": p(1 / 2, 1 / 2, 0),
            "T": p(0, 1 / 2, 1 / 2),
            "U": p(1 / 2, 0, 1 / 2),
            "X": p(1 / 2, 0, 0),
            "Y": p(0, 1 / 2, 0),
            "Z": p(0, 0, 1 / 2),
        },
        (
            (g, "X", "S", "Y", g, "Z", "U", "R", "T", "Z"),
            ("Y", "T"),
            ("U", "X"),
            ("S", "R"),
        ),
    )


def _orcf13_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    zeta = (1 + a**2 / b**2 - a**2 / c**2) / 4
    eta = (1 + a**2 / b**2 + a**2 / c**2) / 4
    g = "Γ"
    p = _point
    points = {
        g: p(0, 0, 0),
        "A": p(1 / 2, 1 / 2 + zeta, zeta),
        "A₁": p(1 / 2, 1 / 2 - zeta, 1 - zeta),
        "L": p(1 / 2, 1 / 2, 1 / 2),
        "T": p(1, 1 / 2, 1 / 2),
        "X": p(0, eta, eta),
        "X₁": p(1, 1 - eta, 1 - eta),
        "Y": p(1 / 2, 0, 1 / 2),
        "Z": p(1 / 2, 1 / 2, 0),
    }
    first = (g, "Y", "T", "Z", g, "X", "A₁", "Y")
    branches: tuple[tuple[str, ...], ...]
    if lattice.appendix_a_case is SetyawanCurtaroloAppendixACase.orcf1:
        branches = (first, ("T", "X₁"), ("X", "A", "Z"), ("L", g))
    else:
        branches = (first, ("X", "A", "Z"), ("L", g))
    return points, branches


def _orcf2_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    phi = (1 + c**2 / b**2 - c**2 / a**2) / 4
    eta = (1 + a**2 / b**2 - a**2 / c**2) / 4
    delta = (1 + b**2 / a**2 - b**2 / c**2) / 4
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "C": p(1 / 2, 1 / 2 - eta, 1 - eta),
            "C₁": p(1 / 2, 1 / 2 + eta, eta),
            "D": p(1 / 2 - delta, 1 / 2, 1 - delta),
            "D₁": p(1 / 2 + delta, 1 / 2, delta),
            "L": p(1 / 2, 1 / 2, 1 / 2),
            "H": p(1 - phi, 1 / 2 - phi, 1 / 2),
            "H₁": p(phi, 1 / 2 + phi, 1 / 2),
            "X": p(0, 1 / 2, 1 / 2),
            "Y": p(1 / 2, 0, 1 / 2),
            "Z": p(1 / 2, 1 / 2, 0),
        },
        (
            (g, "Y", "C", "D", "X", g, "Z", "D₁", "H", "C"),
            ("C₁", "Z"),
            ("X", "H₁"),
            ("H", "Y"),
            ("L", g),
        ),
    )


def _orci_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    zeta = (1 + a**2 / c**2) / 4
    eta = (1 + b**2 / c**2) / 4
    delta = (b**2 - a**2) / (4 * c**2)
    mu = (a**2 + b**2) / (4 * c**2)
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "L": p(-mu, mu, 1 / 2 - delta),
            "L₁": p(mu, -mu, 1 / 2 + delta),
            "L₂": p(1 / 2 - delta, 1 / 2 + delta, -mu),
            "R": p(0, 1 / 2, 0),
            "S": p(1 / 2, 0, 0),
            "T": p(0, 0, 1 / 2),
            "W": p(1 / 4, 1 / 4, 1 / 4),
            "X": p(-zeta, zeta, zeta),
            "X₁": p(zeta, 1 - zeta, -zeta),
            "Y": p(eta, -eta, eta),
            "Y₁": p(1 - eta, eta, -eta),
            "Z": p(1 / 2, 1 / 2, -1 / 2),
        },
        (
            (g, "X", "L", "T", "W", "R", "X₁", "Z", g, "Y", "S", "W"),
            ("L₁", "Y"),
            ("Y₁", "Z"),
        ),
    )


def _orcc_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    zeta = (1 + lattice.a_angstrom**2 / lattice.b_angstrom**2) / 4
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "A": p(zeta, zeta, 1 / 2),
            "A₁": p(-zeta, 1 - zeta, 1 / 2),
            "R": p(0, 1 / 2, 1 / 2),
            "S": p(0, 1 / 2, 0),
            "T": p(-1 / 2, 1 / 2, 1 / 2),
            "X": p(zeta, zeta, 0),
            "X₁": p(-zeta, 1 - zeta, 0),
            "Y": p(-1 / 2, 1 / 2, 0),
            "Z": p(0, 0, 1 / 2),
        },
        (
            (g, "X", "S", "R", "A", "Z", g, "Y", "X₁", "A₁", "T", "Y"),
            ("Z", "T"),
        ),
    )


def _rhl1_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    alpha = math.radians(lattice.alpha_degrees)
    eta = (1 + 4 * math.cos(alpha)) / (2 + 4 * math.cos(alpha))
    nu = 3 / 4 - eta / 2
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "B": p(eta, 1 / 2, 1 - eta),
            "B₁": p(1 / 2, 1 - eta, eta - 1),
            "F": p(1 / 2, 1 / 2, 0),
            "L": p(1 / 2, 0, 0),
            "L₁": p(0, 0, -1 / 2),
            "P": p(eta, nu, nu),
            "P₁": p(1 - nu, 1 - nu, 1 - eta),
            "P₂": p(nu, nu, eta - 1),
            "Q": p(1 - nu, nu, 0),
            "X": p(nu, 0, -nu),
            "Z": p(1 / 2, 1 / 2, 1 / 2),
        },
        ((g, "L", "B₁"), ("B", "Z", g, "X"), ("Q", "F", "P₁", "Z"), ("L", "P")),
    )


def _rhl2_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    alpha = math.radians(lattice.alpha_degrees)
    eta = 1 / (2 * math.tan(alpha / 2) ** 2)
    nu = 3 / 4 - eta / 2
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "F": p(1 / 2, -1 / 2, 0),
            "L": p(1 / 2, 0, 0),
            "P": p(1 - nu, -nu, 1 - nu),
            "P₁": p(nu, nu - 1, nu - 1),
            "Q": p(eta, eta, eta),
            "Q₁": p(1 - eta, -eta, -eta),
            "Z": p(1 / 2, -1 / 2, 1 / 2),
        },
        ((g, "P", "Z", "Q", g, "F", "P₁", "Q₁", "L", "Z"),),
    )


def _mcl_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    b, c = lattice.b_angstrom, lattice.c_angstrom
    alpha = math.radians(lattice.alpha_degrees)
    eta = (1 - b * math.cos(alpha) / c) / (2 * math.sin(alpha) ** 2)
    nu = 1 / 2 - eta * c * math.cos(alpha) / b
    g = "Γ"
    p = _point
    return (
        {
            g: p(0, 0, 0),
            "A": p(1 / 2, 1 / 2, 0),
            "C": p(0, 1 / 2, 1 / 2),
            "D": p(1 / 2, 0, 1 / 2),
            "D₁": p(1 / 2, 0, -1 / 2),
            "E": p(1 / 2, 1 / 2, 1 / 2),
            "H": p(0, eta, 1 - nu),
            "H₁": p(0, 1 - eta, nu),
            "H₂": p(0, eta, -nu),
            "M": p(1 / 2, eta, 1 - nu),
            "M₁": p(1 / 2, 1 - eta, nu),
            "M₂": p(1 / 2, eta, -nu),
            "X": p(0, 1 / 2, 0),
            "Y": p(0, 0, 1 / 2),
            "Y₁": p(0, 0, -1 / 2),
            "Z": p(1 / 2, 0, 0),
        },
        ((g, "Y", "H", "C", "E", "M₁", "A", "X", "H₁"), ("M", "D", "Z"), ("Y", "D")),
    )


def _mclc12_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    alpha = math.radians(lattice.alpha_degrees)
    zeta = (2 - b * math.cos(alpha) / c) / (4 * math.sin(alpha) ** 2)
    eta = 1 / 2 + 2 * zeta * c * math.cos(alpha) / b
    psi = 3 / 4 - a**2 / (4 * b**2 * math.sin(alpha) ** 2)
    phi = psi + (3 / 4 - psi) * b * math.cos(alpha) / c
    g = "Γ"
    p = _point
    points = {
        g: p(0, 0, 0),
        "N": p(1 / 2, 0, 0),
        "N₁": p(0, -1 / 2, 0),
        "F": p(1 - zeta, 1 - zeta, 1 - eta),
        "F₁": p(zeta, zeta, eta),
        "F₂": p(-zeta, -zeta, 1 - eta),
        "F₃": p(1 - zeta, -zeta, 1 - eta),
        "I": p(phi, 1 - phi, 1 / 2),
        "I₁": p(1 - phi, phi - 1, 1 / 2),
        "L": p(1 / 2, 1 / 2, 1 / 2),
        "M": p(1 / 2, 0, 1 / 2),
        "X": p(1 - psi, psi - 1, 0),
        "X₁": p(psi, 1 - psi, 0),
        "X₂": p(psi - 1, -psi, 0),
        "Y": p(1 / 2, 1 / 2, 0),
        "Y₁": p(-1 / 2, -1 / 2, 0),
        "Z": p(0, 0, 1 / 2),
    }
    branches: tuple[tuple[str, ...], ...]
    if lattice.appendix_a_case is SetyawanCurtaroloAppendixACase.mclc1:
        branches = (
            (g, "Y", "F", "L", "I"),
            ("I₁", "Z", "F₁"),
            ("Y", "X₁"),
            ("X", g, "N"),
            ("M", g),
        )
    else:
        branches = ((g, "Y", "F", "L", "I"), ("I₁", "Z", "F₁"), ("N", g, "M"))
    return points, branches


def _mclc34_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    alpha = math.radians(lattice.alpha_degrees)
    mu = (1 + b**2 / a**2) / 4
    delta = b * c * math.cos(alpha) / (2 * a**2)
    zeta = mu - 1 / 4 + (1 - b * math.cos(alpha) / c) / (4 * math.sin(alpha) ** 2)
    eta = 1 / 2 + 2 * zeta * c * math.cos(alpha) / b
    phi = 1 + zeta - 2 * mu
    psi = eta - 2 * delta
    points = _mclc345_common_points(mu, delta, zeta, eta)
    points.update(
        {
            "F": _point(1 - phi, 1 - phi, 1 - psi),
            "F₁": _point(phi, phi - 1, psi),
            "F₂": _point(1 - phi, -phi, 1 - psi),
        }
    )
    g = "Γ"
    first: tuple[str, ...] = (g, "Y", "F", "H", "Z", "I")
    if lattice.appendix_a_case is SetyawanCurtaroloAppendixACase.mclc3:
        first += ("F₁",)
    return points, (first, ("H₁", "Y₁", "X", g, "N"), ("M", g))


def _mclc5_path(
    lattice: SetyawanCurtaroloLattice,
) -> tuple[dict[str, BandVector3], tuple[tuple[str, ...], ...]]:
    a, b, c = lattice.a_angstrom, lattice.b_angstrom, lattice.c_angstrom
    alpha = math.radians(lattice.alpha_degrees)
    zeta = (b**2 / a**2 + (1 - b * math.cos(alpha) / c) / math.sin(alpha) ** 2) / 4
    eta = 1 / 2 + 2 * zeta * c * math.cos(alpha) / b
    mu = eta / 2 + b**2 / (4 * a**2) - b * c * math.cos(alpha) / (2 * a**2)
    nu = 2 * mu - zeta
    omega = (4 * nu - 1 - b**2 * math.sin(alpha) ** 2 / a**2) * c
    omega /= 2 * b * math.cos(alpha)
    delta = zeta * c * math.cos(alpha) / b + omega / 2 - 1 / 4
    rho = 1 - zeta * a**2 / b**2
    points = _mclc345_common_points(mu, delta, zeta, eta)
    points.update(
        {
            "F": _point(nu, nu, omega),
            "F₁": _point(1 - nu, 1 - nu, 1 - omega),
            "F₂": _point(nu, nu - 1, omega),
            "I": _point(rho, 1 - rho, 1 / 2),
            "I₁": _point(1 - rho, rho - 1, 1 / 2),
            "L": _point(1 / 2, 1 / 2, 1 / 2),
        }
    )
    g = "Γ"
    return (
        points,
        (
            (g, "Y", "F", "L", "I"),
            ("I₁", "Z", "H", "F₁"),
            ("H₁", "Y₁", "X", g, "N"),
            ("M", g),
        ),
    )


def _mclc345_common_points(
    mu: float,
    delta: float,
    zeta: float,
    eta: float,
) -> dict[str, BandVector3]:
    return {
        "Γ": _point(0, 0, 0),
        "H": _point(zeta, zeta, eta),
        "H₁": _point(1 - zeta, -zeta, 1 - eta),
        "H₂": _point(-zeta, -zeta, 1 - eta),
        "I": _point(1 / 2, -1 / 2, 1 / 2),
        "M": _point(1 / 2, 0, 1 / 2),
        "N": _point(1 / 2, 0, 0),
        "N₁": _point(0, -1 / 2, 0),
        "X": _point(1 / 2, -1 / 2, 0),
        "Y": _point(mu, mu, delta),
        "Y₁": _point(1 - mu, -mu, -delta),
        "Y₂": _point(-mu, -mu, -delta),
        "Y₃": _point(mu, mu - 1, delta),
        "Z": _point(0, 0, 1 / 2),
    }


def _point(x: int | float, y: int | float, z: int | float) -> BandVector3:
    """Represent Appendix-A coefficients as one reciprocal-fractional row."""
    return float(x), float(y), float(z)
