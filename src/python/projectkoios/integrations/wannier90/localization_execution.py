"""Prepare and execute one identity-bound Wannier90 localization occurrence."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np

from projectkoios.integrations.wannier90.artifacts import (
    Wannier90NativeArtifactIdentity,
)
from projectkoios.integrations.wannier90.disentanglement_matrices import (
    Wannier90DisentanglementMatrixParser,
)
from projectkoios.integrations.wannier90.hamiltonian_blocks import (
    Wannier90HamiltonianBlockParser,
)
from projectkoios.integrations.wannier90.interface_data import (
    Wannier90EigenvalueParser,
    Wannier90NeighborOverlapParser,
    Wannier90ProjectionParser,
)
from projectkoios.integrations.wannier90.localization import (
    Wannier90LocalizationParser,
)
from projectkoios.integrations.wannier90.nnkp import Wannier90NnkpParser
from projectkoios.integrations.wannier90.unitary_matrices import (
    Wannier90UnitaryMatrixParser,
)
from projectkoios.physkit.units.quantities import PhysicalUnit
from projectkoios.simulations.execution import (
    CalculatorExecutionError,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    CalculatorOutputEmissionError,
)

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]

_NNKP_FRACTIONAL_KPOINT_SERIALIZATION_TOLERANCE = 1.0e-8


class Wannier90LocalizationInputRole(StrEnum):
    """Identify one role in the closed ordinary AMN/MMN input inventory."""

    construction_input = "construction-input"
    preprocessing_topology = "preprocessing-topology"
    eigenvalues = "interface-eigenvalues"
    projections = "interface-projections"
    neighbor_overlaps = "interface-neighbor-overlaps"


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationInputArtifact:
    """Bind one prepared input identity to its localization role."""

    role: Wannier90LocalizationInputRole
    identity: Wannier90NativeArtifactIdentity

    def __post_init__(self) -> None:
        if type(self.role) is not Wannier90LocalizationInputRole:
            raise TypeError("role must be a Wannier90LocalizationInputRole")
        if type(self.identity) is not Wannier90NativeArtifactIdentity:
            raise TypeError("identity must be a Wannier90NativeArtifactIdentity")
        if self.identity.byte_count <= 0:
            raise ValueError("localization inputs must be nonempty")


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationInputManifest:
    """Declare one complete, dimensioned ordinary localization input set."""

    schema_version: int
    seedname: str
    kpoint_count: int
    band_count: int
    wannier_count: int
    neighbor_count: int
    parent_preprocessing_sha256: str
    parent_converter_sha256: str
    artifacts: tuple[Wannier90LocalizationInputArtifact, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported localization input schema version")
        _validate_seedname(self.seedname)
        for label, value in (
            ("kpoint_count", self.kpoint_count),
            ("band_count", self.band_count),
            ("wannier_count", self.wannier_count),
            ("neighbor_count", self.neighbor_count),
        ):
            if type(value) is not int or value <= 0:
                raise ValueError(f"{label} must be positive")
        if self.wannier_count >= self.band_count:
            raise ValueError(
                "the first rank-reducing profile requires wannier_count < band_count"
            )
        _validate_sha256(
            self.parent_preprocessing_sha256, "parent_preprocessing_sha256"
        )
        _validate_sha256(self.parent_converter_sha256, "parent_converter_sha256")
        if type(self.artifacts) is not tuple or any(
            type(value) is not Wannier90LocalizationInputArtifact
            for value in self.artifacts
        ):
            raise TypeError("artifacts must be a typed tuple")
        expected = (
            (Wannier90LocalizationInputRole.construction_input, f"{self.seedname}.win"),
            (
                Wannier90LocalizationInputRole.preprocessing_topology,
                f"{self.seedname}.nnkp",
            ),
            (Wannier90LocalizationInputRole.eigenvalues, f"{self.seedname}.eig"),
            (Wannier90LocalizationInputRole.projections, f"{self.seedname}.amn"),
            (
                Wannier90LocalizationInputRole.neighbor_overlaps,
                f"{self.seedname}.mmn",
            ),
        )
        observed = tuple((value.role, value.identity.name) for value in self.artifacts)
        if observed != expected:
            raise ValueError("localization input inventory is not closed and ordered")

    @property
    def total_byte_count(self) -> int:
        return sum(value.identity.byte_count for value in self.artifacts)

    def to_json_bytes(self) -> bytes:
        """Return the canonical manifest representation used for authentication."""
        value: JsonObject = {
            "artifacts": [
                {
                    "byte_count": artifact.identity.byte_count,
                    "name": artifact.identity.name,
                    "role": artifact.role.value,
                    "sha256": artifact.identity.sha256,
                }
                for artifact in self.artifacts
            ],
            "band_count": self.band_count,
            "kpoint_count": self.kpoint_count,
            "neighbor_count": self.neighbor_count,
            "parent_converter_sha256": self.parent_converter_sha256,
            "parent_preprocessing_sha256": self.parent_preprocessing_sha256,
            "route_kind": "first-rank-reducing-amn-mmn-non-spin",
            "schema_version": self.schema_version,
            "seedname": self.seedname,
            "total_byte_count": self.total_byte_count,
            "wannier_count": self.wannier_count,
        }
        return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationPreparationResult:
    """Identify one newly created, verified prepared-input directory."""

    output_directory: Path
    manifest: Wannier90LocalizationInputManifest
    manifest_path: Path


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationInputPreparer:
    """Authenticate, correlate, and copy one closed native input inventory."""

    def prepare(
        self,
        *,
        source_directory: Path,
        output_directory: Path,
        seedname: str,
        kpoint_count: int,
        band_count: int,
        wannier_count: int,
        neighbor_count: int,
        parent_preprocessing_sha256: str,
        parent_converter_sha256: str,
    ) -> Wannier90LocalizationPreparationResult:
        """Create prepared bytes without resolving or invoking an executable."""
        _validate_seedname(seedname)
        if not isinstance(source_directory, Path) or source_directory.is_symlink():
            raise ValueError("source_directory must be a nonsymlink Path")
        if not source_directory.is_dir():
            raise ValueError("source_directory must be an existing directory")
        if not isinstance(output_directory, Path):
            raise TypeError("output_directory must be a Path")
        output = output_directory.absolute()
        if output.exists():
            raise ValueError("output_directory already exists")
        _require_separate_directories(source_directory, output)
        roles = (
            (Wannier90LocalizationInputRole.construction_input, f"{seedname}.win"),
            (Wannier90LocalizationInputRole.preprocessing_topology, f"{seedname}.nnkp"),
            (Wannier90LocalizationInputRole.eigenvalues, f"{seedname}.eig"),
            (Wannier90LocalizationInputRole.projections, f"{seedname}.amn"),
            (
                Wannier90LocalizationInputRole.neighbor_overlaps,
                f"{seedname}.mmn",
            ),
        )
        expected_names = tuple(name for _, name in roles)
        _require_closed_directory(source_directory, expected_names)
        payloads = {
            name: _read_regular_file(source_directory / name, name)
            for name in expected_names
        }
        manifest = Wannier90LocalizationInputManifest(
            schema_version=1,
            seedname=seedname,
            kpoint_count=kpoint_count,
            band_count=band_count,
            wannier_count=wannier_count,
            neighbor_count=neighbor_count,
            parent_preprocessing_sha256=parent_preprocessing_sha256,
            parent_converter_sha256=parent_converter_sha256,
            artifacts=tuple(
                Wannier90LocalizationInputArtifact(
                    role,
                    Wannier90NativeArtifactIdentity(
                        name,
                        len(payloads[name]),
                        hashlib.sha256(payloads[name]).hexdigest(),
                    ),
                )
                for role, name in roles
            ),
        )
        _parse_and_correlate_inputs(manifest, payloads)
        output.mkdir(parents=True)
        for name in expected_names:
            (output / name).write_bytes(payloads[name])
        manifest_path = output / "localization-input-manifest.json"
        manifest_path.write_bytes(manifest.to_json_bytes())
        return Wannier90LocalizationPreparationResult(output, manifest, manifest_path)


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationRunRequest:
    """Declare one separately authorized localization process occurrence."""

    manifest: Wannier90LocalizationInputManifest
    prepared_input_directory: Path
    manifest_path: Path
    manifest_sha256: str
    manifest_byte_count: int
    output_directory: Path
    executable: Path
    executable_sha256: str
    executable_byte_count: int
    executable_version: str
    timeout_seconds: float
    maximum_retained_bytes: int
    execution_authorized: bool = False
    length_unit: PhysicalUnit = PhysicalUnit("angstrom")
    energy_unit: PhysicalUnit = PhysicalUnit("eV")
    kpoint_tolerance: float = 1.0e-10
    isometry_tolerance: float = 1.0e-8
    hamiltonian_hermiticity_tolerance: float = 1.0e-8

    def __post_init__(self) -> None:
        if type(self.manifest) is not Wannier90LocalizationInputManifest:
            raise TypeError("manifest must be a Wannier90LocalizationInputManifest")
        for label, path_value in (
            ("prepared_input_directory", self.prepared_input_directory),
            ("manifest_path", self.manifest_path),
            ("output_directory", self.output_directory),
            ("executable", self.executable),
        ):
            if not isinstance(path_value, Path):
                raise TypeError(f"{label} must be a Path")
        _validate_sha256(self.manifest_sha256, "manifest_sha256")
        _validate_sha256(self.executable_sha256, "executable_sha256")
        if type(self.executable_version) is not str or not self.executable_version:
            raise ValueError("executable_version must be a nonempty string")
        for label, integer_value in (
            ("manifest_byte_count", self.manifest_byte_count),
            ("executable_byte_count", self.executable_byte_count),
            ("maximum_retained_bytes", self.maximum_retained_bytes),
        ):
            if type(integer_value) is not int or integer_value <= 0:
                raise ValueError(f"{label} must be positive")
        for label, float_value in (
            ("timeout_seconds", self.timeout_seconds),
            ("kpoint_tolerance", self.kpoint_tolerance),
            ("isometry_tolerance", self.isometry_tolerance),
            (
                "hamiltonian_hermiticity_tolerance",
                self.hamiltonian_hermiticity_tolerance,
            ),
        ):
            if (
                type(float_value) is not float
                or not math.isfinite(float_value)
                or float_value <= 0.0
            ):
                raise ValueError(f"{label} must be positive and finite")
        if type(self.execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a boolean")
        if type(self.length_unit) is not PhysicalUnit:
            raise TypeError("length_unit must be a PhysicalUnit")
        if type(self.energy_unit) is not PhysicalUnit:
            raise TypeError("energy_unit must be a PhysicalUnit")


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationRunResult:
    """Identify a successful provider occurrence and its durable evidence."""

    output_directory: Path
    input_manifest: Path
    artifact_manifest: Path
    provider_result: Path


class Wannier90LocalizationOutputError(RuntimeError):
    """Report retained provider-output failure after a native process attempt."""

    result_path: Path

    def __init__(self, message: str, result_path: Path) -> None:
        self.result_path = result_path
        super().__init__(f"{message}; provider result: {result_path}")


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationOutputVerifier:
    """Reverify retained localization outputs without invoking a calculator."""

    def verify_to_json_bytes(self, request: Wannier90LocalizationRunRequest) -> bytes:
        """Return immutable verification evidence for an existing occurrence."""
        if type(request) is not Wannier90LocalizationRunRequest:
            raise TypeError("request must be a Wannier90LocalizationRunRequest")
        output = request.output_directory.absolute()
        if output.is_symlink() or not output.is_dir():
            raise ValueError(
                "output_directory must be an existing nonsymlink directory"
            )
        manifest_payload = _verify_file(
            output / "localization-input-manifest.json",
            request.manifest_sha256,
            request.manifest_byte_count,
            "occurrence input manifest",
        )
        if manifest_payload != request.manifest.to_json_bytes():
            raise ValueError("occurrence input manifest disagrees with request")
        payloads: dict[str, bytes] = {}
        for artifact in request.manifest.artifacts:
            identity = artifact.identity
            payloads[identity.name] = _verify_file(
                output / identity.name,
                identity.sha256,
                identity.byte_count,
                identity.name,
            )
        parsed_inputs = _parse_and_correlate_inputs(request.manifest, payloads)
        observations = _inspect_outputs(request, output, parsed_inputs)
        _require_retained_bound(output, request.maximum_retained_bytes)
        value: JsonObject = {
            "comparison_reference": "canonical-construction-input-kpoints",
            "input_manifest_sha256": request.manifest_sha256,
            "observations": observations,
            "schema_version": 1,
            "status": "succeeded",
            "verification_kind": "no-calculator-retained-output-reverification",
        }
        return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


@dataclass(frozen=True, slots=True)
class Wannier90LocalizationRunner:
    """Verify all identities before one no-shell, no-retry native invocation."""

    def run(
        self, request: Wannier90LocalizationRunRequest
    ) -> Wannier90LocalizationRunResult:
        """Stage inputs, execute once, and authenticate selected provider outputs."""
        if type(request) is not Wannier90LocalizationRunRequest:
            raise TypeError("request must be a Wannier90LocalizationRunRequest")
        if not request.execution_authorized:
            raise PermissionError("Wannier90 localization execution is not authorized")
        output = request.output_directory.absolute()
        if output.exists():
            raise ValueError("output_directory already exists")
        _require_separate_directories(request.prepared_input_directory, output)
        manifest_payload = _verify_file(
            request.manifest_path,
            request.manifest_sha256,
            request.manifest_byte_count,
            "prepared-input manifest",
        )
        if manifest_payload != request.manifest.to_json_bytes():
            raise ValueError("prepared-input manifest content disagrees with request")
        expected_names = tuple(
            value.identity.name for value in request.manifest.artifacts
        )
        expected_manifest_path = (
            request.prepared_input_directory / "localization-input-manifest.json"
        )
        if request.manifest_path.absolute() != expected_manifest_path.absolute():
            raise ValueError("manifest_path must identify the prepared-input manifest")
        _require_closed_directory(
            request.prepared_input_directory,
            (*expected_names, request.manifest_path.name),
        )
        payloads: dict[str, bytes] = {}
        for artifact in request.manifest.artifacts:
            identity = artifact.identity
            payloads[identity.name] = _verify_file(
                request.prepared_input_directory / identity.name,
                identity.sha256,
                identity.byte_count,
                identity.name,
            )
        parsed_inputs = _parse_and_correlate_inputs(request.manifest, payloads)
        _verify_file(
            request.executable,
            request.executable_sha256,
            request.executable_byte_count,
            "executable",
            executable=True,
        )
        output.mkdir(parents=True)
        for name, payload in payloads.items():
            (output / name).write_bytes(payload)
        input_manifest = output / "localization-input-manifest.json"
        input_manifest.write_bytes(manifest_payload)
        execution_request = CalculatorExecutionRequest(
            command=(str(request.executable.absolute()), request.manifest.seedname),
            working_directory=output,
            stdout_filename="wannier90.out",
            stderr_filename="wannier90.err",
            required_input_filenames=expected_names,
            timeout_seconds=request.timeout_seconds,
            execution_authorized=True,
        )
        try:
            record = CalculatorExecutor().action(request=execution_request)
        except (CalculatorExecutionError, CalculatorOutputEmissionError) as error:
            result_path = _write_provider_failure(
                output,
                "process-failed",
                str(error),
                request.maximum_retained_bytes,
            )
            raise Wannier90LocalizationOutputError(
                "native localization process failed", result_path
            ) from error
        try:
            observations = _inspect_outputs(request, output, parsed_inputs)
            _require_retained_bound(output, request.maximum_retained_bytes)
        except Exception as error:
            result_path = _write_provider_failure(
                output,
                "output-ineligible",
                f"{type(error).__name__}: {error}",
                request.maximum_retained_bytes,
            )
            raise Wannier90LocalizationOutputError(
                "localization outputs are ineligible", result_path
            ) from error
        artifact_manifest = output / "artifact-manifest.json"
        _write_json(
            artifact_manifest,
            {
                "artifacts": _artifact_observations(output),
                "execution_status": record.status.value,
                "required_outputs": list(_required_outputs(request.manifest.seedname)),
                "schema_version": 1,
            },
        )
        provider_result = output / "provider-result.json"
        _write_json(
            provider_result,
            {
                "executable_version": request.executable_version,
                "observations": observations,
                "schema_version": 1,
                "status": "succeeded",
            },
        )
        return Wannier90LocalizationRunResult(
            output, input_manifest, artifact_manifest, provider_result
        )


def _parse_and_correlate_inputs(
    manifest: Wannier90LocalizationInputManifest,
    payloads: dict[str, bytes],
) -> tuple[tuple[tuple[float, float, float], ...], int, int, int]:
    seed = manifest.seedname
    construction_kpoints = _parse_construction_kpoints(
        payloads[f"{seed}.win"], manifest.kpoint_count
    )
    nnkp = Wannier90NnkpParser().execute(payloads[f"{seed}.nnkp"])
    eig = Wannier90EigenvalueParser().execute(
        payloads[f"{seed}.eig"], PhysicalUnit("eV")
    )
    amn = Wannier90ProjectionParser().execute(payloads[f"{seed}.amn"])
    mmn = Wannier90NeighborOverlapParser().execute(payloads[f"{seed}.mmn"])
    dimensions = (
        eig.kpoint_count,
        eig.band_count,
        amn.projection_count,
        mmn.neighbor_count,
    )
    expected = (
        manifest.kpoint_count,
        manifest.band_count,
        manifest.wannier_count,
        manifest.neighbor_count,
    )
    if dimensions != expected:
        raise ValueError("prepared input dimensions disagree with manifest")
    if (
        amn.kpoint_count != manifest.kpoint_count
        or amn.band_count != manifest.band_count
        or mmn.kpoint_count != manifest.kpoint_count
        or mmn.band_count != manifest.band_count
    ):
        raise ValueError("prepared interface dimensions disagree")
    neighbors = tuple(
        (
            value.source_kpoint_index,
            value.target_kpoint_index,
            *value.reciprocal_cell_shift,
        )
        for value in nnkp.neighbors
    )
    if mmn.normalized_records != neighbors:
        raise ValueError("MMN and NNKP neighbor inventories disagree")
    if not np.allclose(
        np.asarray(nnkp.kpoints, dtype=np.float64),
        np.asarray(construction_kpoints, dtype=np.float64),
        rtol=0.0,
        atol=_NNKP_FRACTIONAL_KPOINT_SERIALIZATION_TOLERANCE,
    ):
        raise ValueError("NNKP k-point order disagrees with construction input")
    return construction_kpoints, *expected[:3]


def _parse_construction_kpoints(
    payload: bytes, expected_count: int
) -> tuple[tuple[float, float, float], ...]:
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("construction input must be ASCII") from error
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.split("!", maxsplit=1)[0].split("#", maxsplit=1)[0].strip()
        lines.append(line)
    starts = [
        index for index, line in enumerate(lines) if line.lower() == "begin kpoints"
    ]
    ends = [index for index, line in enumerate(lines) if line.lower() == "end kpoints"]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise ValueError("construction input must contain one ordered kpoints block")
    values: list[tuple[float, float, float]] = []
    for line in lines[starts[0] + 1 : ends[0]]:
        if not line:
            continue
        fields = line.split()
        if len(fields) != 3:
            raise ValueError("construction k-point record must contain three values")
        try:
            vector = tuple(float(value) for value in fields)
        except ValueError as error:
            raise ValueError("construction k-point record is not numeric") from error
        if len(vector) != 3 or not all(math.isfinite(value) for value in vector):
            raise ValueError("construction k-point record must be finite")
        values.append((vector[0], vector[1], vector[2]))
    if len(values) != expected_count:
        raise ValueError("construction k-point count disagrees with manifest")
    return tuple(values)


def _inspect_outputs(
    request: Wannier90LocalizationRunRequest,
    output: Path,
    parsed_inputs: tuple[tuple[tuple[float, float, float], ...], int, int, int],
) -> JsonObject:
    seed = request.manifest.seedname
    payloads = {
        name: _read_regular_file(output / name, name)
        for name in _required_outputs(seed)
    }
    wout = payloads[f"{seed}.wout"]
    for phrase in (
        b"Disentanglement convergence criteria satisfied",
        b"Wannierisation convergence criteria satisfied",
        b"All done: wannier90 exiting",
    ):
        if phrase not in wout:
            raise ValueError(f"wout lacks native completion phrase: {phrase!r}")
    if b"Maximum number of" in wout:
        raise ValueError("wout reports a maximum-iteration warning")
    localization = Wannier90LocalizationParser().execute(wout, request.length_unit)
    gauge = Wannier90UnitaryMatrixParser().execute(payloads[f"{seed}_u.mat"])
    disentanglement = Wannier90DisentanglementMatrixParser().execute(
        payloads[f"{seed}_u_dis.mat"]
    )
    hamiltonian = Wannier90HamiltonianBlockParser().execute(
        payloads[f"{seed}_hr.dat"], request.energy_unit
    )
    input_kpoints, kpoint_count, band_count, wannier_count = parsed_inputs
    if localization.wannier_count != wannier_count:
        raise ValueError("wout Wannier count disagrees with input")
    if (gauge.kpoint_count, gauge.wannier_count) != (
        kpoint_count,
        wannier_count,
    ):
        raise ValueError("gauge-matrix dimensions disagree with input")
    if (
        disentanglement.kpoint_count,
        disentanglement.band_count,
        disentanglement.wannier_count,
    ) != (kpoint_count, band_count, wannier_count):
        raise ValueError("disentanglement-matrix dimensions disagree with input")
    if hamiltonian.wannier_count != wannier_count:
        raise ValueError("Hamiltonian rank disagrees with input")
    reference_kpoints = np.asarray(input_kpoints, dtype=np.float64)
    kpoint_residuals: dict[str, float] = {}
    for label, observed in (
        ("gauge", gauge.fractional_kpoints.magnitude),
        ("disentanglement", disentanglement.fractional_kpoints.magnitude),
    ):
        residual = float(np.max(np.abs(observed - reference_kpoints)))
        kpoint_residuals[label] = residual
        if residual > request.kpoint_tolerance:
            raise ValueError(
                f"{label} k-point order disagrees with canonical construction input"
            )
    identity = np.eye(wannier_count, dtype=np.complex128)
    gauge_residual = max(
        float(np.max(np.abs(matrix.magnitude.conj().T @ matrix.magnitude - identity)))
        for matrix in gauge.matrices
    )
    disentanglement_residual = max(
        float(np.max(np.abs(matrix.magnitude.conj().T @ matrix.magnitude - identity)))
        for matrix in disentanglement.matrices
    )
    if gauge_residual > request.isometry_tolerance:
        raise ValueError("gauge matrices exceed the unitarity tolerance")
    if disentanglement_residual > request.isometry_tolerance:
        raise ValueError("disentanglement matrices exceed the isometry tolerance")
    blocks = dict(zip(hamiltonian.representatives, hamiltonian.blocks, strict=True))
    hermiticity_residual = 0.0
    for representative, block in blocks.items():
        opposite = tuple(-value for value in representative)
        if opposite not in blocks:
            raise ValueError("Hamiltonian lacks a negative representative")
        hermiticity_residual = max(
            hermiticity_residual,
            float(
                np.max(np.abs(block.magnitude - blocks[opposite].magnitude.conj().T))
            ),
        )
    if hermiticity_residual > request.hamiltonian_hermiticity_tolerance:
        raise ValueError("Hamiltonian exceeds the Hermiticity tolerance")
    return {
        "band_count": band_count,
        "disentanglement_isometry_maximum_residual": disentanglement_residual,
        "gauge_kpoint_maximum_absolute_residual": kpoint_residuals["gauge"],
        "gauge_unitarity_maximum_residual": gauge_residual,
        "hamiltonian_hermiticity_maximum_residual": hermiticity_residual,
        "hamiltonian_representative_count": len(hamiltonian.representatives),
        "kpoint_count": kpoint_count,
        "last_reported_wannierisation_iteration": (
            localization.last_reported_wannierisation_iteration
        ),
        "disentanglement_kpoint_maximum_absolute_residual": kpoint_residuals[
            "disentanglement"
        ],
        "omega_total": float(localization.omega_total.magnitude),
        "wannier_count": wannier_count,
    }


def _required_outputs(seedname: str) -> tuple[str, ...]:
    return (
        f"{seedname}.wout",
        f"{seedname}_hr.dat",
        f"{seedname}_u.mat",
        f"{seedname}_u_dis.mat",
    )


def _write_provider_failure(
    output: Path, status: str, message: str, maximum_retained_bytes: int
) -> Path:
    artifact_manifest = output / "artifact-manifest.json"
    _write_json(
        artifact_manifest,
        {
            "artifacts": _artifact_observations(output),
            "execution_status": status,
            "required_outputs": [],
            "schema_version": 1,
        },
    )
    path = output / "provider-result.json"
    retained_bytes = sum(
        value.stat().st_size
        for value in output.rglob("*")
        if value.is_file() and not value.is_symlink()
    )
    _write_json(
        path,
        {
            "error": message,
            "maximum_retained_bytes": maximum_retained_bytes,
            "retained_bytes_before_provider_result": retained_bytes,
            "schema_version": 1,
            "status": status,
        },
    )
    return path


def _require_retained_bound(output: Path, maximum: int) -> None:
    total = 0
    for value in output.rglob("*"):
        if value.is_symlink():
            raise ValueError("localization occurrence contains a symbolic link")
        if value.is_file():
            total += value.stat().st_size
    if total > maximum:
        raise ValueError("localization occurrence exceeds maximum_retained_bytes")


def _artifact_observations(output: Path) -> JsonObject:
    observations: JsonObject = {}
    for path in sorted(value for value in output.iterdir() if value.is_file()):
        payload = _read_regular_file(path, "artifact")
        observations[path.name] = {
            "byte_count": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return observations


def _require_closed_directory(directory: Path, expected_names: tuple[str, ...]) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("input directory must be an existing nonsymlink directory")
    values = tuple(directory.iterdir())
    if any(value.is_symlink() or not value.is_file() for value in values):
        raise ValueError("input directory must contain regular files only")
    physical_identities = tuple(
        (value.stat().st_dev, value.stat().st_ino) for value in values
    )
    if len(set(physical_identities)) != len(physical_identities):
        raise ValueError("input paths must identify unique physical files")
    observed_names = tuple(sorted(value.name for value in values))
    if observed_names != tuple(sorted(expected_names)):
        raise ValueError("input directory inventory is not closed")


def _require_separate_directories(source: Path, output: Path) -> None:
    source_resolved = source.resolve()
    output_resolved = output.resolve()
    if (
        source_resolved == output_resolved
        or source_resolved.is_relative_to(output_resolved)
        or output_resolved.is_relative_to(source_resolved)
    ):
        raise ValueError("source and output directories must be separate")


def _verify_file(
    path: Path,
    expected_sha256: str,
    expected_size: int,
    label: str,
    *,
    executable: bool = False,
) -> bytes:
    payload = _read_regular_file(path, label)
    if len(payload) != expected_size:
        raise ValueError(f"{label} size mismatch")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise ValueError(f"{label} hash mismatch")
    if executable and not path.stat().st_mode & 0o111:
        raise ValueError(f"{label} is not executable")
    return payload


def _read_regular_file(path: Path, label: str) -> bytes:
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    return path.read_bytes()


def _validate_seedname(value: str) -> None:
    if (
        type(value) is not str
        or not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or not all(character.isalnum() or character in "_.-" for character in value)
    ):
        raise ValueError("seedname must be a safe native basename")


def _validate_sha256(value: str, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")


def _write_json(path: Path, value: JsonObject) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "Wannier90LocalizationInputArtifact",
    "Wannier90LocalizationInputManifest",
    "Wannier90LocalizationInputPreparer",
    "Wannier90LocalizationInputRole",
    "Wannier90LocalizationOutputError",
    "Wannier90LocalizationOutputVerifier",
    "Wannier90LocalizationPreparationResult",
    "Wannier90LocalizationRunner",
    "Wannier90LocalizationRunRequest",
    "Wannier90LocalizationRunResult",
]
