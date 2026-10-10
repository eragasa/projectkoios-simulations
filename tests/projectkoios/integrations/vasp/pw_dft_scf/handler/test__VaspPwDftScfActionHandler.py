from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.handler import (
    VaspPwDftScfActionHandler,
    VaspPwDftScfTask,
)
from projectkoios.integrations.vasp.pw_dft_scf.integration import (
    VaspScfIntegration,
)
from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskCompleted,
    PwDftScfTaskFailed,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.dft.pw.scf.handler import (
    PwDftScfActionHandler,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    ExecutionStatus,
)
from tests.projectkoios.integrations.vasp.outcar import (
    test__VaspOutcarParser as outcar_test,
)
from tests.support.repository_root import REPOSITORY_ROOT

pytestmark = pytest.mark.integration

_FAILURE_EVIDENCE = (
    REPOSITORY_ROOT / "examples/projectkoios/integrations/vasp/pw_dft_scf/"
    "Si/primitive/evidence/failures/negative-lattice-orientation"
)


class VaspPwDftScfActionHandlerTest(unittest.TestCase):
    def test_is_a_concrete_common_handler_and_analyzes_retained_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            (run / "OUTCAR").write_text(outcar_test.OUTCAR, encoding="utf-8")
            (run / "execution.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "succeeded",
                        "returncode": 0,
                    }
                ),
                encoding="utf-8",
            )
            handler = _handler(root, run)

            registered = handler.handle(
                RegisterPwDftScfTask(evaluation_id="silicon-scf")
            )
            analyzed = handler.handle(
                AnalyzePwDftScfOutput(
                    task_id="vasp-task",
                    output_artifact_id="run/OUTCAR",
                )
            )

        self.assertIsInstance(handler, PwDftScfActionHandler)
        self.assertEqual(
            registered,
            (
                PwDftScfTaskRegistered(
                    evaluation_id="silicon-scf",
                    task_id="vasp-task",
                ),
            ),
        )
        self.assertIsInstance(analyzed[0], PwDftScfOutputAnalyzed)

    def test_negative_lattice_error_becomes_a_correlated_failure(self) -> None:
        handler = _handler(
            _FAILURE_EVIDENCE,
            _FAILURE_EVIDENCE,
            output_artifact_id="OUTCAR",
        )

        (event,) = handler.handle(
            AnalyzePwDftScfOutput(
                task_id="vasp-task",
                output_artifact_id="OUTCAR",
            )
        )

        self.assertIsInstance(event, PwDftScfTaskFailed)
        assert isinstance(event, PwDftScfTaskFailed)
        self.assertEqual(event.code, "negative-lattice-orientation")
        self.assertIn("triple product", event.message)

    def test_submit_is_fail_closed_without_explicit_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            handler = _handler(root, run)

            with (
                patch.object(CalculatorExecutor, "action") as action,
                self.assertRaisesRegex(PermissionError, "not authorized"),
            ):
                handler.handle(SubmitPwDftScfTask(task_id="vasp-task"))

            action.assert_not_called()

    def test_submit_composes_the_bounded_executor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            handler = _handler(root, run, execution_authorized=True)
            record = _execution_record(
                run=run,
                status=ExecutionStatus.succeeded,
                returncode=0,
            )

            with patch.object(CalculatorExecutor, "action", return_value=record):
                events = handler.handle(SubmitPwDftScfTask(task_id="vasp-task"))

        self.assertEqual(
            events,
            (
                PwDftScfTaskSubmitted(task_id="vasp-task"),
                PwDftScfTaskCompleted(
                    task_id="vasp-task",
                    output_artifact_id="run/OUTCAR",
                ),
            ),
        )

    def test_recorded_execution_failure_becomes_a_correlated_event(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            handler = _handler(root, run, execution_authorized=True)
            record = _execution_record(
                run=run,
                status=ExecutionStatus.failed,
                returncode=2,
            )
            error = CalculatorExecutionError(
                record=record,
                record_path=run / "execution.json",
            )

            with patch.object(CalculatorExecutor, "action", side_effect=error):
                events = handler.handle(SubmitPwDftScfTask(task_id="vasp-task"))

        self.assertIsInstance(events[0], PwDftScfTaskSubmitted)
        self.assertIsInstance(events[1], PwDftScfTaskFailed)
        assert isinstance(events[1], PwDftScfTaskFailed)
        self.assertEqual(events[1].code, "calculator-failed")


def _handler(
    root: Path,
    run: Path,
    *,
    output_artifact_id: str = "run/OUTCAR",
    execution_authorized: bool = False,
) -> VaspPwDftScfActionHandler:
    integration = VaspScfIntegration(
        artifact_root=root,
        projection_configuration=VaspScfProjectionConfiguration(),
    )
    request = CalculatorExecutionRequest(
        command=("/not/executed/vasp",),
        working_directory=run,
        execution_authorized=execution_authorized,
    )
    return VaspPwDftScfActionHandler(
        integration=integration,
        tasks=(
            VaspPwDftScfTask(
                evaluation_id="silicon-scf",
                task_id="vasp-task",
                output_artifact_id=output_artifact_id,
                execution_request=request,
            ),
        ),
    )


def _execution_record(
    run: Path,
    status: ExecutionStatus,
    returncode: int,
) -> CalculatorExecutionRecord:
    return CalculatorExecutionRecord(
        command=("/not/executed/vasp",),
        working_directory=str(run),
        status=status,
        returncode=returncode,
        stdout_filename="stdout.txt",
        stderr_filename="stderr.txt",
        required_input_filenames=(),
    )


if __name__ == "__main__":
    unittest.main()
