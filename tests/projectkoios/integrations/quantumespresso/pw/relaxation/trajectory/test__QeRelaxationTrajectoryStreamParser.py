from __future__ import annotations

import io
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
)
from projectkoios.integrations.quantumespresso.pw.relaxation._stream import (
    QeRelaxationStdoutTee,
    QeRelaxationTrajectoryStreamParser,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.trajectory import (
    QeRelaxationTrajectoryParser,
)

_OUTPUT = b"""Program PWSCF v.7.5 starts on 1Jan2026
irrelevant diagnostic text
! total energy = -10.000000D+00 Ry
convergence has been achieved in 5 iterations
atom 1 type 1 force = 0.100000 0.000000 0.000000
atom 2 type 1 force = -0.100000 0.000000 0.000000
Total force = 0.141421 Total SCF correction = 0.000002
number of scf cycles = 1
number of bfgs steps = 0
energy new = -10.000000D+00 Ry
ATOMIC_POSITIONS (alat)
Si 0.010000 0.000000 0.000000
Si 0.240000 0.250000 0.250000

more irrelevant diagnostic text
! total energy = -10.100000 Ry
convergence has been achieved in 3 iterations
atom 1 type 1 force = 0.001000 0.000000 0.000000
atom 2 type 1 force = -0.001000 0.000000 0.000000
Total force = 0.001414 Total SCF correction = 0.000001
Begin final coordinates
ATOMIC_POSITIONS (alat)
Si 0.011000 0.000000 0.000000
Si 0.239000 0.250000 0.250000
End final coordinates
JOB DONE.
"""


def _summary(payload: bytes):  # type: ignore[no-untyped-def]
    return QePwStdoutFileParser().parse(
        payload,
        output_file=QePwStdoutFile.from_prefix(prefix="silicon"),
    )


class QeRelaxationTrajectoryStreamParserTest(unittest.TestCase):
    def test_chunk_boundaries_do_not_change_the_trajectory(self) -> None:
        expected = QeRelaxationTrajectoryParser().parse(
            _OUTPUT,
            calculation="relax",
            summary=_summary(_OUTPUT),
        )

        for chunk_size in (1, 2, 7, 4096, len(_OUTPUT)):
            with self.subTest(chunk_size=chunk_size):
                parser = QeRelaxationTrajectoryStreamParser(calculation="relax")
                for offset in range(0, len(_OUTPUT), chunk_size):
                    parser.feed(_OUTPUT[offset : offset + chunk_size])
                observed = parser.finish(summary=_summary(_OUTPUT))
                self.assertEqual(observed, expected)
                self.assertLess(parser.retained_byte_count, len(_OUTPUT))

    def test_tee_writes_exact_bytes_and_parses_the_same_stream(self) -> None:
        source = io.BytesIO(_OUTPUT)
        destination = io.BytesIO()
        parser = QeRelaxationTrajectoryStreamParser(calculation="relax")

        byte_count = QeRelaxationStdoutTee(chunk_size=17).copy(
            source,
            destination,
            parser,
        )
        trajectory = parser.finish(summary=_summary(_OUTPUT))

        self.assertEqual(byte_count, len(_OUTPUT))
        self.assertEqual(destination.getvalue(), _OUTPUT)
        self.assertEqual(len(trajectory.steps), 2)

    def test_subprocess_output_larger_than_a_pipe_buffer_is_drained(self) -> None:
        noise = b"unretained calculator diagnostic\n" * 100_000
        payload = noise + _OUTPUT
        parser = QeRelaxationTrajectoryStreamParser(calculation="relax")

        with TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "pw.out"
            process = subprocess.Popen(
                (
                    sys.executable,
                    "-c",
                    "import sys; sys.stdout.buffer.write("
                    + repr(b"unretained calculator diagnostic\n")
                    + " * 100000 + "
                    + repr(_OUTPUT)
                    + ")",
                ),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            assert process.stdout is not None
            with output_path.open("wb") as destination:
                byte_count = QeRelaxationStdoutTee(chunk_size=8192).copy(
                    process.stdout,
                    destination,
                    parser,
                )
            stderr = process.stderr.read() if process.stderr is not None else b""
            returncode = process.wait(timeout=10.0)
            persisted = output_path.read_bytes()

        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, b"")
        self.assertEqual(byte_count, len(payload))
        self.assertEqual(persisted, payload)
        trajectory = parser.finish(summary=_summary(payload))
        self.assertEqual(len(trajectory.steps), 2)
        self.assertLess(parser.retained_byte_count, len(payload) // 100)

    def test_final_line_does_not_require_a_newline(self) -> None:
        payload = b"Program PWSCF v.7.5\n! total energy = -1.0 Ry"
        parser = QeRelaxationTrajectoryStreamParser(calculation="relax")
        parser.feed(payload)

        trajectory = parser.finish(summary=_summary(payload))

        self.assertEqual(len(trajectory.steps), 1)
        self.assertEqual(trajectory.steps[0].total_energy_ry, -1.0)

    def test_rejects_feed_after_finish(self) -> None:
        payload = b"Program PWSCF v.7.5\n"
        parser = QeRelaxationTrajectoryStreamParser(calculation="relax")
        parser.feed(payload)
        parser.finish(summary=_summary(payload))

        with self.assertRaisesRegex(RuntimeError, "already finished"):
            parser.feed(b"more")


if __name__ == "__main__":
    unittest.main()
