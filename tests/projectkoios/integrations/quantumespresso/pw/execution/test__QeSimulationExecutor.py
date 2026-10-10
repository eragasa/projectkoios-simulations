from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.execution import (
    QeSimulationExecutor,
)
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator_input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    ExecutionStatus,
)

pytestmark = pytest.mark.integration


class QeSimulationExecutorTest(unittest.TestCase):
    def test_rejects_execution_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = _prepared_input_and_library(
                working_directory
            )

            with self.assertRaisesRegex(PermissionError, "not authorized"):
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    Path(sys.executable),
                    working_directory,
                )

            self.assertEqual(tuple(working_directory.iterdir()), ())

    def test_records_missing_library_artifact_without_starting_qe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = _prepared_input_and_library(
                working_directory
            )

            with self.assertRaises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    Path(sys.executable),
                    working_directory,
                    execution_authorized=True,
                )

            self.assertIs(
                caught.exception.record.status,
                ExecutionStatus.failed_preflight,
            )
            self.assertEqual(
                caught.exception.record.error_type,
                "PseudopotentialNotFoundError",
            )
            self.assertTrue(caught.exception.record_path.is_file())
            self.assertFalse((working_directory / "pw.out").exists())


def _prepared_input_and_library(
    working_directory: Path,
) -> tuple[CalculatorInputRecord, QePseudopotentialFile, PseudopotentialLibrary]:
    pseudopotential = _pseudopotential_file()
    content = (
        b"&CONTROL\n calculation = 'scf'\n pseudo_dir = './'\n outdir = './tmp/'\n/\n"
    )
    prepared = CalculatorInputRecord(
        input_id="Si.QE.PreparedInput",
        schema_version=1,
        source=CalculatorInputSourceReference(
            simulation_id="Si.QE.SCF",
            representation="projectkoios.pw-dft-scf+json",
            schema_version=1,
            byte_size=100,
            sha256="1" * 64,
        ),
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        calculator_name="Quantum ESPRESSO pw.x",
        calculator_version_constraint=">=7.5,<8",
        representation="quantum-espresso-pw-input",
        artifacts=(
            CalculatorInputArtifact(
                role="primary-input",
                filename="pw.in",
                media_type="text/plain; charset=us-ascii",
                content=content,
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
        ),
        external_requirements=(
            CalculatorExternalInputRequirement(
                role="pseudopotential",
                stable_id=f"Si.{pseudopotential.sha256}",
                filename=pseudopotential.filename,
                format="upf;version=2.0.1",
                byte_size=pseudopotential.byte_size,
                sha256=pseudopotential.sha256,
                provenance="canonical-simulation-specification:" + "1" * 64,
                element_symbol="Si",
            ),
        ),
        mappings=(),
        preparation_operation="projectkoios.qe.pw.scf.prepare",
        preparation_version="1",
    )
    # The directory exists but intentionally lacks the exact required bytes, so
    # execution preflight exercises PseudopotentialLibrary's fail-closed lookup.
    return prepared, pseudopotential, PseudopotentialLibrary(working_directory)


def _pseudopotential_file() -> QePseudopotentialFile:
    content = b"expected pseudopotential"
    return QePseudopotentialFile(
        pseudopotential=QePseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="ONCVPSP",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
            upf_version="2.0.1",
        ),
        filename="Si.upf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
    )


if __name__ == "__main__":
    unittest.main()
