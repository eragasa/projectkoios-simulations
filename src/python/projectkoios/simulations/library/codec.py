"""Strict canonical JSON codec for version-one simulation specifications."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, cast

from projectkoios.simulations.calculator_input import CalculatorInputSourceReference
from projectkoios.simulations.dft.electronic import (
    DftChargeState,
    DftExchangeCorrelationIdentifierScheme,
    DftExchangeCorrelationModel,
    DftOccupationMethod,
    DftOccupationPolicy,
    DftSpinMode,
    DftSpinTreatment,
    PwDftElectronicConvergencePolicy,
)
from projectkoios.simulations.dft.pseudopotential import (
    Pseudopotential,
    PseudopotentialArtifactFormat,
    PseudopotentialFile,
)
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftCellRelaxationMode,
    PwDftRelaxationConvergencePolicy,
    PwDftRelaxationDegreesOfFreedom,
    PwDftRelaxationInitialization,
)
from projectkoios.simulations.dft.pw.relaxation.specification import (
    PwDftRelaxationSpecification,
)
from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification
from projectkoios.simulations.dft.pw.settings import PwDftKPointSamplingPolicy
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation
from projectkoios.simulations.library.record import SimulationRepresentation
from projectkoios.simulations.structure.library import (
    DerivedStructureProvenance,
    ObservedStructureProvenance,
    ObservedStructureScope,
    StructureProvenanceReference,
    StructureRecord,
    StructureRecordReference,
    StructureRepresentation,
    TransferredStructureProvenance,
)

type SimulationSpecification = PwDftScfSpecification | PwDftRelaxationSpecification


class SimulationSerializationError(ValueError):
    """Report malformed, unsupported, or noncanonical specification bytes."""


def simulation_source_reference(
    specification: SimulationSpecification,
) -> CalculatorInputSourceReference:
    """Return the exact canonical specification identity used by prepared inputs."""
    content = SimulationJsonCodec().dumps(specification)
    representation = {
        PwDftScfSpecification: SimulationRepresentation.PW_DFT_SCF,
        PwDftRelaxationSpecification: SimulationRepresentation.PW_DFT_RELAXATION,
    }.get(type(specification))
    if representation is None:
        raise TypeError("specification must be an exact supported type")
    # Prepared inputs refer to canonical specification bytes, never the request
    # envelope, so evaluation IDs cannot accidentally alter scientific identity.
    return CalculatorInputSourceReference(
        simulation_id=specification.simulation_id,
        representation=f"projectkoios.{representation.value}+json",
        schema_version=1,
        byte_size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
    )


class SimulationJsonCodec:
    """Encode and strictly decode canonical version-one specification JSON."""

    def dumps(self, specification: SimulationSpecification) -> bytes:
        """Return canonical UTF-8 bytes terminated by one newline."""
        if type(specification) is PwDftScfSpecification:
            payload = _encode_scf(specification)
        elif type(specification) is PwDftRelaxationSpecification:
            payload = _encode_relaxation(specification)
        else:
            raise TypeError("specification must be an exact supported type")
        return (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

    def loads(self, content: bytes) -> SimulationSpecification:
        """Decode only bytes already in the one accepted canonical form."""
        if type(content) is not bytes or not content:
            raise SimulationSerializationError("content must be nonempty bytes")
        try:
            text = content.decode("utf-8")
            raw = json.loads(
                text,
                object_pairs_hook=_unique_object,
                parse_constant=_reject_nonfinite,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise SimulationSerializationError("invalid simulation JSON") from error
        if type(raw) is not dict:
            raise SimulationSerializationError("simulation document must be an object")
        table = cast(dict[str, Any], raw)
        try:
            representation = SimulationRepresentation(_string(table["representation"]))
            specification: SimulationSpecification
            if representation is SimulationRepresentation.PW_DFT_SCF:
                specification = _decode_scf(table)
            else:
                specification = _decode_relaxation(table)
        except (KeyError, TypeError, ValueError) as error:
            raise SimulationSerializationError(
                "invalid simulation specification"
            ) from error
        # Re-encoding is the definitive lexical gate. It rejects whitespace,
        # alternate number spellings, key order, and any otherwise equivalent JSON.
        if self.dumps(specification) != content:
            raise SimulationSerializationError("simulation JSON is not canonical")
        return specification


def _encode_scf(value: PwDftScfSpecification) -> dict[str, Any]:
    return {
        "electronic_convergence": _encode_electronic_convergence(
            value.electronic_convergence
        ),
        "kpoint_sampling": _encode_kpoints(value.kpoint_sampling),
        "occupation": _encode_occupation(value.occupation),
        "representation": SimulationRepresentation.PW_DFT_SCF.value,
        "schema_version": 1,
        "simulation": _encode_simulation(value.simulation),
        "simulation_id": value.simulation_id,
        "wavefunction_cutoff_ev": value.wavefunction_cutoff_ev,
    }


def _decode_scf(raw: dict[str, Any]) -> PwDftScfSpecification:
    _keys(
        raw,
        {
            "electronic_convergence",
            "kpoint_sampling",
            "occupation",
            "representation",
            "schema_version",
            "simulation",
            "simulation_id",
            "wavefunction_cutoff_ev",
        },
    )
    _version(raw)
    return PwDftScfSpecification(
        simulation_id=_string(raw["simulation_id"]),
        simulation=_decode_simulation(_object(raw["simulation"])),
        kpoint_sampling=_decode_kpoints(_object(raw["kpoint_sampling"])),
        wavefunction_cutoff_ev=_float(raw["wavefunction_cutoff_ev"]),
        occupation=_decode_occupation(_object(raw["occupation"])),
        electronic_convergence=_decode_electronic_convergence(
            _object(raw["electronic_convergence"])
        ),
    )


def _encode_relaxation(value: PwDftRelaxationSpecification) -> dict[str, Any]:
    return {
        "degrees_of_freedom": {
            "cell_mode": value.degrees_of_freedom.cell_mode.value,
            "relax_atomic_positions": value.degrees_of_freedom.relax_atomic_positions,
            "selected_strain_components": (
                None
                if value.degrees_of_freedom.selected_strain_components is None
                else list(value.degrees_of_freedom.selected_strain_components)
            ),
        },
        "electronic_convergence": _encode_electronic_convergence(
            value.electronic_convergence
        ),
        "initialization": value.initialization.value,
        "ionic_convergence": asdict(value.ionic_convergence),
        "kpoint_sampling": _encode_kpoints(value.kpoint_sampling),
        "occupation": _encode_occupation(value.occupation),
        "representation": SimulationRepresentation.PW_DFT_RELAXATION.value,
        "schema_version": 1,
        "simulation": _encode_simulation(value.simulation),
        "simulation_id": value.simulation_id,
        "wavefunction_cutoff_ev": value.wavefunction_cutoff_ev,
    }


def _decode_relaxation(raw: dict[str, Any]) -> PwDftRelaxationSpecification:
    _keys(
        raw,
        {
            "degrees_of_freedom",
            "electronic_convergence",
            "initialization",
            "ionic_convergence",
            "kpoint_sampling",
            "occupation",
            "representation",
            "schema_version",
            "simulation",
            "simulation_id",
            "wavefunction_cutoff_ev",
        },
    )
    _version(raw)
    degrees = _object(raw["degrees_of_freedom"])
    _keys(
        degrees,
        {"cell_mode", "relax_atomic_positions", "selected_strain_components"},
    )
    raw_mask = degrees["selected_strain_components"]
    mask = None if raw_mask is None else tuple(_bool(v) for v in _array(raw_mask))
    convergence = _object(raw["ionic_convergence"])
    _keys(
        convergence,
        {
            "force_tolerance_ev_per_angstrom",
            "maximum_ionic_steps",
            "pressure_tolerance_kbar",
            "target_pressure_kbar",
            "total_energy_tolerance_ev",
        },
    )
    return PwDftRelaxationSpecification(
        simulation_id=_string(raw["simulation_id"]),
        simulation=_decode_simulation(_object(raw["simulation"])),
        kpoint_sampling=_decode_kpoints(_object(raw["kpoint_sampling"])),
        wavefunction_cutoff_ev=_float(raw["wavefunction_cutoff_ev"]),
        occupation=_decode_occupation(_object(raw["occupation"])),
        electronic_convergence=_decode_electronic_convergence(
            _object(raw["electronic_convergence"])
        ),
        initialization=PwDftRelaxationInitialization(_string(raw["initialization"])),
        degrees_of_freedom=PwDftRelaxationDegreesOfFreedom(
            relax_atomic_positions=_bool(degrees["relax_atomic_positions"]),
            cell_mode=PwDftCellRelaxationMode(_string(degrees["cell_mode"])),
            selected_strain_components=cast(
                tuple[bool, bool, bool, bool, bool, bool] | None,
                mask,
            ),
        ),
        ionic_convergence=PwDftRelaxationConvergencePolicy(
            maximum_ionic_steps=_int(convergence["maximum_ionic_steps"]),
            total_energy_tolerance_ev=_float(convergence["total_energy_tolerance_ev"]),
            force_tolerance_ev_per_angstrom=_float(
                convergence["force_tolerance_ev_per_angstrom"]
            ),
            target_pressure_kbar=_optional_float(convergence["target_pressure_kbar"]),
            pressure_tolerance_kbar=_optional_float(
                convergence["pressure_tolerance_kbar"]
            ),
        ),
    )


def _encode_simulation(value: PwDftSimulation) -> dict[str, Any]:
    return {
        "charge": {
            "charge_state": value.charge.charge_state,
            "delta_n_electrons": value.charge.delta_n_electrons,
        },
        "exchange_correlation": {
            "identifier": value.exchange_correlation.identifier,
            "identifier_scheme": value.exchange_correlation.identifier_scheme.value,
            "pseudopotential_compatibility_label": (
                value.exchange_correlation.pseudopotential_compatibility_label
            ),
        },
        "pseudopotentials": [
            _encode_pseudopotential(v) for v in value.pseudopotentials
        ],
        "spin": {
            "constrain_spin_channel_difference": (
                value.spin.constrain_spin_channel_difference
            ),
            "initial_site_magnetic_moment_vectors_mu_b": [
                list(vector)
                for vector in value.spin.initial_site_magnetic_moment_vectors_mu_b
            ],
            "initial_site_magnetic_moments_mu_b": list(
                value.spin.initial_site_magnetic_moments_mu_b
            ),
            "mode": value.spin.mode.value,
            "spin_quantization_axis": (
                None
                if value.spin.spin_quantization_axis is None
                else list(value.spin.spin_quantization_axis)
            ),
            "spin_channel_electron_difference": (
                value.spin.spin_channel_electron_difference
            ),
        },
        "structure": _encode_structure_record(value.structure),
    }


def _decode_simulation(raw: dict[str, Any]) -> PwDftSimulation:
    _keys(
        raw, {"charge", "exchange_correlation", "pseudopotentials", "spin", "structure"}
    )
    charge = _object(raw["charge"])
    _keys(charge, {"charge_state", "delta_n_electrons"})
    xc = _object(raw["exchange_correlation"])
    _keys(
        xc, {"identifier", "identifier_scheme", "pseudopotential_compatibility_label"}
    )
    spin = _object(raw["spin"])
    _keys(
        spin,
        {
            "constrain_spin_channel_difference",
            "initial_site_magnetic_moment_vectors_mu_b",
            "initial_site_magnetic_moments_mu_b",
            "mode",
            "spin_quantization_axis",
            "spin_channel_electron_difference",
        },
    )
    axis_raw = spin["spin_quantization_axis"]
    return PwDftSimulation(
        structure=_decode_structure_record(_object(raw["structure"])),
        exchange_correlation=DftExchangeCorrelationModel(
            identifier_scheme=DftExchangeCorrelationIdentifierScheme(
                _string(xc["identifier_scheme"])
            ),
            identifier=_string(xc["identifier"]),
            pseudopotential_compatibility_label=_string(
                xc["pseudopotential_compatibility_label"]
            ),
        ),
        charge=DftChargeState(
            delta_n_electrons=_int(charge["delta_n_electrons"]),
            charge_state=_int(charge["charge_state"]),
        ),
        spin=DftSpinTreatment(
            mode=DftSpinMode(_string(spin["mode"])),
            spin_channel_electron_difference=_int(
                spin["spin_channel_electron_difference"]
            ),
            constrain_spin_channel_difference=_bool(
                spin["constrain_spin_channel_difference"]
            ),
            initial_site_magnetic_moments_mu_b=tuple(
                _float(v) for v in _array(spin["initial_site_magnetic_moments_mu_b"])
            ),
            initial_site_magnetic_moment_vectors_mu_b=tuple(
                cast(
                    tuple[float, float, float], tuple(_float(v) for v in _array(vector))
                )
                for vector in _array(spin["initial_site_magnetic_moment_vectors_mu_b"])
            ),
            spin_quantization_axis=(
                None
                if axis_raw is None
                else cast(
                    tuple[float, float, float],
                    tuple(_float(v) for v in _array(axis_raw)),
                )
            ),
        ),
        pseudopotentials=tuple(
            _decode_pseudopotential(_object(v)) for v in _array(raw["pseudopotentials"])
        ),
    )


def _encode_kpoints(value: PwDftKPointSamplingPolicy) -> dict[str, Any]:
    return {
        "mesh": list(value.mesh),
        "shift": list(value.shift),
        "use_spatial_symmetry": value.use_spatial_symmetry,
        "use_time_reversal": value.use_time_reversal,
    }


def _decode_kpoints(raw: dict[str, Any]) -> PwDftKPointSamplingPolicy:
    _keys(raw, {"mesh", "shift", "use_spatial_symmetry", "use_time_reversal"})
    return PwDftKPointSamplingPolicy(
        mesh=cast(tuple[int, int, int], tuple(_int(v) for v in _array(raw["mesh"]))),
        shift=cast(tuple[int, int, int], tuple(_int(v) for v in _array(raw["shift"]))),
        use_spatial_symmetry=_bool(raw["use_spatial_symmetry"]),
        use_time_reversal=_bool(raw["use_time_reversal"]),
    )


def _encode_occupation(value: DftOccupationPolicy) -> dict[str, Any]:
    return {
        "method": value.method.value,
        "methfessel_paxton_order": value.methfessel_paxton_order,
        "smearing_width_ev": value.smearing_width_ev,
    }


def _decode_occupation(raw: dict[str, Any]) -> DftOccupationPolicy:
    _keys(raw, {"method", "methfessel_paxton_order", "smearing_width_ev"})
    raw_order = raw["methfessel_paxton_order"]
    return DftOccupationPolicy(
        method=DftOccupationMethod(_string(raw["method"])),
        smearing_width_ev=_optional_float(raw["smearing_width_ev"]),
        methfessel_paxton_order=None if raw_order is None else _int(raw_order),
    )


def _encode_electronic_convergence(
    value: PwDftElectronicConvergencePolicy,
) -> dict[str, Any]:
    return {
        "energy_tolerance_ev": value.energy_tolerance_ev,
        "maximum_electronic_iterations": value.maximum_electronic_iterations,
    }


def _decode_electronic_convergence(
    raw: dict[str, Any],
) -> PwDftElectronicConvergencePolicy:
    _keys(raw, {"energy_tolerance_ev", "maximum_electronic_iterations"})
    return PwDftElectronicConvergencePolicy(
        energy_tolerance_ev=_float(raw["energy_tolerance_ev"]),
        maximum_electronic_iterations=_int(raw["maximum_electronic_iterations"]),
    )


def _encode_pseudopotential(value: PseudopotentialFile) -> dict[str, Any]:
    pseudopotential = value.pseudopotential
    return {
        "artifact_format": value.artifact_format.value,
        "byte_size": value.byte_size,
        "filename": value.filename,
        "artifact_format_version": value.artifact_format_version,
        "pseudopotential": {
            "exchange_correlation": pseudopotential.exchange_correlation,
            "formalism": pseudopotential.formalism,
            "relativistic_treatment": pseudopotential.relativistic_treatment,
            "symbol": pseudopotential.symbol,
            "valence_electrons": pseudopotential.valence_electrons,
        },
        "sha256": value.sha256,
        "symbol": value.symbol,
    }


def _decode_pseudopotential(raw: dict[str, Any]) -> PseudopotentialFile:
    _keys(
        raw,
        {
            "artifact_format",
            "byte_size",
            "filename",
            "artifact_format_version",
            "pseudopotential",
            "sha256",
            "symbol",
        },
    )
    pseudo = _object(raw["pseudopotential"])
    _keys(
        pseudo,
        {
            "exchange_correlation",
            "formalism",
            "relativistic_treatment",
            "symbol",
            "valence_electrons",
        },
    )
    result = PseudopotentialFile(
        filename=_string(raw["filename"]),
        byte_size=_int(raw["byte_size"]),
        sha256=_string(raw["sha256"]),
        artifact_format=PseudopotentialArtifactFormat(_string(raw["artifact_format"])),
        artifact_format_version=_optional_string(raw["artifact_format_version"]),
        pseudopotential=Pseudopotential(
            symbol=_string(pseudo["symbol"]),
            exchange_correlation=_string(pseudo["exchange_correlation"]),
            formalism=_string(pseudo["formalism"]),
            relativistic_treatment=_string(pseudo["relativistic_treatment"]),
            valence_electrons=_int(pseudo["valence_electrons"]),
        ),
    )
    # Retain the convenient top-level symbol but reject documents in which it
    # disagrees with the scientific pseudopotential payload.
    if result.symbol != _string(raw["symbol"]):
        raise ValueError("pseudopotential symbols must agree")
    return result


def _encode_structure_record(value: StructureRecord) -> dict[str, Any]:
    provenance = value.provenance
    if type(provenance) is TransferredStructureProvenance:
        encoded_provenance: dict[str, Any] = {
            "kind": "transferred",
            "record_path": provenance.record_path,
            "result_sha256": provenance.result_sha256,
            "revision": provenance.revision,
            "source": provenance.source,
            "source_sha256": provenance.source_sha256,
        }
    elif type(provenance) is DerivedStructureProvenance:
        encoded_provenance = {
            "kind": "derived",
            "operation_id": provenance.operation_id,
            "operation_version": provenance.operation_version,
            "parameters_json": provenance.parameters_json,
            "parameters_sha256": provenance.parameters_sha256,
            "parents": [_encode_structure_reference(v) for v in provenance.parents],
            "result_sha256": provenance.result_sha256,
        }
    elif type(provenance) is ObservedStructureProvenance:
        encoded_provenance = {
            "kind": "observed",
            "publication_operation": provenance.publication_operation,
            "publication_version": provenance.publication_version,
            "relaxation_calculation": _encode_structure_provenance_reference(
                provenance.relaxation_calculation
            ),
            "relaxation_evidence": _encode_structure_provenance_reference(
                provenance.relaxation_evidence
            ),
            "result_sha256": provenance.result_sha256,
            "scope": provenance.scope.value,
            "starting_structure": _encode_structure_reference(
                provenance.starting_structure
            ),
        }
    else:
        raise TypeError("unsupported structure provenance")
    return {
        "byte_size": value.byte_size,
        "provenance": encoded_provenance,
        "representation": value.representation.value,
        "schema_version": value.schema_version,
        "sha256": value.sha256,
        "structure_id": value.structure_id,
    }


def _decode_structure_record(raw: dict[str, Any]) -> StructureRecord:
    _keys(
        raw,
        {
            "byte_size",
            "provenance",
            "representation",
            "schema_version",
            "sha256",
            "structure_id",
        },
    )
    provenance_raw = _object(raw["provenance"])
    kind = _string(provenance_raw["kind"])
    decoded_provenance: (
        TransferredStructureProvenance
        | DerivedStructureProvenance
        | ObservedStructureProvenance
    )
    if kind == "transferred":
        _keys(
            provenance_raw,
            {
                "kind",
                "record_path",
                "result_sha256",
                "revision",
                "source",
                "source_sha256",
            },
        )
        decoded_provenance = TransferredStructureProvenance(
            source=_string(provenance_raw["source"]),
            revision=_string(provenance_raw["revision"]),
            record_path=_string(provenance_raw["record_path"]),
            source_sha256=_string(provenance_raw["source_sha256"]),
            result_sha256=_string(provenance_raw["result_sha256"]),
        )
    elif kind == "derived":
        _keys(
            provenance_raw,
            {
                "kind",
                "operation_id",
                "operation_version",
                "parameters_json",
                "parameters_sha256",
                "parents",
                "result_sha256",
            },
        )
        decoded_provenance = DerivedStructureProvenance(
            operation_id=_string(provenance_raw["operation_id"]),
            operation_version=_string(provenance_raw["operation_version"]),
            parents=tuple(
                _decode_structure_reference(_object(v))
                for v in _array(provenance_raw["parents"])
            ),
            parameters_json=_string(provenance_raw["parameters_json"]),
            parameters_sha256=_string(provenance_raw["parameters_sha256"]),
            result_sha256=_string(provenance_raw["result_sha256"]),
        )
    elif kind == "observed":
        _keys(
            provenance_raw,
            {
                "kind",
                "publication_operation",
                "publication_version",
                "relaxation_calculation",
                "relaxation_evidence",
                "result_sha256",
                "scope",
                "starting_structure",
            },
        )
        decoded_provenance = ObservedStructureProvenance(
            starting_structure=_decode_structure_reference(
                _object(provenance_raw["starting_structure"])
            ),
            relaxation_calculation=_decode_structure_provenance_reference(
                _object(provenance_raw["relaxation_calculation"])
            ),
            relaxation_evidence=_decode_structure_provenance_reference(
                _object(provenance_raw["relaxation_evidence"])
            ),
            scope=ObservedStructureScope(_string(provenance_raw["scope"])),
            publication_operation=_string(provenance_raw["publication_operation"]),
            publication_version=_string(provenance_raw["publication_version"]),
            result_sha256=_string(provenance_raw["result_sha256"]),
        )
    else:
        raise ValueError("unknown structure provenance kind")
    return StructureRecord(
        structure_id=_string(raw["structure_id"]),
        representation=StructureRepresentation(_string(raw["representation"])),
        schema_version=_int(raw["schema_version"]),
        byte_size=_int(raw["byte_size"]),
        sha256=_string(raw["sha256"]),
        provenance=decoded_provenance,
    )


def _encode_structure_reference(value: StructureRecordReference) -> dict[str, Any]:
    return {
        "byte_size": value.byte_size,
        "representation": value.representation.value,
        "schema_version": value.schema_version,
        "sha256": value.sha256,
        "structure_id": value.structure_id,
    }


def _decode_structure_reference(raw: dict[str, Any]) -> StructureRecordReference:
    _keys(
        raw,
        {"byte_size", "representation", "schema_version", "sha256", "structure_id"},
    )
    return StructureRecordReference(
        structure_id=_string(raw["structure_id"]),
        representation=StructureRepresentation(_string(raw["representation"])),
        schema_version=_int(raw["schema_version"]),
        byte_size=_int(raw["byte_size"]),
        sha256=_string(raw["sha256"]),
    )


def _encode_structure_provenance_reference(
    value: StructureProvenanceReference,
) -> dict[str, Any]:
    return {
        "byte_size": value.byte_size,
        "representation": value.representation,
        "schema_version": value.schema_version,
        "sha256": value.sha256,
        "stable_id": value.stable_id,
    }


def _decode_structure_provenance_reference(
    raw: dict[str, Any],
) -> StructureProvenanceReference:
    _keys(
        raw,
        {"byte_size", "representation", "schema_version", "sha256", "stable_id"},
    )
    return StructureProvenanceReference(
        stable_id=_string(raw["stable_id"]),
        representation=_string(raw["representation"]),
        schema_version=_int(raw["schema_version"]),
        byte_size=_int(raw["byte_size"]),
        sha256=_string(raw["sha256"]),
    )


def _version(raw: dict[str, Any]) -> None:
    if _int(raw["schema_version"]) != 1:
        raise ValueError("schema_version must be one")


def _keys(raw: dict[str, Any], expected: set[str]) -> None:
    if set(raw) != expected:
        raise ValueError("object keys do not match version-one schema")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> object:
    raise ValueError(f"nonfinite JSON constant is forbidden: {value}")


def _object(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError("value must be an object")
    return cast(dict[str, Any], value)


def _array(value: Any) -> list[Any]:
    if type(value) is not list:
        raise TypeError("value must be an array")
    return value


def _string(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("value must be a string")
    return value


def _optional_string(value: Any) -> str | None:
    return None if value is None else _string(value)


def _bool(value: Any) -> bool:
    if type(value) is not bool:
        raise TypeError("value must be a boolean")
    return value


def _int(value: Any) -> int:
    if type(value) is not int:
        raise TypeError("value must be an integer")
    return value


def _float(value: Any) -> float:
    if type(value) is not float:
        raise TypeError("value must be a JSON floating-point number")
    if value == 0.0 and str(value).startswith("-"):
        raise ValueError("negative zero is not canonical")
    return value


def _optional_float(value: Any) -> float | None:
    return None if value is None else _float(value)
