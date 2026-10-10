"""Extract application-facing data from retained Quantum ESPRESSO SCF evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamData,
    QePwCapturedStreamDataExtractor,
    QePwDataSources,
    QePwExecutionData,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (
    QeQexsdFinalStructure,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from projectkoios.physkit.units import (
    MODEL_SYSTEM_UNIT_CONVERTER,
    PhysicalUnit,
    ScalarQuantity,
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


QeScfExecutionData = QePwExecutionData


@dataclass(frozen=True, slots=True)
class QeScfConsistency:
    """Report mechanical SCF agreement without scientific acceptance policy."""

    stdout_completion_matches_execution: bool
    qexsd_terminal_status_matches: bool | None
    qexsd_atom_count_matches: bool | None

    def __post_init__(self) -> None:
        for label, value in (
            (
                "stdout_completion_matches_execution",
                self.stdout_completion_matches_execution,
            ),
            ("qexsd_terminal_status_matches", self.qexsd_terminal_status_matches),
            ("qexsd_atom_count_matches", self.qexsd_atom_count_matches),
        ):
            if value is not None and type(value) is not bool:
                raise TypeError(f"{label} must be a boolean or None")


@dataclass(frozen=True, slots=True)
class QeScfData:
    """Facade all retained native, normalized, and optional QEXSD SCF data."""

    sources: QePwDataSources
    observation: PwDftScfObservation
    consistency: QeScfConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not QePwDataSources:
            raise TypeError("sources must be QePwDataSources")
        if type(self.sources.execution) is not QePwExecutionData:
            raise TypeError("SCF sources require QePwExecutionData")
        if type(self.sources.execution_artifact) is not QePwNativeArtifact:
            raise TypeError("SCF sources require an execution artifact")
        if type(self.observation) is not PwDftScfObservation:
            raise TypeError("observation must be PwDftScfObservation")
        if type(self.consistency) is not QeScfConsistency:
            raise TypeError("consistency must be QeScfConsistency")
        document_atom_count = (
            getattr(self.qexsd.document, "declared_atom_count", None)
            if self.qexsd is not None
            else None
        )
        expected_consistency = QeScfConsistency(
            stdout_completion_matches_execution=self.streams.stdout.job_completed,
            qexsd_terminal_status_matches=(
                self.streams.stdout.job_completed
                == (self.qexsd.final_structure.exit_status == 0)
                if self.qexsd is not None
                else None
            ),
            qexsd_atom_count_matches=(
                self.streams.stdout.atom_count == document_atom_count
                if type(document_atom_count) is int
                and self.streams.stdout.atom_count is not None
                else None
            ),
        )
        if self.consistency != expected_consistency:
            raise ValueError("consistency does not describe the retained sources")

    @property
    def streams(self) -> QePwCapturedStreamData:
        return self.sources.streams

    @property
    def execution(self) -> QePwExecutionData:
        execution = self.sources.execution
        assert type(execution) is QePwExecutionData
        return execution

    @property
    def execution_artifact(self) -> QePwNativeArtifact:
        artifact = self.sources.execution_artifact
        assert type(artifact) is QePwNativeArtifact
        return artifact

    @property
    def qexsd(self) -> QeQexsdData | None:
        return self.sources.qexsd

    @property
    def final_structure(self) -> QeQexsdFinalStructure | None:
        """Expose the interpreted final QEXSD structure when supplied."""
        return self.qexsd.final_structure if self.qexsd is not None else None

    @property
    def total_energy_ev(self) -> float:
        return self.observation.total_energy_ev

    @property
    def atom_count(self) -> int:
        return self.observation.atom_count

    @property
    def electronic_iteration_count(self) -> int:
        return self.observation.electronic_iteration_count

    @property
    def converged(self) -> bool:
        return self.observation.converged

    @property
    def completed(self) -> bool:
        return self.observation.completed

    @property
    def native_artifact(self) -> PwDftScfNativeArtifact:
        return self.observation.native_artifact

    @property
    def program_version(self) -> str | None:
        return self.observation.program_version

    @property
    def irreducible_kpoint_count(self) -> int | None:
        return self.observation.irreducible_kpoint_count

    @property
    def wavefunction_cutoff_ev(self) -> float | None:
        return self.observation.wavefunction_cutoff_ev

    @property
    def total_magnetization_electrons(self) -> float | None:
        return self.observation.total_magnetization_electrons

    @property
    def diagnostics(self) -> tuple[PwDftScfDiagnostic, ...]:
        return self.observation.diagnostics


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

    def extract(
        self,
        output_artifact_id: str,
        *,
        qexsd_document: object | None = None,
    ) -> QeScfData:
        """Validate retained evidence and assemble one immutable SCF facade."""
        output_path = self._resolve(output_artifact_id)
        execution_path = output_path.parent / "execution.json"
        execution, execution_artifact = self._execution(execution_path)
        if execution.stdout_filename != output_path.name:
            raise QeScfArtifactError(
                "output artifact does not match recorded stdout_filename"
            )
        output_payload = self._read(output_path)
        stderr_path = output_path.parent / execution.stderr_filename
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
        observation = PwDftScfObservation(
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
            # In collinear spin-only QE output, one Bohr magneton per cell is
            # numerically one spin-channel electron difference. Preserve the
            # provider unit in the stream record and normalize only here.
            total_magnetization_electrons=(
                parsed.total_magnetization_bohr_magneton_per_cell
            ),
            diagnostics=diagnostics,
        )
        qexsd = (
            QeQexsdData.from_document(qexsd_document)
            if qexsd_document is not None
            else None
        )
        document_atom_count = (
            getattr(qexsd.document, "declared_atom_count", None)
            if qexsd is not None
            else None
        )
        consistency = QeScfConsistency(
            stdout_completion_matches_execution=parsed.job_completed,
            qexsd_terminal_status_matches=(
                parsed.job_completed == (qexsd.final_structure.exit_status == 0)
                if qexsd is not None
                else None
            ),
            qexsd_atom_count_matches=(
                parsed.atom_count == document_atom_count
                if type(document_atom_count) is int
                else None
            ),
        )
        return QeScfData(
            sources=QePwDataSources(
                streams=streams,
                qexsd=qexsd,
                execution=execution,
                execution_artifact=execution_artifact,
            ),
            observation=observation,
            consistency=consistency,
        )

    def _execution(self, path: Path) -> tuple[QePwExecutionData, QePwNativeArtifact]:
        raw = self._read(path)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise QeScfArtifactError("unsupported execution record")
        if (
            payload.get("status") != "succeeded"
            or type(payload.get("returncode")) is not int
            or payload.get("returncode") != 0
        ):
            raise QeScfArtifactError("QE execution record is not successful")
        stdout_filename = payload.get("stdout_filename")
        stderr_filename = payload.get("stderr_filename")
        if not isinstance(stdout_filename, str):
            raise QeScfArtifactError("execution record lacks stdout_filename")
        if not isinstance(stderr_filename, str):
            raise QeScfArtifactError("execution record lacks stderr_filename")
        execution = QePwExecutionData(
            status="succeeded",
            returncode=0,
            stdout_filename=stdout_filename,
            stderr_filename=stderr_filename,
        )
        return (
            execution,
            QePwNativeArtifact(
                relative_path=str(path.relative_to(self.artifact_root.resolve())),
                sha256=hashlib.sha256(raw).hexdigest(),
                byte_size=len(raw),
            ),
        )

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
