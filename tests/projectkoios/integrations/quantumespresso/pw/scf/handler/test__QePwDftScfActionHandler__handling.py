from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from projectkoios.integrations.quantumespresso.pw.execution import (
    QeSimulationExecutor,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    configuration as qe_configuration,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    handler as qe_handler,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    integration as qe_integration,
)
from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskFailed,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.dft.pw.scf.handler import (
    PwDftScfActionHandler,
)
from projectkoios.simulations.execution import (
    CalculatorExecutableBinding,
    CalculatorExecutableIdentity,
    CalculatorExecutionError,
    CalculatorExecutionRecord,
    ExecutionStatus,
)
from tests.projectkoios.integrations.quantumespresso.pw.scf import (
    support as qe_support,
)

pytestmark = pytest.mark.integration


class TestQePwDftScfActionHandler(unittest.TestCase):
    """Verify QE composition of the common SCF action lifecycle."""

    def test__QePwDftScfActionHandler__analyzes_retained_output(self) -> None:
        """Analyze retained QE output through the common handler contract."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = self._successful_run(root)
            handler = self._handler(root, run)

            registered = handler.handle(
                RegisterPwDftScfTask(evaluation_id="silicon-qe")
            )
            analyzed = handler.handle(
                AnalyzePwDftScfOutput(
                    task_id="qe-task",
                    output_artifact_id="run/pw.out",
                )
            )

        self.assertIsInstance(handler, PwDftScfActionHandler)
        self.assertEqual(
            registered,
            (
                PwDftScfTaskRegistered(
                    evaluation_id="silicon-qe",
                    task_id="qe-task",
                ),
            ),
        )
        self.assertIsInstance(analyzed[0], PwDftScfOutputAnalyzed)

    def test__QePwDftScfActionHandler__requires_authorization(self) -> None:
        """Reject task submission before invoking the provider executor."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            handler = self._handler(root, run)

            with (
                patch.object(QeSimulationExecutor, "execute") as execute,
                self.assertRaisesRegex(PermissionError, "not authorized"),
            ):
                handler.handle(SubmitPwDftScfTask(task_id="qe-task"))

            execute.assert_not_called()

    def test__QePwDftScfActionHandler__correlates_execution_failure(self) -> None:
        """Translate a recorded provider failure into correlated SCF events."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            handler = self._handler(root, run, execution_authorized=True)
            record = CalculatorExecutionRecord(
                command=(sys.executable, "-in", "pw.in"),
                working_directory=str(run),
                status=ExecutionStatus.failed_preflight,
                returncode=None,
                stdout_filename="pw.out",
                stderr_filename="pw.err",
                required_input_filenames=("pw.in", "Si.upf"),
                error_type="FileNotFoundError",
                error_message="missing pseudopotential",
            )
            error = CalculatorExecutionError(
                record=record,
                record_path=run / "execution.json",
            )

            with patch.object(QeSimulationExecutor, "execute", side_effect=error):
                events = handler.handle(SubmitPwDftScfTask(task_id="qe-task"))

        self.assertIsInstance(events[0], PwDftScfTaskSubmitted)
        self.assertIsInstance(events[1], PwDftScfTaskFailed)
        assert isinstance(events[1], PwDftScfTaskFailed)
        self.assertEqual(events[1].code, "calculator-failed-preflight")

    def _handler(
        self, root: Path, run: Path, *, execution_authorized: bool = False
    ) -> qe_handler.QePwDftScfActionHandler:
        """Construct one controlled QE handler composition."""
        integration = qe_integration.QePwDftScfIntegration(
            artifact_root=root,
            projection_configuration=self._configuration(),
        )
        task = qe_handler.QePwDftScfTask(
            evaluation_id="silicon-qe",
            task_id="qe-task",
            output_artifact_id="run/pw.out",
            prepared_input=qe_support.qe_prepared_input(),
            pseudopotentials=(qe_support.qe_pseudopotential_file(),),
            pseudopotential_library=qe_support.qe_library(root),
            executable=self._executable(),
            working_directory=run,
            execution_authorized=execution_authorized,
        )
        return qe_handler.QePwDftScfActionHandler(
            integration=integration,
            tasks=(task,),
        )

    def _executable(self) -> CalculatorExecutableBinding:
        """Bind the deterministic Python test executable to its exact bytes."""
        path = Path(sys.executable).resolve(strict=True)
        content = path.read_bytes()
        return CalculatorExecutableBinding(
            identity=CalculatorExecutableIdentity(
                calculator_name="Python deterministic test executable",
                calculator_version=sys.version.split()[0],
                byte_size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            ),
            path=path,
        )

    def _configuration(self) -> qe_configuration.QeScfProjectionConfiguration:
        """Return one controlled silicon projection configuration."""
        return qe_configuration.QeScfProjectionConfiguration(
            species=(
                qe_configuration.QeScfSpeciesConfiguration(
                    symbol="Si",
                    mass_amu=28.086,
                    pseudopotential_filename="Si.upf",
                ),
            )
        )

    def _successful_run(self, root: Path) -> Path:
        """Write one retained successful QE fixture under ``root``."""
        run = root / "run"
        run.mkdir()
        (run / "pw.out").write_text(qe_support.QE_PW_OUTPUT, encoding="utf-8")
        (run / "pw.err").write_text("", encoding="utf-8")
        (run / "execution.json").write_text(
            json.dumps(qe_support.QE_SUCCESSFUL_EXECUTION_RECORD),
            encoding="utf-8",
        )
        return run
