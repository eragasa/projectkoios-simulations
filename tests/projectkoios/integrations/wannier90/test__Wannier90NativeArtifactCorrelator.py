r"""Software verification of ``Wannier90NativeArtifactCorrelator``.

Evidence profile: claim_bearing

Bounded artifact scope: exact caller-supplied native byte-inventory authentication.

Facet and represented meaning

Logical names, byte counts, SHA-256 identities, and complete inventories are included.

Intrinsic and cross-object scope

Expected identities are compared with identities derived from immutable payload bytes.

VVUQ and scientific exclusions

Authentication establishes byte identity, not scientific validity or convergence.
"""

from pathlib import Path

import pytest

from projectkoios.integrations.wannier90 import (
    Wannier90NativeArtifact,
    Wannier90NativeArtifactCorrelator,
)

pytestmark = pytest.mark.software_verification
SUT = Wannier90NativeArtifactCorrelator


class TestWannier90NativeArtifactCorrelator:
    """Own exact native artifact authentication evidence."""

    def test_method__execute__authenticates_reordered_complete_inventory(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-015

        Requirement: Correlation is name-based and authenticates every supplied byte.

        Method: Correlate two maintained payloads supplied opposite expected order.

        Oracle: Identities are derived independently from the original payload objects.

        Acceptance: Observed identities are returned in exact expected order.

        Interpretation: A pass establishes complete size-and-hash correlation behavior.

        Limitations: The maintained payloads are not scientific Wannier90 outputs.

        Provenance: Maintained synthetic immutable byte fixtures under ``resources``.
        """
        resources = Path(__file__).with_name("resources")
        first = Wannier90NativeArtifact(
            "first.eig",
            (resources / "native-artifact-correlator-first.txt").read_bytes(),
        )
        second = Wannier90NativeArtifact(
            "second.amn",
            (resources / "native-artifact-correlator-second.txt").read_bytes(),
        )
        expected = (first.identity, second.identity)

        result = SUT().execute(expected, (second, first))

        assert result.expected_identities == expected
        assert result.observed_identities == expected
