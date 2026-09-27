"""Stage and optionally execute one identity-bound ``pw2wannier90.x`` run."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw2wannier90.projection import (  # noqa: E501
    QePw2Wannier90InputProjection,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
    QeSavedStateManifestVerifier,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRequest,
    CalculatorExecutor,
)


@dataclass(frozen=True, slots=True)
class QePw2Wannier90RunRequest:
    """Declare projection and separately authorized execution resources."""

    projection: QePw2Wannier90InputProjection
    output_directory: Path
    execute: bool = False
    executable: Path | None = None
    executable_sha256: str | None = None
    executable_byte_size: int | None = None
    nnkp_source: Path | None = None
    saved_state_manifest: Path | None = None
    saved_state_source_root: Path | None = None
    timeout_seconds: float = 1800.0

    def __post_init__(self) -> None:
        if type(self.projection) is not QePw2Wannier90InputProjection:
            raise TypeError("projection must be a QePw2Wannier90InputProjection")
        if not isinstance(self.output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if type(self.execute) is not bool:
            raise TypeError("execute must be a boolean")
        resources = (
            self.executable,
            self.executable_sha256,
            self.executable_byte_size,
            self.nnkp_source,
            self.saved_state_manifest,
            self.saved_state_source_root,
        )
        if self.execute:
            if any(value is None for value in resources):
                raise ValueError("execution requires all identity-bound resources")
        elif any(value is not None for value in resources):
            raise ValueError("execution resources require execute=True")
        if (
            type(self.timeout_seconds) is not float
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0.0
        ):
            raise ValueError("timeout_seconds must be positive and finite")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90RunResult:
    """Identify rendered evidence and whether execution was requested."""

    output_directory: Path
    input_manifest: Path
    artifact_manifest: Path | None
    execution_requested: bool


@dataclass(frozen=True, slots=True)
class QePw2Wannier90Runner:
    """Verify every external identity before creating the output directory."""

    def run(self, request: QePw2Wannier90RunRequest) -> QePw2Wannier90RunResult:
        """Render input or execute only after an explicit authorized request."""
        if type(request) is not QePw2Wannier90RunRequest:
            raise TypeError("request must be a QePw2Wannier90RunRequest")
        projection = request.projection
        output = request.output_directory.absolute()
        if output.exists():
            raise ValueError("output directory already exists")
        outdir = _safe_directory(projection.outdir)

        manifest_payload: bytes | None = None
        manifest: QeSavedStateManifest | None = None
        manifest_paths: tuple[Path, ...] = ()
        if request.execute:
            assert request.executable is not None
            assert request.executable_sha256 is not None
            assert request.executable_byte_size is not None
            assert request.nnkp_source is not None
            assert request.saved_state_manifest is not None
            assert request.saved_state_source_root is not None
            _verify_file(
                request.executable,
                request.executable_sha256,
                request.executable_byte_size,
                "executable",
                executable=True,
            )
            _verify_file(
                request.nnkp_source,
                projection.nnkp_sha256,
                projection.nnkp_byte_size,
                "NNKP",
            )
            manifest_payload = _read_regular_file(
                request.saved_state_manifest,
                "saved-state manifest",
            )
            if hashlib.sha256(manifest_payload).hexdigest() != (
                projection.parent_nscf_saved_state_manifest_sha256
            ):
                raise ValueError("saved-state manifest hash mismatch")
            manifest = QeSavedStateManifestJsonCodec().loads(manifest_payload)
            if manifest.prefix != projection.prefix:
                raise ValueError("saved-state prefix disagrees with converter input")
            if manifest.calculation is not QeSavedStateCalculation.nscf:
                raise ValueError("converter requires an NSCF saved state")
            manifest_paths = QeSavedStateManifestVerifier().verify(
                manifest,
                request.saved_state_source_root,
            )

        output.mkdir(parents=True)
        input_path = output / projection.rendered_input.filename
        input_path.write_text(projection.rendered_input.text, encoding="ascii")
        if manifest_payload is not None:
            (output / "parent-saved-state-manifest.json").write_bytes(manifest_payload)
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
                "input": _observation(input_path),
                "nnkp": {
                    "byte_size": projection.nnkp_byte_size,
                    "filename": projection.nnkp_filename,
                    "sha256": projection.nnkp_sha256,
                },
                "parent_nscf_saved_state_manifest_sha256": (
                    projection.parent_nscf_saved_state_manifest_sha256
                ),
                "prefix": projection.prefix,
                "required_outputs": projection.required_output_filenames,
                "schema_version": 1,
                "seedname": projection.seedname,
            },
        )
        if not request.execute:
            return QePw2Wannier90RunResult(
                output_directory=output,
                input_manifest=input_manifest,
                artifact_manifest=None,
                execution_requested=False,
            )

        assert request.executable is not None
        assert request.nnkp_source is not None
        assert request.saved_state_source_root is not None
        shutil.copyfile(request.nnkp_source, output / projection.nnkp_filename)
        staged_outdir = output / outdir
        staged_outdir.mkdir(parents=True, exist_ok=False)
        required_inputs = [
            projection.rendered_input.filename,
            projection.nnkp_filename,
        ]
        for source in manifest_paths:
            relative = source.relative_to(request.saved_state_source_root)
            destination = staged_outdir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        assert manifest is not None
        QeSavedStateManifestVerifier().verify(manifest, staged_outdir)
        record = CalculatorExecutor().execute(
            CalculatorExecutionRequest(
                command=(
                    str(request.executable.absolute()),
                    "-in",
                    projection.rendered_input.filename,
                ),
                working_directory=output,
                stdout_filename="pw2wannier90.out",
                stderr_filename="pw2wannier90.err",
                required_input_filenames=tuple(required_inputs),
                timeout_seconds=request.timeout_seconds,
                execution_authorized=True,
            )
        )
        artifact_names = (
            projection.rendered_input.filename,
            projection.nnkp_filename,
            "parent-saved-state-manifest.json",
            "pw2wannier90.out",
            "pw2wannier90.err",
            "execution.json",
            *projection.required_output_filenames,
        )
        artifacts = {
            name: _observation(output / name)
            for name in artifact_names
            if (output / name).is_file() and not (output / name).is_symlink()
        }
        artifact_manifest = output / "artifact-manifest.json"
        _write_json(
            artifact_manifest,
            {
                "artifacts": artifacts,
                "execution_status": record.status.value,
                "required_outputs": projection.required_output_filenames,
                "schema_version": 1,
            },
        )
        return QePw2Wannier90RunResult(
            output_directory=output,
            input_manifest=input_manifest,
            artifact_manifest=artifact_manifest,
            execution_requested=True,
        )


def _safe_directory(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or path in {Path("."), Path("")} or ".." in path.parts:
        raise ValueError("converter outdir must be a safe non-current relative path")
    return path


def _read_regular_file(path: Path, label: str) -> bytes:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    return path.read_bytes()


def _verify_file(
    path: Path,
    expected_sha256: str,
    expected_size: int,
    label: str,
    *,
    executable: bool = False,
) -> None:
    payload = _read_regular_file(path, label)
    if len(payload) != expected_size:
        raise ValueError(f"{label} size mismatch")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError(f"{label} hash mismatch")
    if executable and not path.stat().st_mode & 0o111:
        raise ValueError(f"{label} is not executable")


def _observation(path: Path) -> dict[str, object]:
    payload = _read_regular_file(path, "artifact")
    return {
        "byte_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
