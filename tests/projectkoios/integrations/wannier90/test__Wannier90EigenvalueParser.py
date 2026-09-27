r"""Software verification of ``Wannier90EigenvalueParser``.

Evidence profile: claim_bearing

Bounded artifact scope: indexed Wannier90 ``.eig`` text adaptation.

Facet and represented meaning

The ActionObject maps one-based native indices to k-point-by-band energy tables.

Intrinsic and cross-object scope

Complete indexed decoding is included; file discovery and execution are separate.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or establish scientific validity.
"""

import numpy as np
import pytest
from physkit.units.quantities import PhysicalUnit

from projectkoios.integrations.wannier90 import Wannier90EigenvalueParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90EigenvalueParser


class TestWannier90EigenvalueParser:
    """Own parser evidence for native eigenvalue tables."""

    def test_method__execute__decodes_one_based_complete_table(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-007

        Requirement: ``.eig`` band and k-point indices are adapted to matrix axes.

        Method: Parse an authored complete two-by-two indexed text payload.

        Oracle: The expected matrix is assembled directly from the declared indices.

        Acceptance: Two bands at two k points retain their native energy values.

        Interpretation: A pass verifies index adaptation and energy-value retention.

        Limitations: The fixture is not output from a live Wannier90 execution.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"1 1 1.0\n2 1 2.0\n1 2 3.0\n2 2 4.0\n"

        result = Wannier90EigenvalueParser().execute(payload, PhysicalUnit("eV"))

        np.testing.assert_array_equal(
            result.eigenvalues.magnitude, np.asarray([[1.0, 2.0], [3.0, 4.0]])
        )
        assert result.kpoint_count == 2
        assert result.band_count == 2
