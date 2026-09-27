"""Immutable declarations for retained QE SCF convergence evidence."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

_SHA256 = re.compile(r"[0-9a-f]{64}")
_EXPECTED_ARTIFACT_ROLES = frozenset(
    {"pw-input", "pw-stdout", "pw-stderr", "execution-record"}
)


class RetainedQeScfEvidenceError(ValueError):
    """Report malformed, incomplete, escaped, or inconsistent evidence."""


class RetainedArtifactRole(StrEnum):
    """Identify one retained artifact's role without interpreting its content."""

    PW_INPUT = "pw-input"
    PW_STDOUT = "pw-stdout"
    PW_STDERR = "pw-stderr"
    EXECUTION_RECORD = "execution-record"


class RetainedObservationStage(StrEnum):
    """Distinguish the initial grid from later policy-requested points."""

    INITIAL_GRID = "initial-grid"
    ADAPTIVE_EXTENSION = "adaptive-extension"


@dataclass(frozen=True, slots=True)
class RetainedArtifactIdentity:
    """Identify exact retained bytes relative to the evidence directory."""

    role: RetainedArtifactRole
    artifact_id: str
    sha256: str
    byte_size: int


@dataclass(frozen=True, slots=True)
class RetainedStructureIdentity:
    """Identify the repository-owned structure used by every observation."""

    structure_id: str
    repository_path: str
    sha256: str
    byte_size: int
    atom_count: int


@dataclass(frozen=True, slots=True)
class UnretainedCalculatorIdentity:
    """Identify calculator bytes that are deliberately not copied here."""

    program: str
    program_version: str
    source_revision: str
    sha256: str
    byte_size: int
    retained: bool


@dataclass(frozen=True, slots=True)
class UnretainedPseudopotentialIdentity:
    """Identify one pseudopotential without copying its bytes."""

    species: str
    artifact_name: str
    exchange_correlation: str
    formalism: str
    relativistic_treatment: str
    upf_version: str
    sha256: str
    byte_size: int
    retained: bool


@dataclass(frozen=True, slots=True)
class RetainedConvergencePolicy:
    """Declare the bounded policy used to request and assess the grid."""

    tolerance_mev_per_atom: float
    required_consecutive_deltas: int
    mesh_increment: int
    cutoff_increment_ry: float
    extension_steps: int
    maximum_mesh_density: int
    maximum_cutoff_ry: float
    maximum_grid_points: int


@dataclass(frozen=True, slots=True)
class RetainedConvergenceCoordinate:
    """Declare one cubic mesh and its two native QE cutoff values."""

    mesh_density: int
    wavefunction_cutoff_ry: float
    charge_density_cutoff_ry: float


@dataclass(frozen=True, slots=True)
class RetainedNativeObservation:
    """Preserve selected native observations before unit normalization."""

    program_version: str
    job_completed: bool
    scf_converged: bool
    total_energy_ry: float
    atom_count: int
    irreducible_kpoint_count: int
    scf_iteration_count: int
    execution_status: str
    returncode: int


@dataclass(frozen=True, slots=True)
class RetainedDiagnostic:
    """Preserve one structured diagnostic tied to its native stream."""

    code: str
    severity: str
    native_flag: str
    artifact_role: RetainedArtifactRole


@dataclass(frozen=True, slots=True)
class RetainedConvergenceObservation:
    """Bind one coordinate to native observations and exact artifacts."""

    run_id: str
    stage: RetainedObservationStage
    coordinate: RetainedConvergenceCoordinate
    native_observation: RetainedNativeObservation
    diagnostics: tuple[RetainedDiagnostic, ...]
    artifacts: tuple[RetainedArtifactIdentity, ...]

    def artifact(self, role: RetainedArtifactRole) -> RetainedArtifactIdentity:
        """Return the uniquely declared artifact for ``role``."""
        matches = tuple(item for item in self.artifacts if item.role is role)
        if len(matches) != 1:
            raise RetainedQeScfEvidenceError(
                f"{self.run_id} must declare exactly one {role.value} artifact"
            )
        return matches[0]


