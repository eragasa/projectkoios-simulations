"""Load closed-schema, path-complete Quantum ESPRESSO NSCF TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from projectkoios.integrations.quantumespresso.pw.nscf.calculation import (
    QeNscfCalculationConfiguration,
    QeNscfDirectoryResource,
    QeNscfFileResource,
)
from projectkoios.integrations.quantumespresso.pw.nscf.cards import (
    QeNscfDiagonalization,
    QeNscfOccupations,
    QeNscfVerbosity,
)

_MAXIMUM_CONFIGURATION_BYTES = 100_000


@dataclass(frozen=True, slots=True)
class QeNscfCalculationTomlLoader:
    """Load one bounded configuration without granting execution authority."""

    def load(self, path: Path) -> QeNscfCalculationConfiguration:
        """Return validated typed configuration extracted from a closed schema."""
        if not isinstance(path, Path):
            raise TypeError("path must be a Path")
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size > _MAXIMUM_CONFIGURATION_BYTES
        ):
            raise ValueError("configuration must be a bounded regular file")
        with path.open("rb") as stream:
            payload = tomllib.load(stream)
        _schema(payload)
        source = _mapping(payload, "source_input")
        structure = _mapping(payload, "structure")
        calculator = _mapping(payload, "calculator")
        parent = _mapping(payload, "parent_scf")
        pseudo = _mapping(payload, "pseudopotential")
        sampling = _mapping(payload, "sampling")
        qe = _mapping(payload, "qe")
        output = _mapping(payload, "output")
        qualification = _mapping(payload, "qualification")
        reference = (
            _mapping(payload, "reference_nscf") if "reference_nscf" in payload else None
        )
        return QeNscfCalculationConfiguration(
            calculation_id=_string(payload, "calculation_id"),
            integration_id=_string(payload, "integration_id"),
            source_input=_file_resource(source),
            structure=_file_resource(structure),
            structure_id=_string(structure, "structure_id"),
            calculator=_file_resource(calculator),
            calculator_program=_string(calculator, "program"),
            calculator_version=_string(calculator, "program_version"),
            pseudopotential=_file_resource(pseudo),
            pseudopotential_symbol=_string(pseudo, "symbol"),
            pseudopotential_filename=_string(pseudo, "filename"),
            pseudopotential_mass_amu=_float(pseudo, "mass_amu"),
            parent_output_directory=QeNscfDirectoryResource(
                _string(parent, "output_directory")
            ),
            parent_saved_state_root=QeNscfDirectoryResource(
                _string(parent, "saved_state_root")
            ),
            parent_manifest=QeNscfFileResource(
                path=_string(parent, "manifest_path"),
                sha256=_sha(parent, "manifest_sha256"),
                byte_size=_integer(parent, "manifest_byte_size"),
            ),
            parent_calculation=_string(parent, "calculation"),
            parent_prefix=_string(parent, "prefix"),
            output_directory=QeNscfDirectoryResource(_string(output, "directory")),
            reference_output_directory=(
                None
                if reference is None
                else QeNscfDirectoryResource(_string(reference, "output_directory"))
            ),
            kpoint_grid=_triplet(sampling, "kpoint_grid"),
            kpoint_offset=_triplet(sampling, "kpoint_offset"),
            band_count=_integer(sampling, "band_count"),
            wavefunction_cutoff_ry=_float(
                sampling,
                "wavefunction_cutoff_ry",
            ),
            charge_density_cutoff_ry=_optional_float(
                sampling,
                "charge_density_cutoff_ry",
            ),
            electronic_tolerance_ry=_float(
                sampling,
                "electronic_tolerance_ry",
            ),
            occupations=QeNscfOccupations(_string(sampling, "occupations")),
            prefix=_string(qe, "prefix"),
            pseudo_dir=_string(qe, "pseudo_dir"),
            outdir=_string(qe, "outdir"),
            input_filename=_string(qe, "input_filename"),
            verbosity=QeNscfVerbosity(_string(qe, "verbosity")),
            iprint=_integer(qe, "iprint"),
            diagonalization=QeNscfDiagonalization(_string(qe, "diagonalization")),
            full_diagonalization_accuracy=_boolean(
                qe,
                "diago_full_acc",
            ),
            disable_symmetry=_boolean(qe, "disable_symmetry"),
            disable_time_reversal=_boolean(qe, "disable_time_reversal"),
            coordinate_precision=_integer(qe, "coordinate_precision"),
            kpoint_precision=_integer(qe, "kpoint_precision"),
            qualification_statements=_strings(qualification, "statements"),
        )


def _schema(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported configuration schema")
    if payload.get("phase") != "nscf":
        raise ValueError("phase must be nscf")
    _keys(
        payload,
        "configuration",
        {
            "schema_version",
            "calculation_id",
            "phase",
            "integration_id",
            "source_input",
            "structure",
            "calculator",
            "parent_scf",
            "pseudopotential",
            "sampling",
            "qe",
            "output",
            "qualification",
        },
        {"reference_nscf"},
    )
    _keys(_mapping(payload, "source_input"), "source_input", _FILE_KEYS)
    _keys(
        _mapping(payload, "structure"),
        "structure",
        _FILE_KEYS | {"structure_id"},
    )
    _keys(
        _mapping(payload, "calculator"),
        "calculator",
        _FILE_KEYS | {"program", "program_version"},
    )
    _keys(
        _mapping(payload, "parent_scf"),
        "parent_scf",
        {
            "output_directory",
            "saved_state_root",
            "manifest_path",
            "manifest_sha256",
            "manifest_byte_size",
            "calculation",
            "prefix",
        },
    )
    _keys(
        _mapping(payload, "pseudopotential"),
        "pseudopotential",
        _FILE_KEYS | {"symbol", "filename", "mass_amu"},
    )
    _keys(
        _mapping(payload, "sampling"),
        "sampling",
        {
            "kpoint_grid",
            "kpoint_offset",
            "band_count",
            "wavefunction_cutoff_ry",
            "electronic_tolerance_ry",
            "occupations",
        },
        {"charge_density_cutoff_ry"},
    )
    _keys(
        _mapping(payload, "qe"),
        "qe",
        {
            "prefix",
            "pseudo_dir",
            "outdir",
            "input_filename",
            "verbosity",
            "iprint",
            "diagonalization",
            "diago_full_acc",
            "disable_symmetry",
            "disable_time_reversal",
            "coordinate_precision",
            "kpoint_precision",
        },
    )
    _keys(_mapping(payload, "output"), "output", {"directory"})
    _keys(_mapping(payload, "qualification"), "qualification", {"statements"})
    if "reference_nscf" in payload:
        _keys(
            _mapping(payload, "reference_nscf"),
            "reference_nscf",
            {"output_directory"},
        )


_FILE_KEYS = {"path", "sha256", "byte_size"}


def _keys(
    mapping: dict[str, Any],
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    allowed = required | (set() if optional is None else optional)
    missing = required - mapping.keys()
    extra = mapping.keys() - allowed
    if missing or extra:
        raise ValueError(
            f"{label} schema mismatch; missing={sorted(missing)!r}, "
            f"extra={sorted(extra)!r}"
        )


def _mapping(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    if type(value) is not dict or any(type(item) is not str for item in value):
        raise ValueError(f"{key} must be a table")
    return value


def _file_resource(mapping: dict[str, Any]) -> QeNscfFileResource:
    return QeNscfFileResource(
        path=_string(mapping, "path"),
        sha256=_sha(mapping, "sha256"),
        byte_size=_integer(mapping, "byte_size"),
    )


def _string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{key} must be a nonempty stripped string")
    return value


def _sha(mapping: dict[str, Any], key: str) -> str:
    value = _string(mapping, key)
    if len(value) != 64 or any(item not in "0123456789abcdef" for item in value):
        raise ValueError(f"{key} must be lowercase SHA-256")
    return value


def _integer(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise ValueError(f"{key} must be an integer")
    return value


def _float(mapping: dict[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _optional_float(mapping: dict[str, Any], key: str) -> float | None:
    return None if key not in mapping else _float(mapping, key)


def _boolean(mapping: dict[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if type(value) is not bool:
        raise ValueError(f"{key} must be a boolean")
    return value


def _triplet(mapping: dict[str, Any], key: str) -> tuple[int, int, int]:
    value = mapping.get(key)
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(type(item) is not int for item in value)
    ):
        raise ValueError(f"{key} must contain three integers")
    return value[0], value[1], value[2]


def _strings(mapping: dict[str, Any], key: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if (
        not isinstance(value, list)
        or not value
        or any(
            type(item) is not str or not item or item != item.strip() for item in value
        )
    ):
        raise ValueError(f"{key} must contain nonempty stripped strings")
    return tuple(value)
