"""Secure retained-artifact extraction for VASP SCF evidence."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.vasp.data import VaspDataSources, VaspExecutionData
from projectkoios.integrations.vasp.data_extraction import (
    VaspDataArtifactError,
    VaspDataSourceExtractor,
)
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
class VaspScfConsistency:
    """Report mechanical source agreement without scientific acceptance policy."""

    outcar_completion_matches_execution: bool
    vasprun_program_version_matches: bool | None
    vasprun_atom_count_matches: bool | None
    vasprun_kpoint_count_matches: bool | None
    vasprun_total_energy_matches: bool | None


@dataclass(frozen=True, slots=True)
class VaspScfData:
    """Facade retained VASP SCF sources and the normalized neutral observation."""

    sources: VaspDataSources
    observation: PwDftScfObservation
    consistency: VaspScfConsistency

    def __post_init__(self) -> None:
        if type(self.sources) is not VaspDataSources:
            raise TypeError("sources must be VaspDataSources")
        if type(self.observation) is not PwDftScfObservation:
            raise TypeError("observation must be PwDftScfObservation")
        if type(self.consistency) is not VaspScfConsistency:
            raise TypeError("consistency must be VaspScfConsistency")
        expected = _consistency(self.sources)
        if self.consistency != expected:
            raise ValueError("consistency does not describe retained VASP sources")

    @property
    def total_energy_ev(self) -> float:
        return self.observation.total_energy_ev

    @property
    def atom_count(self) -> int:
        return self.observation.atom_count

    @property
    def completed(self) -> bool:
        return self.observation.completed

    @property
    def converged(self) -> bool:
        return self.observation.converged


@dataclass(frozen=True, slots=True)
class VaspScfDataExtractor:
    """Extract one bounded VASP SCF source set into a unified data facade."""

    artifact_root: Path
    maximum_artifact_bytes: int = 100_000_000

    def __post_init__(self) -> None:
        if not self.artifact_root.is_dir() or self.artifact_root.is_symlink():
            raise ValueError("artifact_root must be an existing nonsymlink directory")
        if type(self.maximum_artifact_bytes) is not int or (
            self.maximum_artifact_bytes <= 0
        ):
            raise ValueError("maximum_artifact_bytes must be positive")

    def extract(self, output_artifact_id: str) -> VaspScfData:
        """Validate execution evidence and extract OUTCAR plus optional XML."""
        outcar_path = self._resolve(output_artifact_id)
        run_directory = outcar_path.parent
        execution_path = run_directory / "execution.json"
        execution_payload = self._read(execution_path)
        execution = _execution(execution_payload)
        self._raise_for_captured_failure(run_directory, execution)

        try:
            sources = VaspDataSourceExtractor(
                artifact_root=self.artifact_root,
                maximum_artifact_bytes=self.maximum_artifact_bytes,
            ).extract(output_artifact_id)
        except VaspDataArtifactError as error:
            raise VaspScfArtifactError(str(error)) from error
        outcar = sources.outcar
        outcar_artifact = sources.artifact("outcar")
        if outcar_artifact is None:
            raise VaspScfArtifactError("VASP source data lacks the OUTCAR artifact")
        observation = PwDftScfObservation(
            total_energy_ev=outcar.total_energy_toten_ev,
            atom_count=outcar.atom_count,
            electronic_iteration_count=outcar.electronic_iteration_count,
            converged=outcar.electronic_converged,
            completed=outcar.completed,
            native_artifact=PwDftScfNativeArtifact(
                integration_id=VASP_SCF_INTEGRATION_ID,
                artifact_id=outcar_artifact.relative_path,
                sha256=outcar_artifact.sha256,
                byte_size=outcar_artifact.byte_size,
            ),
            program_version=outcar.program_version,
            irreducible_kpoint_count=outcar.irreducible_kpoint_count,
            wavefunction_cutoff_ev=outcar.wavefunction_cutoff_ev,
        )
        return VaspScfData(
            sources=sources,
            observation=observation,
            consistency=_consistency(sources),
        )

    def _raise_for_captured_failure(
        self,
        run_directory: Path,
        execution: VaspExecutionData,
    ) -> None:
        if execution.stdout_filename is None:
            return
        stdout_path = run_directory / execution.stdout_filename
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
        payload = path.read_bytes()
        if len(payload) > self.maximum_artifact_bytes:
            raise VaspScfArtifactError(f"artifact exceeds byte limit: {path}")
        return payload


@dataclass(frozen=True, slots=True)
class VaspScfOutputArtifactAnalyzer:
    """Compatibility adapter returning the calculator-neutral SCF observation."""

    artifact_root: Path
    maximum_artifact_bytes: int = 100_000_000

    def analyze(self, output_artifact_id: str) -> PwDftScfObservation:
        """Return the neutral observation from the provider data facade."""
        return (
            VaspScfDataExtractor(
                artifact_root=self.artifact_root,
                maximum_artifact_bytes=self.maximum_artifact_bytes,
            )
            .extract(output_artifact_id)
            .observation
        )


def _execution(payload: bytes) -> VaspExecutionData:
    parsed = json.loads(payload.decode("utf-8"))
    if not isinstance(parsed, dict) or parsed.get("schema_version") != 1:
        raise VaspScfArtifactError("unsupported execution record")
    if (
        parsed.get("status") != "succeeded"
        or type(parsed.get("returncode")) is not int
        or parsed.get("returncode") != 0
    ):
        raise VaspScfArtifactError("VASP execution record is not successful")
    stdout = parsed.get("stdout_filename")
    stderr = parsed.get("stderr_filename")
    if stdout is not None and not isinstance(stdout, str):
        raise VaspScfArtifactError("stdout_filename must be a string")
    if stderr is not None and not isinstance(stderr, str):
        raise VaspScfArtifactError("stderr_filename must be a string")
    return VaspExecutionData(
        status="succeeded",
        returncode=0,
        stdout_filename=stdout,
        stderr_filename=stderr,
    )


def _consistency(sources: VaspDataSources) -> VaspScfConsistency:
    vasprun = sources.vasprun
    if vasprun is None:
        return VaspScfConsistency(
            outcar_completion_matches_execution=sources.outcar.completed,
            vasprun_program_version_matches=None,
            vasprun_atom_count_matches=None,
            vasprun_kpoint_count_matches=None,
            vasprun_total_energy_matches=None,
        )
    final_step = vasprun.ionic_steps[-1]
    return VaspScfConsistency(
        outcar_completion_matches_execution=sources.outcar.completed,
        vasprun_program_version_matches=(
            sources.outcar.program_version == vasprun.program_version
        ),
        vasprun_atom_count_matches=(
            sources.outcar.atom_count == len(vasprun.atom_labels)
        ),
        vasprun_kpoint_count_matches=(
            sources.outcar.irreducible_kpoint_count == len(vasprun.k_points)
        ),
        vasprun_total_energy_matches=math.isclose(
            sources.outcar.total_energy_toten_ev,
            final_step.free_energy_ev,
            rel_tol=0.0,
            abs_tol=1.0e-8,
        ),
    )
