"""Extract application-facing data from retained Quantum ESPRESSO SCF evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from physkit.units import MODEL_SYSTEM_UNIT_CONVERTER, PhysicalUnit, ScalarQuantity

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfDiagnostic,
    PwDftScfDiagnosticSeverity,
    PwDftScfNativeArtifact,
    PwDftScfObservation,
)

_IEEE_FLAG_CODES = {
    "IEEE_INVALID_FLAG": "ieee-invalid-flag",
    "IEEE_DIVIDE_BY_ZERO": "ieee-divide-by-zero",
    "IEEE_OVERFLOW_FLAG": "ieee-overflow-flag",
    "IEEE_UNDERFLOW_FLAG": "ieee-underflow-flag",
}


class QeScfArtifactError(ValueError):
    """Report invalid, escaped, oversized, or incomplete retained QE evidence."""


@dataclass(frozen=True, slots=True)
class QeScfDataExtractor:
    """Extract bounded ``pw.out``, stderr, and sibling execution evidence."""

    artifact_root: Path
    maximum_artifact_bytes: int = 100_000_000

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if (
            type(self.maximum_artifact_bytes) is not int
            or self.maximum_artifact_bytes <= 0
        ):
            raise ValueError("maximum_artifact_bytes must be a positive integer")

    def extract(self, output_artifact_id: str) -> PwDftScfObservation:
        """Validate execution success and extract retained ``pw.x`` data."""
        output_path = self._resolve(output_artifact_id)
        execution = self._execution(output_path.parent / "execution.json")
        stdout_filename = execution.get("stdout_filename")
        if not isinstance(stdout_filename, str):
            raise QeScfArtifactError("execution record lacks stdout_filename")
        self._validate_basename(stdout_filename, "stdout_filename")
        if stdout_filename != output_path.name:
            raise QeScfArtifactError(
                "output artifact does not match recorded stdout_filename"
            )
        output_payload = self._read(output_path)
        stderr_filename = execution.get("stderr_filename")
        if not isinstance(stderr_filename, str):
            raise QeScfArtifactError("execution record lacks stderr_filename")
        self._validate_basename(stderr_filename, "stderr_filename")
        stderr_path = output_path.parent / stderr_filename
        stderr_payload = self._read(stderr_path)
        stderr_artifact_id = str(stderr_path.relative_to(self.artifact_root.resolve()))
        streams = QePwCapturedStreamDataExtractor().extract(
            stdout_payload=output_payload,
            stderr_payload=stderr_payload,
            stdout_relative_path=output_artifact_id,
            stderr_relative_path=stderr_artifact_id,
        )
        parsed = streams.stdout
        if (
            parsed.total_energy_ry is None
            or parsed.wavefunction_cutoff_ry is None
            or parsed.atom_count is None
        ):
            raise QeScfArtifactError("pw.x output lacks required SCF observations")
        represented_flags = tuple(
            (flag, _IEEE_FLAG_CODES[flag]) for flag in streams.stderr.ieee_flags
        )
        diagnostics: tuple[PwDftScfDiagnostic, ...] = ()
        if represented_flags:
            stderr_artifact = PwDftScfNativeArtifact(
                integration_id=qe_projection.QE_SCF_INTEGRATION_ID,
                artifact_id=stderr_artifact_id,
                sha256=hashlib.sha256(stderr_payload).hexdigest(),
                byte_size=len(stderr_payload),
            )
            diagnostics = tuple(
                PwDftScfDiagnostic(
                    code=code,
                    severity=PwDftScfDiagnosticSeverity.WARNING,
                    message=(
                        f"Quantum ESPRESSO reported {flag} after a successful run."
                    ),
                    native_artifact=stderr_artifact,
                )
                for flag, code in represented_flags
            )
        return PwDftScfObservation(
            total_energy_ev=self._ry_to_ev(parsed.total_energy_ry),
            atom_count=parsed.atom_count,
            electronic_iteration_count=parsed.scf_iteration_count,
            converged=parsed.scf_converged,
            completed=parsed.job_completed,
            native_artifact=PwDftScfNativeArtifact(
                integration_id=qe_projection.QE_SCF_INTEGRATION_ID,
                artifact_id=str(output_path.relative_to(self.artifact_root.resolve())),
                sha256=hashlib.sha256(output_payload).hexdigest(),
                byte_size=len(output_payload),
            ),
            program_version=parsed.program_version,
            irreducible_kpoint_count=parsed.k_point_count,
            wavefunction_cutoff_ev=self._ry_to_ev(parsed.wavefunction_cutoff_ry),
            diagnostics=diagnostics,
        )

    def _execution(self, path: Path) -> dict[str, object]:
        payload = json.loads(self._read(path).decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise QeScfArtifactError("unsupported execution record")
        if (
            payload.get("status") != "succeeded"
            or type(payload.get("returncode")) is not int
            or payload.get("returncode") != 0
        ):
            raise QeScfArtifactError("QE execution record is not successful")
        return payload

    def _resolve(self, artifact_id: str) -> Path:
        if not artifact_id or Path(artifact_id).is_absolute():
            raise QeScfArtifactError("artifact_id must be a relative path")
        root = self.artifact_root.resolve()
        path = (root / artifact_id).resolve()
        if not path.is_relative_to(root):
            raise QeScfArtifactError("artifact_id must remain inside artifact_root")
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        return path

    def _read(self, path: Path) -> bytes:
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError(path)
        if path.stat().st_size > self.maximum_artifact_bytes:
            raise QeScfArtifactError(f"artifact exceeds byte limit: {path}")
        return path.read_bytes()

    @staticmethod
    def _validate_basename(value: str, label: str) -> None:
        if not value or value in {".", ".."} or "/" in value or "\\" in value:
            raise QeScfArtifactError(f"{label} must be a basename")

    @staticmethod
    def _ry_to_ev(value: float) -> float:
        converted = MODEL_SYSTEM_UNIT_CONVERTER.convert_scalar(
            ScalarQuantity(
                magnitude=value,
                unit=PhysicalUnit(expression="Ry"),
            ),
            PhysicalUnit(expression="eV"),
        )
        return converted.magnitude
