r"""Software verification of ``Wannier90LocalizationParser``.

Evidence profile: claim_bearing

Bounded artifact scope: final-state Wannier90 ``.wout`` observation adaptation.

Facet and represented meaning

The ActionObject retains final centers, spreads, Omega decomposition, and iteration.

Intrinsic and cross-object scope

Final-state selection and typed unit adaptation are included; convergence policy is not.

VVUQ and scientific exclusions

These checks do not authenticate retained bytes or validate localization scientifically.
"""

import numpy as np
import pytest
from physkit.units.quantities import PhysicalUnit

from projectkoios.integrations.wannier90 import Wannier90LocalizationParser

pytestmark = pytest.mark.software_verification
SUT = Wannier90LocalizationParser


class TestWannier90LocalizationParser:
    """Own parser evidence for retained native localization observations."""

    def test_method__execute__selects_final_state_and_converged_iteration(self) -> None:
        """Evidence ID: SV-INTEGRATION-WANNIER90-005

        Requirement: Final centers, spreads, Omega decomposition, and the maximum
        converged iteration are retained separately.

        Method: Parse an authored final-state section and convergence records.

        Oracle: Explicit text values define expected centers and metadata independently.

        Acceptance: The final two-function fixture is decoded in angstrom units.

        Interpretation: A pass verifies final-state selection and unit adaptation.

        Limitations: No live execution or convergence sufficiency is assessed.

        Provenance: The payload is an authored synthetic native-format fixture.
        """
        payload = b"""  3  -1.0  0.1 <-- CONV
Final State
 WF centre and spread    1  ( 0.25, 0.0, 0.0 )  0.10
 WF centre and spread    2  ( -0.25, 0.0, 0.0 )  0.20
 Omega I = 0.01
 Omega D = 0.02
 Omega OD = 0.03
 Omega Total = 0.06
  7  -2.0  0.01 <-- CONV
"""

        result = Wannier90LocalizationParser().execute(
            payload, PhysicalUnit("angstrom")
        )

        assert result.wannier_count == 2
        np.testing.assert_array_equal(
            result.centers.magnitude[:, 0], np.asarray([0.25, -0.25])
        )
        np.testing.assert_array_equal(result.spreads.magnitude, np.asarray([0.1, 0.2]))
        assert result.omega_total.magnitude == 0.06
        assert result.maximum_converged_iteration == 7
