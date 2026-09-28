from __future__ import annotations

import unittest

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfNativeArtifact,
    PwDftScfObservation,
    PwDftScfResult,
    PwDftScfWorkflowFailed,
    PwDftScfWorkflowSucceeded,
)
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskCompleted,
    PwDftScfTaskFailed,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)


class PwDftScfRecordsTest(unittest.TestCase):
    def test_rejects_malformed_action_identities(self) -> None:
        invalid_actions = (
            lambda: RegisterPwDftScfTask(evaluation_id="not a slug"),
            lambda: SubmitPwDftScfTask(task_id=" task "),
            lambda: AnalyzePwDftScfOutput(
                task_id="task",
                output_artifact_id="",
            ),
        )

        for construct in invalid_actions:
            with self.subTest(construct=construct), self.assertRaises(ValueError):
                construct()

    def test_rejects_malformed_event_identities_and_payloads(self) -> None:
        invalid_events = (
            lambda: PwDftScfTaskRegistered(
                evaluation_id="not a slug",
                task_id="task",
            ),
            lambda: PwDftScfTaskSubmitted(task_id=" task "),
            lambda: PwDftScfTaskCompleted(
                task_id="task",
                output_artifact_id="",
            ),
            lambda: PwDftScfOutputAnalyzed(
                task_id="task",
                observation="not-an-observation",  # type: ignore[arg-type]
            ),
            lambda: PwDftScfTaskFailed(
                task_id="task",
                code="not a slug",
                message="failed",
            ),
        )

        for construct in invalid_events:
            with (
                self.subTest(construct=construct),
                self.assertRaises((TypeError, ValueError)),
            ):
                construct()

    def test_rejects_malformed_result_and_outcome_payloads(self) -> None:
        with self.assertRaisesRegex(ValueError, "evaluation_id"):
            PwDftScfResult(
                evaluation_id="",
                task_id="task",
                observation=_observation(),
            )
        with self.assertRaisesRegex(ValueError, "task_id"):
            PwDftScfResult(
                evaluation_id="silicon-scf",
                task_id=" task ",
                observation=_observation(),
            )
        with self.assertRaisesRegex(TypeError, "observation"):
            PwDftScfResult(
                evaluation_id="silicon-scf",
                task_id="task",
                observation="not-an-observation",  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(TypeError, "result"):
            PwDftScfWorkflowSucceeded(result="not-a-result")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "failure message"):
            PwDftScfWorkflowFailed(
                evaluation_id="silicon-scf",
                code="execution-failed",
                message="",
            )


def _observation() -> PwDftScfObservation:
    return PwDftScfObservation(
        total_energy_ev=-10.0,
        atom_count=2,
        electronic_iteration_count=4,
        converged=True,
        completed=True,
        native_artifact=PwDftScfNativeArtifact(
            integration_id=CalculatorIntegrationId(value="mock"),
            artifact_id="mock/output",
            sha256="a" * 64,
            byte_size=100,
        ),
    )


if __name__ == "__main__":
    unittest.main()
