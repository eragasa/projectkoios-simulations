"""Materials Project structure and elemental convex-hull integration."""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

import numpy as np
from monty.json import MontyEncoder
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Structure
from pymatgen.entries.computed_entries import ComputedEntry

from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    ConventionalUnitCell,
    PrimitiveUnitCell,
    UnitCell,
    UnitCellJsonCodec,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)

__all__ = (
    "MaterialsProjectCandidateSnapshot",
    "MaterialsProjectClient",
    "MaterialsProjectElementalReference",
    "MaterialsProjectElementalReferenceRequest",
    "MaterialsProjectElementalReferenceSelector",
    "MaterialsProjectQuerySnapshot",
    "MaterialsProjectStructureAdapter",
    "MaterialsProjectStructureReference",
    "MaterialsProjectStructureRequest",
    "MaterialsProjectStructureRetriever",
)


@runtime_checkable
class MaterialsProjectClient(Protocol):
    """Minimum injected MPRester behavior used by this integration."""

    def get_entries_in_chemsys(
        self,
        elements: list[str],
        additional_criteria: dict[str, list[str]],
    ) -> list[ComputedEntry]:
        """Return compatible entries for an explicit chemical system."""
        ...

    def get_structure_by_material_id(
        self,
        material_id: str,
        final: bool = True,
        conventional_unit_cell: bool = False,
    ) -> Structure | list[Structure]:
        """Return one final structure for an explicit Materials Project identity."""
        ...


@dataclass(frozen=True, slots=True)
class MaterialsProjectStructureRequest:
    """Request one exact Materials Project structure identity."""

    material_id: str
    conventional_unit_cell: bool = False

    def __post_init__(self) -> None:
        if type(self.material_id) is not str:
            raise TypeError("material_id must be a string")
        if re.fullmatch(r"mp-[1-9][0-9]*", self.material_id) is None:
            raise ValueError("material_id must have canonical mp-N form")
        if type(self.conventional_unit_cell) is not bool:
            raise TypeError("conventional_unit_cell must be a bool")


@dataclass(frozen=True, slots=True)
class MaterialsProjectStructureReference:
    """Retain an immutable neutral cell copied from one external MP response."""

    material_id: str
    source_url: str
    database_name: str
    geometry_status: str
    unit_cell: UnitCell
    structure_id: str
    representation: str
    schema_version: int
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        MaterialsProjectStructureRequest(self.material_id)
        for name, value in (
            ("source_url", self.source_url),
            ("database_name", self.database_name),
            ("geometry_status", self.geometry_status),
        ):
            if type(value) is not str:
                raise TypeError(f"{name} must be a string")
            if not value or value != value.strip():
                raise ValueError(f"{name} must be nonempty and stripped")
        if type(self.unit_cell) not in {PrimitiveUnitCell, ConventionalUnitCell}:
            raise TypeError(
                "unit_cell must be an exact PrimitiveUnitCell or ConventionalUnitCell"
            )
        if type(self.structure_id) is not str or not self.structure_id:
            raise ValueError("structure_id must be nonempty")
        expected_representation = (
            "conventional"
            if type(self.unit_cell) is ConventionalUnitCell
            else "primitive"
        )
        if self.representation != expected_representation:
            raise ValueError("representation must match the exact unit-cell type")
        if self.schema_version != 1:
            raise ValueError("schema_version must be one")
        content = (
            UnitCellJsonCodec()
            .dumps(
                self.unit_cell,
                structure_id=self.structure_id,
            )
            .encode("utf-8")
        )
        if self.byte_size != len(content):
            raise ValueError("structure byte_size must match canonical content")
        if self.sha256 != hashlib.sha256(content).hexdigest():
            raise ValueError("structure SHA-256 must match canonical content")


