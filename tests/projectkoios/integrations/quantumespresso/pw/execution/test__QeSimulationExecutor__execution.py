from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.execution import QeSimulationExecutor
from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.calculator.input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputRecord,
    CalculatorInputSourceReference,
)
from projectkoios.simulations.dft.pseudopotential.library import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.execution import (
    CalculatorExecutableBinding,
    CalculatorExecutableIdentity,
    CalculatorExecutionError,
    ExecutionStatus,
)

pytestmark = pytest.mark.integration


class TestQeSimulationExecutor:
    """Verify exact QE staging and explicit execution authority.

    Notes
    -----
    Execution tests use deterministic shell fixtures only. They do not invoke
    Quantum ESPRESSO or establish scientific validity.
    """

    def _executable_binding(
        self,
        path: Path,
        *,
        calculator_version: str = "fixture-1",
        expected_content: bytes | None = None,
    ) -> CalculatorExecutableBinding:
        """Bind one absolute executable path to exact expected bytes.

        Parameters
        ----------
        path
            Absolute executable deployment path.
        calculator_version
            Exact declared fixture or program version.
        expected_content
            Expected bytes, or the current file bytes when omitted.

        Returns
        -------
        CalculatorExecutableBinding
            Exact executable identity and deployment binding.
        """
        content = path.read_bytes() if expected_content is None else expected_content
        return CalculatorExecutableBinding(
            identity=CalculatorExecutableIdentity(
                calculator_name="controlled pw.x executable",
                calculator_version=calculator_version,
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
            path=path,
        )

    def _pseudopotential_file(self) -> tuple[QePseudopotentialFile, bytes]:
        """Return one exact controlled pseudopotential requirement and bytes."""
        content = b"expected pseudopotential"
        return (
            QePseudopotentialFile(
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
            ),
            content,
        )

    def _prepared_input_and_library(
        self,
        root: Path,
        *,
        preparation_operation: str = "projectkoios.qe.pw.scf.prepare",
        install_pseudopotential: bool = False,
    ) -> tuple[
        CalculatorInputRecord,
        QePseudopotentialFile,
        PseudopotentialLibrary,
    ]:
        """Construct exact controlled input and an explicit deployment library."""
        pseudopotential, pseudopotential_bytes = self._pseudopotential_file()
        content = (
            b"&CONTROL\n calculation = 'scf'\n pseudo_dir = './'\n"
            b" outdir = './tmp/'\n/\n"
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
            preparation_operation=preparation_operation,
            preparation_version="1",
        )
        library_root = root / "pseudopotential-library"
        library_root.mkdir()
        if install_pseudopotential:
            (library_root / pseudopotential.filename).write_bytes(pseudopotential_bytes)
        return prepared, pseudopotential, PseudopotentialLibrary(library_root)

    def test__QeSimulationExecutor__requires_explicit_authorization(self) -> None:
        """Reject execution before inspecting or staging deployment resources."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory
            )
            executable = self._executable_binding(
                Path(sys.executable).resolve(strict=True),
                calculator_version=sys.version.split()[0],
            )

            with pytest.raises(PermissionError, match="not authorized"):
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                )

            assert {path.name for path in working_directory.iterdir()} == {
                "pseudopotential-library"
            }

    def test__QeSimulationExecutor__accepts_relaxation_preparation(self) -> None:
        """Admit the maintained relaxation preparation operation before authority."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory,
                preparation_operation="projectkoios.qe.pw.relaxation.prepare",
            )
            executable = self._executable_binding(
                Path(sys.executable).resolve(strict=True),
                calculator_version=sys.version.split()[0],
            )

            with pytest.raises(PermissionError, match="not authorized"):
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                )

    def test__QeSimulationExecutor__records_missing_library_artifact(self) -> None:
        """Record exact pseudopotential resolution failure before process entry."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory
            )
            executable = self._executable_binding(
                Path(sys.executable).resolve(strict=True),
                calculator_version=sys.version.split()[0],
            )

            with pytest.raises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                    execution_authorized=True,
                )

            assert caught.value.record.status is ExecutionStatus.failed_preflight
            assert caught.value.record.error_type == "PseudopotentialNotFoundError"
            assert caught.value.record_path.is_file()
            assert not (working_directory / "pw.out").exists()

    def test__QeSimulationExecutor__records_executable_identity_mismatch(self) -> None:
        """Fail preflight when deployed executable bytes differ from identity."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory,
                install_pseudopotential=True,
            )
            executable = self._executable_binding(
                Path(sys.executable).resolve(strict=True),
                expected_content=b"not the deployed executable",
            )

            with pytest.raises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                    execution_authorized=True,
                )

            assert caught.value.record.status is ExecutionStatus.failed_preflight
            assert caught.value.record.error_type == "ValueError"
            assert caught.value.record.error_message is not None
            assert "executable preparation failed" in caught.value.record.error_message
            assert not (working_directory / ".projectkoios-pw.x").exists()

    def test__QeSimulationExecutor__rejects_private_copy_overwrite(self) -> None:
        """Fail preflight rather than overwrite an existing private executable."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory,
                install_pseudopotential=True,
            )
            source = working_directory / "controlled-pw.x"
            source.write_bytes(b"#!/bin/sh\nexit 0\n")
            source.chmod(0o500)
            executable = self._executable_binding(source)
            staged = working_directory / ".projectkoios-pw.x"
            existing_content = b"retained deployment artifact"
            staged.write_bytes(existing_content)

            with pytest.raises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                    execution_authorized=True,
                )

            assert caught.value.record.status is ExecutionStatus.failed_preflight
            assert caught.value.record.error_type == "FileExistsError"
            assert staged.read_bytes() == existing_content

    def test__QeSimulationExecutor__reverifies_private_copy(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reject a private copy changed before its post-publication recheck."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory,
                install_pseudopotential=True,
            )
            source = working_directory / "controlled-pw.x"
            source.write_bytes(b"#!/bin/sh\nexit 0\n")
            source.chmod(0o500)
            executable = self._executable_binding(source)
            original_link = os.link

            def publish_then_corrupt(source_path: str, destination_path: str) -> None:
                original_link(source_path, destination_path)
                destination = Path(destination_path)
                destination.chmod(0o700)
                destination.write_bytes(b"changed after publication")
                destination.chmod(0o500)

            monkeypatch.setattr(os, "link", publish_then_corrupt)

            with pytest.raises(CalculatorExecutionError) as caught:
                QeSimulationExecutor().execute(
                    prepared,
                    (pseudopotential,),
                    library,
                    executable,
                    working_directory,
                    execution_authorized=True,
                )

            assert caught.value.record.status is ExecutionStatus.failed_preflight
            assert caught.value.record.error_message is not None
            assert "staged executable verification failed" in (
                caught.value.record.error_message
            )

    def test__QeSimulationExecutor__executes_verified_private_copy(self) -> None:
        """Execute a verified private copy while preserving the execution wire."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            working_directory = Path(temporary_directory)
            prepared, pseudopotential, library = self._prepared_input_and_library(
                working_directory,
                install_pseudopotential=True,
            )
            source = working_directory / "controlled-pw.x"
            source.write_bytes(b"#!/bin/sh\nprintf 'controlled stdout\\n'\n")
            source.chmod(0o500)
            executable = self._executable_binding(source)

            record = QeSimulationExecutor().execute(
                prepared,
                (pseudopotential,),
                library,
                executable,
                working_directory,
                execution_authorized=True,
            )

            staged = working_directory / ".projectkoios-pw.x"
            assert record.status is ExecutionStatus.succeeded
            assert record.command[0] == str(staged)
            assert staged.read_bytes() == source.read_bytes()
            assert staged.stat().st_mode & 0o777 == 0o500
            assert (working_directory / "pw.out").read_bytes() == (
                b"controlled stdout\n"
            )
            execution_payload = json.loads(
                (working_directory / "execution.json").read_text(encoding="utf-8")
            )
            assert set(execution_payload) == {
                "command",
                "error_message",
                "error_type",
                "required_input_filenames",
                "returncode",
                "schema_version",
                "status",
                "stderr_filename",
                "stdout_filename",
                "working_directory",
            }
            assert execution_payload["schema_version"] == 1
