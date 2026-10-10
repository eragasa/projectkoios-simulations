"""Render and explicitly execute one configuration-owned QE NSCF run."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.nscf.calculation import (
    QeNscfFileResource,
)
from projectkoios.integrations.quantumespresso.pw.nscf.loading import (
    QeNscfCalculationTomlLoader,
)
from projectkoios.integrations.quantumespresso.pw.nscf.projection import (
    QeNscfInputProjector,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateCalculation,
    QeSavedStateManifestBuilder,
    QeSavedStateManifestJsonCodec,
    QeSavedStateManifestVerifier,
    QeSavedStatePseudopotential,
)
from projectkoios.physkit.periodic.unit_cell import (
    ConventionalUnitCell,
    PrimitiveUnitCell,
    UnitCell,
    UnitCellJsonCodec,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRequest,
    CalculatorExecutor,
)
from projectkoios.simulations.structure import (
    StructureRecord,
    StructureRepresentation,
    StructureResolution,
    TransferredStructureProvenance,
)

_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class QeNscfCalculationRunRequest:
    """Declare one configuration and separately authorize its calculator run."""

    configuration_path: Path
    execute: bool = False
    timeout_seconds: float = 3600.0

    def __post_init__(self) -> None:
        if not isinstance(self.configuration_path, Path):
            raise TypeError("configuration_path must be a Path")
        if type(self.execute) is not bool:
            raise TypeError("execute must be a boolean")
        if (
            type(self.timeout_seconds) is not float
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0.0
        ):
            raise ValueError("timeout_seconds must be positive and finite")


@dataclass(frozen=True, slots=True)
class QeNscfSavedStateHandoff:
    """Bind a verified NSCF saved state for a downstream provider adapter."""

    manifest_path: Path
    source_root: Path
    manifest_sha256: str
    manifest_byte_size: int
    prefix: str

    def __post_init__(self) -> None:
        for label, path in (
            ("manifest_path", self.manifest_path),
            ("source_root", self.source_root),
        ):
            if not isinstance(path, Path) or not path.is_absolute():
                raise TypeError(f"{label} must be an absolute Path")
        if (
            type(self.manifest_sha256) is not str
            or _SHA256.fullmatch(self.manifest_sha256) is None
        ):
            raise ValueError("manifest_sha256 must be a lowercase SHA-256")
        if type(self.manifest_byte_size) is not int or self.manifest_byte_size <= 0:
            raise ValueError("manifest_byte_size must be positive")
        if type(self.prefix) is not str or not self.prefix:
            raise ValueError("prefix must be nonempty")


@dataclass(frozen=True, slots=True)
class QeNscfCalculationRunResult:
    """Identify rendered and optional executed NSCF evidence."""

    output_directory: Path
    input_manifest: Path
    artifact_manifest: Path | None
    saved_state_manifest: Path | None
    saved_state_handoff: QeNscfSavedStateHandoff | None
    execution_requested: bool


@dataclass(frozen=True, slots=True)
class QeNscfCalculationRunner:
    """Resolve every path from TOML and verify identities before side effects."""

    def run(
        self,
        request: QeNscfCalculationRunRequest,
    ) -> QeNscfCalculationRunResult:
        """Render or execute one path-complete NSCF configuration."""
        if type(request) is not QeNscfCalculationRunRequest:
            raise TypeError("request must be a QeNscfCalculationRunRequest")
        configuration_path = request.configuration_path.absolute()
        configuration = QeNscfCalculationTomlLoader().load(configuration_path)
        directory = configuration_path.parent
        output = configuration.output_directory.resolve(directory)
        if output.exists():
            raise ValueError("configured output directory already exists")

        source_input = configuration.source_input.resolve(directory)
        structure_path = configuration.structure.resolve(directory)
        _verify_resource(source_input, configuration.source_input, "source input")
        _verify_resource(structure_path, configuration.structure, "structure")
        unit_cell = UnitCellJsonCodec().loads(
            structure_path.read_text(encoding="utf-8"),
            expected_structure_id=configuration.structure_id,
        )
        representation = {
            PrimitiveUnitCell: StructureRepresentation.primitive,
            ConventionalUnitCell: StructureRepresentation.conventional,
            UnitCell: StructureRepresentation.unit_cell,
        }.get(type(unit_cell))
        if representation is None:
            raise TypeError("decoded NSCF structure has an unsupported unit-cell type")
        structure_record = StructureRecord(
            structure_id=configuration.structure_id,
            representation=representation,
            schema_version=1,
            sha256=configuration.structure.sha256,
            byte_size=configuration.structure.byte_size,
            provenance=TransferredStructureProvenance(
                source="QeNscfCalculationConfiguration",
                revision=_sha256(configuration_path),
                record_path=f"structure/{structure_path.name}",
                source_sha256=configuration.structure.sha256,
                result_sha256=configuration.structure.sha256,
            ),
        )
        projection = QeNscfInputProjector(
            configuration.projection_configuration()
        ).project(
            StructureResolution(
                record=structure_record,
                path=structure_path,
                unit_cell=unit_cell,
            )
        )

        executable: Path | None = None
        pseudopotential: Path | None = None
        parent_manifest_payload: bytes | None = None
        parent_manifest = None
        parent_paths: tuple[Path, ...] = ()
        parent_root: Path | None = None
        if request.execute:
            executable = configuration.calculator.resolve(directory)
            pseudopotential = configuration.pseudopotential.resolve(directory)
            parent_output = configuration.parent_output_directory.resolve(directory)
            parent_root = configuration.parent_saved_state_root.resolve(directory)
            parent_manifest_path = configuration.parent_manifest.resolve(directory)
            _verify_directory(parent_output, "parent output directory")
            _verify_directory(parent_root, "parent saved-state root")
            resolved_output = output.resolve()
            resolved_parent_output = parent_output.resolve()
            if resolved_output.is_relative_to(
                resolved_parent_output
            ) or resolved_parent_output.is_relative_to(resolved_output):
                raise ValueError("NSCF output and parent output must not overlap")
            if configuration.reference_output_directory is not None:
                _verify_directory(
                    configuration.reference_output_directory.resolve(directory),
                    "reference NSCF output directory",
                )
            if not parent_root.resolve().is_relative_to(parent_output.resolve()):
                raise ValueError("parent saved-state root must be inside parent output")
            if not parent_manifest_path.resolve().is_relative_to(
                parent_output.resolve()
            ):
                raise ValueError("parent manifest must be inside parent output")
            _verify_resource(executable, configuration.calculator, "calculator")
            if not executable.stat().st_mode & 0o111:
                raise ValueError("calculator must be executable")
            _verify_resource(
                pseudopotential,
                configuration.pseudopotential,
                "pseudopotential",
            )
            _verify_resource(
                parent_manifest_path,
                configuration.parent_manifest,
                "parent manifest",
            )
            parent_manifest_payload = parent_manifest_path.read_bytes()
            parent_manifest = QeSavedStateManifestJsonCodec().loads(
                parent_manifest_payload
            )
            if parent_manifest.calculation is not QeSavedStateCalculation.scf:
                raise ValueError(
                    "NSCF parent manifest must identify an SCF calculation"
                )
            if parent_manifest.prefix != configuration.prefix:
                raise ValueError("parent manifest prefix disagrees with NSCF input")
            if parent_manifest.structure_sha256 != configuration.structure.sha256:
                raise ValueError("parent structure identity disagrees with NSCF input")
            declared_pseudo = parent_manifest.pseudopotentials
            if len(declared_pseudo) != 1 or (
                declared_pseudo[0].filename != configuration.pseudopotential_filename
                or declared_pseudo[0].sha256 != configuration.pseudopotential.sha256
                or declared_pseudo[0].byte_size
                != configuration.pseudopotential.byte_size
            ):
                raise ValueError(
                    "parent pseudopotential identity disagrees with NSCF input"
                )
            parent_paths = QeSavedStateManifestVerifier().verify(
                parent_manifest,
                parent_root,
            )

        output.mkdir(parents=True)
        input_path = output / configuration.input_filename
        input_path.write_text(projection.rendered_input.text, encoding="ascii")
        input_manifest = output / "input-manifest.json"
        _write_json(
            input_manifest,
            {
                "calculation_id": configuration.calculation_id,
                "calculator": {
                    "byte_size": configuration.calculator.byte_size,
                    "path": configuration.calculator.path,
                    "program": configuration.calculator_program,
                    "program_version": configuration.calculator_version,
                    "sha256": configuration.calculator.sha256,
                },
                "configuration_sha256": _sha256(configuration_path),
                "kpoint_count": projection.kpoint_count,
                "band_count": projection.band_count,
                "parent_manifest_sha256": configuration.parent_manifest.sha256,
                "pseudopotential": {
                    "byte_size": configuration.pseudopotential.byte_size,
                    "filename": configuration.pseudopotential_filename,
                    "path": configuration.pseudopotential.path,
                    "sha256": configuration.pseudopotential.sha256,
                },
                "qualification": configuration.qualification_statements,
                "rendered_input": _observation(input_path),
                "schema_version": 1,
                "source_input": {
                    "path": configuration.source_input.path,
                    "sha256": configuration.source_input.sha256,
                    "byte_size": configuration.source_input.byte_size,
                },
                "structure": {
                    "path": configuration.structure.path,
                    "sha256": configuration.structure.sha256,
                    "byte_size": configuration.structure.byte_size,
                    "structure_id": configuration.structure_id,
                },
            },
        )
        if not request.execute:
            return QeNscfCalculationRunResult(
                output_directory=output,
                input_manifest=input_manifest,
                artifact_manifest=None,
                saved_state_manifest=None,
                saved_state_handoff=None,
                execution_requested=False,
            )

        assert executable is not None
        assert pseudopotential is not None
        assert parent_manifest_payload is not None
        assert parent_manifest is not None
        assert parent_root is not None
        shutil.copyfile(
            pseudopotential,
            output / configuration.pseudopotential_filename,
        )
        (output / "parent-saved-state-manifest.json").write_bytes(
            parent_manifest_payload
        )
        outdir = _safe_outdir(configuration.outdir)
        staged_root = output / outdir
        staged_root.mkdir(parents=True, exist_ok=False)
        for source in parent_paths:
            relative = source.relative_to(parent_root)
            destination = staged_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        QeSavedStateManifestVerifier().verify(parent_manifest, staged_root)

        record = CalculatorExecutor().execute(
            CalculatorExecutionRequest(
                command=(
                    str(executable),
                    "-in",
                    configuration.input_filename,
                ),
                working_directory=output,
                stdout_filename="pw.out",
                stderr_filename="pw.err",
                required_input_filenames=(
                    configuration.input_filename,
                    configuration.pseudopotential_filename,
                ),
                timeout_seconds=request.timeout_seconds,
                execution_authorized=True,
            )
        )
        child_manifest = QeSavedStateManifestBuilder().build(
            source_root=staged_root,
            prefix=configuration.prefix,
            calculation=QeSavedStateCalculation.nscf,
            producer_version=configuration.calculator_version,
            executable_sha256=configuration.calculator.sha256,
            input_sha256=_sha256(input_path),
            structure_id=configuration.structure_id,
            structure_sha256=configuration.structure.sha256,
            pseudopotentials=(
                QeSavedStatePseudopotential(
                    symbol=configuration.pseudopotential_symbol,
                    filename=configuration.pseudopotential_filename,
                    sha256=configuration.pseudopotential.sha256,
                    byte_size=configuration.pseudopotential.byte_size,
                ),
            ),
        )
        child_manifest_payload = QeSavedStateManifestJsonCodec().dumps(child_manifest)
        child_manifest_path = output / "nscf-saved-state-manifest.json"
        child_manifest_path.write_bytes(child_manifest_payload)
        QeSavedStateManifestVerifier().verify(child_manifest, staged_root)
        saved_state_handoff = QeNscfSavedStateHandoff(
            manifest_path=child_manifest_path.absolute(),
            source_root=staged_root.absolute(),
            manifest_sha256=hashlib.sha256(child_manifest_payload).hexdigest(),
            manifest_byte_size=len(child_manifest_payload),
            prefix=configuration.prefix,
        )
        artifact_manifest = output / "artifact-manifest.json"
        _write_json(
            artifact_manifest,
            {
                "artifacts": {
                    name: _observation(output / name)
                    for name in (
                        configuration.input_filename,
                        configuration.pseudopotential_filename,
                        "parent-saved-state-manifest.json",
                        "pw.out",
                        "pw.err",
                        "execution.json",
                        "nscf-saved-state-manifest.json",
                    )
                },
                "execution_status": record.status.value,
                "schema_version": 1,
            },
        )
        return QeNscfCalculationRunResult(
            output_directory=output,
            input_manifest=input_manifest,
            artifact_manifest=artifact_manifest,
            saved_state_manifest=child_manifest_path,
            saved_state_handoff=saved_state_handoff,
            execution_requested=True,
        )


def _safe_outdir(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or path in {Path("."), Path("")} or ".." in path.parts:
        raise ValueError("outdir must be a safe non-current relative path")
    return path


def _verify_directory(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"{label} must be a regular directory")


def _verify_resource(
    path: Path,
    resource: QeNscfFileResource,
    label: str,
) -> None:
    if type(resource) is not QeNscfFileResource:
        raise TypeError("resource must be a QeNscfFileResource")
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    if path.stat().st_size != resource.byte_size:
        raise ValueError(f"{label} byte-size mismatch")
    if _sha256(path) != resource.sha256:
        raise ValueError(f"{label} SHA-256 mismatch")


def _observation(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular file")
    return {"byte_size": path.stat().st_size, "sha256": _sha256(path)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
