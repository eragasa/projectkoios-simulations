"""Resolve, stage, and execute one Quantum ESPRESSO simulation."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PwInputWriter,
)
from projectkoios.integrations.quantumespresso.pw.simulation import (
    QuantumEspressoSimulation,
)
from projectkoios.simulations.dft.pseudopotential_repository import (
    PseudopotentialRepository,
)
from projectkoios.simulations.execution import (
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorExecutor,
)


@dataclass(frozen=True, slots=True)
class QeSimulationExecutor:
    """Resolve exact pseudopotentials before staging and executing ``pw.x``."""

    def execute(
        self,
        simulation: QuantumEspressoSimulation,
        repository: PseudopotentialRepository,
        executable: Path,
        working_directory: Path,
        *,
        timeout_seconds: float | None = None,
        execution_authorized: bool = False,
    ) -> CalculatorExecutionRecord:
        """Run ``pw.x`` or record and raise a pseudopotential preflight failure."""
        if type(simulation) is not QuantumEspressoSimulation:
            raise TypeError("simulation must be a QuantumEspressoSimulation")
        if type(repository) is not PseudopotentialRepository:
            raise TypeError("repository must be a PseudopotentialRepository")
        if not isinstance(executable, Path):
            raise TypeError("executable must be a Path")
        if not isinstance(working_directory, Path):
            raise TypeError("working_directory must be a Path")
        if type(execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a bool")
        if not execution_authorized:
            raise PermissionError("Quantum ESPRESSO execution is not authorized")
        pseudo_dir = simulation.input_file.control_block.pseudo_dir
        if pseudo_dir not in {".", "./"}:
            raise ValueError(
                "QeSimulationExecutor requires ControlBlock.pseudo_dir to be '.'"
            )

        request = CalculatorExecutionRequest(
            command=(str(executable), "-in", simulation.input_filename),
            working_directory=working_directory,
            stdout_filename=simulation.output_filename,
            stderr_filename="pw.err",
            required_input_filenames=(
                simulation.input_filename,
                *(item.filename for item in simulation.pseudopotentials),
            ),
            timeout_seconds=timeout_seconds,
            execution_authorized=True,
        )
        executor = CalculatorExecutor()
        try:
            _prepare_outdir(
                working_directory,
                simulation.input_file.control_block.outdir,
            )
            resolved = tuple(
                (item, repository.resolve(item)) for item in simulation.pseudopotentials
            )
            _write_atomic(
                working_directory / simulation.input_filename,
                PwInputWriter().render(simulation.input_file).encode("ascii"),
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
