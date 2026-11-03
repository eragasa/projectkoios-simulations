from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from projectkoios.integrations.quantumespresso.pw.relaxation.structure import (  # noqa: E501
    QexsdFinalStructureExtractor,
)
from projectkoios.physkit.units import PhysicalUnit
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)


class QexsdFinalStructureExtractorTest(unittest.TestCase):
    def test__QexsdFinalStructureExtractor__extracts_cell_and_positions(
        self,
    ) -> None:
        extracted = QexsdFinalStructureExtractor(
            QEXSD_FIXTURES.final_structure_document()
        ).extract()

        np.testing.assert_allclose(
            extracted.unit_cell.H.magnitude,
            np.array(((2.0, 1.0, 0.5), (0.0, 3.0, 1.0), (0.0, 0.0, 4.0))),
        )
        self.assertEqual(extracted.unit_cell.H.unit, PhysicalUnit("bohr"))
        np.testing.assert_allclose(
            extracted.unit_cell.atomic_basis.atoms[1].position_fractional.magnitude,
            np.array((0.25, 0.5, 0.75)),
        )
        self.assertEqual(extracted.source_sha256, "a" * 64)
        self.assertEqual(extracted.qexsd_version, "25.05.21")
        self.assertEqual(extracted.exit_status, 0)
        self.assertIn("no vector reordering", extracted.transformation)

    def test__QexsdFinalStructureExtractor__does_not_wrap_fractional_coordinates(
        self,
    ) -> None:
        document = replace(
            QEXSD_FIXTURES.final_structure_document(),
            atoms=((1, "Si", (0.0, 0.0, 0.0)), (2, "Si", (2.5, -0.25, 2.0))),
        )

        extracted = QexsdFinalStructureExtractor(document).extract()

        np.testing.assert_allclose(
            extracted.unit_cell.atomic_basis.atoms[1].position_fractional.magnitude,
            np.array((1.25, -0.25, 0.5)),
        )

    def test__QexsdFinalStructureExtractor__rejects_raw_xml(
        self,
    ) -> None:
        with self.assertRaisesRegex(TypeError, "QexsdDocument"):
            QexsdFinalStructureExtractor(
                b"<espresso />"  # type: ignore[arg-type]
            )

    def test__QexsdFinalStructureExtractor__rejects_singular_output_cell(self) -> None:
        document = replace(
            QEXSD_FIXTURES.final_structure_document(),
            direct_lattice_vectors=(
                (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 4.0, 0.0),
            ),
        )

        with self.assertRaisesRegex(ValueError, "nonsingular"):
            QexsdFinalStructureExtractor(document).extract()


if __name__ == "__main__":
    unittest.main()
