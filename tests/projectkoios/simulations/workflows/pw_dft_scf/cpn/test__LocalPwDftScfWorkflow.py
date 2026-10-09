from __future__ import annotations

import unittest

from projectkoios.simulations.dft.pw.scf.actions import (
    RegisterPwDftScfTask,
    SubmitPwDftScfTask,
)
from projectkoios.simulations.dft.pw.scf.base import PwDftScfWorkflowFailed
from projectkoios.simulations.dft.pw.scf.events import (
    PwDftScfTaskFailed,
    PwDftScfTaskRegistered,
    PwDftScfTaskSubmitted,
)
from projectkoios.simulations.workflows.pw_dft_scf.configuration import (
    PwDftScfRuntimeConfiguration,
)
from projectkoios.simulations.workflows.pw_dft_scf.cpn.workflow import (
    LocalPwDftScfWorkflow,
)
from projectkoios.simulations.workflows.pw_dft_scf.workflow.base import (
    PwDftScfWorkflowStatus,
)


class LocalPwDftScfWorkflowTest(unittest.TestCase):
    def test_replays_deterministic_failure_lifecycle_without_calculator(self) -> None:
        workflow = LocalPwDftScfWorkflow(
            "silicon-scf",
            PwDftScfRuntimeConfiguration(maximum_internal_firings=20),
        )
        self.assertEqual(
            workflow.pending_actions(),
            (RegisterPwDftScfTask("silicon-scf"),),
        )

        self.assertEqual(
            workflow.accept(PwDftScfTaskRegistered("silicon-scf", "task-1")),
            ("accept_registration",),
        )
        self.assertEqual(workflow.pending_actions(), (SubmitPwDftScfTask("task-1"),))
        self.assertEqual(
            workflow.accept(PwDftScfTaskSubmitted("task-1")),
            ("accept_submission",),
        )
        self.assertEqual(
            workflow.status(),
            PwDftScfWorkflowStatus.waiting_for_completion,
        )
        self.assertEqual(
            workflow.accept(
                PwDftScfTaskFailed("task-1", "provider-failure", "synthetic failure")
            ),
            ("accept_failure",),
        )
        self.assertEqual(workflow.status(), PwDftScfWorkflowStatus.terminated)
        self.assertIsInstance(workflow.outcome(), PwDftScfWorkflowFailed)


if __name__ == "__main__":
    unittest.main()
