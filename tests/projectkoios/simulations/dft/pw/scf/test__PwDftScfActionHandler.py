from __future__ import annotations

import unittest

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.scf.actions import (
    AnalyzePwDftScfOutput,
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfAction,
    PwDftScfNativeArtifact,
    PwDftScfObservation,
    PwDftScfRequest,
)
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfOutputAnalyzed,
    PwDftScfTaskCompleted,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.dft.pw.scf.handler import (
    MockPwDftScfActionHandler,
    MockPwDftScfTask,
    PwDftScfActionHandler,
    ReplayPwDftScfActionHandler,
    ReplayPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.integration import (
    PwDftScfInputProjection,
    PwDftScfIntegration,
)


class PwDftScfActionHandlerTest(unittest.TestCase):
    def test_mock_handler_drives_the_common_action_contract(self) -> None:
        observation = _observation()
        handler = MockPwDftScfActionHandler(
            tasks=(
                MockPwDftScfTask(
                    evaluation_id="silicon-scf",
                    task_id="task",
                    output_artifact_id="mock/output",
                    observation=observation,
                ),
            )
        )

        registered = handler.handle(RegisterPwDftScfTask(evaluation_id="silicon-scf"))
        submitted = handler.handle(SubmitPwDftScfTask(task_id="task"))
        analyzed = handler.handle(
            AnalyzePwDftScfOutput(
                task_id="task",
                output_artifact_id="mock/output",
            )
        )

        self.assertEqual(
            registered,
            (
                PwDftScfTaskRegistered(
                    evaluation_id="silicon-scf",
                    task_id="task",
                ),
            ),
        )
        self.assertEqual(
            submitted,
            (
                PwDftScfTaskSubmitted(task_id="task"),
                PwDftScfTaskCompleted(
                    task_id="task",
                    output_artifact_id="mock/output",
                ),
            ),
        )
        self.assertEqual(
            analyzed,
            (
                PwDftScfOutputAnalyzed(
                    task_id="task",
                    observation=observation,
                ),
            ),
        )

    def test_replay_handler_uses_retained_analysis_without_execution(self) -> None:
        integration = _FakeIntegration(_observation())
        handler = ReplayPwDftScfActionHandler(
            integration=integration,
            tasks=(
                ReplayPwDftScfTask(
                    evaluation_id="silicon-scf",
                    task_id="task",
                    output_artifact_id="retained/output",
                ),
            ),
        )

        events = handler.handle(
            AnalyzePwDftScfOutput(
                task_id="task",
                output_artifact_id="retained/output",
            )
        )

        self.assertEqual(
            events,
            (
                PwDftScfOutputAnalyzed(
                    task_id="task",
                    observation=integration.observation,
                ),
            ),
        )
        self.assertEqual(integration.analyzed_artifact_ids, ["retained/output"])

    def test_concrete_handlers_share_the_nominal_base(self) -> None:
        mock = MockPwDftScfActionHandler(
            tasks=(
                MockPwDftScfTask(
                    evaluation_id="evaluation",
                    task_id="task",
                    output_artifact_id="mock/output",
                    observation=_observation(),
                ),
            )
        )
        replay = ReplayPwDftScfActionHandler(
            integration=_FakeIntegration(_observation()),
            tasks=(
                ReplayPwDftScfTask(
                    evaluation_id="evaluation",
                    task_id="task",
                    output_artifact_id="retained/output",
                ),
            ),
        )

        self.assertIsInstance(mock, PwDftScfActionHandler)
        self.assertIsInstance(replay, PwDftScfActionHandler)
        with self.assertRaisesRegex(TypeError, "unsupported SCF action"):
            mock.handle(PwDftScfAction())


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


class _FakeIntegration(PwDftScfIntegration):
    __slots__ = ("analyzed_artifact_ids", "observation")

    def __init__(self, observation: PwDftScfObservation) -> None:
        self.observation = observation
        self.analyzed_artifact_ids: list[str] = []

    @property
    def integration_id(self) -> CalculatorIntegrationId:
        return CalculatorIntegrationId(value="fake")

    def project(self, request: PwDftScfRequest) -> PwDftScfInputProjection:
        raise NotImplementedError

    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        self.analyzed_artifact_ids.append(output_artifact_id)
        return self.observation


if __name__ == "__main__":
    unittest.main()
