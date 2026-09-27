r"""Software verification of ``Wannier90UnitaryMatrixData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 gauge-matrix record invariants.

Facet and represented meaning

The DataObject correlates fractional reciprocal points with native complex matrices.

Intrinsic and cross-object scope

Path cardinality and homogeneous matrix dimensions are included; unitarity is separate.

VVUQ and scientific exclusions

These checks do not execute Wannier90 or validate a gauge physically.
"""

import numpy as np
import pytest
from physkit.units.quantities import ComplexMatrixQuantity, MatrixQuantity, Unitless

from projectkoios.integrations.wannier90 import Wannier90UnitaryMatrixData

pytestmark = pytest.mark.software_verification
SUT = Wannier90UnitaryMatrixData


class TestWannier90UnitaryMatrixData:
    """Own data-contract evidence for retained native gauge matrices."""

    def test_constructor__matrices__requires_one_matrix_per_kpoint(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-002

        Requirement: Native k points and gauge matrices have correlated cardinality.

        Method: Construct an authored record with unequal point and matrix counts.

        Oracle: The one-matrix-per-point contract independently requires rejection.

        Acceptance: One matrix for two k points raises ``ValueError``.

        Interpretation: A pass verifies cross-inventory cardinality enforcement.

        Limitations: Matrix unitarity and retained-artifact identity are not assessed.

        Provenance: The quantities are authored synthetic software fixtures.
        """
        points = MatrixQuantity(np.zeros((2, 3)), Unitless())
        matrix = ComplexMatrixQuantity(np.eye(2), Unitless())

        with pytest.raises(ValueError, match="matrix count"):
            Wannier90UnitaryMatrixData(points, (matrix,))
