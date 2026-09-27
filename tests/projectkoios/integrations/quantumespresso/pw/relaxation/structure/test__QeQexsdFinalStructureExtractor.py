from __future__ import annotations

import unittest
from dataclasses import dataclass, replace

import numpy as np

from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (  # noqa: E501
    QeQexsdFinalStructureExtractor,
)


@dataclass(frozen=True, slots=True)
class _ParsedQexsdDocument:
    source_path: str = "/evidence/data-file-schema.xml"
    source_sha256: str = "a" * 64
    source_byte_count: int = 123
    qexsd_version: str = "25.05.21"
    producing_application: str = "Quantum ESPRESSO"
    producing_application_version: str | None = "7.5"
    declared_unit_system_label: str = "Hartree atomic units"
    atomic_structure_alat: float = 2.0
    direct_lattice_vectors: tuple[tuple[float, float, float], ...] = (
        (2.0, 0.0, 0.0),
        (1.0, 3.0, 0.0),
        (0.5, 1.0, 4.0),
    )
    direct_lattice_source_label: str = "output/atomic_structure/cell/a1,a2,a3"
    atoms: tuple[tuple[int, str, tuple[float, float, float]], ...] = (
        (1, "Si", (0.0, 0.0, 0.0)),
        (2, "Si", (1.375, 2.25, 3.0)),
    )
    declared_atom_count: int = 2
    atomic_positions_source_label: str = "output/atomic_structure/atomic_positions"
    exit_status: int = 0


class QeQexsdFinalStructureExtractorTest(unittest.TestCase):
    def test_extracts_source_ordered_cell_and_fractional_positions(self) -> None:
        extracted = QeQexsdFinalStructureExtractor().extract(_ParsedQexsdDocument())

        np.testing.assert_allclose(
            extracted.unit_cell.H.magnitude,
            np.array(((2.0, 1.0, 0.5), (0.0, 3.0, 1.0), (0.0, 0.0, 4.0))),
        )
        self.assertEqual(extracted.unit_cell.H.unit.expression, "bohr")
        np.testing.assert_allclose(
            extracted.unit_cell.atomic_basis.atoms[1].position_fractional.magnitude,
            np.array((0.25, 0.5, 0.75)),
        )
        self.assertEqual(extracted.source_sha256, "a" * 64)
        self.assertEqual(extracted.qexsd_version, "25.05.21")
        self.assertEqual(extracted.exit_status, 0)
        self.assertIn("no vector reordering", extracted.transformation)

    def test_does_not_wrap_fractional_coordinates(self) -> None:
        document = replace(
            _ParsedQexsdDocument(),
            atoms=((1, "Si", (0.0, 0.0, 0.0)), (2, "Si", (2.5, -0.25, 2.0))),
        )

        extracted = QeQexsdFinalStructureExtractor().extract(document)

        np.testing.assert_allclose(
            extracted.unit_cell.atomic_basis.atoms[1].position_fractional.magnitude,
            np.array((1.25, -0.25, 0.5)),
        )

    def test_rejects_raw_xml_instead_of_duplicating_parser_ownership(self) -> None:
        with self.assertRaisesRegex(TypeError, "QuantumEspressoXsdDocumentParser"):
            QeQexsdFinalStructureExtractor().extract(b"<espresso />")

    def test_rejects_singular_output_cell(self) -> None:
        document = replace(
            _ParsedQexsdDocument(),
            direct_lattice_vectors=(
                (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 4.0, 0.0),
            ),
        )

        with self.assertRaisesRegex(ValueError, "nonsingular"):
            QeQexsdFinalStructureExtractor().extract(document)


if __name__ == "__main__":
    unittest.main()
