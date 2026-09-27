r"""Software verification of ``Wannier90UnitaryMatrixParser``.

Evidence profile: claim_bearing

Bounded artifact scope: ordered Wannier90 ``_u.mat`` text adaptation.

Facet and represented meaning

The ActionObject retains fractional reciprocal points and column-major gauge matrices.

Intrinsic and cross-object scope

Dimension and complex-entry decoding are included; gauge analysis is separate.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or validate localization.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90UnitaryMatrixParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90UnitaryMatrixParser


class TestWannier90UnitaryMatrixParser:
    """Own parser evidence for retained native gauge matrices."""

    def test_method__execute__preserves_column_major_native_entries(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-001

        Requirement: ``_u.mat`` entries are decoded in native column-major order.

        Method: Parse authored two-point matrices with distinct complex entries.

        Oracle: Explicit native-order entries independently define the expected
        matrices.

        Acceptance: Two matrices retain k-point order and expected complex entries.

        Interpretation: A pass verifies point order and column-major matrix adaptation.

        Limitations: Matrix unitarity and live executable behavior are not assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""created by fixture
2 2 2

0.0 0.0 0.0
1.0 0.0
0.0 1.0
2.0 0.0
0.0 2.0

0.5 0.0 0.0
3.0 0.0
0.0 3.0
4.0 0.0
0.0 4.0
"""

        result = Wannier90UnitaryMatrixParser().execute(payload)

        assert result.kpoint_count == 2
        np.testing.assert_array_equal(
            result.fractional_kpoints.magnitude[:, 0], np.asarray([0.0, 0.5])
        )
        np.testing.assert_array_equal(
            result.matrices[0].magnitude,
            np.asarray([[1.0, 2.0], [1.0j, 2.0j]]),
        )
