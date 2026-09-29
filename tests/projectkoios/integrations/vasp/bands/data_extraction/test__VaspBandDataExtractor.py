from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.bands.data_extraction import (
    VaspBandDataExtractor,
)
from projectkoios.simulations.dft.pw.bands import (
    BandPath,
    BandPathBranch,
    BandPathCoordinateSystem,
    BandPathVertex,
)
from tests.projectkoios.integrations.vasp.kpoints import (
    test__VaspKpointsWriter as kpoints_test,
)
from tests.projectkoios.integrations.vasp.nscf.data_extraction import (
    test__VaspNscfDataExtractor as nscf_test,
)


class VaspBandDataExtractorTest(unittest.TestCase):
    def test_correlates_line_mode_samples_and_native_spectrum(self) -> None:
        path = BandPath(
            branches=(
                BandPathBranch(
                    vertices=(
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("X", (0.5, 0.0, 0.0)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="test path",
        )

        data = VaspBandDataExtractor().extract(
            nscf_test._sources(),
            calculation=kpoints_test._calculation(path),
            points_per_segment=2,
            expected_band_count=2,
            reference_energy_ev=0.1,
            reference_label="vasprun.xml Fermi energy",
        )

        self.assertEqual(data.diagram.kpoint_count, 2)
        self.assertEqual(data.diagram.band_count, 2)
        self.assertEqual(data.diagram.branches[0].tick_indices, (0, 1))
        self.assertEqual(data.diagram.branches[0].tick_labels, ("G", "X"))
        self.assertGreater(data.diagram.path_coordinate[1], 0.0)
        self.assertEqual(data.diagram.energies_ev[0][1], (-0.8, 0.7))
        self.assertTrue(data.consistency.atom_count_matches)
        self.assertTrue(data.consistency.configured_unit_cell_matches)
        self.assertTrue(data.consistency.path_coordinates_match)

    def test_rejects_output_from_a_different_unit_cell_basis(self) -> None:
        path = BandPath(
            branches=(
                BandPathBranch(
                    vertices=(
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("X", (0.5, 0.0, 0.0)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="test path",
        )

        with self.assertRaisesRegex(ValueError, "unit cell disagrees"):
            VaspBandDataExtractor().extract(
                nscf_test._sources(),
                calculation=kpoints_test._calculation(path, canonical_basis=True),
                points_per_segment=2,
                expected_band_count=2,
            )

    def test_rejects_path_that_disagrees_with_xml_kpoints(self) -> None:
        path = BandPath(
            branches=(
                BandPathBranch(
                    vertices=(
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("L", (0.5, 0.5, 0.5)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="wrong path",
        )

        with self.assertRaisesRegex(ValueError, "disagree"):
            VaspBandDataExtractor().extract(
                nscf_test._sources(),
                calculation=kpoints_test._calculation(path),
                points_per_segment=2,
                expected_band_count=2,
            )


if __name__ == "__main__":
    unittest.main()
