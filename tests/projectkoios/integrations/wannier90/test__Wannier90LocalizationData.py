r"""Software verification of ``Wannier90LocalizationData``.

Evidence profile: claim_bearing

Bounded artifact scope: final native Wannier90 localization record invariants.

Facet and represented meaning

The DataObject correlates centers, spreads, Omega components, and iteration metadata.

Intrinsic and cross-object scope

Center/spread cardinality and squared units are included; convergence meaning is not.

VVUQ and scientific exclusions

These checks do not execute localization or establish numerical or scientific validity.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90LocalizationData
from projectkoios.physkit.units.quantities import (
    MatrixQuantity,
    PhysicalUnit,
    ScalarQuantity,
    VectorQuantity,
)

pytestmark = pytest.mark.software_verification
SUT = Wannier90LocalizationData


class TestWannier90LocalizationData:
    """Own data-contract evidence for retained native localization observations."""

    def test_constructor__spreads__requires_one_value_per_center(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-006

        Requirement: Final center and spread inventories have equal cardinality.

        Method: Construct an authored record with unequal center and spread counts.

        Oracle: The one-spread-per-center contract independently requires rejection.

        Acceptance: Two centers with one spread raise ``ValueError``.

        Interpretation: A pass verifies correlated localization inventory enforcement.

        Limitations: Convergence and physical localization quality are not assessed.

        Provenance: The quantities are authored synthetic software fixtures.
        """
        squared = PhysicalUnit("angstrom ** 2")
        omega = ScalarQuantity(0.0, squared)

        with pytest.raises(ValueError, match="one spread"):
            Wannier90LocalizationData(
                MatrixQuantity(np.zeros((2, 3)), PhysicalUnit("angstrom")),
                VectorQuantity(np.zeros(1), squared),
                omega,
                omega,
                omega,
                omega,
                "Ang",
                (0,),
                0,
            )
