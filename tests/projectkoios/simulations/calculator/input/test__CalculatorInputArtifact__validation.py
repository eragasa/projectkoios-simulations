from __future__ import annotations

import pytest

from projectkoios.simulations.calculator.input import CalculatorInputArtifact


class TestCalculatorInputArtifact:
    """Verify exact calculator-input artifact validation."""

    def test__CalculatorInputArtifact__rejects_digest_mismatch(self) -> None:
        """Reject a declared digest that does not identify the retained bytes."""
        with pytest.raises(ValueError, match="must match content"):
            CalculatorInputArtifact(
                role="primary-input",
                filename="pw.in",
                media_type="text/plain",
                content=b"input",
                byte_size=5,
                sha256="0" * 64,
            )
