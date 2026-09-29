r"""Software verification of ``Wannier90EigenvalueData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 eigenvalue-table record invariants.

Facet and represented meaning

The DataObject retains a complete finite energy table indexed by k point and band.

Intrinsic and cross-object scope

Nonempty table dimensions are included; native execution and physics are separate.

VVUQ and scientific exclusions

These checks do not execute Wannier90 or establish numerical or scientific validity.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90EigenvalueData
from projectkoios.physkit.units.quantities import MatrixQuantity, PhysicalUnit

pytestmark = pytest.mark.software_verification
SUT = Wannier90EigenvalueData


class TestWannier90EigenvalueData:
    """Own data-contract evidence for native eigenvalue tables."""

    def test_constructor__eigenvalues__rejects_empty_axis(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-008

        Requirement: Native eigenvalue tables contain at least one k point and band.

        Method: Construct the record with an authored empty-axis quantity.

        Oracle: The declared nonempty-table invariant independently requires rejection.

        Acceptance: An empty k-point axis raises ``ValueError``.

        Interpretation: A pass verifies intrinsic table cardinality enforcement.

        Limitations: No native file, executable, or scientific observable is assessed.

        Provenance: The input is an authored synthetic software fixture.
        """
        with pytest.raises(ValueError, match="must be nonempty"):
            Wannier90EigenvalueData(
                MatrixQuantity(np.empty((0, 2)), PhysicalUnit("eV"))
            )
