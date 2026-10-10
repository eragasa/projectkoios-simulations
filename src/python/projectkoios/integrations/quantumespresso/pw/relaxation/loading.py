"""Load closed-schema Quantum ESPRESSO relaxation calculation TOML."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDegreesOfFreedom,
    QeCellDynamics,
)
from projectkoios.integrations.quantumespresso.pw.inputfile.ions import (
    QeIonDynamics,
)

from .calculation import (
    FileIdentity,
    QeRelaxationCalculationConfiguration,
    QeRelaxationPhase,
    StructureIdentity,
)
from .options import (
    QeIonicRelaxationOptions,
    QeLatticeVectorRelaxationOptions,
)

_MAXIMUM_CONFIGURATION_BYTES = 100_000


@dataclass(frozen=True, slots=True)
class QeRelaxationCalculationTomlLoader:
    """Load one bounded QE relaxation calculation declaration."""

    def load(self, path: Path) -> QeRelaxationCalculationConfiguration:
        """Return a validated calculation configuration without resolving resources."""
        if not isinstance(path, Path):
            raise TypeError("path must be a Path")
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size > _MAXIMUM_CONFIGURATION_BYTES
        ):
            raise ValueError("configuration must be a bounded regular file")
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 2:
            raise ValueError("unsupported configuration schema")
        _validate_schema(payload)
        structure = _mapping(payload, "structure")
        calculator = _mapping(payload, "calculator")
        pseudopotential = _mapping(payload, "pseudopotential")
        sampling = _mapping(payload, "sampling")
        ionic = _mapping(payload, "ionic_relaxation")
        qe = _mapping(payload, "qe")
        qualification = _mapping(payload, "qualification")
        phase = _phase(payload)
        lattice = (
            None if phase == "relax" else _mapping(payload, "lattice_vector_relaxation")
        )
        return QeRelaxationCalculationConfiguration(
            calculation_id=_string(payload, "calculation_id"),
            phase=phase,
            integration_id=_string(payload, "integration_id"),
            energy_convergence_tolerance_mev_per_atom=_float(
                payload,
                "energy_convergence_tolerance_mev_per_atom",
            ),
            structure=StructureIdentity(
                repository_path=_string(structure, "repository_path"),
                structure_id=_string(structure, "structure_id"),
                byte_size=_integer(structure, "byte_size"),
                sha256=_sha_string(structure, "sha256"),
            ),
            calculator=FileIdentity(
                byte_size=_integer(calculator, "byte_size"),
                sha256=_sha_string(calculator, "sha256"),
            ),
            calculator_program=_string(calculator, "program"),
            calculator_version=_string(calculator, "program_version"),
            calculator_source_revision=_string(calculator, "source_revision"),
            pseudopotential=FileIdentity(
                byte_size=_integer(pseudopotential, "byte_size"),
                sha256=_sha_string(pseudopotential, "sha256"),
            ),
            pseudopotential_symbol=_string(pseudopotential, "symbol"),
            pseudopotential_filename=_string(pseudopotential, "filename"),
            pseudopotential_exchange_correlation=_string(
                pseudopotential,
                "exchange_correlation",
            ),
            pseudopotential_formalism=_string(pseudopotential, "formalism"),
            pseudopotential_relativistic_treatment=_string(
                pseudopotential,
                "relativistic_treatment",
            ),
            pseudopotential_upf_version=_string(
                pseudopotential,
                "upf_version",
            ),
            pseudopotential_valence_electrons=_integer(
                pseudopotential,
                "valence_electrons",
            ),
            pseudopotential_mass_amu=_float(pseudopotential, "mass_amu"),
            kpoint_mesh=_integer_triplet(sampling, "kpoint_mesh"),
            kpoint_shift=_integer_triplet(sampling, "kpoint_shift"),
            wavefunction_cutoff_ry=_float(sampling, "wavefunction_cutoff_ry"),
            charge_density_cutoff_ry=_float(sampling, "charge_density_cutoff_ry"),
            electronic_tolerance_ry=_float(sampling, "electronic_tolerance_ry"),
            electronic_atol_ry=_float(sampling, "electronic_atol_ry"),
            ionic_relaxation=QeIonicRelaxationOptions(
                dynamics=QeIonDynamics(_string(ionic, "dynamics")),
                maximum_steps=_integer(ionic, "maximum_steps"),
                total_energy_tolerance_ry=_float(
                    ionic,
                    "total_energy_tolerance_ry",
                ),
                force_tolerance_ry_per_bohr=_float(
                    ionic,
                    "force_tolerance_ry_per_bohr",
                ),
            ),
            lattice_vector_relaxation=(
                None
                if lattice is None
                else QeLatticeVectorRelaxationOptions(
                    dynamics=QeCellDynamics(_string(lattice, "dynamics")),
                    degrees_of_freedom=QeCellDegreesOfFreedom(
                        _string(lattice, "degrees_of_freedom")
                    ),
                    target_pressure_kbar=_float(lattice, "target_pressure_kbar"),
                    pressure_tolerance_kbar=_float(
                        lattice,
                        "pressure_tolerance_kbar",
                    ),
                )
            ),
            prefix=_string(qe, "prefix"),
            pseudo_dir=_string(qe, "pseudo_dir"),
            outdir=_string(qe, "outdir"),
            input_filename=_string(qe, "input_filename"),
            coordinate_precision=_integer(qe, "coordinate_precision"),
            qualification_statements=_string_tuple(qualification, "statements"),
        )


def _validate_schema(payload: dict[str, object]) -> None:
    phase = _phase(payload)
    _require_schema_keys(
        payload,
        "configuration",
        {
            "schema_version",
            "calculation_id",
            "phase",
            "integration_id",
            "energy_convergence_tolerance_mev_per_atom",
            "structure",
            "calculator",
            "pseudopotential",
            "sampling",
            "ionic_relaxation",
            "qe",
            "qualification",
        }
        | ({"lattice_vector_relaxation"} if phase == "vc-relax" else set()),
    )
    _require_schema_keys(
        _mapping(payload, "structure"),
        "structure",
        {"repository_path", "structure_id", "byte_size", "sha256"},
    )
    _require_schema_keys(
        _mapping(payload, "calculator"),
        "calculator",
        {
            "program",
            "program_version",
            "byte_size",
            "sha256",
            "source_revision",
        },
    )
    _require_schema_keys(
        _mapping(payload, "pseudopotential"),
        "pseudopotential",
        {
            "symbol",
            "filename",
            "byte_size",
            "sha256",
            "exchange_correlation",
            "formalism",
            "relativistic_treatment",
            "upf_version",
            "valence_electrons",
            "mass_amu",
        },
    )
    _require_schema_keys(
        _mapping(payload, "sampling"),
        "sampling",
        {
            "kpoint_mesh",
            "kpoint_shift",
            "wavefunction_cutoff_ry",
            "charge_density_cutoff_ry",
            "electronic_tolerance_ry",
            "electronic_atol_ry",
        },
    )
    _require_schema_keys(
        _mapping(payload, "ionic_relaxation"),
        "ionic_relaxation",
        {
            "dynamics",
            "maximum_steps",
            "total_energy_tolerance_ry",
            "force_tolerance_ry_per_bohr",
        },
    )
    if phase == "vc-relax":
        _require_schema_keys(
            _mapping(payload, "lattice_vector_relaxation"),
            "lattice_vector_relaxation",
            {
                "dynamics",
                "degrees_of_freedom",
                "target_pressure_kbar",
                "pressure_tolerance_kbar",
            },
        )
    _require_schema_keys(
        _mapping(payload, "qe"),
        "qe",
        {"prefix", "pseudo_dir", "outdir", "input_filename", "coordinate_precision"},
    )
    _require_schema_keys(
        _mapping(payload, "qualification"),
        "qualification",
        {"statements"},
    )


def _require_schema_keys(
    mapping: dict[str, object],
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


def _mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a table")
    return value


def _string(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{key} must be a nonempty stripped string")
    return value


def _phase(mapping: dict[str, object]) -> QeRelaxationPhase:
    value = _string(mapping, "phase")
    if value not in ("relax", "vc-relax"):
        raise ValueError("phase must be relax or vc-relax")
    return cast(QeRelaxationPhase, value)


def _sha_string(mapping: dict[str, object], key: str) -> str:
    value = _string(mapping, key)
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{key} must be lowercase SHA-256")
    return value


def _integer(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise ValueError(f"{key} must be an integer")
    return value


def _float(mapping: dict[str, object], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _integer_triplet(mapping: dict[str, object], key: str) -> tuple[int, int, int]:
    value = mapping.get(key)
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(type(item) is not int for item in value)
    ):
        raise ValueError(f"{key} must contain three integers")
    return value[0], value[1], value[2]


def _string_tuple(mapping: dict[str, object], key: str) -> tuple[str, ...]:
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
