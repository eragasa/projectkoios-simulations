from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from projectkoios.integrations.quantumespresso.epw.execution import (
    QeEpwRunner,
    QeEpwRunRequest,
    QeEpwStagedInput,
)
from projectkoios.integrations.quantumespresso.epw.input import (
    QeEpwInputAssignment,
    QeEpwInputConfiguration,
    QeEpwInputRenderer,
    QeEpwRenderedInput,
)


class QeEpwRunnerTest(unittest.TestCase):
    def test_render_only_requires_no_execution_resources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "rendered"

            result = QeEpwRunner().run(
                QeEpwRunRequest(
                    rendered_input=_rendered_input(),
                    output_directory=output,
                )
            )

            self.assertFalse(result.execution_requested)
            self.assertIsNone(result.artifact_manifest)
            self.assertIsNone(result.stream_observation)
            self.assertTrue((output / "epw.in").is_file())
            self.assertTrue(result.input_manifest.is_file())
            self.assertFalse((output / "execution.json").exists())

    def test_executes_stub_after_verifying_and_staging_exact_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run"
            parent = root / "parent.dat"
            parent.write_bytes(b"verified parent state\n")
            executable = root / "epw.x"
            executable.write_text(
                "#!/bin/sh\n"
                "test -f state/parent.dat || exit 7\n"
                "printf 'native output\\n' > linewidth.dat\n"
                "printf 'Program EPW v.5.9 starts\\n'\n"
                "printf 'Electron-Phonon interpolation\\n'\n"
                "printf 'Total program execution\\n'\n"
                "printf 'EPW : 1.0s CPU 1.1s WALL\\n'\n"
                "printf 'JOB DONE.\\n'\n",
                encoding="ascii",
            )
            executable.chmod(0o755)
            executable_payload = executable.read_bytes()
            parent_payload = parent.read_bytes()

            result = QeEpwRunner().run(
                QeEpwRunRequest(
                    rendered_input=_rendered_input(),
                    output_directory=output,
                    execute=True,
                    executable=executable,
                    executable_sha256=hashlib.sha256(executable_payload).hexdigest(),
                    executable_byte_size=len(executable_payload),
                    staged_inputs=(
                        QeEpwStagedInput(
                            source=parent,
                            relative_path="state/parent.dat",
                            sha256=hashlib.sha256(parent_payload).hexdigest(),
                            byte_size=len(parent_payload),
                        ),
                    ),
                    timeout_seconds=30.0,
                )
            )

            self.assertTrue(result.execution_requested)
            self.assertTrue((output / "state/parent.dat").is_file())
            self.assertTrue((output / "linewidth.dat").is_file())
            self.assertIsNotNone(result.stream_observation)
            assert result.stream_observation is not None
            self.assertEqual(result.stream_observation.program_version, "5.9")
            self.assertTrue(result.stream_observation.job_done)
            self.assertTrue(result.stream_observation.total_program_execution_reported)
            self.assertEqual(result.stream_observation.fatal_diagnostics, ())
            assert result.artifact_manifest is not None
            artifact_manifest = json.loads(result.artifact_manifest.read_text())
            self.assertEqual(artifact_manifest["execution_status"], "succeeded")
            self.assertIn("execution.json", artifact_manifest["artifacts"])

    def test_identity_failure_precedes_output_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "run"
            executable = root / "epw.x"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
            executable.chmod(0o755)
            payload = executable.read_bytes()

            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                QeEpwRunner().run(
                    QeEpwRunRequest(
                        rendered_input=_rendered_input(),
                        output_directory=output,
                        execute=True,
                        executable=executable,
                        executable_sha256="0" * 64,
                        executable_byte_size=len(payload),
                        timeout_seconds=30.0,
                    )
                )

            self.assertFalse(output.exists())

    def test_execution_resources_require_explicit_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "epw.x"
            with self.assertRaisesRegex(ValueError, "execute=True"):
                QeEpwRunRequest(
                    rendered_input=_rendered_input(),
                    output_directory=Path(directory) / "run",
                    executable=executable,
                    executable_sha256="0" * 64,
                    executable_byte_size=1,
                )


def _rendered_input() -> QeEpwRenderedInput:
    return QeEpwInputRenderer().render(
        QeEpwInputConfiguration(
            assignments=(
                QeEpwInputAssignment("prefix", "si"),
                QeEpwInputAssignment("outdir", "./tmp"),
                QeEpwInputAssignment("elph", True),
            )
        )
    )


if __name__ == "__main__":
    unittest.main()
