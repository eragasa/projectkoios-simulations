r"""Software verification of ``Wannier90NeighborListParser``.

Evidence profile: claim_bearing

Bounded artifact scope: Wannier90 ``.nnkp`` neighbor-list adaptation.

Facet and represented meaning

The ActionObject retains the declared count and ordered five-integer records.

Intrinsic and cross-object scope

Block selection and integer decoding are included; preprocessing is separate.

VVUQ and scientific exclusions

These checks do not run Wannier90 or establish scientific validity.
"""

import pytest

from projectkoios.integrations.wannier90 import Wannier90NeighborListParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90NeighborListParser


class TestWannier90NeighborListParser:
    """Own parser evidence for native neighbor lists."""

    def test_method__execute__preserves_ordered_neighbor_records(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-013

        Requirement: The ``nnkpts`` block retains native indices and reciprocal shifts.

        Method: Parse an authored two-point, one-neighbor block.

        Oracle: Explicit block lines independently define the expected records.

        Acceptance: The declared count and both records agree exactly.

        Interpretation: A pass verifies bounded block and integer adaptation.

        Limitations: No preprocessing execution or overlap construction is assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""begin nnkpts
1
1 2 0 0 0
2 1 1 0 0
end nnkpts
"""

        result = Wannier90NeighborListParser().execute(payload)

        assert result.neighbor_count == 1
        assert result.kpoint_count == 2
        assert result.records == ((1, 2, 0, 0, 0), (2, 1, 1, 0, 0))
