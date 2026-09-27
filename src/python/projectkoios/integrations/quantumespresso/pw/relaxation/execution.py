"""Prepare and optionally execute one verified QE relaxation calculation."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

from physkit.periodic.unit_cell import UnitCellJsonCodec

from projectkoios.simulations.execution import (
    CalculatorExecutionRequest,
    CalculatorExecutor,
)

from .calculation import QeRelaxationCalculationConfiguration
from .loading import QeRelaxationCalculationTomlLoader
from .rendering import QeRelaxationCalculationRenderer


@dataclass(frozen=True, slots=True)
class QeRelaxationStructureOverride:
    """Identify an explicit structure supplied instead of the declared default."""

    path: Path
    structure_id: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")
        if (
            type(self.structure_id) is not str
            or not self.structure_id
            or self.structure_id != self.structure_id.strip()
        ):
            raise ValueError("structure_id must be a nonempty stripped string")
        _validate_sha256(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationRunRequest:
    """Declare rendering and explicitly authorized execution resources."""

    configuration_path: Path
    output_directory: Path
    execute: bool = False
    structure_override: QeRelaxationStructureOverride | None = None
    executable: Path | None = None
    pseudopotential: Path | None = None
    timeout_seconds: float = 1800.0

    def __post_init__(self) -> None:
        if not isinstance(self.configuration_path, Path):
            raise TypeError("configuration_path must be a Path")
        if not isinstance(self.output_directory, Path):
            raise TypeError("output_directory must be a Path")
        if type(self.execute) is not bool:
            raise TypeError("execute must be a bool")
        if self.structure_override is not None and (
            type(self.structure_override) is not QeRelaxationStructureOverride
        ):
            raise TypeError(
                "structure_override must be a QeRelaxationStructureOverride or None"
            )
        if self.execute:
            if not isinstance(self.executable, Path) or not isinstance(
                self.pseudopotential,
                Path,
            ):
                raise ValueError(
                    "execution requires executable and pseudopotential paths"
                )
        elif self.executable is not None or self.pseudopotential is not None:
            raise ValueError("execution resources require execute=True")
        if (
            type(self.timeout_seconds) is not float
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0.0
        ):
            raise ValueError("timeout_seconds must be positive and finite")


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationRunResult:
    """Identify rendered manifests and whether calculator execution was requested."""

    output_directory: Path
    input_manifest: Path
    artifact_manifest: Path | None
    execution_requested: bool


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationRunner:
    """Verify identities, render input, and optionally invoke ``pw.x``."""

    def run(
        self,
        request: QeRelaxationCalculationRunRequest,
    ) -> QeRelaxationCalculationRunResult:
        """Run one calculation after all declared resources pass preflight."""
        if type(request) is not QeRelaxationCalculationRunRequest:
            raise TypeError("request must be a QeRelaxationCalculationRunRequest")
        configuration_path = request.configuration_path.absolute()
        configuration = QeRelaxationCalculationTomlLoader().load(configuration_path)
        output = request.output_directory.resolve()
        if output.exists():
            raise ValueError("output directory already exists")

        structure_path, structure_id, structure_sha256, structure_size = (
            self._resolve_structure(
                configuration=configuration,
                configuration_directory=configuration_path.parent,
                override=request.structure_override,
            )
        )
        _verify_file(
            structure_path,
            expected_sha256=structure_sha256,
            expected_size=structure_size,
            label="structure",
        )
        unit_cell = UnitCellJsonCodec().loads(
            structure_path.read_text(encoding="utf-8"),
            expected_structure_id=structure_id,
        )
        rendered = QeRelaxationCalculationRenderer().render(
            configuration,
            unit_cell,
        )

        if request.execute:
            assert request.executable is not None
            assert request.pseudopotential is not None
            _verify_file(
                request.executable,
                expected_sha256=configuration.calculator.sha256,
                expected_size=configuration.calculator.byte_size,
                label="calculator",
            )
            _verify_file(
                request.pseudopotential,
                expected_sha256=configuration.pseudopotential.sha256,
                expected_size=configuration.pseudopotential.byte_size,
                label="pseudopotential",
            )

        output.mkdir(parents=True)
        input_path = output / configuration.input_filename
        input_path.write_text(rendered, encoding="ascii")
        input_manifest = output / "input-manifest.json"
        _write_json(
            input_manifest,
            {
                "calculation_id": configuration.calculation_id,
                "calculator": {
                    "byte_size": configuration.calculator.byte_size,
                    "program": configuration.calculator_program,
                    "program_version": configuration.calculator_version,
                    "sha256": configuration.calculator.sha256,
                    "source_revision": configuration.calculator_source_revision,
                },
                "configuration_sha256": _sha256(configuration_path),
                "energy_convergence_tolerance_mev_per_atom": (
                    configuration.energy_convergence_tolerance_mev_per_atom
                ),
                "input": _file_observation(input_path),
                "phase": configuration.phase,
                "pseudopotential": {
                    "byte_size": configuration.pseudopotential.byte_size,
                    "filename": configuration.pseudopotential_filename,
                    "sha256": configuration.pseudopotential.sha256,
                    "symbol": configuration.pseudopotential_symbol,
                },
                "qualification": configuration.qualification_statements,
                "schema_version": 1,
                "structure": {
                    "byte_size": structure_path.stat().st_size,
                    "reference": (
                        configuration.structure.repository_path
                        if request.structure_override is None
                        else "operator-supplied"
                    ),
                    "sha256": structure_sha256,
                    "structure_id": structure_id,
                },
            },
        )
        if not request.execute:
            return QeRelaxationCalculationRunResult(
                output_directory=output,
                input_manifest=input_manifest,
                artifact_manifest=None,
                execution_requested=False,
            )

        assert request.executable is not None
        assert request.pseudopotential is not None
        shutil.copyfile(
            request.pseudopotential,
            output / configuration.pseudopotential_filename,
        )
        (output / "tmp").mkdir()
        record = CalculatorExecutor().execute(
            CalculatorExecutionRequest(
                command=(
                    str(request.executable.resolve()),
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
        xml_path = (
            output / "tmp" / f"{configuration.prefix}.save" / "data-file-schema.xml"
        )
        artifacts = {
            name: _file_observation(output / name)
            for name in (
                configuration.input_filename,
                configuration.pseudopotential_filename,
                "pw.out",
                "pw.err",
                "execution.json",
            )
        }
        if xml_path.is_file():
            artifacts["data-file-schema.xml"] = _file_observation(xml_path)
        artifact_manifest = output / "artifact-manifest.json"
        _write_json(
            artifact_manifest,
            {
                "artifacts": artifacts,
                "execution_status": record.status.value,
                "phase": configuration.phase,
                "schema_version": 1,
            },
        )
        return QeRelaxationCalculationRunResult(
            output_directory=output,
            input_manifest=input_manifest,
            artifact_manifest=artifact_manifest,
            execution_requested=True,
        )

    @staticmethod
    def _resolve_structure(
        *,
        configuration: QeRelaxationCalculationConfiguration,
        configuration_directory: Path,
        override: QeRelaxationStructureOverride | None,
    ) -> tuple[Path, str, str, int | None]:
        if override is None:
            return (
                (
                    configuration_directory / configuration.structure.repository_path
                ).absolute(),
                configuration.structure.structure_id,
                configuration.structure.sha256,
                configuration.structure.byte_size,
            )
        return (
            override.path.absolute(),
            override.structure_id,
            override.sha256,
            None,
        )


def _verify_file(
    path: Path,
    *,
    expected_sha256: str,
    expected_size: int | None,
    label: str,
) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} must be a regular nonsymlink file")
    if expected_size is not None and path.stat().st_size != expected_size:
        raise ValueError(f"{label} byte-size mismatch")
    if _sha256(path) != expected_sha256:
        raise ValueError(f"{label} SHA-256 mismatch")


def _file_observation(path: Path) -> dict[str, object]:
    return {"byte_size": path.stat().st_size, "sha256": _sha256(path)}


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_sha256(value: str, label: str) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be lowercase SHA-256")
