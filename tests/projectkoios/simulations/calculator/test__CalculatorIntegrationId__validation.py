from __future__ import annotations

import pytest

from projectkoios.simulations.calculator import CalculatorIntegrationId


class TestCalculatorIntegrationId:
    """Verify stable calculator-integration identity validation."""

    def test__CalculatorIntegrationId__accepts_lowercase_slug(self) -> None:
        """Retain a valid source-controlled integration slug exactly."""
        assert CalculatorIntegrationId("quantum-espresso").value == "quantum-espresso"

    def test__CalculatorIntegrationId__rejects_non_slug(self) -> None:
        """Reject provider labels outside the lowercase slug vocabulary."""
        with pytest.raises(ValueError, match="lowercase slug"):
            CalculatorIntegrationId("Quantum Espresso")