@dataclass(frozen=True, slots=True)
class MaterialsProjectStructureAdapter:
    """Copy a mutable ordered pymatgen structure into an immutable neutral cell."""

    def action(
        self,
        *,
        request: MaterialsProjectStructureRequest,
        source: Structure,
    ) -> MaterialsProjectStructureReference:
        """Adapt angstrom lattice vectors and fractional sites without aliasing."""
        if type(request) is not MaterialsProjectStructureRequest:
            raise TypeError("request must be a MaterialsProjectStructureRequest")
        if type(source) is not Structure:
            raise TypeError("source must be a pymatgen Structure")
        atoms: list[Atom] = []
        for source_site in source:
            if not source_site.is_ordered:
                raise ValueError("disordered Materials Project sites are unsupported")
            coordinates = np.asarray(source_site.frac_coords, dtype=np.float64).copy()
            if coordinates.shape != (3,) or not np.all(np.isfinite(coordinates)):
                raise ValueError(
                    "pymatgen fractional coordinates must be three finite values"
                )
            # IEEE signed zero carries no structural meaning but would create
            # different canonical bytes for identical fractional coordinates.
            coordinates[coordinates == 0.0] = 0.0
            atoms.append(
                Atom(
                    symbol=source_site.specie.symbol,
                    position_fractional=VectorQuantity(
                        magnitude=coordinates.copy(),
                        unit=Unitless(),
                    ),
                )
            )
        matrix = np.asarray(source.lattice.matrix, dtype=np.float64).copy()
        if matrix.shape != (3, 3) or not np.all(np.isfinite(matrix)):
            raise ValueError(
                "pymatgen lattice matrix must be three by three and finite"
            )
        # Normalize signed zero before PhysKit canonical serialization for the
        # same exact-identity reason as fractional coordinates above.
        matrix[matrix == 0.0] = 0.0
        cell_type: type[UnitCell] = (
            ConventionalUnitCell
            if request.conventional_unit_cell
            else PrimitiveUnitCell
        )
        unit_cell = cell_type(
            direct_lattice=DirectLattice3D(
                a1=matrix[0].copy(),
                a2=matrix[1].copy(),
                a3=matrix[2].copy(),
            ),
            lattice_parameter=ScalarQuantity(1.0, PhysicalUnit("angstrom")),
            atomic_basis=AtomicBasis(atoms=tuple(atoms)),
        )
        structure_id = (
            f"materials-project.{request.material_id}."
            f"{'conventional' if request.conventional_unit_cell else 'primitive'}"
        )
        structure_content = (
            UnitCellJsonCodec()
            .dumps(
                unit_cell,
                structure_id=structure_id,
            )
            .encode("utf-8")
        )
        return MaterialsProjectStructureReference(
            material_id=request.material_id,
            source_url=(
                f"https://materialsproject.org/materials/{request.material_id}"
            ),
            database_name="Materials Project",
            geometry_status="external_reference_not_calculation_input",
            unit_cell=unit_cell,
            structure_id=structure_id,
            representation=(
                "conventional" if request.conventional_unit_cell else "primitive"
            ),
            schema_version=1,
            byte_size=len(structure_content),
            sha256=hashlib.sha256(structure_content).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class MaterialsProjectStructureRetriever:
    """Retrieve one explicit structure through an injected MPRester client."""

    def action(
        self,
        *,
        client: MaterialsProjectClient,
        request: MaterialsProjectStructureRequest,
    ) -> MaterialsProjectStructureReference:
        """Retrieve and immediately copy one final ordered structure."""
        if not isinstance(client, MaterialsProjectClient):
            raise TypeError("client must implement MaterialsProjectClient")
        if type(request) is not MaterialsProjectStructureRequest:
            raise TypeError("request must be a MaterialsProjectStructureRequest")
        source = client.get_structure_by_material_id(
            request.material_id,
            final=True,
            conventional_unit_cell=request.conventional_unit_cell,
        )
        if type(source) is not Structure:
            raise ValueError("MPRester must return exactly one final Structure")
        return MaterialsProjectStructureAdapter().action(
            request=request,
            source=source,
        )


@dataclass(frozen=True, slots=True)
class MaterialsProjectElementalReferenceRequest:
    """Declare one element and exact MP thermodynamic compatibility scheme."""

    element_symbol: str
    thermo_types: tuple[str, ...]
    conventional_unit_cell: bool = False

    def __post_init__(self) -> None:
        if type(self.element_symbol) is not str:
            raise TypeError("element_symbol must be a string")
        try:
            element = Element(self.element_symbol)
        except ValueError as error:
            raise ValueError(
                "element_symbol must identify a chemical element"
            ) from error
        if element.symbol != self.element_symbol:
            raise ValueError("element_symbol must use canonical capitalization")
        if type(self.thermo_types) is not tuple or not self.thermo_types:
            raise TypeError("thermo_types must be a nonempty tuple")
        if any(
            type(value) is not str or not value or value != value.strip()
            for value in self.thermo_types
        ):
            raise ValueError("thermo_types must contain nonempty stripped strings")
        if len(self.thermo_types) != len(set(self.thermo_types)):
            raise ValueError("thermo_types must be unique")
        if type(self.conventional_unit_cell) is not bool:
            raise TypeError("conventional_unit_cell must be a bool")


@dataclass(frozen=True, slots=True)
class MaterialsProjectCandidateSnapshot:
    """Retain one canonical candidate entry exactly as received for selection."""

    material_id: str
    canonical_json: str
    byte_size: int
    sha256: str

    def __post_init__(self) -> None:
        MaterialsProjectStructureRequest(self.material_id)
        if type(self.canonical_json) is not str or not self.canonical_json:
            raise ValueError("canonical_json must be a nonempty string")
        canonical_bytes = self.canonical_json.encode("utf-8")
        if type(self.byte_size) is not int or self.byte_size != len(canonical_bytes):
            raise ValueError("candidate byte_size must match canonical_json")
        if (
            type(self.sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.sha256) is None
            or hashlib.sha256(canonical_bytes).hexdigest() != self.sha256
        ):
            raise ValueError("candidate SHA-256 must match canonical_json")


@dataclass(frozen=True, slots=True)
class MaterialsProjectQuerySnapshot:
    """Retain query identity and the complete canonical candidate response."""

    element_symbol: str
    thermo_types: tuple[str, ...]
    criteria_json: str
    candidates: tuple[MaterialsProjectCandidateSnapshot, ...]
    source_order_content_identities: tuple[tuple[str, str], ...]
    response_byte_size: int
    response_sha256: str
    client_implementation: str
    retrieved_at_utc: str
    mp_api_version: str
    pymatgen_version: str
    api_endpoint: str | None
    database_release: str | None

    def __post_init__(self) -> None:
        MaterialsProjectElementalReferenceRequest(
            element_symbol=self.element_symbol,
            thermo_types=self.thermo_types,
        )
        if type(self.criteria_json) is not str or not self.criteria_json:
            raise ValueError("criteria_json must be a nonempty string")
        if type(self.candidates) is not tuple or not self.candidates:
            raise ValueError("candidates must be a nonempty tuple")
        if any(
            type(value) is not MaterialsProjectCandidateSnapshot
            for value in self.candidates
        ):
            raise TypeError(
                "candidates must contain MaterialsProjectCandidateSnapshot values"
            )
        identities = tuple(
            (value.material_id, value.sha256) for value in self.candidates
        )
        if identities != tuple(sorted(identities)) or len(identities) != len(
            set(identities)
        ):
            raise ValueError("candidate content identities must be unique and sorted")
        if type(self.source_order_content_identities) is not tuple or sorted(
            self.source_order_content_identities
        ) != sorted(identities):
            raise ValueError(
                "source_order_content_identities must be a permutation of candidates"
            )
        response_bytes = (
            json.dumps(
                {
                    "candidates": [
                        json.loads(value.canonical_json) for value in self.candidates
                    ],
                    "criteria": json.loads(self.criteria_json),
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        if type(self.response_byte_size) is not int or self.response_byte_size != len(
            response_bytes
        ):
            raise ValueError("response_byte_size must match canonical response")
        if (
            type(self.response_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", self.response_sha256) is None
            or hashlib.sha256(response_bytes).hexdigest() != self.response_sha256
        ):
            raise ValueError("response_sha256 must match canonical response")
        for label, value in (
            ("client_implementation", self.client_implementation),
            ("retrieved_at_utc", self.retrieved_at_utc),
            ("mp_api_version", self.mp_api_version),
            ("pymatgen_version", self.pymatgen_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        try:
            retrieved = datetime.fromisoformat(self.retrieved_at_utc)
        except ValueError as error:
            raise ValueError(
                "retrieved_at_utc must be an ISO-8601 timestamp"
            ) from error
        if retrieved.tzinfo is None or retrieved.utcoffset() is None:
            raise ValueError("retrieved_at_utc must include a UTC offset")
        for label, optional_value in (
            ("api_endpoint", self.api_endpoint),
            ("database_release", self.database_release),
        ):
            if optional_value is not None and (
                type(optional_value) is not str
                or not optional_value
                or optional_value != optional_value.strip()
            ):
                raise ValueError(f"{label} must be nonempty or None")


@dataclass(frozen=True, slots=True)
class MaterialsProjectElementalReference:
    """Record the elemental entry selected by one explicit convex hull."""

    request: MaterialsProjectElementalReferenceRequest
    material_id: str
    energy_per_atom_ev: float
    energy_above_hull_ev: float
    entry_count: int
    structure: MaterialsProjectStructureReference
    query_snapshot: MaterialsProjectQuerySnapshot
    selected_candidate_sha256: str

    def __post_init__(self) -> None:
        if type(self.request) is not MaterialsProjectElementalReferenceRequest:
            raise TypeError(
                "request must be a MaterialsProjectElementalReferenceRequest"
            )
        MaterialsProjectStructureRequest(self.material_id)
        for name, value in (
            ("energy_per_atom_ev", self.energy_per_atom_ev),
            ("energy_above_hull_ev", self.energy_above_hull_ev),
        ):
            if type(value) is not float:
                raise TypeError(f"{name} must be a built-in float")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.energy_above_hull_ev < 0.0:
            raise ValueError("energy_above_hull_ev must be nonnegative")
        if type(self.entry_count) is not int:
            raise TypeError("entry_count must be a built-in int")
        if self.entry_count <= 0:
            raise ValueError("entry_count must be positive")
        if type(self.structure) is not MaterialsProjectStructureReference:
            raise TypeError("structure must be a MaterialsProjectStructureReference")
        if self.structure.material_id != self.material_id:
            raise ValueError("structure material identity must match the hull entry")
        if type(self.query_snapshot) is not MaterialsProjectQuerySnapshot:
            raise TypeError("query_snapshot must be MaterialsProjectQuerySnapshot")
        if self.query_snapshot.element_symbol != self.request.element_symbol or (
            self.query_snapshot.thermo_types != self.request.thermo_types
        ):
            raise ValueError("query snapshot must match the elemental request")
        selected = tuple(
            value
            for value in self.query_snapshot.candidates
            if value.material_id == self.material_id
            and value.sha256 == self.selected_candidate_sha256
        )
        if len(selected) != 1:
            raise ValueError(
                "selected material and digest must occur once in query candidates"
            )
        if self.entry_count != len(self.query_snapshot.candidates):
            raise ValueError("entry_count must match query snapshot candidates")


@dataclass(frozen=True, slots=True)
class MaterialsProjectElementalReferenceSelector:
    """Select an elemental MP reference through pymatgen's convex hull."""

    def action(
        self,
        *,
        client: MaterialsProjectClient,
        request: MaterialsProjectElementalReferenceRequest,
    ) -> MaterialsProjectElementalReference:
        """Return the pymatgen elemental reference and its exact MP structure."""
        if not isinstance(client, MaterialsProjectClient):
            raise TypeError("client must implement MaterialsProjectClient")
        if type(request) is not MaterialsProjectElementalReferenceRequest:
            raise TypeError(
                "request must be a MaterialsProjectElementalReferenceRequest"
            )
        entries = client.get_entries_in_chemsys(
            [request.element_symbol],
            additional_criteria={"thermo_types": list(request.thermo_types)},
        )
        if not isinstance(entries, list) or not entries:
            raise ValueError("MPRester must return a nonempty entry list")
        if any(not isinstance(entry, ComputedEntry) for entry in entries):
            raise TypeError("MPRester entries must be ComputedEntry values")
        candidate_by_object_identity: dict[int, MaterialsProjectCandidateSnapshot] = {}
        candidate_snapshots: list[MaterialsProjectCandidateSnapshot] = []
        for entry in entries:
            # Thermo entries identify calculations with suffixed values such as
            # ``mp-23-r2SCAN``. Structure retrieval requires the unsuffixed
            # material identity returned in the entry metadata. Retain the whole
            # entry in canonical_json so calculation identity is not discarded.
            entry_data = entry.data if isinstance(entry.data, dict) else {}
            raw_material_id = entry_data.get("material_id")
            candidate_material_id = (
                str(raw_material_id)
                if raw_material_id is not None
                else str(entry.entry_id)
            )
            MaterialsProjectStructureRequest(candidate_material_id)
            # mp-api returns oxidation-state maps keyed by pymatgen Element
            # objects. ComputedStructureEntry.as_dict() delegates through JSON,
            # whose object keys must be scalar JSON keys. Normalize those keys on
            # a shallow snapshot; never mutate the entry used by PhaseDiagram.
            snapshot_entry = copy.copy(entry)
            snapshot_data = dict(entry_data)
            oxidation_states = snapshot_data.get("oxidation_states")
            if isinstance(oxidation_states, dict):
                snapshot_data["oxidation_states"] = {
                    str(key): value for key, value in oxidation_states.items()
                }
            snapshot_entry.data = snapshot_data
            canonical_json = (
                json.dumps(
                    snapshot_entry.as_dict(),
                    cls=MontyEncoder,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            canonical_bytes = canonical_json.encode("utf-8")
            snapshot = MaterialsProjectCandidateSnapshot(
                material_id=candidate_material_id,
                canonical_json=canonical_json,
                byte_size=len(canonical_bytes),
                sha256=hashlib.sha256(canonical_bytes).hexdigest(),
            )
            candidate_by_object_identity[id(entry)] = snapshot
            candidate_snapshots.append(snapshot)
        candidate_by_content_identity = {
            (value.material_id, value.sha256): value for value in candidate_snapshots
        }
        if len(candidate_by_content_identity) != len(candidate_snapshots):
            raise ValueError("Materials Project returned duplicate candidate content")
        ordered_candidates = tuple(
            candidate_by_content_identity[identity]
            for identity in sorted(candidate_by_content_identity)
        )
        criteria_json = (
            json.dumps(
                {
                    "additional_criteria": {"thermo_types": list(request.thermo_types)},
                    "elements": [request.element_symbol],
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )
        response_bytes = (
            json.dumps(
                {
                    "candidates": [
                        json.loads(value.canonical_json) for value in ordered_candidates
                    ],
                    "criteria": json.loads(criteria_json),
                },
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        api_endpoint = getattr(client, "endpoint", None)
        if type(api_endpoint) is not str or not api_endpoint.strip():
            api_endpoint = None
        database_release = getattr(client, "database_version", None)
        if type(database_release) is not str or not database_release.strip():
            database_release = None
        query_snapshot = MaterialsProjectQuerySnapshot(
            element_symbol=request.element_symbol,
            thermo_types=request.thermo_types,
            criteria_json=criteria_json,
            candidates=ordered_candidates,
            source_order_content_identities=tuple(
                (value.material_id, value.sha256) for value in candidate_snapshots
            ),
            response_byte_size=len(response_bytes),
            response_sha256=hashlib.sha256(response_bytes).hexdigest(),
            client_implementation=(
                f"{type(client).__module__}.{type(client).__qualname__}"
            ),
            retrieved_at_utc=datetime.now(UTC).isoformat(),
            mp_api_version=importlib.metadata.version("mp-api"),
            pymatgen_version=importlib.metadata.version("pymatgen"),
            api_endpoint=api_endpoint,
            database_release=database_release,
        )
        phase_diagram = PhaseDiagram(entries)
        selected = phase_diagram.el_refs.get(Element(request.element_symbol))
        if selected is None:
            raise ValueError("pymatgen did not select an elemental reference")
        selected_data = selected.data if isinstance(selected.data, dict) else {}
        raw_selected_material_id = selected_data.get("material_id")
        material_id = (
            str(raw_selected_material_id)
            if raw_selected_material_id is not None
            else str(selected.entry_id)
        )
        MaterialsProjectStructureRequest(material_id)
        energy_per_atom = selected.energy_per_atom
        if energy_per_atom is None:
            raise ValueError("selected elemental entry has no energy per atom")
        hull_value = phase_diagram.get_e_above_hull(selected)
        if hull_value is None:
            raise ValueError("selected elemental entry has no hull distance")
        energy_above_hull = float(hull_value)
        if abs(energy_above_hull) <= 1.0e-12:
            energy_above_hull = 0.0
        selected_snapshot = candidate_by_object_identity.get(id(selected))
        if selected_snapshot is None:
            selected_snapshot_entry = copy.copy(selected)
            selected_snapshot_data = dict(selected_data)
            selected_oxidation_states = selected_snapshot_data.get("oxidation_states")
            if isinstance(selected_oxidation_states, dict):
                selected_snapshot_data["oxidation_states"] = {
                    str(key): value for key, value in selected_oxidation_states.items()
                }
            selected_snapshot_entry.data = selected_snapshot_data
            selected_canonical_json = (
                json.dumps(
                    selected_snapshot_entry.as_dict(),
                    cls=MontyEncoder,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            selected_sha256 = hashlib.sha256(
                selected_canonical_json.encode("utf-8")
            ).hexdigest()
            selected_matches = tuple(
                value
                for value in ordered_candidates
                if value.material_id == material_id and value.sha256 == selected_sha256
            )
            if len(selected_matches) != 1:
                raise ValueError(
                    "selected hull entry is not uniquely present in query snapshot"
                )
            selected_snapshot = selected_matches[0]
        structure = MaterialsProjectStructureRetriever().action(
            client=client,
            request=MaterialsProjectStructureRequest(
                material_id=material_id,
                conventional_unit_cell=request.conventional_unit_cell,
            ),
        )
        return MaterialsProjectElementalReference(
            request=request,
            material_id=material_id,
            energy_per_atom_ev=float(energy_per_atom),
            energy_above_hull_ev=energy_above_hull,
            entry_count=len(entries),
            structure=structure,
            query_snapshot=query_snapshot,
            selected_candidate_sha256=selected_snapshot.sha256,
        )
