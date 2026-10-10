"""Render and explicitly execute identity-bound ``epw.x`` requests."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.epw.input import QeEpwRenderedInput
from projectkoios.integrations.quantumespresso.epw.streams import (
    QeEpwStreamObservation,
    QeEpwStreamParser,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRequest,
    CalculatorExecutor,
)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_STREAM_BYTES = 64 * 1024 * 1024
_RESERVED_PATHS = {
    "artifact-manifest.json",
    "epw.err",
    "epw.out",
    "execution.json",
    "input-manifest.json",
}


@dataclass(frozen=True, slots=True)
class QeEpwStagedInput:
    """Bind one required EPW input artifact to an exact source identity."""

    source: Path
    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.source, Path):
            raise TypeError("source must be a Path")
        _relative_path(self.relative_path)
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("sha256 must be lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class QeEpwRunRequest:
    """Declare rendering and separately authorized EPW execution resources."""

    rendered_input: QeEpwRenderedInput
    output_directory: Path
    execute: bool = False
    executable: Path | None = None
    executable_sha256: str | None = None
    executable_byte_size: int | None = None
    staged_inputs: tuple[QeEpwStagedInput, ...] = ()
    timeout_seconds: float = 3600.0

    def __post_init__(self) -> None:
        if type(self.rendered_input) is not QeEpwRenderedInput:
            raise TypeError("rendered_input must be a QeEpwRenderedInput")
        if not isinstance(self.output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if type(self.execute) is not bool:
            raise TypeError("execute must be a boolean")
        if type(self.staged_inputs) is not tuple or any(
            type(item) is not QeEpwStagedInput for item in self.staged_inputs
        ):
            raise TypeError("staged_inputs must contain QeEpwStagedInput records")
        paths = tuple(item.relative_path for item in self.staged_inputs)
        if len(paths) != len(set(paths)):
            raise ValueError("staged input paths must be unique")
        path_objects = tuple(Path(path) for path in paths)
        if any(
            left in right.parents
            for index, left in enumerate(path_objects)
            for right in path_objects[index + 1 :]
        ) or any(
            right in left.parents
            for index, left in enumerate(path_objects)
            for right in path_objects[index + 1 :]
        ):
            raise ValueError("staged input paths must not contain one another")
        collisions = _RESERVED_PATHS | {self.rendered_input.filename}
        if any(path.parts[0] in collisions for path in path_objects):
            raise ValueError(
                "staged input path collides with a maintained run artifact"
            )
        resources = (
            self.executable,
            self.executable_sha256,
            self.executable_byte_size,
        )
        if self.execute:
            if any(value is None for value in resources):
                raise ValueError("execution requires an identity-bound executable")
            if (
                type(self.executable_sha256) is not str
                or _SHA256.fullmatch(self.executable_sha256) is None
            ):
                raise ValueError("executable_sha256 must be lowercase SHA-256")
            if (
                type(self.executable_byte_size) is not int
                or self.executable_byte_size <= 0
            ):
                raise ValueError("executable_byte_size must be positive")
        elif any(value is not None for value in resources) or self.staged_inputs:
            raise ValueError("execution resources require execute=True")
        if (
            type(self.timeout_seconds) is not float
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0.0
        ):
            raise ValueError("timeout_seconds must be positive and finite")


@dataclass(frozen=True, slots=True)
class QeEpwRunResult:
    """Identify rendered evidence and optional provider stream observations."""

    output_directory: Path
    input_manifest: Path
    artifact_manifest: Path | None
    execution_requested: bool
    stream_observation: QeEpwStreamObservation | None


@dataclass(frozen=True, slots=True)
class QeEpwRunner:
    """Verify every external identity before any execution-side filesystem effect."""

    def run(self, request: QeEpwRunRequest) -> QeEpwRunResult:
        """Render input or execute only after an explicit identity-bound request."""
        if type(request) is not QeEpwRunRequest:
            raise TypeError("request must be a QeEpwRunRequest")
        output = request.output_directory.absolute()
        if output.exists():
            raise ValueError("output directory already exists")

        if request.execute:
            assert request.executable is not None
            assert request.executable_sha256 is not None
            assert request.executable_byte_size is not None
            _verify_file(
                request.executable,
                request.executable_sha256,
                request.executable_byte_size,
                "executable",
                executable=True,
            )
            for staged_input in request.staged_inputs:
                _verify_file(
                    staged_input.source,
                    staged_input.sha256,
                    staged_input.byte_size,
                    f"staged input {staged_input.relative_path}",
                )

        output.mkdir(parents=True)
        input_path = output / request.rendered_input.filename
        input_path.write_text(request.rendered_input.text, encoding="ascii")
        input_manifest = output / "input-manifest.json"
        _write_json(
            input_manifest,
            {
                "executable": (
                    {
                        "byte_size": request.executable_byte_size,
                        "sha256": request.executable_sha256,
                    }
                    if request.execute
                    else None
                ),
                "input": {
                    "filename": request.rendered_input.filename,
                    **_observation(input_path),
                },
                "schema_version": 1,
                "staged_inputs": [
                    {
                        "byte_size": item.byte_size,
                        "relative_path": item.relative_path,
                        "sha256": item.sha256,
                    }
                    for item in request.staged_inputs
                ],
            },
        )
        if not request.execute:
            return QeEpwRunResult(
                output_directory=output,
                input_manifest=input_manifest,
                artifact_manifest=None,
                execution_requested=False,
                stream_observation=None,
            )

        for staged_input in request.staged_inputs:
            destination = output / staged_input.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged_input.source, destination)
            _verify_file(
                destination,
                staged_input.sha256,
                staged_input.byte_size,
                f"staged copy {staged_input.relative_path}",
            )

        assert request.executable is not None
        record = CalculatorExecutor().action(
            request=CalculatorExecutionRequest(
                command=(
                    str(request.executable.absolute()),
                    "-in",
                    request.rendered_input.filename,
                ),
                working_directory=output,
                stdout_filename="epw.out",
                stderr_filename="epw.err",
                required_input_filenames=(request.rendered_input.filename,),
                timeout_seconds=request.timeout_seconds,
                execution_authorized=True,
            )
        )
        stdout_payload = _read_regular_file(
            output / "epw.out",
            "EPW stdout",
            max_byte_size=_MAX_STREAM_BYTES,
        )
        stderr_payload = _read_regular_file(
            output / "epw.err",
            "EPW stderr",
            max_byte_size=_MAX_STREAM_BYTES,
        )
        stream_observation = QeEpwStreamParser().parse(
            stdout_payload,
            stderr_payload,
        )
        artifacts = {
            name: _observation(output / name)
            for name in (
                request.rendered_input.filename,
                "input-manifest.json",
                "epw.out",
                "epw.err",
                "execution.json",
            )
        }
        artifact_manifest = output / "artifact-manifest.json"
        _write_json(
            artifact_manifest,
            {
                "artifacts": artifacts,
                "execution_status": record.status.value,
                "schema_version": 1,
                "stream_observation": {
                    "electron_phonon_interpolation_reported": (
                        stream_observation.electron_phonon_interpolation_reported
                    ),
                    "fatal_diagnostics": stream_observation.fatal_diagnostics,
                    "job_done": stream_observation.job_done,
                    "program_version": stream_observation.program_version,
                    "stderr_byte_size": stream_observation.stderr_byte_size,
                    "stderr_sha256": stream_observation.stderr_sha256,
                    "stdout_byte_size": stream_observation.stdout_byte_size,
                    "stdout_sha256": stream_observation.stdout_sha256,
                    "total_program_execution_reported": (
                        stream_observation.total_program_execution_reported
                    ),
                    "wannierization_reported": (
                        stream_observation.wannierization_reported
                    ),
                },
            },
        )
        return QeEpwRunResult(
            output_directory=output,
            input_manifest=input_manifest,
            artifact_manifest=artifact_manifest,
            execution_requested=True,
            stream_observation=stream_observation,
        )


def _relative_path(value: str) -> Path:
    if type(value) is not str or not value or "\\" in value or "\0" in value:
        raise ValueError("relative_path must be a safe POSIX relative path")
    path = Path(value)
    if (
        path.is_absolute()
        or path in {Path("."), Path("")}
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise ValueError("relative_path must be a safe POSIX relative path")
    return path


def _read_regular_file(
    path: Path,
    label: str,
    *,
    max_byte_size: int,
) -> bytes:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    if path.stat().st_size > max_byte_size:
        raise ValueError(f"{label} exceeds the byte limit")
    return path.read_bytes()


def _verify_file(
    path: Path,
    expected_sha256: str,
    expected_size: int,
    label: str,
    *,
    executable: bool = False,
) -> None:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    if path.stat().st_size != expected_size:
        raise ValueError(f"{label} size mismatch")
    if _sha256(path) != expected_sha256:
        raise ValueError(f"{label} hash mismatch")
    if executable and not path.stat().st_mode & 0o111:
        raise ValueError(f"{label} is not executable")


def _observation(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular file")
    return {
        "byte_size": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
