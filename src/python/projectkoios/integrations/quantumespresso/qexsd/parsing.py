"""Mechanical parsing of explicit QEXSD bytes into immutable native values.

``QuantumEspressoXsdDocumentParser`` recognizes the exact observed QEXSD 23.03.10
and 25.05.21 formats under the shared QES 1.0 namespace. It performs no file
discovery or input/output and exposes no XML nodes. Native values, source order,
declared units, and structural relationships are preserved without scientific
interpretation or conversion.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import ClassVar

from .records import QexsdDocument, QexsdSource, Spectrum, Vector3


@dataclass(frozen=True, slots=True)
class QuantumEspressoXsdDocumentParser:
    """Parse an explicit :class:`QexsdSource` into native immutable values.

    Parameters
    ----------
    source
        Explicit bytes and already verified source identity.

    Attributes
    ----------
    SUPPORTED_NAMESPACE
        Exact namespace accepted for the observed source.
    SUPPORTED_QEXSD_VERSIONS
        Exact ordered QEXSD format versions accepted by this bounded parser.

    Notes
    -----
    The target-first ActionObject name identifies the parsed DataObject and parser
    responsibility for ``QexsdSource -> QexsdDocument``. It does not
    open paths, parse stdout, convert units, or construct backend-neutral meaning.
    """

    SUPPORTED_NAMESPACE: ClassVar[str] = (
        "http://www.quantum-espresso.org/ns/qes/qes-1.0"
    )
    SUPPORTED_QEXSD_VERSIONS: ClassVar[tuple[str, ...]] = (
        "23.03.10",
        "25.05.21",
    )

    source: QexsdSource

    def __post_init__(self) -> None:
        if type(self.source) is not QexsdSource:
            raise TypeError("source must be a QexsdSource")

    def execute(self) -> QexsdDocument:
        """Return the mechanically parsed immutable QEXSD document.

        Returns
        -------
        QexsdDocument
            Ordered native values from the supported document.

        Raises
        ------
        ValueError
            If XML syntax, namespace, root, version, required structure,
            singleton cardinality, numeric values, dimensions, references,
            grids, or exit status violate the supported contract.
        """
        source = self.source
        if b"<!DOCTYPE" in source.content.upper():
            raise ValueError("QEXSD document type declarations are unsupported")
        try:
            root = ET.fromstring(source.content)
        except ET.ParseError as error:
            raise ValueError("malformed QEXSD XML") from error
        expected_root = f"{{{self.SUPPORTED_NAMESPACE}}}espresso"
        if root.tag != expected_root:
            if root.tag.endswith("}espresso"):
                raise ValueError("unsupported QEXSD namespace")
            raise ValueError("unsupported QEXSD root")

        declared_units = self._attribute(root, "Units", "espresso")
        general_info = self._single(root, "general_info")
        output = self._single(root, "output")
        exit_element = self._single(root, "exit_status")

        xml_format = self._single(general_info, "xml_format")
        if self._attribute(xml_format, "NAME", "xml_format") != "QEXSD":
            raise ValueError("unsupported XML format name")
        qexsd_version = self._attribute(xml_format, "VERSION", "xml_format")
        if qexsd_version not in self.SUPPORTED_QEXSD_VERSIONS:
            raise ValueError(f"unsupported QEXSD version: {qexsd_version!r}")
        creator = self._single(general_info, "creator")
        producer = self._attribute(creator, "NAME", "creator")
        producer_version = creator.attrib.get("VERSION")
        if producer_version == "":
            producer_version = None

        species_element = self._single(output, "atomic_species")
        declared_species_count = self._positive_int_attribute(
            species_element, "ntyp", "atomic_species"
        )
        species: list[tuple[str, float, str]] = []
        for element in self._children(species_element, "species"):
            name = self._attribute(element, "name", "species")
            mass = self._scalar(self._single(element, "mass"), "species mass")
            pseudo = self._text(self._single(element, "pseudo_file"), "pseudo_file")
            species.append((name, mass, pseudo))
        if len(species) != declared_species_count:
            raise ValueError(
                "declared species count disagrees with species declarations"
            )

        structure = self._single(output, "atomic_structure")
        declared_atom_count = self._positive_int_attribute(
            structure, "nat", "atomic_structure"
        )
        atomic_structure_alat = self._finite_float(
            self._attribute(structure, "alat", "atomic_structure"),
            "atomic_structure.alat",
        )
        if atomic_structure_alat <= 0:
            raise ValueError("atomic_structure.alat must be positive")
        positions = self._single(structure, "atomic_positions")
        atoms: list[tuple[int, str, Vector3]] = []
        for atom in self._children(positions, "atom"):
            index = self._positive_int_attribute(atom, "index", "atom")
            species_name = self._attribute(atom, "name", "atom")
            atoms.append((index, species_name, self._vector(atom, "atomic position")))
        cell = self._single(structure, "cell")
        direct = (
            self._vector(self._single(cell, "a1"), "a1"),
            self._vector(self._single(cell, "a2"), "a2"),
            self._vector(self._single(cell, "a3"), "a3"),
        )

        basis_set = self._single(output, "basis_set")
        reciprocal = self._single(basis_set, "reciprocal_lattice")
        reciprocal_vectors = (
            self._vector(self._single(reciprocal, "b1"), "b1"),
            self._vector(self._single(reciprocal, "b2"), "b2"),
            self._vector(self._single(reciprocal, "b3"), "b3"),
        )
        fft_grid = self._grid(self._single(basis_set, "fft_grid"), "fft_grid")
        fft_smooth = self._grid(self._single(basis_set, "fft_smooth"), "fft_smooth")
        fft_box = self._grid(self._single(basis_set, "fft_box"), "fft_box")

        band_structure = self._single(output, "band_structure")
        band_count = self._positive_int(self._single(band_structure, "nbnd"), "nbnd")
        sampled_count = self._positive_int(self._single(band_structure, "nks"), "nks")
        entries = self._children(band_structure, "ks_energies")
        k_points: list[Vector3] = []
        weights: list[float] = []
        eigenvalues: list[tuple[float, ...]] = []
        occupation_rows: list[tuple[float, ...] | None] = []
        for entry in entries:
            k_point = self._single(entry, "k_point")
            k_points.append(self._vector(k_point, "k-point"))
            weights.append(
                self._finite_float(
                    self._attribute(k_point, "weight", "k_point"), "k-point weight"
                )
            )
            eigenvalue_element = self._single(entry, "eigenvalues")
            eigenvalue_row = self._numeric_sequence(eigenvalue_element, "eigenvalues")
            self._check_declared_size(eigenvalue_element, eigenvalue_row, "eigenvalues")
            eigenvalues.append(eigenvalue_row)
            occupation_elements = self._children(entry, "occupations")
            if len(occupation_elements) > 1:
                raise ValueError("duplicated singleton section: occupations")
            if occupation_elements:
                occupation_row = self._numeric_sequence(
                    occupation_elements[0], "occupations"
                )
                self._check_declared_size(
                    occupation_elements[0], occupation_row, "occupations"
                )
                occupation_rows.append(occupation_row)
            else:
                occupation_rows.append(None)
        if any(row is None for row in occupation_rows) and not all(
            row is None for row in occupation_rows
        ):
            raise ValueError(
                "occupations must be present for every k-point or unavailable"
            )
        occupations: Spectrum | None
        if all(row is None for row in occupation_rows):
            occupations = None
        else:
            occupations = tuple(row for row in occupation_rows if row is not None)

        total_energy = self._scalar(
            self._single(self._single(output, "total_energy"), "etot"),
            "total energy",
        )
        exit_status = self._integer(exit_element, "exit_status")

        return QexsdDocument(
            source_path=source.canonical_path,
            source_sha256=source.sha256,
            source_byte_count=source.byte_count,
            namespace=self.SUPPORTED_NAMESPACE,
            qexsd_version=qexsd_version,
            producing_application=producer,
            producing_application_version=producer_version,
            declared_unit_system_label=declared_units,
            atomic_structure_alat=atomic_structure_alat,
            direct_lattice_vectors=direct,
            direct_lattice_source_label="output/atomic_structure/cell/a1,a2,a3",
            reciprocal_lattice_coefficients=reciprocal_vectors,
            reciprocal_lattice_source_label=(
                "output/basis_set/reciprocal_lattice/b1,b2,b3"
            ),
            species=tuple(species),
            atoms=tuple(atoms),
            declared_atom_count=declared_atom_count,
            atomic_positions_source_label="output/atomic_structure/atomic_positions",
            k_points=tuple(k_points),
            k_point_weights=tuple(weights),
            sampled_k_point_count=sampled_count,
            k_point_source_label="output/band_structure/ks_energies/k_point",
            eigenvalues=tuple(eigenvalues),
            occupations=occupations,
            eigenvalue_source_label="output/band_structure/ks_energies/eigenvalues",
            band_count=band_count,
            total_energy=total_energy,
            total_energy_source_label="output/total_energy/etot",
            fft_grid=fft_grid,
            fft_smooth=fft_smooth,
            fft_box=fft_box,
            exit_status=exit_status,
        )

    def _children(self, parent: ET.Element, tag: str) -> list[ET.Element]:
        """Return direct unqualified children in source order."""
        return [child for child in parent if child.tag == tag]

    def _single(self, parent: ET.Element, tag: str) -> ET.Element:
        """Return one required direct child and reject missing or duplicates."""
        children = self._children(parent, tag)
        if not children:
            raise ValueError(f"missing required QEXSD section: {tag}")
        if len(children) != 1:
            raise ValueError(f"duplicated singleton section: {tag}")
        return children[0]

    def _attribute(self, element: ET.Element, name: str, context: str) -> str:
        """Return one required nonempty XML attribute without normalization."""
        value = element.attrib.get(name)
        if value is None or value == "":
            raise ValueError(f"{context} requires nonempty attribute {name}")
        return value

    def _text(self, element: ET.Element, context: str) -> str:
        """Return stripped nonempty element text for native token content."""
        value = element.text
        if value is None or value.strip() == "":
            raise ValueError(f"{context} requires text")
        return value.strip()

    def _finite_float(self, text: str, context: str) -> float:
        """Parse one finite XML floating-point token without unit conversion."""
        try:
            value = float(text)
        except ValueError as error:
            raise ValueError(f"{context} must be a floating-point token") from error
        if not math.isfinite(value):
            raise ValueError(f"{context} must be finite")
        return value

    def _numeric_sequence(self, element: ET.Element, context: str) -> tuple[float, ...]:
        """Parse an ordered nonempty whitespace-delimited finite sequence."""
        tokens = self._text(element, context).split()
        if not tokens:
            raise ValueError(f"{context} must not be empty")
        return tuple(self._finite_float(token, context) for token in tokens)

    def _vector(self, element: ET.Element, context: str) -> Vector3:
        """Parse one ordered native three-vector."""
        values = self._numeric_sequence(element, context)
        if len(values) != 3:
            raise ValueError(f"{context} must have exactly three components")
        return (values[0], values[1], values[2])

    def _scalar(self, element: ET.Element, context: str) -> float:
        """Parse exactly one finite floating-point value."""
        values = self._numeric_sequence(element, context)
        if len(values) != 1:
            raise ValueError(f"{context} must contain exactly one value")
        return values[0]

    def _integer(self, element: ET.Element, context: str) -> int:
        """Parse one exact base-ten integer token without float coercion."""
        text = self._text(element, context)
        try:
            return int(text, 10)
        except ValueError as error:
            raise ValueError(f"{context} must be an integer") from error

    def _positive_int(self, element: ET.Element, context: str) -> int:
        """Parse one strictly positive represented integer."""
        value = self._integer(element, context)
        if value <= 0:
            raise ValueError(f"{context} must be positive")
        return value

    def _positive_int_attribute(
        self, element: ET.Element, name: str, context: str
    ) -> int:
        """Parse one required strictly positive integer attribute."""
        text = self._attribute(element, name, context)
        try:
            value = int(text, 10)
        except ValueError as error:
            raise ValueError(f"{context}.{name} must be an integer") from error
        if value <= 0:
            raise ValueError(f"{context}.{name} must be positive")
        return value

    def _grid(self, element: ET.Element, context: str) -> tuple[int, int, int]:
        """Parse three required positive FFT-grid dimensions."""
        return tuple(
            self._positive_int_attribute(element, name, context)
            for name in ("nr1", "nr2", "nr3")
        )  # type: ignore[return-value]

    def _check_declared_size(
        self, element: ET.Element, values: tuple[float, ...], context: str
    ) -> None:
        """Check a required native size attribute against parsed values."""
        declared = self._positive_int_attribute(element, "size", context)
        if declared != len(values):
            raise ValueError(f"{context} declared size disagrees with values")
