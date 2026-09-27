r"""Software verification of ``Wannier90NeighborOverlapData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 neighbor-overlap record invariants.

Facet and represented meaning

The DataObject retains complete ordered neighbor headers and overlap matrices.

Intrinsic and cross-object scope

Per-k-point neighbor cardinality is included; overlap quality is separate.

VVUQ and scientific exclusions

These checks do not execute Wannier90 or validate a physical subspace.
"""

import numpy as np
import pytest
from physkit.units.quantities import ComplexMatrixQuantity, Unitless

from projectkoios.integrations.wannier90 import Wannier90NeighborOverlapData

pytestmark = pytest.mark.software_verification
SUT = Wannier90NeighborOverlapData


class TestWannier90NeighborOverlapData:
    """Own data-contract evidence for native neighbor-overlap matrices."""

    def test_constructor__first_indices__requires_declared_neighbor_count(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-012

        Requirement: Each first k point owns the declared number of neighbor records.

        Method: Construct an authored inventory with duplicate first-point ownership.

        Oracle: Independent counting requires one declared neighbor for each point.

        Acceptance: Duplicating the first index leaves another point uncovered and
        raises ``ValueError``.

        Interpretation: A pass verifies complete per-point neighbor coverage.

        Limitations: Matrix values and physical overlap quality are not assessed.

        Provenance: The inventory is an authored synthetic software fixture.
        """
        matrix = ComplexMatrixQuantity(np.asarray([[1.0]]), Unitless())

        with pytest.raises(ValueError, match="each first k point"):
            Wannier90NeighborOverlapData(
                2,
                1,
                (0, 0),
                (1, 0),
                ((0, 0, 0), (0, 0, 0)),
                (matrix, matrix),
            )
