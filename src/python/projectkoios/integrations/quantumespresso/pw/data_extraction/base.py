"""Common exact-artifact and captured-stream extraction for ``pw.x`` modes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from projectkoios.integrations.quantumespresso.outputs.pw_stderr import (
    QePwStderrFile,
    QePwStderrFileParser,
    QePwStderrFileResult,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFile,
    QePwStdoutFileParser,
    QePwStdoutFileResult,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class QePwNativeArtifact:
    """Identify one exact native ``pw.x`` artifact by relative path and bytes."""

    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if type(self.relative_path) is not str or not self.relative_path:
            raise ValueError("relative_path must be a nonempty string")
        path = PurePosixPath(self.relative_path)
        if (
            "\\" in self.relative_path
            or path.is_absolute()
            or path == PurePosixPath(".")
            or ".." in path.parts
        ):
            raise ValueError("relative_path must be a safe relative POSIX path")
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class QePwCapturedStreamData:
    """Retain parsed native streams alongside exact supporting identities."""

    stdout_artifact: QePwNativeArtifact
    stderr_artifact: QePwNativeArtifact
    stdout: QePwStdoutFileResult
    stderr: QePwStderrFileResult

    def __post_init__(self) -> None:
        if type(self.stdout_artifact) is not QePwNativeArtifact:
            raise TypeError("stdout_artifact must be a QePwNativeArtifact")
        if type(self.stderr_artifact) is not QePwNativeArtifact:
            raise TypeError("stderr_artifact must be a QePwNativeArtifact")
        if type(self.stdout) is not QePwStdoutFileResult:
            raise TypeError("stdout must be a QePwStdoutFileResult")
        if type(self.stderr) is not QePwStderrFileResult:
            raise TypeError("stderr must be a QePwStderrFileResult")
        if self.stdout.output_file.relative_path != self.stdout_artifact.relative_path:
            raise ValueError("stdout result and artifact paths disagree")
        if self.stderr.output_file.relative_path != self.stderr_artifact.relative_path:
            raise ValueError("stderr result and artifact paths disagree")


@dataclass(frozen=True, slots=True)
class QePwCapturedStreamDataExtractor:
    """Extract reusable native stream data without deciding mode acceptance."""

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        stdout_relative_path: str = "pw.out",
        stderr_relative_path: str = "pw.err",
    ) -> QePwCapturedStreamData:
        """Parse exact captured bytes and bind their cryptographic identities."""
        if type(stdout_payload) is not bytes or type(stderr_payload) is not bytes:
            raise TypeError("captured stream payloads must be bytes")
        stdout_artifact = self._artifact(stdout_relative_path, stdout_payload)
        stderr_artifact = self._artifact(stderr_relative_path, stderr_payload)
        stdout = QePwStdoutFileParser().parse(
            stdout_payload,
            output_file=QePwStdoutFile(relative_path=stdout_relative_path),
        )
        stderr = QePwStderrFileParser().parse(
            stderr_payload,
            output_file=QePwStderrFile(relative_path=stderr_relative_path),
        )
        return QePwCapturedStreamData(
            stdout_artifact=stdout_artifact,
            stderr_artifact=stderr_artifact,
            stdout=stdout,
            stderr=stderr,
        )

    @staticmethod
    def _artifact(relative_path: str, payload: bytes) -> QePwNativeArtifact:
        return QePwNativeArtifact(
            relative_path=relative_path,
            sha256=hashlib.sha256(payload).hexdigest(),
            byte_size=len(payload),
        )
