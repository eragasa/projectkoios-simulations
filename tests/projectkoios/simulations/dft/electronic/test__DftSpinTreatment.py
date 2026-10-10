from __future__ import annotations

import pytest

from projectkoios.simulations.dft.electronic import (
    DftExchangeCorrelationIdentifierScheme,
    DftExchangeCorrelationModel,
    DftOccupationMethod,
    DftOccupationPolicy,
    DftSpinMode,
    DftSpinTreatment,
    PwDftElectronicConvergencePolicy,
)


def test_represents_exact_exchange_correlation_identity() -> None:
    model = DftExchangeCorrelationModel(
        identifier_scheme=DftExchangeCorrelationIdentifierScheme.LIBXC_COMPOSITE,
        identifier="GGA_X_PBE+GGA_C_PBE",
        pseudopotential_compatibility_label="PBE",
    )

    assert model.identifier == "GGA_X_PBE+GGA_C_PBE"


def test_represents_fixed_and_smeared_occupations() -> None:
    fixed = DftOccupationPolicy(method=DftOccupationMethod.FIXED)
    smeared = DftOccupationPolicy(
        method=DftOccupationMethod.METHFESSEL_PAXTON,
        smearing_width_ev=0.1,
        methfessel_paxton_order=1,
    )

    assert fixed.smearing_width_ev is None
    assert smeared.methfessel_paxton_order == 1


def test_rejects_smearing_without_width() -> None:
    with pytest.raises(ValueError, match="smearing_width_ev"):
        DftOccupationPolicy(method=DftOccupationMethod.GAUSSIAN)


def test_represents_electronic_convergence() -> None:
    policy = PwDftElectronicConvergencePolicy(
        energy_tolerance_ev=1.0e-8,
        maximum_electronic_iterations=100,
    )

    assert policy.maximum_electronic_iterations == 100


def test_represents_noncollinear_vector_moments() -> None:
    treatment = DftSpinTreatment(
        mode=DftSpinMode.NONCOLLINEAR,
        initial_site_magnetic_moment_vectors_mu_b=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ),
    )

    assert treatment.mode is DftSpinMode.NONCOLLINEAR


def test_represents_spin_orbit_quantization_axis() -> None:
    treatment = DftSpinTreatment(
        mode=DftSpinMode.SPIN_ORBIT,
        initial_site_magnetic_moment_vectors_mu_b=((0.0, 0.0, 1.0),),
        spin_quantization_axis=(0.0, 0.0, 1.0),
    )

    assert treatment.spin_quantization_axis == (0.0, 0.0, 1.0)


def test_rejects_vector_moments_for_collinear_spin() -> None:
    with pytest.raises(ValueError, match="vector moments"):
        DftSpinTreatment(
            mode=DftSpinMode.COLLINEAR,
            constrain_spin_channel_difference=True,
            spin_channel_electron_difference=1,
            initial_site_magnetic_moment_vectors_mu_b=((0.0, 0.0, 1.0),),
        )


def test_rejects_spin_orbit_without_quantization_axis() -> None:
    with pytest.raises(ValueError, match="quantization axis"):
        DftSpinTreatment(mode=DftSpinMode.SPIN_ORBIT)
