"""Calculator-neutral electronic charge and spin declarations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum

_LIBXC_COMPOSITE = re.compile(r"[A-Z][A-Z0-9_]*(?:\+[A-Z][A-Z0-9_]*)*")
_COMPATIBILITY_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")


@dataclass(frozen=True, slots=True)
class DftChargeState:
    """Declare added-electron and charge-state values with one sign convention."""

    delta_n_electrons: int = 0
    charge_state: int = 0

    def __post_init__(self) -> None:
        if type(self.delta_n_electrons) is not int:
            raise TypeError("delta_n_electrons must be an integer")
        if type(self.charge_state) is not int:
            raise TypeError("charge_state must be an integer")
        if self.charge_state != -self.delta_n_electrons:
            raise ValueError("charge_state must equal -delta_n_electrons")


class DftExchangeCorrelationIdentifierScheme(StrEnum):
    """Name the closed identifier vocabulary used for an XC model."""

    LIBXC_COMPOSITE = "libxc-composite"


@dataclass(frozen=True, slots=True)
class DftExchangeCorrelationModel:
    """Identify exact neutral XC intent and pseudopotential compatibility."""

    identifier_scheme: DftExchangeCorrelationIdentifierScheme
    identifier: str
    pseudopotential_compatibility_label: str

    def __post_init__(self) -> None:
        if type(self.identifier_scheme) is not DftExchangeCorrelationIdentifierScheme:
            raise TypeError(
                "identifier_scheme must be a DftExchangeCorrelationIdentifierScheme"
            )
        if (
            type(self.identifier) is not str
            or not self.identifier.isascii()
            or not _LIBXC_COMPOSITE.fullmatch(self.identifier)
        ):
            raise ValueError("identifier must be a canonical Libxc composite")
        if (
            type(self.pseudopotential_compatibility_label) is not str
            or not self.pseudopotential_compatibility_label.isascii()
            or not _COMPATIBILITY_LABEL.fullmatch(
                self.pseudopotential_compatibility_label
            )
        ):
            raise ValueError(
                "pseudopotential_compatibility_label must be canonical ASCII text"
            )


class DftOccupationMethod(StrEnum):
    """Select the calculator-neutral occupation family."""

    FIXED = "fixed"
    GAUSSIAN = "gaussian"
    FERMI_DIRAC = "fermi-dirac"
    METHFESSEL_PAXTON = "methfessel-paxton"
    MARZARI_VANDERBILT_COLD = "marzari-vanderbilt-cold"


@dataclass(frozen=True, slots=True)
class DftOccupationPolicy:
    """Declare exact occupation and smearing intent."""

    method: DftOccupationMethod
    smearing_width_ev: float | None = None
    methfessel_paxton_order: int | None = None

    def __post_init__(self) -> None:
        if type(self.method) is not DftOccupationMethod:
            raise TypeError("method must be a DftOccupationMethod")
        if self.smearing_width_ev is not None and (
            type(self.smearing_width_ev) is not float
            or not math.isfinite(self.smearing_width_ev)
            or self.smearing_width_ev <= 0.0
        ):
            raise ValueError(
                "smearing_width_ev must be positive and finite when represented"
            )
        if self.methfessel_paxton_order is not None and (
            type(self.methfessel_paxton_order) is not int
            or self.methfessel_paxton_order < 0
        ):
            raise ValueError(
                "methfessel_paxton_order must be nonnegative when represented"
            )
        if self.method is DftOccupationMethod.FIXED:
            if (
                self.smearing_width_ev is not None
                or self.methfessel_paxton_order is not None
            ):
                raise ValueError("fixed occupations cannot carry smearing controls")
        elif self.smearing_width_ev is None:
            raise ValueError("smearing methods require smearing_width_ev")
        if self.method is DftOccupationMethod.METHFESSEL_PAXTON:
            if self.methfessel_paxton_order is None:
                raise ValueError(
                    "Methfessel-Paxton occupations require an explicit order"
                )
        elif self.methfessel_paxton_order is not None:
            raise ValueError(
                "only Methfessel-Paxton occupations carry an expansion order"
            )


@dataclass(frozen=True, slots=True)
class PwDftElectronicConvergencePolicy:
    """Declare shared electronic convergence quantities."""

    energy_tolerance_ev: float
    maximum_electronic_iterations: int

    def __post_init__(self) -> None:
        if (
            type(self.energy_tolerance_ev) is not float
            or not math.isfinite(self.energy_tolerance_ev)
            or self.energy_tolerance_ev <= 0.0
        ):
            raise ValueError("energy_tolerance_ev must be positive and finite")
        if (
            type(self.maximum_electronic_iterations) is not int
            or self.maximum_electronic_iterations <= 0
        ):
            raise ValueError("maximum_electronic_iterations must be positive")


class DftSpinMode(StrEnum):
    """Classify calculator-neutral spin intent independently of provider support."""

    UNPOLARIZED = "unpolarized"
    COLLINEAR = "collinear"
    NONCOLLINEAR = "noncollinear"
    SPIN_ORBIT = "spin-orbit-coupled"


@dataclass(frozen=True, slots=True)
class DftSpinTreatment:
    """Declare collinear spin population and optional initial moments."""

    mode: DftSpinMode = DftSpinMode.UNPOLARIZED
    spin_channel_electron_difference: int = 0
    constrain_spin_channel_difference: bool = False
    initial_site_magnetic_moments_mu_b: tuple[float, ...] = ()
    initial_site_magnetic_moment_vectors_mu_b: tuple[
        tuple[float, float, float], ...
    ] = ()
    spin_quantization_axis: tuple[float, float, float] | None = None

    def __post_init__(self) -> None:
        if type(self.mode) is not DftSpinMode:
            raise TypeError("mode must be a DftSpinMode")
        if type(self.spin_channel_electron_difference) is not int:
            raise TypeError("spin_channel_electron_difference must be an integer")
        if type(self.constrain_spin_channel_difference) is not bool:
            raise TypeError("constrain_spin_channel_difference must be a bool")
        if type(self.initial_site_magnetic_moments_mu_b) is not tuple or any(
            type(value) is not float or not math.isfinite(value)
            for value in self.initial_site_magnetic_moments_mu_b
        ):
            raise TypeError(
                "initial_site_magnetic_moments_mu_b must contain finite floats"
            )
        if type(self.initial_site_magnetic_moment_vectors_mu_b) is not tuple or any(
            type(vector) is not tuple
            or len(vector) != 3
            or any(
                type(value) is not float or not math.isfinite(value) for value in vector
            )
            for vector in self.initial_site_magnetic_moment_vectors_mu_b
        ):
            raise TypeError(
                "initial_site_magnetic_moment_vectors_mu_b must contain finite "
                "three-float tuples"
            )
        if self.spin_quantization_axis is not None:
            axis = self.spin_quantization_axis
            if (
                type(axis) is not tuple
                or len(axis) != 3
                or any(
                    type(value) is not float or not math.isfinite(value)
                    for value in axis
                )
            ):
                raise TypeError(
                    "spin_quantization_axis must be a finite three-float tuple"
                )
            if not math.isclose(
                math.sqrt(sum(value * value for value in axis)),
                1.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            ):
                raise ValueError("spin_quantization_axis must be a unit vector")
        if self.mode is DftSpinMode.UNPOLARIZED and (
            self.spin_channel_electron_difference != 0
            or self.constrain_spin_channel_difference
            or self.initial_site_magnetic_moments_mu_b
            or self.initial_site_magnetic_moment_vectors_mu_b
            or self.spin_quantization_axis is not None
        ):
            raise ValueError(
                "unpolarized spin treatment cannot carry spin polarization"
            )
        if self.mode is DftSpinMode.COLLINEAR:
            if (
                not self.constrain_spin_channel_difference
                and not self.initial_site_magnetic_moments_mu_b
            ):
                raise ValueError(
                    "collinear spin treatment requires an explicit population "
                    "constraint or initial site moments"
                )
            if (
                self.initial_site_magnetic_moment_vectors_mu_b
                or self.spin_quantization_axis is not None
            ):
                raise ValueError(
                    "collinear spin treatment cannot carry vector moments or an axis"
                )
        if self.mode is DftSpinMode.NONCOLLINEAR and (
            self.spin_channel_electron_difference != 0
            or self.constrain_spin_channel_difference
            or self.initial_site_magnetic_moments_mu_b
            or self.spin_quantization_axis is not None
        ):
            raise ValueError(
                "noncollinear spin treatment cannot carry collinear population data "
                "or a spin-orbit quantization axis"
            )
        if self.mode is DftSpinMode.SPIN_ORBIT:
            if (
                self.spin_channel_electron_difference != 0
                or self.constrain_spin_channel_difference
                or self.initial_site_magnetic_moments_mu_b
            ):
                raise ValueError(
                    "spin-orbit treatment cannot carry collinear population data"
                )
            if self.spin_quantization_axis is None:
                raise ValueError(
                    "spin-orbit treatment requires a spin quantization axis"
                )
