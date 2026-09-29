"""Bounded incremental extraction of native ``vasprun.xml`` observations."""

from __future__ import annotations

import io
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

_MAX_VASPRUN_BYTES = 100_000_000

type VaspVector3 = tuple[float, float, float]
type VaspMatrix3 = tuple[VaspVector3, VaspVector3, VaspVector3]
type VaspSpectrum = tuple[tuple[tuple[float, ...], ...], ...]


class VaspRunXmlError(ValueError):
    """Report malformed, unsupported, or oversized ``vasprun.xml`` evidence."""


@dataclass(frozen=True, slots=True)
class VaspStructure:
    """Retain one native VASP structure in Angstrom and fractional coordinates."""

    lattice_vectors_angstrom: VaspMatrix3
    positions_fractional: tuple[VaspVector3, ...]

    def __post_init__(self) -> None:
        _validate_matrix(self.lattice_vectors_angstrom, "lattice_vectors_angstrom")
        if (
            type(self.positions_fractional) is not tuple
            or not self.positions_fractional
        ):
            raise ValueError("positions_fractional must be a nonempty tuple")
        for vector in self.positions_fractional:
            _validate_vector(vector, "fractional position")


@dataclass(frozen=True, slots=True)
class VaspElectronicStep:
    """Retain one electronic iteration's native energy observations in eV."""

    free_energy_ev: float
    energy_without_entropy_ev: float
    energy_sigma_zero_ev: float

    def __post_init__(self) -> None:
        for label, value in (
            ("free_energy_ev", self.free_energy_ev),
            ("energy_without_entropy_ev", self.energy_without_entropy_ev),
            ("energy_sigma_zero_ev", self.energy_sigma_zero_ev),
        ):
            _finite(value, label)


@dataclass(frozen=True, slots=True)
class VaspIonicStep:
    """Retain one source-ordered ``calculation`` element from ``vasprun.xml``."""

    sequence_index: int
    electronic_steps: tuple[VaspElectronicStep, ...]
    structure: VaspStructure
    forces_ev_per_angstrom: tuple[VaspVector3, ...]
    stress_kbar: VaspMatrix3
    free_energy_ev: float
    energy_without_entropy_ev: float
    energy_sigma_zero_ev: float

    def __post_init__(self) -> None:
        if type(self.sequence_index) is not int or self.sequence_index <= 0:
            raise ValueError("sequence_index must be positive")
        if type(self.electronic_steps) is not tuple or not self.electronic_steps:
            raise ValueError("electronic_steps must be a nonempty tuple")
        if any(type(step) is not VaspElectronicStep for step in self.electronic_steps):
            raise TypeError("electronic_steps must contain VaspElectronicStep values")
        if type(self.structure) is not VaspStructure:
            raise TypeError("structure must be VaspStructure")
        if type(self.forces_ev_per_angstrom) is not tuple or len(
            self.forces_ev_per_angstrom
        ) != len(self.structure.positions_fractional):
            raise ValueError("forces must match the structure atom count")
        for vector in self.forces_ev_per_angstrom:
            _validate_vector(vector, "force")
        _validate_matrix(self.stress_kbar, "stress_kbar")
        for label, value in (
            ("free_energy_ev", self.free_energy_ev),
            ("energy_without_entropy_ev", self.energy_without_entropy_ev),
            ("energy_sigma_zero_ev", self.energy_sigma_zero_ev),
        ):
            _finite(value, label)


