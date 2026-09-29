"""Extract a unified data facade from Quantum ESPRESSO NSCF evidence."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol, cast

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwCapturedStreamData,
    QePwCapturedStreamDataExtractor,
    QePwDataSources,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
)
from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (
    QeQexsdFinalStructure,
)
from projectkoios.simulations.execution import CalculatorExecutionRecord

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REQUIRED_FIELDS = (
    "source_path",
    "source_sha256",
    "source_byte_count",
    "qexsd_version",
    "producing_application",
    "producing_application_version",
    "declared_unit_system_label",
    "k_points",
    "k_point_weights",
    "sampled_k_point_count",
    "k_point_source_label",
    "eigenvalues",
    "occupations",
    "eigenvalue_source_label",
    "band_count",
    "exit_status",
)

type _Vector3 = tuple[float, float, float]
type _Spectrum = tuple[tuple[float, ...], ...]


class _QexsdNscfDocument(Protocol):
    source_path: str
    source_sha256: str
    source_byte_count: int
    qexsd_version: str
    producing_application: str
    producing_application_version: str | None
    declared_unit_system_label: str
    k_points: tuple[_Vector3, ...]
    k_point_weights: tuple[float, ...]
    sampled_k_point_count: int
    k_point_source_label: str
    eigenvalues: _Spectrum
    occupations: _Spectrum | None
    eigenvalue_source_label: str
    band_count: int
    exit_status: int


@dataclass(frozen=True, slots=True)
class QeNscfSpectralData:
    """Retain source-ordered native QEXSD spectral observations."""

    source_path: str
    source_sha256: str
    source_byte_count: int
    qexsd_version: str
    producing_application: str
    producing_application_version: str | None
    declared_unit_system_label: str
    k_points: tuple[_Vector3, ...]
    k_point_weights: tuple[float, ...]
    sampled_k_point_count: int
    k_point_source_label: str
    eigenvalues: _Spectrum
    occupations: _Spectrum | None
    eigenvalue_source_label: str
    band_count: int
    exit_status: int

    def __post_init__(self) -> None:
        for label, value in (
            ("source_path", self.source_path),
            ("qexsd_version", self.qexsd_version),
            ("producing_application", self.producing_application),
            ("declared_unit_system_label", self.declared_unit_system_label),
            ("k_point_source_label", self.k_point_source_label),
            ("eigenvalue_source_label", self.eigenvalue_source_label),
        ):
            if type(value) is not str or not value:
                raise ValueError(f"{label} must be nonempty")
        if (
            type(self.source_sha256) is not str
            or _SHA256.fullmatch(self.source_sha256) is None
        ):
            raise ValueError("source_sha256 must be lowercase SHA-256")
        if type(self.source_byte_count) is not int or self.source_byte_count < 0:
            raise ValueError("source_byte_count must be nonnegative")
        if self.producing_application_version is not None and (
            type(self.producing_application_version) is not str
            or not self.producing_application_version
        ):
            raise ValueError("producing_application_version must be nonempty or None")
        if type(self.band_count) is not int or self.band_count <= 0:
            raise ValueError("band_count must be positive")
        if type(self.sampled_k_point_count) is not int or (
            self.sampled_k_point_count <= 0
        ):
            raise ValueError("sampled_k_point_count must be positive")
        if type(self.k_points) is not tuple or len(self.k_points) != (
            self.sampled_k_point_count
        ):
            raise ValueError("k_points must match sampled_k_point_count")
        for vector in self.k_points:
            if (
                type(vector) is not tuple
                or len(vector) != 3
                or any(
                    type(value) is not float or not math.isfinite(value)
                    for value in vector
                )
            ):
                raise ValueError("k_points must contain finite float three-vectors")
        if type(self.k_point_weights) is not tuple or len(self.k_point_weights) != len(
            self.k_points
        ):
            raise ValueError("k-point weights must match k-points")
        if any(
            type(value) is not float or not math.isfinite(value) or value < 0.0
            for value in self.k_point_weights
        ):
            raise ValueError("k-point weights must be finite and nonnegative")
        self._validate_spectrum(self.eigenvalues, "eigenvalues")
        if self.occupations is not None:
            self._validate_spectrum(self.occupations, "occupations")
        if type(self.exit_status) is not int or not 0 <= self.exit_status <= 255:
            raise ValueError("exit_status must be in 0..255")

    def _validate_spectrum(self, value: _Spectrum, label: str) -> None:
        if type(value) is not tuple or len(value) != len(self.k_points):
            raise ValueError(f"{label} must match the k-point count")
        for row in value:
            if type(row) is not tuple or len(row) != self.band_count:
                raise ValueError(f"{label} rows must match band_count")
            if any(type(item) is not float or not math.isfinite(item) for item in row):
                raise ValueError(f"{label} must contain finite floats")


@dataclass(frozen=True, slots=True)
class QeNscfConsistency:
    """Report mechanical NSCF agreement without scientific acceptance policy."""

    terminal_status_matches: bool
    stdout_kpoint_count_matches: bool | None
    declared_band_count_matches: bool
    declared_kpoint_count_matches: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("terminal_status_matches", self.terminal_status_matches),
            ("stdout_kpoint_count_matches", self.stdout_kpoint_count_matches),
            ("declared_band_count_matches", self.declared_band_count_matches),
            ("declared_kpoint_count_matches", self.declared_kpoint_count_matches),
        ):
            if value is not None and type(value) is not bool:
                raise TypeError(f"{label} must be a boolean or None")
        if not self.declared_band_count_matches:
            raise ValueError("declared band count must match extracted QEXSD data")
        if not self.declared_kpoint_count_matches:
            raise ValueError("declared k-point count must match extracted QEXSD data")


@dataclass(frozen=True, slots=True)
class QeNscfData:
    """Facade all retained native and interpreted QE NSCF data."""

    sources: QePwDataSources
    spectral: QeNscfSpectralData
    consistency: QeNscfConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not QePwDataSources:
            raise TypeError("sources must be QePwDataSources")
        if type(self.sources.qexsd) is not QeQexsdData:
            raise TypeError("NSCF sources require QeQexsdData")
        if type(self.spectral) is not QeNscfSpectralData:
            raise TypeError("spectral must be QeNscfSpectralData")
        if type(self.consistency) is not QeNscfConsistency:
            raise TypeError("consistency must be QeNscfConsistency")
        if self.qexsd.document is None:
            raise ValueError("qexsd must retain its parsed document")
        if self.spectral.source_path != self.qexsd.final_structure.source_path:
            raise ValueError("spectral data and QEXSD structure paths disagree")
        if self.spectral.source_sha256 != self.qexsd.final_structure.source_sha256:
            raise ValueError("spectral data and QEXSD structure identities disagree")
        if self.spectral.exit_status != self.qexsd.final_structure.exit_status:
            raise ValueError("spectral data and QEXSD exit status disagree")
        expected = QeNscfConsistency(
            terminal_status_matches=(
                self.streams.stdout.job_completed == (self.spectral.exit_status == 0)
            ),
            stdout_kpoint_count_matches=(
                self.streams.stdout.k_point_count == self.spectral.sampled_k_point_count
                if self.streams.stdout.k_point_count is not None
                else None
            ),
            declared_band_count_matches=True,
            declared_kpoint_count_matches=True,
        )
        if self.consistency != expected:
            raise ValueError("consistency does not describe the retained sources")
        if self.sources.execution is not None and (
            type(self.sources.execution) is not CalculatorExecutionRecord
        ):
            raise TypeError("NSCF execution must be CalculatorExecutionRecord or None")

    @property
    def streams(self) -> QePwCapturedStreamData:
        return self.sources.streams

    @property
    def qexsd(self) -> QeQexsdData:
        qexsd = self.sources.qexsd
        assert type(qexsd) is QeQexsdData
        return qexsd

    @property
    def execution(self) -> CalculatorExecutionRecord | None:
        execution = self.sources.execution
        assert execution is None or type(execution) is CalculatorExecutionRecord
        return execution

    @property
    def stdout_artifact(self) -> QePwNativeArtifact:
        return self.streams.stdout_artifact

    @property
    def stderr_artifact(self) -> QePwNativeArtifact:
        return self.streams.stderr_artifact

    @property
    def final_structure(self) -> QeQexsdFinalStructure:
        return self.qexsd.final_structure

    @property
    def document(self) -> object:
        return self.qexsd.document

    @property
    def source_path(self) -> str:
        return self.spectral.source_path

    @property
    def source_sha256(self) -> str:
        return self.spectral.source_sha256

    @property
    def source_byte_count(self) -> int:
        return self.spectral.source_byte_count

    @property
    def qexsd_version(self) -> str:
        return self.spectral.qexsd_version

    @property
    def producing_application(self) -> str:
        return self.spectral.producing_application

    @property
    def producing_application_version(self) -> str | None:
        return self.spectral.producing_application_version

    @property
    def declared_unit_system_label(self) -> str:
        return self.spectral.declared_unit_system_label

    @property
    def k_points(self) -> tuple[_Vector3, ...]:
        return self.spectral.k_points

    @property
    def k_point_weights(self) -> tuple[float, ...]:
        return self.spectral.k_point_weights

    @property
    def sampled_k_point_count(self) -> int:
        return self.spectral.sampled_k_point_count

    @property
    def k_point_source_label(self) -> str:
        return self.spectral.k_point_source_label

    @property
    def eigenvalues(self) -> _Spectrum:
        return self.spectral.eigenvalues

    @property
    def occupations(self) -> _Spectrum | None:
        return self.spectral.occupations

    @property
    def eigenvalue_source_label(self) -> str:
        return self.spectral.eigenvalue_source_label

    @property
    def band_count(self) -> int:
        return self.spectral.band_count

    @property
    def exit_status(self) -> int:
        return self.spectral.exit_status


@dataclass(frozen=True, slots=True)
class QeNscfDataExtractor:
    """Extract captured streams and QEXSD into one NSCF data facade."""

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        qexsd_document: object,
        expected_band_count: int,
        expected_kpoint_count: int,
        execution: CalculatorExecutionRecord | None = None,
        stdout_relative_path: str = "pw.out",
        stderr_relative_path: str = "pw.err",
    ) -> QeNscfData:
        """Extract native arrays and fail closed on declared shape mismatch."""
        if type(expected_band_count) is not int or expected_band_count <= 0:
            raise ValueError("expected_band_count must be positive")
        if type(expected_kpoint_count) is not int or expected_kpoint_count <= 0:
            raise ValueError("expected_kpoint_count must be positive")
        if any(not hasattr(qexsd_document, field) for field in _REQUIRED_FIELDS):
            raise TypeError(
                "qexsd_document must be produced by QuantumEspressoXsdDocumentParser"
            )
        document = cast("_QexsdNscfDocument", qexsd_document)
        if document.band_count != expected_band_count:
            raise ValueError("QEXSD band count disagrees with the NSCF declaration")
        if document.sampled_k_point_count != expected_kpoint_count:
            raise ValueError("QEXSD k-point count disagrees with the NSCF declaration")
        streams = QePwCapturedStreamDataExtractor().extract(
            stdout_payload=stdout_payload,
            stderr_payload=stderr_payload,
            stdout_relative_path=stdout_relative_path,
            stderr_relative_path=stderr_relative_path,
        )
        if streams.stdout.k_point_count is not None and (
            streams.stdout.k_point_count != expected_kpoint_count
        ):
            raise ValueError("stdout k-point count disagrees with the NSCF declaration")
        spectral = QeNscfSpectralData(
            source_path=document.source_path,
            source_sha256=document.source_sha256,
            source_byte_count=document.source_byte_count,
            qexsd_version=document.qexsd_version,
            producing_application=document.producing_application,
            producing_application_version=document.producing_application_version,
            declared_unit_system_label=document.declared_unit_system_label,
            k_points=document.k_points,
            k_point_weights=document.k_point_weights,
            sampled_k_point_count=document.sampled_k_point_count,
            k_point_source_label=document.k_point_source_label,
            eigenvalues=document.eigenvalues,
            occupations=document.occupations,
            eigenvalue_source_label=document.eigenvalue_source_label,
            band_count=document.band_count,
            exit_status=document.exit_status,
        )
        qexsd = QeQexsdData.from_document(qexsd_document)
        consistency = QeNscfConsistency(
            terminal_status_matches=(
                streams.stdout.job_completed == (document.exit_status == 0)
            ),
            stdout_kpoint_count_matches=(
                streams.stdout.k_point_count == document.sampled_k_point_count
                if streams.stdout.k_point_count is not None
                else None
            ),
            declared_band_count_matches=(document.band_count == expected_band_count),
            declared_kpoint_count_matches=(
                document.sampled_k_point_count == expected_kpoint_count
            ),
        )
        return QeNscfData(
            sources=QePwDataSources(
                streams=streams,
                qexsd=qexsd,
                execution=execution,
            ),
            spectral=spectral,
            consistency=consistency,
        )
