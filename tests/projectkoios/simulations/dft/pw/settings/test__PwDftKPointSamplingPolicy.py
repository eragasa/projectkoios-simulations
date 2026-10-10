from __future__ import annotations

import pytest

from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy


def test_represents_mesh_shift_and_reduction_policy() -> None:
    policy = PwDftKPointSamplingPolicy(
        mesh=(8, 8, 8),
        shift=(0, 0, 0),
        use_spatial_symmetry=False,
        use_time_reversal=False,
    )

    assert policy.mesh == (8, 8, 8)
    assert policy.use_spatial_symmetry is False


def test_rejects_boolean_mesh_values() -> None:
    with pytest.raises(ValueError, match="positive integers"):
        PwDftKPointSamplingPolicy(
            mesh=(True, 8, 8),  # type: ignore[arg-type]
            shift=(0, 0, 0),
            use_spatial_symmetry=False,
            use_time_reversal=False,
        )