@dataclass(frozen=True, slots=True)
class RetainedQeScfConvergenceEvidence:
    """Compose one complete, data-only QE convergence evidence record."""

    schema_version: int
    evidence_kind: str
    evidence_id: str
    qualifications: tuple[str, ...]
    structure: RetainedStructureIdentity
    calculator: UnretainedCalculatorIdentity
    pseudopotentials: tuple[UnretainedPseudopotentialIdentity, ...]
    policy: RetainedConvergencePolicy
    observations: tuple[RetainedConvergenceObservation, ...]


@dataclass(frozen=True, slots=True)
class RetainedQeScfEvidenceLoader:
    """Load a closed manifest and verify every repository-retained identity."""

    repository_root: Path
    maximum_file_bytes: int = 100_000_000

    def __post_init__(self) -> None:
        if not self.repository_root.is_dir() or self.repository_root.is_symlink():
            raise ValueError("repository_root must be an existing nonsymlink directory")
        if type(self.maximum_file_bytes) is not int or self.maximum_file_bytes <= 0:
            raise ValueError("maximum_file_bytes must be a positive integer")

    def load(self, manifest_path: Path) -> RetainedQeScfConvergenceEvidence:
        """Return validated declarations after checking all retained bytes."""
        manifest_file = self._resolve_inside(self.repository_root, manifest_path)
        payload = self._mapping(
            json.loads(self._read(manifest_file).decode("utf-8")),
            "manifest",
            {
                "schema_version",
                "evidence_kind",
                "evidence_id",
                "qualifications",
                "structure",
                "calculator",
                "pseudopotentials",
                "policy",
                "observations",
            },
        )
        schema_version = self._integer(payload, "schema_version")
        if schema_version != 1:
            raise RetainedQeScfEvidenceError("unsupported evidence schema_version")
        evidence_kind = self._string(payload, "evidence_kind")
        if evidence_kind != "qe-pw-scf-convergence-grid":
            raise RetainedQeScfEvidenceError("unsupported evidence_kind")
        evidence_root = manifest_file.parent
        structure = self._structure(payload.get("structure"))
        calculator = self._calculator(payload.get("calculator"))
        pseudopotentials = tuple(
            self._pseudopotential(item)
            for item in self._array(payload, "pseudopotentials")
        )
        policy = self._policy(payload.get("policy"))
        observations = tuple(
            self._observation(item) for item in self._array(payload, "observations")
        )
        evidence = RetainedQeScfConvergenceEvidence(
            schema_version=schema_version,
            evidence_kind=evidence_kind,
            evidence_id=self._string(payload, "evidence_id"),
            qualifications=tuple(
                self._string_value(item, "qualification")
                for item in self._array(payload, "qualifications")
            ),
            structure=structure,
            calculator=calculator,
            pseudopotentials=pseudopotentials,
            policy=policy,
            observations=observations,
        )
        self._validate_composition(evidence)
        self._verify_repository_artifact(
            structure.repository_path,
            structure.sha256,
            structure.byte_size,
        )
        for observation in evidence.observations:
            for artifact in observation.artifacts:
                self._verify_retained_artifact(evidence_root, artifact)
        return evidence

    def _structure(self, value: object) -> RetainedStructureIdentity:
        payload = self._mapping(
            value,
            "structure",
            {"structure_id", "repository_path", "sha256", "byte_size", "atom_count"},
        )
        return RetainedStructureIdentity(
            structure_id=self._string(payload, "structure_id"),
            repository_path=self._relative_path(payload, "repository_path"),
            sha256=self._sha256(payload, "sha256"),
            byte_size=self._integer(payload, "byte_size", positive=True),
            atom_count=self._integer(payload, "atom_count", positive=True),
        )

    def _calculator(self, value: object) -> UnretainedCalculatorIdentity:
        payload = self._mapping(
            value,
            "calculator",
            {
                "program",
                "program_version",
                "source_revision",
                "sha256",
                "byte_size",
                "retained",
            },
        )
        retained = self._boolean(payload, "retained")
        if retained:
            raise RetainedQeScfEvidenceError(
                "calculator identity must not claim unretained bytes are retained"
            )
        return UnretainedCalculatorIdentity(
            program=self._string(payload, "program"),
            program_version=self._string(payload, "program_version"),
            source_revision=self._string(payload, "source_revision"),
            sha256=self._sha256(payload, "sha256"),
            byte_size=self._integer(payload, "byte_size", positive=True),
            retained=retained,
        )

    def _pseudopotential(self, value: object) -> UnretainedPseudopotentialIdentity:
        payload = self._mapping(
            value,
            "pseudopotential",
            {
                "species",
                "artifact_name",
                "exchange_correlation",
                "formalism",
                "relativistic_treatment",
                "upf_version",
                "sha256",
                "byte_size",
                "retained",
            },
        )
        retained = self._boolean(payload, "retained")
        if retained:
            raise RetainedQeScfEvidenceError(
                "pseudopotential identity must not claim unretained bytes are retained"
            )
        return UnretainedPseudopotentialIdentity(
            species=self._string(payload, "species"),
            artifact_name=self._basename(payload, "artifact_name"),
            exchange_correlation=self._string(payload, "exchange_correlation"),
            formalism=self._string(payload, "formalism"),
            relativistic_treatment=self._string(payload, "relativistic_treatment"),
            upf_version=self._string(payload, "upf_version"),
            sha256=self._sha256(payload, "sha256"),
            byte_size=self._integer(payload, "byte_size", positive=True),
            retained=retained,
        )

    def _policy(self, value: object) -> RetainedConvergencePolicy:
        payload = self._mapping(
            value,
            "policy",
            {
                "tolerance_mev_per_atom",
                "required_consecutive_deltas",
                "mesh_increment",
                "cutoff_increment_ry",
                "extension_steps",
                "maximum_mesh_density",
                "maximum_cutoff_ry",
                "maximum_grid_points",
            },
        )
        return RetainedConvergencePolicy(
            tolerance_mev_per_atom=self._number(
                payload, "tolerance_mev_per_atom", positive=True
            ),
            required_consecutive_deltas=self._integer(
                payload, "required_consecutive_deltas", positive=True
            ),
            mesh_increment=self._integer(payload, "mesh_increment", positive=True),
            cutoff_increment_ry=self._number(
                payload, "cutoff_increment_ry", positive=True
            ),
            extension_steps=self._integer(payload, "extension_steps", positive=True),
            maximum_mesh_density=self._integer(
                payload, "maximum_mesh_density", positive=True
            ),
            maximum_cutoff_ry=self._number(payload, "maximum_cutoff_ry", positive=True),
            maximum_grid_points=self._integer(
                payload, "maximum_grid_points", positive=True
            ),
        )

    def _observation(self, value: object) -> RetainedConvergenceObservation:
        payload = self._mapping(
            value,
            "observation",
            {
                "run_id",
                "stage",
                "coordinate",
                "native_observation",
                "diagnostics",
                "artifacts",
            },
        )
        coordinate_payload = self._mapping(
            payload.get("coordinate"),
            "coordinate",
            {"mesh_density", "wavefunction_cutoff_ry", "charge_density_cutoff_ry"},
        )
        native_payload = self._mapping(
            payload.get("native_observation"),
            "native_observation",
            {
                "program_version",
                "job_completed",
                "scf_converged",
                "total_energy_ry",
                "atom_count",
                "irreducible_kpoint_count",
                "scf_iteration_count",
                "execution_status",
                "returncode",
            },
        )
        stage_value = self._string(payload, "stage")
        try:
            stage = RetainedObservationStage(stage_value)
        except ValueError as error:
            raise RetainedQeScfEvidenceError(
                f"unsupported observation stage: {stage_value}"
            ) from error
        return RetainedConvergenceObservation(
            run_id=self._string(payload, "run_id"),
            stage=stage,
            coordinate=RetainedConvergenceCoordinate(
                mesh_density=self._integer(
                    coordinate_payload, "mesh_density", positive=True
                ),
                wavefunction_cutoff_ry=self._number(
                    coordinate_payload, "wavefunction_cutoff_ry", positive=True
                ),
                charge_density_cutoff_ry=self._number(
                    coordinate_payload, "charge_density_cutoff_ry", positive=True
                ),
            ),
            native_observation=RetainedNativeObservation(
                program_version=self._string(native_payload, "program_version"),
                job_completed=self._boolean(native_payload, "job_completed"),
                scf_converged=self._boolean(native_payload, "scf_converged"),
                total_energy_ry=self._number(native_payload, "total_energy_ry"),
                atom_count=self._integer(native_payload, "atom_count", positive=True),
                irreducible_kpoint_count=self._integer(
                    native_payload, "irreducible_kpoint_count", positive=True
                ),
                scf_iteration_count=self._integer(
                    native_payload, "scf_iteration_count", positive=True
                ),
                execution_status=self._string(native_payload, "execution_status"),
                returncode=self._integer(native_payload, "returncode"),
            ),
            diagnostics=tuple(
                self._diagnostic(item)
                for item in self._array(payload, "diagnostics", allow_empty=True)
            ),
            artifacts=tuple(
                self._artifact(item) for item in self._array(payload, "artifacts")
            ),
        )

    def _diagnostic(self, value: object) -> RetainedDiagnostic:
        payload = self._mapping(
            value,
            "diagnostic",
            {"code", "severity", "native_flag", "artifact_role"},
        )
        role = self._artifact_role(self._string(payload, "artifact_role"))
        return RetainedDiagnostic(
            code=self._string(payload, "code"),
            severity=self._string(payload, "severity"),
            native_flag=self._string(payload, "native_flag"),
            artifact_role=role,
        )

    def _artifact(self, value: object) -> RetainedArtifactIdentity:
        payload = self._mapping(
            value,
            "artifact",
            {"role", "artifact_id", "sha256", "byte_size"},
        )
        return RetainedArtifactIdentity(
            role=self._artifact_role(self._string(payload, "role")),
            artifact_id=self._relative_path(payload, "artifact_id"),
            sha256=self._sha256(payload, "sha256"),
            byte_size=self._integer(payload, "byte_size", positive=True),
        )

    @staticmethod
    def _artifact_role(value: str) -> RetainedArtifactRole:
        try:
            return RetainedArtifactRole(value)
        except ValueError as error:
            raise RetainedQeScfEvidenceError(
                f"unsupported artifact role: {value}"
            ) from error

    def _validate_composition(self, evidence: RetainedQeScfConvergenceEvidence) -> None:
        if not evidence.qualifications:
            raise RetainedQeScfEvidenceError("qualifications must not be empty")
        if not evidence.pseudopotentials:
            raise RetainedQeScfEvidenceError("pseudopotentials must not be empty")
        if not evidence.observations:
            raise RetainedQeScfEvidenceError("observations must not be empty")
        run_ids = tuple(item.run_id for item in evidence.observations)
        coordinates = tuple(item.coordinate for item in evidence.observations)
        if len(run_ids) != len(set(run_ids)):
            raise RetainedQeScfEvidenceError("observation run_id values must be unique")
        if len(coordinates) != len(set(coordinates)):
            raise RetainedQeScfEvidenceError("observation coordinates must be unique")
        artifact_ids: list[str] = []
        for observation in evidence.observations:
            roles = {item.role.value for item in observation.artifacts}
            if roles != _EXPECTED_ARTIFACT_ROLES or len(observation.artifacts) != 4:
                raise RetainedQeScfEvidenceError(
                    f"{observation.run_id} must declare all four artifact roles once"
                )
            artifact_ids.extend(item.artifact_id for item in observation.artifacts)
            native = observation.native_observation
            if native.program_version != evidence.calculator.program_version:
                raise RetainedQeScfEvidenceError("observation program version mismatch")
            if native.atom_count != evidence.structure.atom_count:
                raise RetainedQeScfEvidenceError("observation atom count mismatch")
            if not native.job_completed or not native.scf_converged:
                raise RetainedQeScfEvidenceError(
                    "convergence grid contains an incomplete or unconverged calculation"
                )
            if native.execution_status != "succeeded" or native.returncode != 0:
                raise RetainedQeScfEvidenceError(
                    "convergence grid contains an unsuccessful execution"
                )
            if any(item.severity != "warning" for item in observation.diagnostics):
                raise RetainedQeScfEvidenceError(
                    "successful evidence may only retain warning diagnostics"
                )
        if len(artifact_ids) != len(set(artifact_ids)):
            raise RetainedQeScfEvidenceError("artifact_id values must be unique")

    def _verify_repository_artifact(
        self, repository_path: str, expected_sha256: str, expected_size: int
    ) -> None:
        path = self._resolve_inside(self.repository_root, Path(repository_path))
        self._verify_bytes(path, expected_sha256, expected_size)

    def _verify_retained_artifact(
        self, evidence_root: Path, artifact: RetainedArtifactIdentity
    ) -> None:
        path = self._resolve_inside(evidence_root, Path(artifact.artifact_id))
        self._verify_bytes(path, artifact.sha256, artifact.byte_size)

    def _verify_bytes(
        self, path: Path, expected_sha256: str, expected_size: int
    ) -> None:
        payload = self._read(path)
        if len(payload) != expected_size:
            raise RetainedQeScfEvidenceError(f"artifact byte_size mismatch: {path}")
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise RetainedQeScfEvidenceError(f"artifact sha256 mismatch: {path}")

    def _read(self, path: Path) -> bytes:
        if not path.is_file() or path.is_symlink():
            raise RetainedQeScfEvidenceError(f"artifact must be a regular file: {path}")
        if path.stat().st_size > self.maximum_file_bytes:
            raise RetainedQeScfEvidenceError(f"artifact exceeds byte limit: {path}")
        return path.read_bytes()

    @staticmethod
    def _resolve_inside(root: Path, path: Path) -> Path:
        if path.is_absolute():
            candidate = path.resolve()
        else:
            candidate = (root.resolve() / path).resolve()
        if not candidate.is_relative_to(root.resolve()):
            raise RetainedQeScfEvidenceError("artifact path escapes its declared root")
        return candidate

    @staticmethod
    def _mapping(
        value: object, label: str, expected_keys: set[str]
    ) -> dict[str, object]:
        if not isinstance(value, dict) or any(type(key) is not str for key in value):
            raise RetainedQeScfEvidenceError(f"{label} must be an object")
        keys = set(value)
        if keys != expected_keys:
            missing = sorted(expected_keys - keys)
            unexpected = sorted(keys - expected_keys)
            raise RetainedQeScfEvidenceError(
                f"{label} keys mismatch; missing={missing}, unexpected={unexpected}"
            )
        return value

    @staticmethod
    def _array(
        mapping: dict[str, object], key: str, *, allow_empty: bool = False
    ) -> list[object]:
        value = mapping.get(key)
        if not isinstance(value, list) or (not value and not allow_empty):
            suffix = "" if allow_empty else " nonempty"
            raise RetainedQeScfEvidenceError(f"{key} must be a{suffix} array")
        return value

    @classmethod
    def _string(cls, mapping: dict[str, object], key: str) -> str:
        return cls._string_value(mapping.get(key), key)

    @staticmethod
    def _string_value(value: object, label: str) -> str:
        if type(value) is not str or not value or value != value.strip():
            raise RetainedQeScfEvidenceError(
                f"{label} must be a nonempty stripped string"
            )
        return value

    @classmethod
    def _basename(cls, mapping: dict[str, object], key: str) -> str:
        value = cls._string(mapping, key)
        if Path(value).name != value or value in {".", ".."}:
            raise RetainedQeScfEvidenceError(f"{key} must be a basename")
        return value

    @classmethod
    def _relative_path(cls, mapping: dict[str, object], key: str) -> str:
        value = cls._string(mapping, key)
        path = Path(value)
        if path.is_absolute() or value in {".", ".."}:
            raise RetainedQeScfEvidenceError(f"{key} must be a relative path")
        return value

    @staticmethod
    def _boolean(mapping: dict[str, object], key: str) -> bool:
        value = mapping.get(key)
        if type(value) is not bool:
            raise RetainedQeScfEvidenceError(f"{key} must be a boolean")
        return value

    @staticmethod
    def _integer(
        mapping: dict[str, object], key: str, *, positive: bool = False
    ) -> int:
        value = mapping.get(key)
        if type(value) is not int or (positive and value <= 0):
            qualifier = "positive " if positive else ""
            raise RetainedQeScfEvidenceError(f"{key} must be a {qualifier}integer")
        return value

    @staticmethod
    def _number(
        mapping: dict[str, object], key: str, *, positive: bool = False
    ) -> float:
        value = mapping.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RetainedQeScfEvidenceError(f"{key} must be a number")
        number = float(value)
        if not math.isfinite(number) or (positive and number <= 0.0):
            qualifier = "positive " if positive else "finite "
            raise RetainedQeScfEvidenceError(
                f"{key} must be a {qualifier}finite number"
            )
        return number

    @classmethod
    def _sha256(cls, mapping: dict[str, object], key: str) -> str:
        value = cls._string(mapping, key)
        if _SHA256.fullmatch(value) is None:
            raise RetainedQeScfEvidenceError(f"{key} must be lowercase SHA-256")
        return value