@dataclass(frozen=True, slots=True)
class VaspRunXmlData:
    """Retain structured native observations from one complete ``vasprun.xml``."""

    program: str
    program_version: str
    atom_labels: tuple[str, ...]
    incar_ibrion: int
    incar_nsw: int
    incar_isif: int
    initial_structure: VaspStructure
    final_structure: VaspStructure
    k_points: tuple[VaspVector3, ...]
    k_point_weights: tuple[float, ...]
    ionic_steps: tuple[VaspIonicStep, ...]
    eigenvalues_ev: VaspSpectrum | None
    occupations: VaspSpectrum | None
    fermi_energy_ev: float | None

    def __post_init__(self) -> None:
        for label, value in (
            ("program", self.program),
            ("program_version", self.program_version),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be a nonempty stripped string")
        if type(self.atom_labels) is not tuple or not self.atom_labels:
            raise ValueError("atom_labels must be a nonempty tuple")
        for int_label, int_value in (
            ("incar_ibrion", self.incar_ibrion),
            ("incar_nsw", self.incar_nsw),
            ("incar_isif", self.incar_isif),
        ):
            if type(int_value) is not int:
                raise TypeError(f"{int_label} must be an integer")
        if self.incar_nsw < 0:
            raise ValueError("incar_nsw must be nonnegative")
        if any(type(label) is not str or not label for label in self.atom_labels):
            raise ValueError("atom_labels must contain nonempty strings")
        for structure in (self.initial_structure, self.final_structure):
            if type(structure) is not VaspStructure:
                raise TypeError("initial and final structures must be VaspStructure")
            if len(structure.positions_fractional) != len(self.atom_labels):
                raise ValueError("structure atom count must match atom_labels")
        if type(self.k_points) is not tuple or not self.k_points:
            raise ValueError("k_points must be a nonempty tuple")
        for vector in self.k_points:
            _validate_vector(vector, "k-point")
        if type(self.k_point_weights) is not tuple or len(self.k_point_weights) != len(
            self.k_points
        ):
            raise ValueError("k-point weights must match k-points")
        if any(
            type(value) is not float or not math.isfinite(value) or value < 0.0
            for value in self.k_point_weights
        ):
            raise ValueError("k-point weights must be finite and nonnegative")
        if type(self.ionic_steps) is not tuple or not self.ionic_steps:
            raise ValueError("ionic_steps must be a nonempty tuple")
        if tuple(step.sequence_index for step in self.ionic_steps) != tuple(
            range(1, len(self.ionic_steps) + 1)
        ):
            raise ValueError("ionic_steps must retain contiguous source order")
        if (self.eigenvalues_ev is None) is not (self.occupations is None):
            raise ValueError(
                "eigenvalues and occupations must both be present or absent"
            )
        if self.eigenvalues_ev is not None:
            _validate_spectrum(
                self.eigenvalues_ev,
                spin_count=len(self.eigenvalues_ev),
                kpoint_count=len(self.k_points),
                label="eigenvalues_ev",
            )
            assert self.occupations is not None
            _validate_spectrum(
                self.occupations,
                spin_count=len(self.eigenvalues_ev),
                kpoint_count=len(self.k_points),
                label="occupations",
            )
            if tuple(len(row) for spin in self.eigenvalues_ev for row in spin) != tuple(
                len(row) for spin in self.occupations for row in spin
            ):
                raise ValueError("eigenvalue and occupation shapes disagree")
        if self.fermi_energy_ev is not None:
            _finite(self.fermi_energy_ev, "fermi_energy_ev")


@dataclass(frozen=True, slots=True)
class VaspRunXmlParser:
    """Incrementally parse top-level XML elements and clear them after use."""

    maximum_bytes: int = _MAX_VASPRUN_BYTES

    def __post_init__(self) -> None:
        if type(self.maximum_bytes) is not int or self.maximum_bytes <= 0:
            raise ValueError("maximum_bytes must be positive")

    def parse(self, payload: bytes) -> VaspRunXmlData:
        """Parse bounded XML bytes without retaining the complete element tree."""
        if type(payload) is not bytes:
            raise TypeError("vasprun.xml payload must be bytes")
        if len(payload) > self.maximum_bytes:
            raise VaspRunXmlError("vasprun.xml exceeds the byte limit")
        if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
            raise VaspRunXmlError("vasprun.xml must not contain a DTD or entity")

        program: str | None = None
        version: str | None = None
        atom_labels: tuple[str, ...] | None = None
        incar_ibrion: int | None = None
        incar_nsw: int | None = None
        incar_isif: int | None = None
        initial_structure: VaspStructure | None = None
        final_structure: VaspStructure | None = None
        k_points: tuple[VaspVector3, ...] | None = None
        weights: tuple[float, ...] | None = None
        steps: list[VaspIonicStep] = []
        eigenvalues: VaspSpectrum | None = None
        occupations: VaspSpectrum | None = None
        fermi_energy: float | None = None
        stack: list[ET.Element] = []
        try:
            events = ET.iterparse(io.BytesIO(payload), events=("start", "end"))
            for event, element in events:
                if event == "start":
                    stack.append(element)
                    continue
                if len(stack) == 2:
                    if element.tag == "generator":
                        program = _named_text(element, "program")
                        version = _named_text(element, "version")
                    elif element.tag == "incar":
                        incar_ibrion = _required_named_int(element, "IBRION")
                        incar_nsw = _required_named_int(element, "NSW")
                        incar_isif = _optional_named_int(element, "ISIF", default=2)
                    elif element.tag == "atominfo":
                        atom_labels = _atom_labels(element)
                    elif element.tag == "kpoints":
                        k_points = _varray(element, "kpointlist")
                        weight_vectors = _varray(element, "weights")
                        weights = tuple(vector[0] for vector in weight_vectors)
                    elif element.tag == "structure":
                        name = element.attrib.get("name")
                        if name == "initialpos":
                            initial_structure = _structure(element)
                        elif name == "finalpos":
                            final_structure = _structure(element)
                    elif element.tag == "calculation":
                        step, step_eigenvalues, step_occupations, step_fermi = (
                            _calculation(element, len(steps) + 1)
                        )
                        steps.append(step)
                        if step_eigenvalues is not None:
                            eigenvalues = step_eigenvalues
                            occupations = step_occupations
                        if step_fermi is not None:
                            fermi_energy = step_fermi
                    element.clear()
                stack.pop()
        except (ET.ParseError, UnicodeError, ValueError) as error:
            raise VaspRunXmlError(f"invalid vasprun.xml: {error}") from error

        if program is None or version is None:
            raise VaspRunXmlError("vasprun.xml lacks generator metadata")
        if atom_labels is None:
            raise VaspRunXmlError("vasprun.xml lacks atom labels")
        if incar_ibrion is None or incar_nsw is None or incar_isif is None:
            raise VaspRunXmlError("vasprun.xml lacks required INCAR mode values")
        if initial_structure is None or final_structure is None:
            raise VaspRunXmlError("vasprun.xml lacks initial or final structure")
        if k_points is None or weights is None:
            raise VaspRunXmlError("vasprun.xml lacks k-point data")
        if not steps:
            raise VaspRunXmlError("vasprun.xml contains no calculation steps")
        return VaspRunXmlData(
            program=program,
            program_version=version,
            atom_labels=atom_labels,
            incar_ibrion=incar_ibrion,
            incar_nsw=incar_nsw,
            incar_isif=incar_isif,
            initial_structure=initial_structure,
            final_structure=final_structure,
            k_points=k_points,
            k_point_weights=weights,
            ionic_steps=tuple(steps),
            eigenvalues_ev=eigenvalues,
            occupations=occupations,
            fermi_energy_ev=fermi_energy,
        )


def _calculation(
    element: ET.Element,
    sequence_index: int,
) -> tuple[VaspIonicStep, VaspSpectrum | None, VaspSpectrum | None, float | None]:
    electronic_steps = tuple(
        _electronic_step(item) for item in element.findall("scstep")
    )
    structure_element = element.find("structure")
    if structure_element is None:
        raise ValueError("calculation lacks structure")
    forces = _varray(element, "forces")
    stress_rows = _varray(element, "stress")
    if len(stress_rows) != 3:
        raise ValueError("calculation stress must have three rows")
    final_energy = _energy(element.find("energy"))
    eigenvalues, occupations = _eigenvalues(element.find("eigenvalues"))
    fermi = _optional_named_float(element.find("dos"), "efermi")
    return (
        VaspIonicStep(
            sequence_index=sequence_index,
            electronic_steps=electronic_steps,
            structure=_structure(structure_element),
            forces_ev_per_angstrom=forces,
            stress_kbar=(stress_rows[0], stress_rows[1], stress_rows[2]),
            free_energy_ev=final_energy.free_energy_ev,
            energy_without_entropy_ev=final_energy.energy_without_entropy_ev,
            energy_sigma_zero_ev=final_energy.energy_sigma_zero_ev,
        ),
        eigenvalues,
        occupations,
        fermi,
    )


def _electronic_step(element: ET.Element) -> VaspElectronicStep:
    return _energy(element.find("energy"))


def _energy(element: ET.Element | None) -> VaspElectronicStep:
    if element is None:
        raise ValueError("energy element is missing")
    return VaspElectronicStep(
        free_energy_ev=_required_named_float(element, "e_fr_energy"),
        energy_without_entropy_ev=_required_named_float(element, "e_wo_entrp"),
        energy_sigma_zero_ev=_required_named_float(element, "e_0_energy"),
    )


def _structure(element: ET.Element) -> VaspStructure:
    crystal = element.find("crystal")
    if crystal is None:
        raise ValueError("structure lacks crystal")
    basis = _varray(crystal, "basis")
    positions = _varray(element, "positions")
    if len(basis) != 3:
        raise ValueError("structure basis must have three rows")
    return VaspStructure(
        lattice_vectors_angstrom=(basis[0], basis[1], basis[2]),
        positions_fractional=positions,
    )


def _atom_labels(element: ET.Element) -> tuple[str, ...]:
    array = element.find("array[@name='atoms']/set")
    if array is None:
        raise ValueError("atominfo lacks atoms array")
    labels: list[str] = []
    for record in array.findall("rc"):
        column = record.find("c")
        if column is None or column.text is None or not column.text.strip():
            raise ValueError("atom declaration lacks label")
        labels.append(column.text.strip())
    if not labels:
        raise ValueError("atominfo contains no atoms")
    return tuple(labels)


def _varray(element: ET.Element, name: str) -> tuple[VaspVector3, ...]:
    varray = element.find(f"varray[@name='{name}']")
    if varray is None:
        raise ValueError(f"missing varray {name}")
    values: list[VaspVector3] = []
    for vector in varray.findall("v"):
        tokens = (vector.text or "").split()
        if len(tokens) not in {1, 3}:
            raise ValueError(f"varray {name} contains invalid row width")
        parsed = tuple(float(token) for token in tokens)
        if len(parsed) == 1:
            values.append((parsed[0], 0.0, 0.0))
        else:
            values.append((parsed[0], parsed[1], parsed[2]))
    if not values:
        raise ValueError(f"varray {name} is empty")
    return tuple(values)


def _eigenvalues(
    element: ET.Element | None,
) -> tuple[VaspSpectrum | None, VaspSpectrum | None]:
    if element is None:
        return None, None
    root_set = element.find("array/set")
    if root_set is None:
        raise ValueError("eigenvalues array lacks root set")
    eigen_spins: list[tuple[tuple[float, ...], ...]] = []
    occupation_spins: list[tuple[tuple[float, ...], ...]] = []
    for spin_set in root_set.findall("set"):
        eigen_kpoints: list[tuple[float, ...]] = []
        occupation_kpoints: list[tuple[float, ...]] = []
        for kpoint_set in spin_set.findall("set"):
            eigen_row: list[float] = []
            occupation_row: list[float] = []
            for row in kpoint_set.findall("r"):
                tokens = (row.text or "").split()
                if len(tokens) < 2:
                    raise ValueError("eigenvalue row requires energy and occupation")
                eigen_row.append(float(tokens[0]))
                occupation_row.append(float(tokens[1]))
            if not eigen_row:
                raise ValueError("eigenvalue k-point row is empty")
            eigen_kpoints.append(tuple(eigen_row))
            occupation_kpoints.append(tuple(occupation_row))
        eigen_spins.append(tuple(eigen_kpoints))
        occupation_spins.append(tuple(occupation_kpoints))
    if not eigen_spins:
        raise ValueError("eigenvalues array contains no spin sets")
    return tuple(eigen_spins), tuple(occupation_spins)


def _named_text(element: ET.Element, name: str) -> str:
    item = element.find(f"i[@name='{name}']")
    if item is None or item.text is None or not item.text.strip():
        raise ValueError(f"missing named value {name}")
    return item.text.strip()


def _required_named_float(element: ET.Element, name: str) -> float:
    return float(_named_text(element, name))


def _required_named_int(element: ET.Element, name: str) -> int:
    return int(_named_text(element, name))


def _optional_named_int(element: ET.Element, name: str, *, default: int) -> int:
    item = element.find(f"i[@name='{name}']")
    if item is None or item.text is None or not item.text.strip():
        return default
    return int(item.text)


def _optional_named_float(element: ET.Element | None, name: str) -> float | None:
    if element is None:
        return None
    item = element.find(f"i[@name='{name}']")
    if item is None or item.text is None or not item.text.strip():
        return None
    return float(item.text)


def _finite(value: float, label: str) -> None:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _validate_vector(value: VaspVector3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three values")
    for component in value:
        _finite(component, label)


def _validate_matrix(value: VaspMatrix3, label: str) -> None:
    if type(value) is not tuple or len(value) != 3:
        raise ValueError(f"{label} must contain three rows")
    for row in value:
        _validate_vector(row, label)


def _validate_spectrum(
    value: VaspSpectrum,
    *,
    spin_count: int,
    kpoint_count: int,
    label: str,
) -> None:
    if type(value) is not tuple or len(value) != spin_count:
        raise ValueError(f"{label} spin count is invalid")
    band_count: int | None = None
    for spin in value:
        if type(spin) is not tuple or len(spin) != kpoint_count:
            raise ValueError(f"{label} k-point count is invalid")
        for row in spin:
            if type(row) is not tuple or not row:
                raise ValueError(f"{label} band rows must be nonempty tuples")
            if band_count is None:
                band_count = len(row)
            elif len(row) != band_count:
                raise ValueError(f"{label} band counts disagree")
            for item in row:
                _finite(item, label)
