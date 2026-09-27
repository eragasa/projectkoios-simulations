r"""Software verification of ``Wannier90ProjectionParser``.

Evidence profile: claim_bearing

Bounded artifact scope: indexed Wannier90 ``.amn`` text adaptation.

Facet and represented meaning

The ActionObject maps native band, projection, and k-point indices to complex matrices.

Intrinsic and cross-object scope

Complete indexed decoding is included; projection generation is separate.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or validate localization.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90ProjectionParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90ProjectionParser


class TestWannier90ProjectionParser:
    """Own parser evidence for native projection matrices."""

    def test_method__execute__decodes_indexed_complex_amplitudes(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-009

        Requirement: ``.amn`` entries map band rows and projection columns per k point.

        Method: Parse an authored complete identity-projection text payload.

        Oracle: The expected identity matrix follows directly from explicit entries.

        Acceptance: A one-k-point two-band identity projection is reconstructed.

        Interpretation: A pass verifies native index and complex-value adaptation.

        Limitations: No projection optimization or scientific comparison is assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""fixture
2 1 2
1 1 1 1.0 0.0
2 1 1 0.0 0.0
1 2 1 0.0 0.0
2 2 1 1.0 0.0
"""

        result = Wannier90ProjectionParser().execute(payload)

        assert result.kpoint_count == 1
        np.testing.assert_array_equal(result.matrices[0].magnitude, np.eye(2))
