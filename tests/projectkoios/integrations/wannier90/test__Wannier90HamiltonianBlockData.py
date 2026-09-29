r"""Software verification of ``Wannier90HamiltonianBlockData``.

Evidence profile: claim_bearing

Bounded artifact scope: native Wannier90 real-space Hamiltonian-block invariants.

Facet and represented meaning

The DataObject binds integer representatives, degeneracies, and energy-valued blocks.

Intrinsic and cross-object scope

Positive degeneracies and homogeneous square blocks are included; interpolation is not.

VVUQ and scientific exclusions

These checks do not execute Wannier90 or validate a represented Hamiltonian physically.
"""

import numpy as np
import pytest

from projectkoios.integrations.wannier90 import Wannier90HamiltonianBlockData
from projectkoios.physkit.units.quantities import ComplexMatrixQuantity, PhysicalUnit

pytestmark = pytest.mark.software_verification
SUT = Wannier90HamiltonianBlockData


class TestWannier90HamiltonianBlockData:
    """Own data-contract evidence for retained native Hamiltonian blocks."""

    def test_constructor__degeneracies__requires_positive_values(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-004

        Requirement: Native Wigner--Seitz degeneracies are positive integers.

        Method: Construct an authored scalar block with a zero native degeneracy.

        Oracle: The positive-degeneracy invariant independently requires rejection.

        Acceptance: A zero degeneracy raises ``ValueError``.

        Interpretation: A pass verifies intrinsic native metadata enforcement.

        Limitations: Interpolation and Hamiltonian numerical agreement are not assessed.

        Provenance: The block is an authored synthetic software fixture.
        """
        block = ComplexMatrixQuantity(np.asarray([[1.0]]), PhysicalUnit("eV"))

        with pytest.raises(ValueError, match="must be positive"):
            Wannier90HamiltonianBlockData(((0, 0, 0),), (0,), (block,))
