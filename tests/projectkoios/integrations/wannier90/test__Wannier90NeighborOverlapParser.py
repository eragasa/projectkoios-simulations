r"""Software verification of ``Wannier90NeighborOverlapParser``.

Evidence profile: claim_bearing

Bounded artifact scope: ordered Wannier90 ``.mmn`` text adaptation.

Facet and represented meaning

The ActionObject retains native neighbor headers and column-major complex overlaps.

Intrinsic and cross-object scope

Header and matrix decoding are included; overlap construction is separate.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or validate Wannier localization.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90NeighborOverlapParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90NeighborOverlapParser


class TestWannier90NeighborOverlapParser:
    """Own parser evidence for native neighbor-overlap matrices."""

    def test_method__execute__preserves_header_and_column_major_matrix(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-011

        Requirement: ``.mmn`` neighbor indices, reciprocal shift, and complex matrix
        retain native order.

        Method: Parse one authored two-band neighbor block with distinct entries.

        Oracle: Explicit native-order entries define the expected matrix independently.

        Acceptance: One two-band neighbor record is decoded exactly.

        Interpretation: A pass verifies header and column-major matrix adaptation.

        Limitations: No live executable output or scientific overlap is assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""fixture
2 1 1
1 1 1 0 0
1.0 0.0
0.0 1.0
2.0 0.0
0.0 2.0
"""

        result = Wannier90NeighborOverlapParser().execute(payload)

        assert result.first_kpoint_indices == (0,)
        assert result.second_kpoint_indices == (0,)
        assert result.reciprocal_shifts == ((1, 0, 0),)
        np.testing.assert_array_equal(
            result.matrices[0].magnitude,
            np.asarray([[1.0, 2.0], [1.0j, 2.0j]]),
        )
