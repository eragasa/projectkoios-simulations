r"""Software verification of ``Wannier90HamiltonianBlockParser``.

Evidence profile: claim_bearing

Bounded artifact scope: Wannier90 ``_hr.dat`` block and degeneracy adaptation.

Facet and represented meaning

The ActionObject retains native representatives, degeneracies, and indexed blocks.

Intrinsic and cross-object scope

Text decoding is included; no interpolation or degeneracy convention is applied.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or validate a Hamiltonian physically.
"""

import numpy as np
import pytest
from physkit.units.quantities import PhysicalUnit

from projectkoios.integrations.wannier90 import Wannier90HamiltonianBlockParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90HamiltonianBlockParser


class TestWannier90HamiltonianBlockParser:
    """Own parser evidence for retained native Hamiltonian blocks."""

    def test_method__execute__preserves_degeneracies_and_matrix_indices(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-003

        Requirement: ``_hr.dat`` adaptation retains degeneracies without applying
        an interpolation convention.

        Method: Parse two authored scalar representatives with distinct degeneracies.

        Oracle: Explicit headers and entries define expected metadata independently.

        Acceptance: Two scalar representatives retain coordinates, values, and
        distinct native degeneracies.

        Interpretation: A pass verifies lossless native block adaptation.

        Limitations: No interpolation, execution, or numerical comparison is assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""created by fixture
1
2
1 2
-1 0 0 1 1 0.5 -0.25
0 0 0 1 1 2.0 0.0
"""

        result = Wannier90HamiltonianBlockParser().execute(payload, PhysicalUnit("eV"))

        assert result.representatives == ((-1, 0, 0), (0, 0, 0))
        assert result.degeneracies == (1, 2)
        np.testing.assert_array_equal(
            result.blocks[0].magnitude, np.asarray([[0.5 - 0.25j]])
        )
