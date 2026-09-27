"""Extract native spectral data from parsed Quantum ESPRESSO NSCF evidence."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Protocol, cast

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (  # noqa: E501
    QePwCapturedStreamData,
    QePwCapturedStreamDataExtractor,
)

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
class QeNscfData:
    """Retain source-ordered NSCF data without native-unit normalization."""

    streams: QePwCapturedStreamData
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
        if type(self.streams) is not QePwCapturedStreamData:
            raise TypeError("streams must be QePwCapturedStreamData")
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
class QeNscfDataExtractor:
    """Own NSCF extraction from captured streams and maintained-parser QEXSD."""

    def extract(
        self,
        *,
        stdout_payload: bytes,
        stderr_payload: bytes,
        qexsd_document: object,
        expected_band_count: int,
        expected_kpoint_count: int,
        stdout_relative_path: str = "pw.out",
        stderr_relative_path: str = "pw.err",
    ) -> QeNscfData:
        """Extract raw native arrays and fail closed on declared shape mismatch."""
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
        return QeNscfData(
            streams=streams,
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
