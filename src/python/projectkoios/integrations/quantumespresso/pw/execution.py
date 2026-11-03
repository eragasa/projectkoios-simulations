"""Resolve, stage, and execute one Quantum ESPRESSO simulation."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from projectkoios.simulations.calculator.input import CalculatorInputRecord
from projectkoios.simulations.dft.pseudopotential import PseudopotentialFile
from projectkoios.simulations.dft.pseudopotential.library import (
    PseudopotentialLibrary,
)
from projectkoios.simulations.execution import (
    CalculatorExecutableBinding,
    CalculatorExecutablePreparationFailure,
    CalculatorExecutablePreparer,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    CalculatorPreparedExecutable,
)


class QeSimulationExecutor:
    """Stage exact prepared inputs before executing ``pw.x``.

    Notes
    -----
    This action owns provider-specific staging and delegates process entry to the
    calculator-neutral executor. It requires separate explicit execution authority
    and does not select scientific settings, pseudopotentials, or retry policy.
    """

    __slots__ = ()

    def execute(
        self,
        prepared_input: CalculatorInputRecord,
        pseudopotentials: tuple[PseudopotentialFile, ...],
        pseudopotential_library: PseudopotentialLibrary,
        executable: CalculatorExecutableBinding,
        working_directory: Path,
        *,
        output_filename: str = "pw.out",
        timeout_seconds: float | None = None,
        execution_authorized: bool = False,
    ) -> CalculatorExecutionRecord:
        """Stage exact files and run one explicitly authorized ``pw.x`` attempt.

        Parameters
        ----------
        prepared_input
            Exact rendered QE input record.
        pseudopotentials
            Exact pseudopotential requirements declared by the simulation.
        pseudopotential_library
            Explicit deployment library used only to locate matching bytes.
        executable
            Exact executable identity bound to one absolute deployment path.
        working_directory
            Existing nonsymlink directory for the isolated attempt artifacts.
        output_filename
            Basename for retained standard-output bytes.
        timeout_seconds
            Positive finite process timeout, or ``None`` for no timeout.
        execution_authorized
            Explicit authority for this one calculator attempt.

        Returns
        -------
        CalculatorExecutionRecord
            Durable successful process record.

        Raises
        ------
        PermissionError
            If execution authority is absent.
        CalculatorExecutionError
            If exact preparation, staging, or process execution fails.

        Notes
        -----
        A verified private executable copy is staged before process entry. The copy
        closes source mutation during staging, but the current mutable working
        directory does not yet provide descriptor-bound process entry.
        """
        if type(prepared_input) is not CalculatorInputRecord:
            raise TypeError("prepared_input must be a CalculatorInputRecord")
        if prepared_input.integration_id.value != "quantum-espresso":
            raise ValueError("prepared input must target Quantum ESPRESSO")
        if prepared_input.representation != "quantum-espresso-pw-input":
            raise ValueError("prepared input representation must be QE pw.x input")
        if prepared_input.preparation_operation not in {
            "projectkoios.qe.pw.scf.prepare",
            "projectkoios.qe.pw.relaxation.prepare",
        }:
            raise ValueError(
                "prepared input operation must be a supported QE pw.x preparation"
            )
        if type(pseudopotentials) is not tuple or not pseudopotentials:
            raise ValueError("pseudopotentials must be a nonempty tuple")
        if any(not isinstance(item, PseudopotentialFile) for item in pseudopotentials):
            raise TypeError("pseudopotentials must contain PseudopotentialFile values")
        if type(pseudopotential_library) is not PseudopotentialLibrary:
            raise TypeError("pseudopotential_library must be a PseudopotentialLibrary")
        if type(executable) is not CalculatorExecutableBinding:
            raise TypeError("executable must be a CalculatorExecutableBinding")
        if not isinstance(working_directory, Path):
            raise TypeError("working_directory must be a Path")
        if type(execution_authorized) is not bool:
            raise TypeError("execution_authorized must be a bool")
        # Authority is checked before inspecting executable or library deployment
        # state and before creating any attempt artifact.
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

        staged_executable = working_directory / ".projectkoios-pw.x"
        required_filenames = (
            *(artifact.filename for artifact in prepared_input.artifacts),
            *(item.filename for item in pseudopotentials),
        )
        if staged_executable.name in required_filenames:
            raise ValueError("private executable filename conflicts with an input")
        request = CalculatorExecutionRequest(
            command=(str(staged_executable), "-in", primary_input.filename),
            working_directory=working_directory,
            stdout_filename=output_filename,
            stderr_filename="pw.err",
            required_input_filenames=required_filenames,
            timeout_seconds=timeout_seconds,
            execution_authorized=True,
        )
        executor = CalculatorExecutor()
        try:
            executable_preparation = CalculatorExecutablePreparer(executable).prepare()
            if type(executable_preparation) is CalculatorExecutablePreparationFailure:
                raise ValueError(
                    "executable preparation failed: "
                    f"{executable_preparation.code.value}: "
                    f"{executable_preparation.observed_condition}"
                )
            assert type(executable_preparation) is CalculatorPreparedExecutable
            self._prepare_outdir(working_directory, "./tmp/")
            # Scientific intent has already selected complete immutable file
            # identities. The injected deployment library locates those exact bytes;
            # it never chooses by element or filename and grants no authority.
            resolved = tuple(
                (item, pseudopotential_library.resolve(item))
                for item in pseudopotentials
            )
            self._copy_executable_atomic(
                executable_preparation,
                staged_executable,
            )
            for artifact in prepared_input.artifacts:
                self._write_atomic(
                    working_directory / artifact.filename,
                    artifact.content,
                )
            for item, source in resolved:
                self._copy_atomic(source, working_directory / item.filename)
        except (OSError, LookupError, ValueError) as error:
            executor.record_preflight_failure(request=request, error=error)
        return executor.action(request=request)

    def _prepare_outdir(self, working_directory: Path, outdir: str | None) -> None:
        if outdir is None or outdir in {".", "./"}:
            return
        relative = Path(outdir)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(
                "ControlBlock.outdir must remain within the working directory"
            )
        destination = working_directory / relative
        if destination.is_symlink():
            raise ValueError("ControlBlock.outdir must not be a symbolic link")
        destination.mkdir(parents=True, exist_ok=True)

    def _write_atomic(self, destination: Path, payload: bytes) -> None:
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

    def _copy_atomic(self, source: Path, destination: Path) -> None:
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

    def _copy_executable_atomic(
        self,
        prepared: CalculatorPreparedExecutable,
        destination: Path,
    ) -> None:
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as temporary:
                temporary_name = temporary.name
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(prepared.binding.path, flags)
                # Open the admitted final path without following a replacement
                # symlink; the staged digest below still detects byte mutation.
                with os.fdopen(descriptor, "rb") as stream:
                    shutil.copyfileobj(stream, temporary)
                temporary.flush()
                os.fsync(temporary.fileno())
            # The private copy needs only owner read and execute permission. Its byte
            # identity is independent of mode, and denying writes limits accidental
            # mutation before the subsequent identity recheck and process entry.
            os.chmod(temporary_name, 0o500)
            # Hard-link publication is no-replace: an existing destination fails
            # rather than being overwritten by an execution attempt.
            os.link(temporary_name, destination)
            staged = CalculatorExecutableBinding(
                identity=prepared.binding.identity,
                path=destination,
            )
            staged_preparation = CalculatorExecutablePreparer(staged).prepare()
            if type(staged_preparation) is CalculatorExecutablePreparationFailure:
                raise ValueError(
                    "staged executable verification failed: "
                    f"{staged_preparation.code.value}: "
                    f"{staged_preparation.observed_condition}"
                )
        finally:
            if temporary_name is not None and os.path.exists(temporary_name):
                os.unlink(temporary_name)
