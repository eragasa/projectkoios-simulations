"""Secure retained-artifact analysis for VASP SCF OUTCAR evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.vasp.outcar import VaspOutcarParser
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VASP_SCF_INTEGRATION_ID,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfNativeArtifact,
    PwDftScfObservation,
)


class VaspScfArtifactError(ValueError):
    """Report invalid, escaped, oversized, or failed retained VASP evidence."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "output-analysis-failed",
        native_artifact: PwDftScfNativeArtifact | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.native_artifact = native_artifact


@dataclass(frozen=True, slots=True)
class VaspScfOutputArtifactAnalyzer:
    """Analyze one bounded OUTCAR and its sibling execution record."""

    artifact_root: Path
    maximum_artifact_bytes: int = 100_000_000

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if self.maximum_artifact_bytes <= 0:
            raise ValueError("maximum_artifact_bytes must be positive")

    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        """Validate execution success and normalize the retained OUTCAR result."""
        outcar_path = self._resolve(output_artifact_id)
        execution_path = outcar_path.parent / "execution.json"
        execution_payload = self._read(execution_path)
        execution = json.loads(execution_payload.decode("utf-8"))
        if not isinstance(execution, dict) or execution.get("schema_version") != 1:
            raise VaspScfArtifactError("unsupported execution record")
        if (
            execution.get("status") != "succeeded"
            or type(execution.get("returncode")) is not int
            or execution.get("returncode") != 0
        ):
            raise VaspScfArtifactError("VASP execution record is not successful")
        self._raise_for_captured_failure(outcar_path.parent, execution)
        payload = self._read(outcar_path)
        parsed = VaspOutcarParser().parse(payload.decode("utf-8"))
        return PwDftScfObservation(
            total_energy_ev=parsed.total_energy_toten_ev,
            atom_count=parsed.atom_count,
            electronic_iteration_count=parsed.electronic_iteration_count,
            converged=parsed.electronic_converged,
            completed=parsed.completed,
            native_artifact=PwDftScfNativeArtifact(
                integration_id=VASP_SCF_INTEGRATION_ID,
                artifact_id=str(outcar_path.relative_to(self.artifact_root.resolve())),
                sha256=hashlib.sha256(payload).hexdigest(),
                byte_size=len(payload),
            ),
            program_version=parsed.program_version,
            irreducible_kpoint_count=parsed.irreducible_kpoint_count,
            wavefunction_cutoff_ev=parsed.wavefunction_cutoff_ev,
        )

    def _raise_for_captured_failure(
        self,
        run_directory: Path,
        execution: dict[str, object],
    ) -> None:
        stdout_filename = execution.get("stdout_filename")
        if stdout_filename is None:
            return
        if not isinstance(stdout_filename, str):
            raise VaspScfArtifactError("stdout_filename must be a string")
        self._validate_basename(stdout_filename, "stdout_filename")
        stdout_path = run_directory / stdout_filename
        payload = self._read(stdout_path)
        if b"triple product of the basis vectors is negative" not in payload:
            return
        artifact_id = str(stdout_path.relative_to(self.artifact_root.resolve()))
        raise VaspScfArtifactError(
            "VASP rejected the POSCAR because the triple product of its basis "
            "vectors is negative.",
            code="negative-lattice-orientation",
            native_artifact=PwDftScfNativeArtifact(
                integration_id=VASP_SCF_INTEGRATION_ID,
                artifact_id=artifact_id,
                sha256=hashlib.sha256(payload).hexdigest(),
                byte_size=len(payload),
            ),
        )

    def _resolve(self, artifact_id: str) -> Path:
        if not artifact_id or Path(artifact_id).is_absolute():
            raise VaspScfArtifactError("artifact_id must be a relative path")
        root = self.artifact_root.resolve()
        path = (root / artifact_id).resolve()
        if not path.is_relative_to(root):
            raise VaspScfArtifactError("artifact_id must remain inside artifact_root")
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        return path

    def _read(self, path: Path) -> bytes:
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        if path.stat().st_size > self.maximum_artifact_bytes:
            raise VaspScfArtifactError(f"artifact exceeds byte limit: {path}")
        return path.read_bytes()

    @staticmethod
    def _validate_basename(value: str, label: str) -> None:
        if not value or value in {".", ".."} or "/" in value or "\\" in value:
            raise VaspScfArtifactError(f"{label} must be a basename")
