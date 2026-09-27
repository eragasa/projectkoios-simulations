"""Effect-free inspection of retained LAMMPS text artifacts."""

from __future__ import annotations

import ast
import hashlib
import math
import re
from collections.abc import Mapping, Sequence

from projectkoios.integrations.lammps.models import (
    LammpsCommandIntent,
    LammpsDataStructureObservation,
    LammpsIntegrationObservation,
    LammpsTemplateObservation,
    ObservedSetting,
    SourceFileEvidence,
    Vector3,
)

_COMMAND = re.compile(
    r"(?P<program>\S+)\s+-i\s+(?P<input>[^\s>]+)\s*>\s*(?P<output>\S+)"
)
_COUNT = re.compile(r"^\s*(\d+)\s+(atoms|atom types)\s*$")
_BOUND = re.compile(r"^\s*(\S+)\s+(\S+)\s+([xyz])lo\s+\3hi\s*$")
_TILT = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+xy\s+xz\s+yz\s*$")


def inspect_lammps_templates(
    *,
    simulation_settings: Sequence[ObservedSetting],
    evidence_by_path: Mapping[str, SourceFileEvidence],
    text_by_path: Mapping[str, str],
) -> LammpsIntegrationObservation:
    """Inspect retained templates without expanding or executing commands."""
    for path, evidence in evidence_by_path.items():
        if path != evidence.relative_path:
            raise ValueError("LAMMPS evidence-map key does not match its evidence path")
    templates: list[LammpsTemplateObservation] = []
    for setting in simulation_settings:
        if type(setting) is not ObservedSetting:
            raise TypeError("simulation_settings must contain ObservedSetting")
        if setting.key != "lmps_sim_type" or len(setting.values) != 2:
            raise ValueError("LAMMPS simulation setting must have name and directory")
        simulation_name, directory_name = setting.values
        template_directory = f"lmp_scripts_db/{directory_name}"
        prefix = template_directory + "/"
        files = tuple(
            sorted(
                (
                    evidence
                    for path, evidence in evidence_by_path.items()
                    if path.startswith(prefix)
                ),
                key=lambda item: item.relative_path,
            )
        )
        if not files:
            raise ValueError(f"LAMMPS template is missing: {template_directory}")
        runner_path = prefix + "runsimulation.sh"
        runner = evidence_by_path.get(runner_path)
        runner_text = text_by_path.get(runner_path)
        if runner is None or runner_text is None:
            raise ValueError(f"LAMMPS runner is missing: {runner_path}")
        _verify_text_evidence(runner_text, runner, "LAMMPS runner")
        matches = [
            match
            for line in runner_text.splitlines()
            if (match := _COMMAND.search(line)) is not None
        ]
        if len(matches) != 1:
            raise ValueError(f"LAMMPS runner command is ambiguous: {runner_path}")
        program = matches[0].group("program")
        if program not in {"$LAMMPS_BIN", "${LAMMPS_BIN}"} and not program.rsplit(
            "/", 1
        )[-1].startswith("lmp"):
            raise ValueError(f"LAMMPS runner executable is unsupported: {runner_path}")
        input_name = matches[0].group("input")
        stdout_name = matches[0].group("output")
        input_path = prefix + input_name
        if input_path not in evidence_by_path:
            raise ValueError(f"LAMMPS input script is missing: {input_path}")
        intent = LammpsCommandIntent(
            simulation_name=simulation_name,
            executable_environment_variable="LAMMPS_BIN",
            input_script=input_name,
            stdout_artifact=stdout_name,
            runner_script=runner,
        )
        templates.append(
            LammpsTemplateObservation(
                simulation_name=simulation_name,
                template_directory=template_directory,
                files=files,
                command_intent=intent,
            )
        )
    return LammpsIntegrationObservation(templates=tuple(templates))


