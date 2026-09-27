r"""Software verification of ``Wannier90NeighborListData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 neighbor-list record invariants.

Facet and represented meaning

The DataObject retains complete equal-size neighbor groups by first k point.

Intrinsic and cross-object scope

Positive one-based indices and group cardinality are included.

VVUQ and scientific exclusions

These checks do not run Wannier90 or validate a reciprocal mesh scientifically.
"""

import pytest

from projectkoios.integrations.wannier90 import Wannier90NeighborListData

pytestmark = pytest.mark.software_verification
SUT = Wannier90NeighborListData


class TestWannier90NeighborListData:
    """Own record evidence for native neighbor lists."""

    def test_constructor__records__requires_each_first_point_group(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-014

        Requirement: Every inferred first k point owns the declared neighbor count.

        Method: Construct two records assigned to the same first point.

        Oracle: Independent group counting leaves the second point uncovered.

        Acceptance: Construction raises ``ValueError``.

        Interpretation: A pass verifies complete first-point group enforcement.

        Limitations: Neighbor geometry and overlap values are not assessed.

        Provenance: The records are authored synthetic software fixtures.
        """
        with pytest.raises(ValueError, match="each first k point"):
            Wannier90NeighborListData(1, ((1, 2, 0, 0, 0), (1, 1, 1, 0, 0)))
