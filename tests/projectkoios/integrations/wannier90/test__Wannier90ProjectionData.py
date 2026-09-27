r"""Software verification of ``Wannier90ProjectionData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 projection-matrix record invariants.

Facet and represented meaning

The DataObject retains homogeneous band-by-projection matrices over reciprocal points.

Intrinsic and cross-object scope

Matrix-shape correlation is included; projection quality is separate.

VVUQ and scientific exclusions

These checks do not execute Wannier90 or validate a physical projection choice.
"""

import numpy as np
import pytest
from physkit.units.quantities import ComplexMatrixQuantity, Unitless

from projectkoios.integrations.wannier90 import Wannier90ProjectionData

pytestmark = pytest.mark.software_verification
SUT = Wannier90ProjectionData


class TestWannier90ProjectionData:
    """Own data-contract evidence for native projection matrices."""

    def test_constructor__matrices__requires_equal_shapes(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-010

        Requirement: Every reciprocal point has the same band/projection dimensions.

        Method: Construct the record from two authored matrices with unequal shapes.

        Oracle: The homogeneous path contract independently requires equal shapes.

        Acceptance: Mismatched projection matrix shapes raise ``ValueError``.

        Interpretation: A pass verifies cross-point dimension enforcement.

        Limitations: Projection completeness and physical suitability are not assessed.

        Provenance: The matrices are authored synthetic software fixtures.
        """
        with pytest.raises(ValueError, match="equal shape"):
            Wannier90ProjectionData(
                (
                    ComplexMatrixQuantity(np.ones((2, 1)), Unitless()),
                    ComplexMatrixQuantity(np.ones((2, 2)), Unitless()),
                )
            )