def inspect_lammps_data_structure(
    *, name: str, evidence: SourceFileEvidence, text: str
) -> LammpsDataStructureObservation:
    """Parse bounded structural syntax without constructing a simulation."""
    if type(text) is not str or not text:
        raise ValueError("LAMMPS structure text is outside the inspection bound")
    _verify_text_evidence(text, evidence, "LAMMPS structure")
    lines = text.splitlines()
    species_order = _species_order(lines)
    counts: dict[str, int] = {}
    bounds_by_axis: dict[str, tuple[float, float]] = {}
    tilt: Vector3 | None = None
    atoms_index: int | None = None
    for index, line in enumerate(lines):
        if match := _COUNT.fullmatch(line):
            label = match.group(2)
            if label in counts:
                raise ValueError(f"duplicate LAMMPS {label} declaration")
            counts[label] = int(match.group(1))
        elif match := _BOUND.fullmatch(line):
            axis = match.group(3)
            if axis in bounds_by_axis:
                raise ValueError(f"duplicate LAMMPS {axis} bound")
            bounds_by_axis[axis] = (
                _finite_real(match.group(1), "bound"),
                _finite_real(match.group(2), "bound"),
            )
        elif match := _TILT.fullmatch(line):
            if tilt is not None:
                raise ValueError("duplicate LAMMPS tilt-factor declaration")
            tilt = (
                _finite_real(match.group(1), "tilt factor"),
                _finite_real(match.group(2), "tilt factor"),
                _finite_real(match.group(3), "tilt factor"),
            )
        elif line.strip().split("#", 1)[0].strip() == "Atoms":
            if atoms_index is not None:
                raise ValueError("duplicate LAMMPS Atoms section")
            atoms_index = index
    if set(counts) != {"atoms", "atom types"}:
        raise ValueError("LAMMPS atom counts are incomplete")
    if set(bounds_by_axis) != {"x", "y", "z"}:
        raise ValueError("LAMMPS bounds are incomplete")
    if tilt is None or atoms_index is None:
        raise ValueError("LAMMPS tilt factors or Atoms section are absent")
    atom_lines = [line for line in lines[atoms_index + 1 :] if line.strip()]
    if len(atom_lines) != counts["atoms"]:
        raise ValueError("LAMMPS atom record count does not agree")
    atom_style: str | None = None
    identifiers: list[int] = []
    for line in atom_lines:
        fields = line.split()
        current_style = (
            "atomic" if len(fields) == 5 else "charge" if len(fields) == 6 else None
        )
        if current_style is None:
            raise ValueError("LAMMPS atom record has unsupported fields")
        if atom_style is None:
            atom_style = current_style
        elif current_style != atom_style:
            raise ValueError("LAMMPS atom styles are inconsistent")
        try:
            identifier = int(fields[0])
            atom_type = int(fields[1])
        except ValueError as error:
            raise ValueError(
                "LAMMPS atom identifiers and types must be integers"
            ) from error
        if not 1 <= atom_type <= counts["atom types"]:
            raise ValueError("LAMMPS atom type lies outside the declared count")
        identifiers.append(identifier)
        for token in fields[2:]:
            _finite_real(token, "atom value")
    if identifiers != list(range(1, counts["atoms"] + 1)):
        raise ValueError("LAMMPS atom identifiers are incomplete or unordered")
    assert atom_style is not None
    return LammpsDataStructureObservation(
        name=name,
        evidence=evidence,
        species_order=species_order,
        atom_count=counts["atoms"],
        atom_type_count=counts["atom types"],
        atom_style=atom_style,
        bounds=(bounds_by_axis["x"], bounds_by_axis["y"], bounds_by_axis["z"]),
        tilt_factors=tilt,
    )


def _verify_text_evidence(text: str, evidence: SourceFileEvidence, label: str) -> None:
    payload = text.encode("utf-8")
    if len(payload) != evidence.byte_size:
        raise ValueError(f"{label} text size does not match its evidence")
    if hashlib.sha256(payload).hexdigest() != evidence.sha256:
        raise ValueError(f"{label} text hash does not match its evidence")


def _species_order(lines: list[str]) -> tuple[str, ...]:
    first = next((line.strip() for line in lines if line.strip()), "")
    if not first.startswith("#"):
        raise ValueError("LAMMPS species comment is absent")
    try:
        value = ast.literal_eval(first[1:].strip())
    except (SyntaxError, ValueError) as error:
        raise ValueError("LAMMPS species comment is invalid") from error
    if not isinstance(value, list) or any(type(item) is not str for item in value):
        raise ValueError("LAMMPS species comment must contain a string list")
    return tuple(value)


def _finite_real(token: str, label: str) -> float:
    try:
        value = float(token)
    except ValueError as error:
        raise ValueError(f"LAMMPS {label} must be numeric") from error
    if not math.isfinite(value):
        raise ValueError(f"LAMMPS {label} must be finite")
    return value
