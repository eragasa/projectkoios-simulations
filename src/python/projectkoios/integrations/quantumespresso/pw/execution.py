"""Resolve, stage, and execute one Quantum ESPRESSO simulation."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from projectkoios.simulations.calculator_input import CalculatorInputRecord
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorExecutor,
)


@dataclass(frozen=True, slots=True)
class QeSimulationExecutor:
    """Stage exact prepared inputs before executing ``pw.x``."""

    def execute(
        self,
        prepared_input: CalculatorInputRecord,
        pseudopotentials: tuple[PseudopotentialFile, ...],
        pseudopotential_library: PseudopotentialLibrary,
        executable: Path,
        working_directory: Path,
        *,
        output_filename: str = "pw.out",
        timeout_seconds: float | None = None,
        execution_authorized: bool = False,
    ) -> CalculatorExecutionRecord:
        """Run ``pw.x`` or record and raise an exact-input preflight failure."""
        if type(prepared_input) is not CalculatorInputRecord:
            raise TypeError("prepared_input must be a CalculatorInputRecord")
        if prepared_input.integration_id.value != "quantum-espresso":
            raise ValueError("prepared input must target Quantum ESPRESSO")
        if prepared_input.representation != "quantum-espresso-pw-input":
            raise ValueError("prepared input representation must be QE pw.x input")
        if prepared_input.preparation_operation != "projectkoios.qe.pw.scf.prepare":
            raise ValueError("prepared input operation must be QE SCF preparation")
        if type(pseudopotentials) is not tuple or not pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        if any(not isinstance(item, PseudopotentialFile) for item in pseudopotentials):
            raise TypeError("pseudopotentials must contain PseudopotentialFile values")
        if type(pseudopotential_library) is not PseudopotentialLibrary:
            raise TypeError("pseudopotential_library must be a PseudopotentialLibrary")
        if not isinstance(executable, Path):
            raise TypeError("executable must be a Path")
        if not isinstance(working_directory, Path):
            raise TypeError("working_directory must be a Path")
        if type(execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a bool")
        if not execution_authorized:
            raise PermissionError("Quantum ESPRESSO execution is not authorized")
        if type(output_filename) is not str:
            raise TypeError("output_filename must be a string")
        primary_inputs = tuple(
            artifact
            for artifact in prepared_input.artifacts
            if artifact.role == "primary-input"
        )
        if len(primary_inputs) != 1:
            raise ValueError("QE prepared input must have one primary-input artifact")
        primary_input = primary_inputs[0]
        declared_requirements = tuple(
            sorted(
                (
                    requirement.filename,
                    requirement.sha256,
                    requirement.byte_size,
                    requirement.element_symbol,
                )
                for requirement in prepared_input.external_requirements
            )
        )
        bound_requirements = tuple(
            sorted(
                (item.filename, item.sha256, item.byte_size, item.symbol)
                for item in pseudopotentials
            )
        )
        if declared_requirements != bound_requirements:
            raise ValueError(
                "prepared external requirements must match bound pseudopotentials"
            )

        request = CalculatorExecutionRequest(
            command=(str(executable), "-in", primary_input.filename),
            working_directory=working_directory,
            stdout_filename=output_filename,
            stderr_filename="pw.err",
            required_input_filenames=(
                *(artifact.filename for artifact in prepared_input.artifacts),
                *(item.filename for item in pseudopotentials),
            ),
            timeout_seconds=timeout_seconds,
            execution_authorized=True,
        )
        executor = CalculatorExecutor()
        try:
            _prepare_outdir(working_directory, "./tmp/")
            # Scientific intent has already selected complete immutable file
            # identities. The injected deployment library locates those exact
            # bytes during execution preflight; it never chooses by element or
            # filename and it grants no calculator authority.
            resolved = tuple(
                (item, pseudopotential_library.resolve(item))
                for item in pseudopotentials
            )
            for artifact in prepared_input.artifacts:
                _write_atomic(
                    working_directory / artifact.filename,
                    artifact.content,
                )
            for item, source in resolved:
                _copy_atomic(source, working_directory / item.filename)
        except (OSError, LookupError, ValueError) as error:
            executor.record_preflight_failure(request, error)
        return executor.execute(request)


def _prepare_outdir(working_directory: Path, outdir: str | None) -> None:
    if outdir is None or outdir in {".", "./"}:
        return
    relative = Path(outdir)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("ControlBlock.outdir must remain within the working directory")
    destination = working_directory / relative
    if destination.is_symlink():
        raise ValueError("ControlBlock.outdir must not be a symbolic link")
    destination.mkdir(parents=True, exist_ok=True)


def _write_atomic(destination: Path, payload: bytes) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _copy_atomic(source: Path, destination: Path) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, destination)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)
