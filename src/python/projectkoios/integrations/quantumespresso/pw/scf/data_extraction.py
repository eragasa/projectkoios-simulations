"""Extract application-facing data from retained Quantum ESPRESSO SCF evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

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
from projectkoios.physkit.core.actions import DataObjectActionizer
from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
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


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfOutputParsingRequest(DataObject):
    """Supply bounded native SCF stream bytes without a filesystem capability."""

    stdout_payload: bytes
    stderr_payload: bytes
    stdout_relative_path: str = "pw.out"
    stderr_relative_path: str = "pw.err"
    maximum_stream_bytes: int = 100_000_000

    def __post_init__(self) -> None:
        for label, payload in (
            ("stdout_payload", self.stdout_payload),
            ("stderr_payload", self.stderr_payload),
        ):
            if type(payload) is not bytes:
                raise TypeError(f"{label} must be bytes")
        for label, value in (
            ("stdout_relative_path", self.stdout_relative_path),
            ("stderr_relative_path", self.stderr_relative_path),
        ):
            if type(value) is not str or not value:
                raise ValueError(f"{label} must be a nonempty string")
            path = PurePosixPath(value)
            if (
                "\\" in value
                or path.is_absolute()
                or path == PurePosixPath(".")
                or ".." in path.parts
                or str(path) != value
            ):
                raise ValueError(f"{label} must be a safe relative POSIX path")
        if self.stdout_relative_path == self.stderr_relative_path:
            raise ValueError("stdout and stderr relative paths must differ")
        if type(self.maximum_stream_bytes) is not int or self.maximum_stream_bytes <= 0:
            raise ValueError("maximum_stream_bytes must be a positive integer")
        for label, payload in (
            ("stdout", self.stdout_payload),
            ("stderr", self.stderr_payload),
        ):
            if len(payload) > self.maximum_stream_bytes:
                raise QeScfArtifactError(f"{label} exceeds byte limit")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfOutputParsingResult(ResultsObject):
    """Correlate one pure parse with its exact supplied stream bytes."""

    request: QeScfOutputParsingRequest
    streams: QePwCapturedStreamData

    def __post_init__(self) -> None:
        if type(self.request) is not QeScfOutputParsingRequest:
            raise TypeError("request must be a QeScfOutputParsingRequest")
        if type(self.streams) is not QePwCapturedStreamData:
            raise TypeError("streams must be QePwCapturedStreamData")
        if self.streams.stdout_artifact.relative_path != (
            self.request.stdout_relative_path
        ):
            raise ValueError("stdout artifact path does not match the parse request")
        if self.streams.stderr_artifact.relative_path != (
            self.request.stderr_relative_path
        ):
            raise ValueError("stderr artifact path does not match the parse request")
        if self.streams.stdout_artifact.byte_size != len(self.request.stdout_payload):
            raise ValueError("stdout artifact size does not match the parse request")
        if self.streams.stderr_artifact.byte_size != len(self.request.stderr_payload):
            raise ValueError("stderr artifact size does not match the parse request")
        if (
            self.streams.stdout_artifact.sha256
            != hashlib.sha256(self.request.stdout_payload).hexdigest()
        ):
            raise ValueError("stdout artifact digest does not match the parse request")
        if (
            self.streams.stderr_artifact.sha256
            != hashlib.sha256(self.request.stderr_payload).hexdigest()
        ):
            raise ValueError("stderr artifact digest does not match the parse request")


class QeScfOutputParser(
    DataObjectActionizer[QeScfOutputParsingRequest, QeScfOutputParsingResult]
):
    """Parse exact supplied native bytes without filesystem or process access."""

    __slots__ = ()

    def action(
        self,
        *,
        request: QeScfOutputParsingRequest,
    ) -> QeScfOutputParsingResult:
        """Return provider-native stream records and their exact identities."""
        if type(request) is not QeScfOutputParsingRequest:
            raise TypeError("request must be a QeScfOutputParsingRequest")
        streams = QePwCapturedStreamDataExtractor().extract(
            stdout_payload=request.stdout_payload,
            stderr_payload=request.stderr_payload,
            stdout_relative_path=request.stdout_relative_path,
            stderr_relative_path=request.stderr_relative_path,
        )
        return QeScfOutputParsingResult(request=request, streams=streams)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfNormalizationRequest(DataObject):
    """Supply parsed native SCF records with exact execution lineage."""

    sources: QePwDataSources

    def __post_init__(self) -> None:
        if type(self.sources) is not QePwDataSources:
            raise TypeError("sources must be QePwDataSources")
        if type(self.sources.execution) is not QePwExecutionData:
            raise TypeError("SCF normalization requires QePwExecutionData")
        if type(self.sources.execution_artifact) is not QePwNativeArtifact:
            raise TypeError("SCF normalization requires an execution artifact")


@dataclass(frozen=True, slots=True, kw_only=True)
class QeScfNormalizationResult(ResultsObject):
    """Correlate one normalization with its provider-native sources."""

    request: QeScfNormalizationRequest
    data: QeScfData

    def __post_init__(self) -> None:
        if type(self.request) is not QeScfNormalizationRequest:
            raise TypeError("request must be a QeScfNormalizationRequest")
        if type(self.data) is not QeScfData:
            raise TypeError("data must be QeScfData")
        if self.data.sources is not self.request.sources:
            raise ValueError("normalized data must retain the exact requested sources")


class QeScfNormalizer(
    DataObjectActionizer[QeScfNormalizationRequest, QeScfNormalizationResult]
):
    """Normalize parsed QE SCF facts without acceptance or authority policy."""

    __slots__ = ()

    def action(
        self,
        *,
        request: QeScfNormalizationRequest,
    ) -> QeScfNormalizationResult:
        """Map exact provider-native facts into one neutral SCF observation."""
        if type(request) is not QeScfNormalizationRequest:
            raise TypeError("request must be a QeScfNormalizationRequest")
        sources = request.sources
        parsed = sources.streams.stdout
        if (
            parsed.total_energy_ry is None
            or parsed.wavefunction_cutoff_ry is None
            or parsed.atom_count is None
        ):
            raise QeScfArtifactError("pw.x output lacks required SCF observations")

        represented_flags = tuple(
            (flag, _IEEE_FLAG_CODES[flag]) for flag in sources.streams.stderr.ieee_flags
        )
        diagnostics: tuple[PwDftScfDiagnostic, ...] = ()
        if represented_flags:
            artifact = sources.streams.stderr_artifact
            stderr_artifact = PwDftScfNativeArtifact(
                integration_id=qe_projection.QE_SCF_INTEGRATION_ID,
                artifact_id=artifact.relative_path,
                sha256=artifact.sha256,
                byte_size=artifact.byte_size,
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

        native_output = sources.streams.stdout_artifact
        observation = PwDftScfObservation(
            total_energy_ev=self._ry_to_ev(parsed.total_energy_ry),
            atom_count=parsed.atom_count,
            electronic_iteration_count=parsed.scf_iteration_count,
            converged=parsed.scf_converged,
            completed=parsed.job_completed,
            native_artifact=PwDftScfNativeArtifact(
                integration_id=qe_projection.QE_SCF_INTEGRATION_ID,
                artifact_id=native_output.relative_path,
                sha256=native_output.sha256,
                byte_size=native_output.byte_size,
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
        qexsd = sources.qexsd
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
        data = QeScfData(
            sources=sources,
            observation=observation,
            consistency=consistency,
        )
        return QeScfNormalizationResult(request=request, data=data)

    def _ry_to_ev(self, value: float) -> float:
        converted = MODEL_SYSTEM_UNIT_CONVERTER.convert_scalar(
            ScalarQuantity(
                magnitude=value,
                unit=PhysicalUnit(expression="Ry"),
            ),
            PhysicalUnit(expression="eV"),
        )
        return converted.magnitude


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
        output_artifact_id = str(output_path.relative_to(self.artifact_root.resolve()))
        stderr_path = output_path.parent / execution.stderr_filename
        stderr_payload = self._read(stderr_path)
        stderr_artifact_id = str(stderr_path.relative_to(self.artifact_root.resolve()))
        parsing = QeScfOutputParser().action(
            request=QeScfOutputParsingRequest(
                stdout_payload=output_payload,
                stderr_payload=stderr_payload,
                stdout_relative_path=output_artifact_id,
                stderr_relative_path=stderr_artifact_id,
                maximum_stream_bytes=self.maximum_artifact_bytes,
            )
        )
        qexsd = (
            QeQexsdData.from_document(qexsd_document)
            if qexsd_document is not None
            else None
        )
        normalization = QeScfNormalizer().action(
            request=QeScfNormalizationRequest(
                sources=QePwDataSources(
                    streams=parsing.streams,
                    qexsd=qexsd,
                    execution=execution,
                    execution_artifact=execution_artifact,
                )
            )
        )
        return normalization.data

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
