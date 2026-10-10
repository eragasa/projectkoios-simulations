"""File, parser, and result composition for captured ``pw.x`` stdout."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import final

from projectkoios.integrations.quantumespresso.outputs.base import (
    QeOutputFile,
    QeOutputFileParser,
    QeOutputFileResult,
    QuantumEspressoOutputFileError,
)

_MAX_OUTPUT_BYTES = 100_000_000
_FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"
_VERSION = re.compile(r"Program\s+PWSCF\s+v\.([^\s]+)", re.IGNORECASE)
_ATOM_COUNT = re.compile(r"number of atoms/cell\s*=\s*(\d+)", re.IGNORECASE)
_K_POINT_COUNT = re.compile(r"number of k points\s*=\s*(\d+)", re.IGNORECASE)
_CUTOFF = re.compile(rf"kinetic-energy cutoff\s*=\s*({_FLOAT})\s*Ry", re.IGNORECASE)
_TOTAL_ENERGY = re.compile(rf"!\s+total energy\s*=\s*({_FLOAT})\s*Ry", re.IGNORECASE)
_TOTAL_MAGNETIZATION = re.compile(
    rf"\btotal magnetization\s*=\s*({_FLOAT})\s+Bohr mag/cell",
    re.IGNORECASE,
)
_ABSOLUTE_MAGNETIZATION = re.compile(
    rf"\babsolute magnetization\s*=\s*({_FLOAT})\s+Bohr mag/cell",
    re.IGNORECASE,
)
_PRESSURE = re.compile(rf"\bP=\s*({_FLOAT})", re.IGNORECASE)
_TOTAL_FORCE = re.compile(
    rf"Total force\s*=\s*({_FLOAT})\s+Total SCF correction\s*=\s*({_FLOAT})",
    re.IGNORECASE,
)
_ATOM_FORCE = re.compile(
    rf"atom\s+\d+\s+type\s+\d+\s+force\s*=\s*"
    rf"({_FLOAT})\s+({_FLOAT})\s+({_FLOAT})",
    re.IGNORECASE,
)
_FORCE_BLOCK = re.compile(r"Forces acting on atoms", re.IGNORECASE)
_STRESS_HEADER = re.compile(r"total\s+stress\s+\(Ry/bohr\*\*3\)", re.IGNORECASE)
_BFGS_CONVERGED = re.compile(
    r"bfgs converged in\s+(\d+)\s+scf cycles and\s+(\d+)\s+bfgs steps",
    re.IGNORECASE,
)
_BFGS_NEW_OBJECTIVE = re.compile(
    rf"\b(energy|enthalpy)\s+new\s*=\s*({_FLOAT})\s*Ry",
    re.IGNORECASE,
)
_FINAL_OBJECTIVE = re.compile(
    rf"Final\s+(energy|enthalpy)\s*=\s*({_FLOAT})\s*Ry",
    re.IGNORECASE,
)
_BFGS_CRITERIA = re.compile(
    rf"criteria:\s*energy\s*<\s*({_FLOAT}),\s*force\s*<\s*({_FLOAT})"
    rf"(?:,\s*cell\s*<\s*({_FLOAT}))?",
    re.IGNORECASE,
)
_LEFT_HANDED_AXES = re.compile(r"axis vectors are left-handed", re.IGNORECASE)
_ITERATION = re.compile(r"^\s*iteration\s+#", re.IGNORECASE)
_SCF_NOT_CONVERGED = re.compile(r"convergence NOT achieved", re.IGNORECASE)
_END_BFGS = re.compile(r"End of BFGS Geometry Optimization", re.IGNORECASE)

type QeStressTensor = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


@final
@dataclass(frozen=True, slots=True)
class QePwStdoutFile(QeOutputFile):
    """Declare one captured ``pw.x`` standard-output file."""

    @classmethod
    def from_prefix(
        cls,
        *,
        prefix: str,
        directory: str = "",
    ) -> QePwStdoutFile:
        """Construct the conventional captured ``prefix.out`` declaration."""
        cls._validate_prefix(prefix)
        return cls(relative_path=cls._join(directory, f"{prefix}.out"))


@final
@dataclass(frozen=True, slots=True)
class QePwStdoutFileResult(QeOutputFileResult[QePwStdoutFile]):
    """Represent selected raw ``pw.x`` stdout observations in native units."""

    program_version: str | None
    job_completed: bool
    scf_converged: bool
    total_energy_ry: float | None
    total_magnetization_bohr_magneton_per_cell: float | None
    absolute_magnetization_bohr_magneton_per_cell: float | None
    wavefunction_cutoff_ry: float | None
    pressure_kbar: float | None
    total_force_ry_per_bohr: float | None
    total_scf_correction_ry_per_bohr: float | None
    maximum_atomic_force_ry_per_bohr: float | None
    maximum_force_component_ry_per_bohr: float | None
    stress_ry_per_bohr_cubed: QeStressTensor | None
    geometry_optimization_converged: bool
    bfgs_scf_cycle_count: int | None
    bfgs_step_count: int | None
    bfgs_energy_threshold_ry: float | None
    bfgs_force_threshold_ry_per_bohr: float | None
    bfgs_cell_threshold_kbar: float | None
    optimizer_total_force_ry_per_bohr: float | None
    optimizer_maximum_atomic_force_ry_per_bohr: float | None
    optimizer_maximum_force_component_ry_per_bohr: float | None
    optimizer_pressure_kbar: float | None
    optimizer_stress_ry_per_bohr_cubed: QeStressTensor | None
    bfgs_objective_kind: str | None
    previous_bfgs_objective_ry: float | None
    final_bfgs_objective_ry: float | None
    bfgs_energy_change_ry: float | None
    final_enthalpy_ry: float | None
    final_energy_ry: float | None
    scf_nonconvergence_count: int
    left_handed_axis_warning: bool
    atom_count: int | None
    k_point_count: int | None
    scf_iteration_count: int

    def __post_init__(self) -> None:
        super(QePwStdoutFileResult, self).__post_init__()
        if type(self.output_file) is not QePwStdoutFile:
            raise TypeError("output_file must be a QePwStdoutFile")
        if self.program_version is not None and not self.program_version:
            raise ValueError("program version must be nonempty when represented")
        for label, value in (
            ("total energy", self.total_energy_ry),
            (
                "total magnetization",
                self.total_magnetization_bohr_magneton_per_cell,
            ),
            (
                "absolute magnetization",
                self.absolute_magnetization_bohr_magneton_per_cell,
            ),
            ("wavefunction cutoff", self.wavefunction_cutoff_ry),
            ("pressure", self.pressure_kbar),
            ("total force", self.total_force_ry_per_bohr),
            ("SCF force correction", self.total_scf_correction_ry_per_bohr),
            ("maximum atomic force", self.maximum_atomic_force_ry_per_bohr),
            ("maximum force component", self.maximum_force_component_ry_per_bohr),
            ("optimizer total force", self.optimizer_total_force_ry_per_bohr),
            (
                "optimizer maximum atomic force",
                self.optimizer_maximum_atomic_force_ry_per_bohr,
            ),
            (
                "optimizer maximum force component",
                self.optimizer_maximum_force_component_ry_per_bohr,
            ),
            ("optimizer pressure", self.optimizer_pressure_kbar),
            ("previous BFGS objective", self.previous_bfgs_objective_ry),
            ("final BFGS objective", self.final_bfgs_objective_ry),
            ("BFGS energy change", self.bfgs_energy_change_ry),
            ("final enthalpy", self.final_enthalpy_ry),
            ("final energy", self.final_energy_ry),
            ("BFGS energy threshold", self.bfgs_energy_threshold_ry),
            ("BFGS force threshold", self.bfgs_force_threshold_ry_per_bohr),
            ("BFGS cell threshold", self.bfgs_cell_threshold_kbar),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{label} must be finite when represented")
        for label, value in (
            ("total force", self.total_force_ry_per_bohr),
            ("SCF force correction", self.total_scf_correction_ry_per_bohr),
            ("maximum atomic force", self.maximum_atomic_force_ry_per_bohr),
            ("maximum force component", self.maximum_force_component_ry_per_bohr),
            ("optimizer total force", self.optimizer_total_force_ry_per_bohr),
            (
                "optimizer maximum atomic force",
                self.optimizer_maximum_atomic_force_ry_per_bohr,
            ),
            (
                "optimizer maximum force component",
                self.optimizer_maximum_force_component_ry_per_bohr,
            ),
        ):
            if value is not None and value < 0.0:
                raise ValueError(f"{label} must be nonnegative when represented")
        for label, value in (
            ("BFGS energy threshold", self.bfgs_energy_threshold_ry),
            ("BFGS force threshold", self.bfgs_force_threshold_ry_per_bohr),
            ("BFGS cell threshold", self.bfgs_cell_threshold_kbar),
        ):
            if value is not None and value <= 0.0:
                raise ValueError(f"{label} must be positive when represented")
        if self.bfgs_objective_kind not in {None, "energy", "enthalpy"}:
            raise ValueError("bfgs_objective_kind must be energy, enthalpy, or None")
        objective_values = (
            self.previous_bfgs_objective_ry,
            self.final_bfgs_objective_ry,
            self.bfgs_energy_change_ry,
        )
        if self.bfgs_objective_kind is None and any(
            value is not None for value in objective_values
        ):
            raise ValueError("BFGS objective values require an objective kind")
        if self.bfgs_energy_change_ry is not None and self.bfgs_energy_change_ry < 0.0:
            raise ValueError("BFGS energy change must be nonnegative")
        self._validate_stress(self.stress_ry_per_bohr_cubed, "stress")
        self._validate_stress(
            self.optimizer_stress_ry_per_bohr_cubed,
            "optimizer stress",
        )
        if self.geometry_optimization_converged and (
            self.bfgs_scf_cycle_count is None or self.bfgs_step_count is None
        ):
            raise ValueError("converged geometry optimization requires BFGS counts")
        for label, value in (
            ("BFGS SCF cycle count", self.bfgs_scf_cycle_count),
            ("BFGS step count", self.bfgs_step_count),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{label} must be nonnegative when represented")
        if self.scf_nonconvergence_count < 0:
            raise ValueError("SCF nonconvergence count must be nonnegative")
        if type(self.left_handed_axis_warning) is not bool:
            raise TypeError("left_handed_axis_warning must be a boolean")
        if (
            self.absolute_magnetization_bohr_magneton_per_cell is not None
            and self.absolute_magnetization_bohr_magneton_per_cell < 0.0
        ):
            raise ValueError("absolute magnetization must be nonnegative")
        if self.wavefunction_cutoff_ry is not None and self.wavefunction_cutoff_ry <= 0:
            raise ValueError("wavefunction cutoff must be positive")
        if self.atom_count is not None and self.atom_count <= 0:
            raise ValueError("atom count must be positive")
        if self.k_point_count is not None and self.k_point_count <= 0:
            raise ValueError("k-point count must be positive")
        if self.scf_iteration_count < 0:
            raise ValueError("SCF iteration count must be nonnegative")

    @staticmethod
    def _validate_stress(value: QeStressTensor | None, label: str) -> None:
        if value is None:
            return
        if len(value) != 3 or any(len(row) != 3 for row in value):
            raise ValueError(f"{label} must be a three by three tensor")
        if any(not math.isfinite(component) for row in value for component in row):
            raise ValueError(f"{label} must contain finite values")


@final
@dataclass(frozen=True, slots=True)
class QePwStdoutFileParser(QeOutputFileParser[QePwStdoutFile]):
    """Parse one bounded captured ``pw.x`` standard-output file."""

    def parse(
        self,
        payload: bytes,
        *,
        output_file: QePwStdoutFile,
    ) -> QePwStdoutFileResult:
        """Return the last represented scalar value for repeated observations."""
        if type(payload) is not bytes:
            raise TypeError("pw.x stdout payload must be bytes")
        if len(payload) > _MAX_OUTPUT_BYTES:
            raise QuantumEspressoOutputFileError("pw.x stdout exceeds the byte limit")
        if type(output_file) is not QePwStdoutFile:
            raise TypeError("output_file must be a QePwStdoutFile")
        text = payload.decode("utf-8")
        program_version: str | None = None
        total_energy: float | None = None
        total_magnetization: float | None = None
        absolute_magnetization: float | None = None
        wavefunction_cutoff: float | None = None
        pressure: float | None = None
        total_force: float | None = None
        total_scf_correction: float | None = None
        maximum_atomic_force: float | None = None
        maximum_force_component: float | None = None
        current_atomic_forces: list[tuple[float, float, float]] = []
        stress: QeStressTensor | None = None
        bfgs_scf_cycle_count: int | None = None
        bfgs_step_count: int | None = None
        bfgs_energy_threshold: float | None = None
        bfgs_force_threshold: float | None = None
        bfgs_cell_threshold: float | None = None
        optimizer_total_force: float | None = None
        optimizer_maximum_atomic_force: float | None = None
        optimizer_maximum_force_component: float | None = None
        optimizer_pressure: float | None = None
        optimizer_stress: QeStressTensor | None = None
        previous_bfgs_objective: float | None = None
        previous_bfgs_objective_kind: str | None = None
        final_bfgs_objective: float | None = None
        final_bfgs_objective_kind: str | None = None
        final_enthalpy: float | None = None
        final_energy: float | None = None
        end_bfgs = False
        atom_count: int | None = None
        k_point_count: int | None = None
        iteration_count = 0
        scf_nonconvergence_count = 0
        left_handed_axis_warning = False
        recognized = False
        lines = text.splitlines()

        for index, line in enumerate(lines):
            if match := _VERSION.search(line):
                program_version = match.group(1)
                recognized = True
            if match := _ATOM_COUNT.search(line):
                atom_count = int(match.group(1))
                recognized = True
            if match := _K_POINT_COUNT.search(line):
                k_point_count = int(match.group(1))
                recognized = True
            if match := _CUTOFF.search(line):
                wavefunction_cutoff = self._native_float(match.group(1))
                recognized = True
            if match := _TOTAL_ENERGY.search(line):
                total_energy = self._native_float(match.group(1))
                recognized = True
            if match := _TOTAL_MAGNETIZATION.search(line):
                total_magnetization = self._native_float(match.group(1))
                recognized = True
            if match := _ABSOLUTE_MAGNETIZATION.search(line):
                absolute_magnetization = self._native_float(match.group(1))
                recognized = True
            if match := _PRESSURE.search(line):
                pressure = self._native_float(match.group(1))
                recognized = True
            if _FORCE_BLOCK.search(line):
                current_atomic_forces = []
                recognized = True
            if match := _ATOM_FORCE.search(line):
                current_atomic_forces.append(
                    (
                        self._native_float(match.group(1)),
                        self._native_float(match.group(2)),
                        self._native_float(match.group(3)),
                    )
                )
                recognized = True
            if match := _TOTAL_FORCE.search(line):
                total_force = self._native_float(match.group(1))
                total_scf_correction = self._native_float(match.group(2))
                if current_atomic_forces:
                    maximum_atomic_force = max(
                        math.sqrt(sum(component**2 for component in force))
                        for force in current_atomic_forces
                    )
                    maximum_force_component = max(
                        abs(component)
                        for force in current_atomic_forces
                        for component in force
                    )
                    current_atomic_forces = []
                recognized = True
            if _STRESS_HEADER.search(line):
                represented_stress = self._stress_after(lines, index)
                if represented_stress is not None:
                    stress = represented_stress
                recognized = True
            if match := _BFGS_CONVERGED.search(line):
                bfgs_scf_cycle_count = int(match.group(1))
                bfgs_step_count = int(match.group(2))
                optimizer_total_force = total_force
                optimizer_maximum_atomic_force = maximum_atomic_force
                optimizer_maximum_force_component = maximum_force_component
                optimizer_pressure = pressure
                optimizer_stress = stress
                recognized = True
            if _END_BFGS.search(line):
                end_bfgs = True
                recognized = True
            if match := _BFGS_CRITERIA.search(line):
                bfgs_energy_threshold = self._native_float(match.group(1))
                bfgs_force_threshold = self._native_float(match.group(2))
                bfgs_cell_threshold = (
                    self._native_float(match.group(3))
                    if match.group(3) is not None
                    else None
                )
                recognized = True
            if match := _BFGS_NEW_OBJECTIVE.search(line):
                previous_bfgs_objective_kind = match.group(1).casefold()
                previous_bfgs_objective = self._native_float(match.group(2))
                recognized = True
            if match := _FINAL_OBJECTIVE.search(line):
                final_bfgs_objective_kind = match.group(1).casefold()
                final_bfgs_objective = self._native_float(match.group(2))
                if final_bfgs_objective_kind == "enthalpy":
                    final_enthalpy = final_bfgs_objective
                else:
                    final_energy = final_bfgs_objective
                recognized = True
            if _SCF_NOT_CONVERGED.search(line):
                scf_nonconvergence_count += 1
                recognized = True
            if _LEFT_HANDED_AXES.search(line):
                left_handed_axis_warning = True
                recognized = True
            if _ITERATION.search(line):
                iteration_count += 1
                recognized = True

        if not recognized:
            raise QuantumEspressoOutputFileError(
                "text contains no supported pw.x stdout observations"
            )
        objective_kind = (
            final_bfgs_objective_kind
            if final_bfgs_objective_kind == previous_bfgs_objective_kind
            else None
        )
        bfgs_energy_change = (
            abs(final_bfgs_objective - previous_bfgs_objective)
            if objective_kind is not None
            and final_bfgs_objective is not None
            and previous_bfgs_objective is not None
            else None
        )
        lowered = text.casefold()
        return QePwStdoutFileResult(
            output_file=output_file,
            program_version=program_version,
            job_completed="job done." in lowered,
            scf_converged="convergence has been achieved" in lowered,
            total_energy_ry=total_energy,
            total_magnetization_bohr_magneton_per_cell=total_magnetization,
            absolute_magnetization_bohr_magneton_per_cell=absolute_magnetization,
            wavefunction_cutoff_ry=wavefunction_cutoff,
            pressure_kbar=pressure,
            total_force_ry_per_bohr=total_force,
            total_scf_correction_ry_per_bohr=total_scf_correction,
            maximum_atomic_force_ry_per_bohr=maximum_atomic_force,
            maximum_force_component_ry_per_bohr=maximum_force_component,
            stress_ry_per_bohr_cubed=stress,
            geometry_optimization_converged=(
                end_bfgs
                and bfgs_scf_cycle_count is not None
                and bfgs_step_count is not None
            ),
            bfgs_scf_cycle_count=bfgs_scf_cycle_count,
            bfgs_step_count=bfgs_step_count,
            bfgs_energy_threshold_ry=bfgs_energy_threshold,
            bfgs_force_threshold_ry_per_bohr=bfgs_force_threshold,
            bfgs_cell_threshold_kbar=bfgs_cell_threshold,
            optimizer_total_force_ry_per_bohr=optimizer_total_force,
            optimizer_maximum_atomic_force_ry_per_bohr=(optimizer_maximum_atomic_force),
            optimizer_maximum_force_component_ry_per_bohr=(
                optimizer_maximum_force_component
            ),
            optimizer_pressure_kbar=optimizer_pressure,
            optimizer_stress_ry_per_bohr_cubed=optimizer_stress,
            bfgs_objective_kind=objective_kind,
            previous_bfgs_objective_ry=(
                previous_bfgs_objective if objective_kind is not None else None
            ),
            final_bfgs_objective_ry=(
                final_bfgs_objective if objective_kind is not None else None
            ),
            bfgs_energy_change_ry=bfgs_energy_change,
            final_enthalpy_ry=final_enthalpy,
            final_energy_ry=final_energy,
            scf_nonconvergence_count=scf_nonconvergence_count,
            left_handed_axis_warning=left_handed_axis_warning,
            atom_count=atom_count,
            k_point_count=k_point_count,
            scf_iteration_count=iteration_count,
        )

    @classmethod
    def _stress_after(
        cls,
        lines: list[str],
        header_index: int,
    ) -> QeStressTensor | None:
        rows: list[tuple[float, float, float]] = []
        for line in lines[header_index + 1 : header_index + 4]:
            values = line.split()
            if len(values) < 3:
                return None
            try:
                row = tuple(cls._native_float(value) for value in values[:3])
            except ValueError:
                return None
            rows.append((row[0], row[1], row[2]))
        if len(rows) != 3:
            return None
        return (rows[0], rows[1], rows[2])

    @staticmethod
    def _native_float(value: str) -> float:
        """Decode one QE native floating-point token."""
        return float(value.replace("D", "E").replace("d", "e"))
