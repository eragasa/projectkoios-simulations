"""Parse complete ordered relaxation observations from captured ``pw.x`` stdout."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal

from projectkoios.integrations.quantumespresso.outputs.base import (
    QuantumEspressoOutputFileError,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFileResult,
    QeStressTensor,
)

_MAX_OUTPUT_BYTES = 100_000_000
_FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"
_TOTAL_ENERGY = re.compile(rf"!\s+total energy\s*=\s*({_FLOAT})\s*Ry", re.I)
_SCF_CONVERGED = re.compile(
    r"convergence has been achieved in\s+(\d+)\s+iterations",
    re.I,
)
_SCF_NOT_CONVERGED = re.compile(r"convergence NOT achieved", re.I)
_FORCE = re.compile(
    rf"atom\s+(\d+)\s+type\s+(\d+)\s+force\s*=\s*"
    rf"({_FLOAT})\s+({_FLOAT})\s+({_FLOAT})",
    re.I,
)
_TOTAL_FORCE = re.compile(
    rf"Total force\s*=\s*({_FLOAT})\s+Total SCF correction\s*=\s*({_FLOAT})",
    re.I,
)
_STRESS_HEADER = re.compile(
    rf"total\s+stress\s+\(Ry/bohr\*\*3\).*?P=\s*({_FLOAT})",
    re.I,
)
_SCF_CYCLES = re.compile(r"number of scf cycles\s*=\s*(\d+)", re.I)
_OPTIMIZER_STEPS = re.compile(r"number of bfgs steps\s*=\s*(\d+)", re.I)
_OBJECTIVE = re.compile(
    rf"\b(energy|enthalpy)\s+(old|new)\s*=\s*({_FLOAT})\s*Ry",
    re.I,
)
_CELL_HEADER = re.compile(r"^\s*CELL_PARAMETERS(?:\s*\(([^)]*)\))?\s*$", re.I)
_POSITIONS_HEADER = re.compile(r"^\s*ATOMIC_POSITIONS(?:\s*\(([^)]*)\))?\s*$", re.I)
_FINAL_COORDINATES_BEGIN = re.compile(r"^\s*Begin final coordinates\s*$", re.I)
_FINAL_COORDINATES_END = re.compile(r"^\s*End final coordinates\s*$", re.I)

_QeVector3 = tuple[float, float, float]
_QeMovementMask = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class QeRelaxationAtomicPosition:
    """Retain one source-ordered native atomic-position declaration."""

    label: str
    coordinates: _QeVector3
    movement_mask: _QeMovementMask | None = None

    def __post_init__(self) -> None:
        if (
            type(self.label) is not str
            or not self.label
            or self.label != self.label.strip()
        ):
            raise ValueError("label must be a nonempty stripped string")
        _finite_vector(self.coordinates, "coordinates")
        if self.movement_mask is not None and (
            type(self.movement_mask) is not tuple
            or len(self.movement_mask) != 3
            or any(
                type(value) is not int or value not in {0, 1}
                for value in self.movement_mask
            )
        ):
            raise ValueError("movement_mask must contain three zero-or-one integers")


@dataclass(frozen=True, slots=True)
class QeRelaxationAtomicForce:
    """Retain one indexed atomic force in native Ry/bohr units."""

    atom_index: int
    type_index: int
    force_ry_per_bohr: _QeVector3

    def __post_init__(self) -> None:
        if type(self.atom_index) is not int or self.atom_index <= 0:
            raise ValueError("atom_index must be positive")
        if type(self.type_index) is not int or self.type_index <= 0:
            raise ValueError("type_index must be positive")
        _finite_vector(self.force_ry_per_bohr, "force_ry_per_bohr")


@dataclass(frozen=True, slots=True)
class QeRelaxationCell:
    """Retain one emitted native cell-parameter block without conversion."""

    source_label: str
    vectors: tuple[_QeVector3, _QeVector3, _QeVector3]

    def __post_init__(self) -> None:
        if (
            type(self.source_label) is not str
            or not self.source_label
            or self.source_label != self.source_label.strip()
        ):
            raise ValueError("source_label must be a nonempty stripped string")
        if type(self.vectors) is not tuple or len(self.vectors) != 3:
            raise ValueError("vectors must contain three vectors")
        for vector in self.vectors:
            _finite_vector(vector, "cell vector")


@dataclass(frozen=True, slots=True)
class QeRelaxationPositionBlock:
    """Retain one emitted native atomic-position block without conversion."""

    source_label: str
    atoms: tuple[QeRelaxationAtomicPosition, ...]
    final_coordinates: bool

    def __post_init__(self) -> None:
        if (
            type(self.source_label) is not str
            or not self.source_label
            or self.source_label != self.source_label.strip()
        ):
            raise ValueError("source_label must be a nonempty stripped string")
        if type(self.atoms) is not tuple or not self.atoms:
            raise ValueError("atoms must be a nonempty tuple")
        if any(type(atom) is not QeRelaxationAtomicPosition for atom in self.atoms):
            raise TypeError("atoms must contain QeRelaxationAtomicPosition values")
        if type(self.final_coordinates) is not bool:
            raise TypeError("final_coordinates must be a boolean")


@dataclass(frozen=True, slots=True)
class QeRelaxationTrajectoryStep:
    """Retain one SCF evaluation and any subsequently emitted geometry."""

    sequence_index: int
    total_energy_ry: float
    scf_converged: bool
    scf_iteration_count: int | None
    atomic_forces: tuple[QeRelaxationAtomicForce, ...]
    total_force_ry_per_bohr: float | None
    total_scf_correction_ry_per_bohr: float | None
    pressure_kbar: float | None
    stress_ry_per_bohr_cubed: QeStressTensor | None
    optimizer_scf_cycle_count: int | None
    optimizer_step_count: int | None
    objective_kind: Literal["energy", "enthalpy"] | None
    previous_objective_ry: float | None
    new_objective_ry: float | None
    emitted_cell: QeRelaxationCell | None
    emitted_positions: QeRelaxationPositionBlock | None

    def __post_init__(self) -> None:
        if type(self.sequence_index) is not int or self.sequence_index <= 0:
            raise ValueError("sequence_index must be positive")
        _finite(self.total_energy_ry, "total_energy_ry")
        if type(self.scf_converged) is not bool:
            raise TypeError("scf_converged must be a boolean")
        if self.scf_iteration_count is not None and (
            type(self.scf_iteration_count) is not int or self.scf_iteration_count <= 0
        ):
            raise ValueError("scf_iteration_count must be positive or None")
        if type(self.atomic_forces) is not tuple or any(
            type(force) is not QeRelaxationAtomicForce for force in self.atomic_forces
        ):
            raise TypeError("atomic_forces must contain QeRelaxationAtomicForce values")
        if self.atomic_forces and tuple(
            force.atom_index for force in self.atomic_forces
        ) != tuple(range(1, len(self.atomic_forces) + 1)):
            raise ValueError("atomic forces must retain contiguous source order")
        for label, value in (
            ("total_force_ry_per_bohr", self.total_force_ry_per_bohr),
            ("total_scf_correction_ry_per_bohr", self.total_scf_correction_ry_per_bohr),
        ):
            if value is not None:
                _finite(value, label)
                if value < 0.0:
                    raise ValueError(f"{label} must be nonnegative")
        if self.pressure_kbar is not None:
            _finite(self.pressure_kbar, "pressure_kbar")
        _validate_stress(self.stress_ry_per_bohr_cubed)
        for label, value in (
            ("optimizer_scf_cycle_count", self.optimizer_scf_cycle_count),
            ("optimizer_step_count", self.optimizer_step_count),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{label} must be nonnegative or None")
        if self.objective_kind not in {None, "energy", "enthalpy"}:
            raise ValueError("objective_kind must be energy, enthalpy, or None")
        if self.objective_kind is None and (
            self.previous_objective_ry is not None or self.new_objective_ry is not None
        ):
            raise ValueError("objective values require an objective_kind")
        for label, value in (
            ("previous_objective_ry", self.previous_objective_ry),
            ("new_objective_ry", self.new_objective_ry),
        ):
            if value is not None:
                _finite(value, label)
        if (
            self.emitted_cell is not None
            and type(self.emitted_cell) is not QeRelaxationCell
        ):
            raise TypeError("emitted_cell must be a QeRelaxationCell or None")
        if self.emitted_positions is not None and (
            type(self.emitted_positions) is not QeRelaxationPositionBlock
        ):
            raise TypeError(
                "emitted_positions must be a QeRelaxationPositionBlock or None"
            )


@dataclass(frozen=True, slots=True)
class QeRelaxationTrajectory:
    """Retain every represented relaxation evaluation in source order."""

    calculation: Literal["relax", "vc-relax"]
    summary: QePwStdoutFileResult
    steps: tuple[QeRelaxationTrajectoryStep, ...]

    def __post_init__(self) -> None:
        if self.calculation not in {"relax", "vc-relax"}:
            raise ValueError("calculation must be relax or vc-relax")
        if type(self.summary) is not QePwStdoutFileResult:
            raise TypeError("summary must be a QePwStdoutFileResult")
        if type(self.steps) is not tuple:
            raise TypeError("steps must be a tuple")
        if any(type(step) is not QeRelaxationTrajectoryStep for step in self.steps):
            raise TypeError("steps must contain QeRelaxationTrajectoryStep values")
        if tuple(step.sequence_index for step in self.steps) != tuple(
            range(1, len(self.steps) + 1)
        ):
            raise ValueError("trajectory steps must retain contiguous source order")
        if self.calculation == "relax" and any(
            step.emitted_cell is not None for step in self.steps
        ):
            raise ValueError("relax trajectory must not contain emitted cell blocks")


@dataclass(slots=True)
class _MutableStep:
    total_energy_ry: float
    scf_converged: bool = False
    scf_iteration_count: int | None = None
    atomic_forces: list[QeRelaxationAtomicForce] | None = None
    total_force_ry_per_bohr: float | None = None
    total_scf_correction_ry_per_bohr: float | None = None
    pressure_kbar: float | None = None
    stress_ry_per_bohr_cubed: QeStressTensor | None = None
    optimizer_scf_cycle_count: int | None = None
    optimizer_step_count: int | None = None
    objective_kind: Literal["energy", "enthalpy"] | None = None
    previous_objective_ry: float | None = None
    new_objective_ry: float | None = None
    emitted_cell: QeRelaxationCell | None = None
    emitted_positions: QeRelaxationPositionBlock | None = None


@dataclass(frozen=True, slots=True)
class QeRelaxationTrajectoryParser:
    """Parse bounded native relaxation observations without acceptance policy."""

    def parse(
        self,
        payload: bytes,
        *,
        calculation: Literal["relax", "vc-relax"],
        summary: QePwStdoutFileResult,
    ) -> QeRelaxationTrajectory:
        """Return all represented SCF evaluations and emitted geometries."""
        if type(payload) is not bytes:
            raise TypeError("pw.x stdout payload must be bytes")
        if len(payload) > _MAX_OUTPUT_BYTES:
            raise QuantumEspressoOutputFileError("pw.x stdout exceeds the byte limit")
        if calculation not in {"relax", "vc-relax"}:
            raise ValueError("calculation must be relax or vc-relax")
        if type(summary) is not QePwStdoutFileResult:
            raise TypeError("summary must be a QePwStdoutFileResult")
        text = payload.decode("utf-8")
        lines = text.splitlines()
        steps: list[QeRelaxationTrajectoryStep] = []
        current: _MutableStep | None = None
        final_coordinates = False
        index = 0
        while index < len(lines):
            line = lines[index]
            if _FINAL_COORDINATES_BEGIN.search(line):
                final_coordinates = True
                index += 1
                continue
            if _FINAL_COORDINATES_END.search(line):
                final_coordinates = False
                index += 1
                continue
            if match := _TOTAL_ENERGY.search(line):
                if current is not None:
                    steps.append(self._freeze(current, len(steps) + 1))
                current = _MutableStep(total_energy_ry=_native_float(match.group(1)))
                current.atomic_forces = []
                index += 1
                continue
            if current is None:
                index += 1
                continue
            if match := _SCF_CONVERGED.search(line):
                current.scf_converged = True
                current.scf_iteration_count = int(match.group(1))
            elif _SCF_NOT_CONVERGED.search(line):
                current.scf_converged = False
                current.scf_iteration_count = None
            elif match := _FORCE.search(line):
                assert current.atomic_forces is not None
                current.atomic_forces.append(
                    QeRelaxationAtomicForce(
                        atom_index=int(match.group(1)),
                        type_index=int(match.group(2)),
                        force_ry_per_bohr=(
                            _native_float(match.group(3)),
                            _native_float(match.group(4)),
                            _native_float(match.group(5)),
                        ),
                    )
                )
            elif match := _TOTAL_FORCE.search(line):
                current.total_force_ry_per_bohr = _native_float(match.group(1))
                current.total_scf_correction_ry_per_bohr = _native_float(match.group(2))
            elif match := _STRESS_HEADER.search(line):
                current.pressure_kbar = _native_float(match.group(1))
                current.stress_ry_per_bohr_cubed = _parse_stress(lines, index)
            elif match := _SCF_CYCLES.search(line):
                current.optimizer_scf_cycle_count = int(match.group(1))
            elif match := _OPTIMIZER_STEPS.search(line):
                current.optimizer_step_count = int(match.group(1))
            elif match := _OBJECTIVE.search(line):
                kind = match.group(1).casefold()
                position = match.group(2).casefold()
                if (
                    current.objective_kind is not None
                    and current.objective_kind != kind
                ):
                    raise QuantumEspressoOutputFileError(
                        "relaxation step mixes energy and enthalpy objectives"
                    )
                current.objective_kind = "energy" if kind == "energy" else "enthalpy"
                if position == "old":
                    current.previous_objective_ry = _native_float(match.group(3))
                else:
                    current.new_objective_ry = _native_float(match.group(3))
            elif match := _CELL_HEADER.match(line):
                current.emitted_cell = _parse_cell(lines, index, match.group(1))
                index += 3
            elif match := _POSITIONS_HEADER.match(line):
                current.emitted_positions = _parse_positions(
                    lines,
                    index,
                    match.group(1),
                    final_coordinates=final_coordinates,
                )
                index += len(current.emitted_positions.atoms)
            index += 1
        if current is not None:
            steps.append(self._freeze(current, len(steps) + 1))
        return QeRelaxationTrajectory(
            calculation=calculation,
            summary=summary,
            steps=tuple(steps),
        )

    @staticmethod
    def _freeze(step: _MutableStep, sequence_index: int) -> QeRelaxationTrajectoryStep:
        return QeRelaxationTrajectoryStep(
            sequence_index=sequence_index,
            total_energy_ry=step.total_energy_ry,
            scf_converged=step.scf_converged,
            scf_iteration_count=step.scf_iteration_count,
            atomic_forces=tuple(step.atomic_forces or ()),
            total_force_ry_per_bohr=step.total_force_ry_per_bohr,
            total_scf_correction_ry_per_bohr=(step.total_scf_correction_ry_per_bohr),
            pressure_kbar=step.pressure_kbar,
            stress_ry_per_bohr_cubed=step.stress_ry_per_bohr_cubed,
            optimizer_scf_cycle_count=step.optimizer_scf_cycle_count,
            optimizer_step_count=step.optimizer_step_count,
            objective_kind=step.objective_kind,
            previous_objective_ry=step.previous_objective_ry,
            new_objective_ry=step.new_objective_ry,
            emitted_cell=step.emitted_cell,
            emitted_positions=step.emitted_positions,
        )


def _parse_stress(lines: list[str], header_index: int) -> QeStressTensor | None:
    rows: list[_QeVector3] = []
    for line in lines[header_index + 1 : header_index + 4]:
        values = line.split()
        if len(values) < 3:
            return None
        try:
            rows.append(
                (
                    _native_float(values[0]),
                    _native_float(values[1]),
                    _native_float(values[2]),
                )
            )
        except ValueError:
            return None
    if len(rows) != 3:
        return None
    return (rows[0], rows[1], rows[2])


def _parse_cell(
    lines: list[str],
    header_index: int,
    source_label: str | None,
) -> QeRelaxationCell:
    if source_label is None or not source_label.strip():
        raise QuantumEspressoOutputFileError(
            "CELL_PARAMETERS block must declare its source units"
        )
    vectors: list[_QeVector3] = []
    for line in lines[header_index + 1 : header_index + 4]:
        values = line.split()
        if len(values) < 3:
            raise QuantumEspressoOutputFileError("CELL_PARAMETERS block is incomplete")
        try:
            vectors.append(
                (
                    _native_float(values[0]),
                    _native_float(values[1]),
                    _native_float(values[2]),
                )
            )
        except ValueError as error:
            raise QuantumEspressoOutputFileError(
                "CELL_PARAMETERS block contains invalid coordinates"
            ) from error
    if len(vectors) != 3:
        raise QuantumEspressoOutputFileError("CELL_PARAMETERS block is incomplete")
    return QeRelaxationCell(
        source_label=source_label.strip(),
        vectors=(vectors[0], vectors[1], vectors[2]),
    )


def _parse_positions(
    lines: list[str],
    header_index: int,
    source_label: str | None,
    *,
    final_coordinates: bool,
) -> QeRelaxationPositionBlock:
    if source_label is None or not source_label.strip():
        raise QuantumEspressoOutputFileError(
            "ATOMIC_POSITIONS block must declare its source units"
        )
    atoms: list[QeRelaxationAtomicPosition] = []
    for line in lines[header_index + 1 :]:
        values = line.split()
        if len(values) not in {4, 7}:
            break
        try:
            coordinates = (
                _native_float(values[1]),
                _native_float(values[2]),
                _native_float(values[3]),
            )
            movement_mask = (
                None
                if len(values) == 4
                else (int(values[4]), int(values[5]), int(values[6]))
            )
            atoms.append(
                QeRelaxationAtomicPosition(
                    label=values[0],
                    coordinates=coordinates,
                    movement_mask=movement_mask,
                )
            )
        except (TypeError, ValueError) as error:
            raise QuantumEspressoOutputFileError(
                "ATOMIC_POSITIONS block contains invalid coordinates or constraints"
            ) from error
    if not atoms:
        raise QuantumEspressoOutputFileError("ATOMIC_POSITIONS block is empty")
    return QeRelaxationPositionBlock(
        source_label=source_label.strip(),
        atoms=tuple(atoms),
        final_coordinates=final_coordinates,
    )


def _native_float(value: str) -> float:
    return float(value.replace("D", "E").replace("d", "e"))


def _finite(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _finite_vector(value: _QeVector3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three values")
    if any(
        type(component) is not float or not math.isfinite(component)
        for component in value
    ):
        raise ValueError(f"{label} must contain finite floats")


def _validate_stress(value: QeStressTensor | None) -> None:
    if value is None:
        return
    if (
        type(value) is not tuple
        or len(value) != 3
        or any(len(row) != 3 for row in value)
    ):
        raise ValueError("stress must be a three by three tensor")
    if any(
        type(component) is not float or not math.isfinite(component)
        for row in value
        for component in row
    ):
        raise ValueError("stress must contain finite floats")
