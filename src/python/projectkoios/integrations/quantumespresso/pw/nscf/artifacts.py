"""Correlate one executed QE NSCF artifact set without scientific policy."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifestJsonCodec,
    QeSavedStateManifestVerifier,
)


@dataclass(frozen=True, slots=True)
class QeNscfArtifactObservation:
    """Bind one regular artifact to its exact bytes."""

    path: Path
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            raise TypeError("path must be an absolute Path")
        if (
            type(self.sha256) is not str
            or len(self.sha256) != 64
            or not set(self.sha256) <= set("0123456789abcdef")
        ):
            raise ValueError("sha256 must be a lowercase SHA-256")
        if type(self.byte_size) is not int or self.byte_size < 0:
            raise ValueError("byte_size must be nonnegative")


@dataclass(frozen=True, slots=True)
class QeNscfArtifactSet:
    """Correlate the native files required for later NSCF extraction."""

    input_file: QeNscfArtifactObservation
    stdout_file: QeNscfArtifactObservation
    stderr_file: QeNscfArtifactObservation
    execution_record: QeNscfArtifactObservation
    saved_state_manifest: QeNscfArtifactObservation
    qexsd_file: QeNscfArtifactObservation
    prefix: str


@dataclass(frozen=True, slots=True)
class QeNscfArtifactInspector:
    """Verify and correlate artifacts from one maintained NSCF execution."""

    max_observed_file_bytes: int = 64 * 1024 * 1024

    def __post_init__(self) -> None:
        if (
            type(self.max_observed_file_bytes) is not int
            or self.max_observed_file_bytes <= 0
        ):
            raise ValueError("max_observed_file_bytes must be positive")

    def inspect(
        self,
        *,
        output_directory: Path,
        input_filename: str,
        saved_state_manifest: Path,
        saved_state_source_root: Path,
    ) -> QeNscfArtifactSet:
        """Verify one NSCF artifact set and select its sole QEXSD document."""
        if not isinstance(output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if output_directory.is_symlink() or not output_directory.is_dir():
            raise ValueError(
                "output_directory must be an existing nonsymlink directory"
            )
        if not isinstance(saved_state_source_root, Path):
            raise TypeError("saved_state_source_root must be a Path")
        if saved_state_source_root.is_symlink() or not saved_state_source_root.is_dir():
            raise ValueError(
                "saved_state_source_root must be an existing nonsymlink directory"
            )
        if (
            type(input_filename) is not str
            or not input_filename
            or Path(input_filename).name != input_filename
        ):
            raise ValueError("input_filename must be a basename")
        manifest_observation = self._observe(
            saved_state_manifest,
            "saved-state manifest",
        )
        manifest = QeSavedStateManifestJsonCodec().loads(
            saved_state_manifest.read_bytes()
        )
        if manifest.calculation is not QeSavedStateCalculation.nscf:
            raise ValueError("artifact inspection requires an NSCF saved state")
        QeSavedStateManifestVerifier().verify(manifest, saved_state_source_root)
        qexsd_artifacts = tuple(
            artifact
            for artifact in manifest.artifacts
            if artifact.role is QeSavedStateArtifactRole.qexsd
        )
        if len(qexsd_artifacts) != 1:
            raise ValueError("NSCF saved state must declare exactly one QEXSD artifact")
        qexsd = qexsd_artifacts[0]
        qexsd_path = saved_state_source_root / qexsd.relative_path
        qexsd_observation = self._observe(qexsd_path, "QEXSD artifact")
        if (
            qexsd_observation.sha256 != qexsd.sha256
            or qexsd_observation.byte_size != qexsd.byte_size
        ):
            raise ValueError("QEXSD artifact identity disagrees with manifest")
        return QeNscfArtifactSet(
            input_file=self._observe(output_directory / input_filename, "input"),
            stdout_file=self._observe(output_directory / "pw.out", "stdout"),
            stderr_file=self._observe(output_directory / "pw.err", "stderr"),
            execution_record=self._observe(
                output_directory / "execution.json",
                "execution record",
            ),
            saved_state_manifest=manifest_observation,
            qexsd_file=qexsd_observation,
            prefix=manifest.prefix,
        )

    def _observe(self, path: Path, label: str) -> QeNscfArtifactObservation:
        if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
            raise ValueError(f"{label} must be a regular file")
        byte_size = path.stat().st_size
        if byte_size > self.max_observed_file_bytes:
            raise ValueError(f"{label} exceeds the observation byte bound")
        payload = path.read_bytes()
        return QeNscfArtifactObservation(
            path=path.absolute(),
            sha256=hashlib.sha256(payload).hexdigest(),
            byte_size=len(payload),
        )
