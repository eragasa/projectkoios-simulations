from __future__ import annotations

import hashlib

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator.input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputMapping,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)


class TestCalculatorInputRecord:
    """Verify exact prepared-input record identity behavior."""

    def test__CalculatorInputRecord__has_deterministic_content_identity(self) -> None:
        """Derive identity from canonical metadata without embedding input bytes."""
        content = b"&CONTROL\n calculation='scf'\n/\n"
        record = CalculatorInputRecord(
            input_id="si-p-neutral-scf-qe",
            schema_version=1,
            source=CalculatorInputSourceReference(
                simulation_id="si-p-neutral-scf",
                representation="projectkoios.pw-dft-scf+json",
                schema_version=1,
                byte_size=512,
                sha256="1" * 64,
            ),
            integration_id=CalculatorIntegrationId("quantum-espresso"),
            calculator_name="Quantum ESPRESSO pw.x",
            calculator_version_constraint=">=7.4,<8",
            representation="quantum-espresso-pw-input",
            artifacts=(
                CalculatorInputArtifact(
                    role="primary-input",
                    filename="pw.in",
                    media_type="text/plain; charset=utf-8",
                    content=content,
                    byte_size=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                ),
            ),
            external_requirements=(
                CalculatorExternalInputRequirement(
                    role="pseudopotential",
                    stable_id="Si.upf",
                    filename="Si.upf",
                    format="upf",
                    byte_size=1024,
                    sha256="2" * 64,
                    provenance="SSSP efficiency release 1.3.0",
                    element_symbol="Si",
                ),
            ),
            mappings=(
                CalculatorInputMapping(
                    neutral_field="delta_n_electrons",
                    neutral_value="0",
                    native_fields=("SYSTEM.tot_charge",),
                    native_values=("0",),
                    effect="constraint",
                    qualification="QE positive charge removes electrons.",
                ),
            ),
            preparation_operation="projectkoios.qe.pw.scf.render",
            preparation_version="1",
        )

        assert record.canonical_bytes.endswith(b"\n")
        assert record.byte_size == len(record.canonical_bytes)
        assert record.sha256 == hashlib.sha256(record.canonical_bytes).hexdigest()
        # Canonical identity describes the artifact without duplicating native bytes
        # into the metadata envelope.
        assert b"&CONTROL" not in record.canonical_bytes
        assert not hasattr(record, "execution_authorized")
