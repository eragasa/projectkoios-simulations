from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from projectkoios.integrations.quantumespresso.pw.bands.data_extraction import (
    QeBandsDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.bands.path import (
    QeBandsPathProjection,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QexsdData,
)
from projectkoios.simulations.dft.pw.bands import (
    BandPath,
    BandPathBranch,
    BandPathCoordinateSystem,
    BandPathVertex,
    PwDftBandsSimulation,
)
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010 import (
    SetyawanCurtaroloAppendixACase,
    SetyawanCurtaroloLattice,
    SetyawanCurtaroloPathBinder,
    SetyawanCurtaroloPathBindingRequest,
    SetyawanCurtaroloPathDefinition,
)
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)
from tests.projectkoios.simulations.dft.pw.support import (
    resolved_pw_dft_simulation,
)


class QeBandsDataTest(unittest.TestCase):
    def test__QeBandsData__projects_a_bound_setyawan_curtarolo_path(self) -> None:
        qexsd = QexsdData.from_document(QEXSD_FIXTURES.bands_document())
        simulation = resolved_pw_dft_simulation(qexsd.final_structure.unit_cell)
        lattice_parameter = simulation.lattice_vectors_angstrom[0][0]
        definition = SetyawanCurtaroloPathDefinition(
            SetyawanCurtaroloLattice(
                appendix_a_case=SetyawanCurtaroloAppendixACase.cub,
                a_angstrom=lattice_parameter,
                b_angstrom=lattice_parameter,
                c_angstrom=lattice_parameter,
            )
        )
        calculation = (
            SetyawanCurtaroloPathBinder()
            .action(
                request=SetyawanCurtaroloPathBindingRequest(
                    definition=definition,
                    simulation=simulation,
                )
            )
            .calculation
        )

        card = QeBandsPathProjection(
            calculation,
            points_per_segment=2,
        ).to_kpoints_card()

        self.assertEqual(card.option, "crystal_b")
        self.assertEqual(card.lines[0], "8")
        self.assertEqual(
            card.lines[1],
            "0.0000000000 0.0000000000 0.0000000000 2 ! Γ",
        )
        self.assertEqual(
            card.lines[2],
            "0.0000000000 0.5000000000 0.0000000000 2 ! X",
        )

    def test__QeBandsData__projects_crystal_b_path_and_extracts_full_precision_qexsd(
        self,
    ) -> None:
        qexsd = QexsdData.from_document(QEXSD_FIXTURES.bands_document())
        projection = QeBandsPathProjection(
            PwDftBandsSimulation(
                simulation=resolved_pw_dft_simulation(qexsd.final_structure.unit_cell),
                path=_BAND_PATH,
            ),
            points_per_segment=2,
        )

        group = projection.to_kpoints_card().to_input_group()
        data = _BANDS_DATA_EXTRACTOR.extract(
            qexsd,
            projection=projection,
            expected_band_count=2,
            reference_energy_ev=1.0,
            reference_label="explicit reference",
        )

        self.assertEqual(group.tag, "K_POINTS crystal_b")
        self.assertEqual(
            group.lines,
            (
                "2",
                "0.0000000000 0.0000000000 0.0000000000 2 ! G",
                "0.5000000000 0.0000000000 0.0000000000 1 ! X",
            ),
        )
        self.assertEqual(projection.expected_sample_count, 3)
        np.testing.assert_allclose(
            data.diagram.energies_ev[0][1], (-1.5, 1.5), rtol=0.0, atol=1.0e-14
        )
        np.testing.assert_allclose(
            data.diagram.shifted_energies_ev[0][0],
            (-3.0, 0.0),
            rtol=0.0,
            atol=1.0e-14,
        )
        self.assertEqual(data.diagram.branches[0].tick_indices, (0, 2))
        np.testing.assert_allclose(
            data.diagram.path_coordinate,
            (0.0, 0.25, 0.5),
            rtol=0.0,
            atol=1.0e-14,
        )
        self.assertEqual(
            data.diagram.sampled_kpoints_reciprocal_fractional,
            ((0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.5, 0.0, 0.0)),
        )
        self.assertIs(data.qexsd, qexsd)
        self.assertEqual(data.maximum_kpoint_deviation, 0.0)

    def test__QeBandsData__keeps_discontinuous_branches_adjacent_without_adding_jump(
        self,
    ) -> None:
        path = BandPath(
            branches=(
                BandPathBranch(
                    (
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                        BandPathVertex("X", (0.5, 0.0, 0.0)),
                    )
                ),
                BandPathBranch(
                    (
                        BandPathVertex("K", (0.5, 0.5, 0.0)),
                        BandPathVertex("G", (0.0, 0.0, 0.0)),
                    )
                ),
            ),
            coordinate_system=BandPathCoordinateSystem.reciprocal_fractional,
            convention="discontinuous test path",
        )
        document = replace(
            QEXSD_FIXTURES.bands_document(),
            k_points=(
                (0.0, 0.0, 0.0),
                (0.25, 0.0, 0.0),
                (0.5, 0.0, 0.0),
                (0.5, 0.5, 0.0),
                (0.25, 0.25, 0.0),
                (0.0, 0.0, 0.0),
            ),
            k_point_weights=(1.0 / 6.0,) * 6,
            sampled_k_point_count=6,
            eigenvalues=((0.0, 1.0),) * 6,
            occupations=((1.0, 0.0),) * 6,
        )

        qexsd = QexsdData.from_document(document)
        data = _BANDS_DATA_EXTRACTOR.extract(
            qexsd,
            projection=QeBandsPathProjection(
                PwDftBandsSimulation(
                    simulation=resolved_pw_dft_simulation(
                        qexsd.final_structure.unit_cell
                    ),
                    path=path,
                ),
                points_per_segment=2,
            ),
        )

        np.testing.assert_allclose(
            data.diagram.path_coordinate[2:4],
            (0.5, 0.5),
            rtol=0.0,
            atol=1.0e-14,
        )
        self.assertEqual(
            tuple(
                (branch.start_index, branch.stop_index)
                for branch in data.diagram.branches
            ),
            ((0, 3), (3, 6)),
        )

    def test__QeBandsData__rejects_declared_band_count_disagreement(self) -> None:
        qexsd = QexsdData.from_document(QEXSD_FIXTURES.bands_document())
        with self.assertRaisesRegex(ValueError, "band count"):
            _BANDS_DATA_EXTRACTOR.extract(
                qexsd,
                projection=QeBandsPathProjection(
                    PwDftBandsSimulation(
                        simulation=resolved_pw_dft_simulation(
                            qexsd.final_structure.unit_cell
                        ),
                        path=_BAND_PATH,
                    ),
                    points_per_segment=2,
                ),
                expected_band_count=3,
            )

    def test__QeBandsData__rejects_qexsd_from_a_different_unit_cell(self) -> None:
        qexsd = QexsdData.from_document(QEXSD_FIXTURES.bands_document())
        other_document = replace(
            QEXSD_FIXTURES.bands_document(),
            direct_lattice_vectors=(
                (2.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
        )
        other_qexsd = QexsdData.from_document(other_document)

        with self.assertRaisesRegex(ValueError, "unit cell disagrees"):
            _BANDS_DATA_EXTRACTOR.extract(
                qexsd,
                projection=QeBandsPathProjection(
                    PwDftBandsSimulation(
                        simulation=resolved_pw_dft_simulation(
                            other_qexsd.final_structure.unit_cell
                        ),
                        path=_BAND_PATH,
                    ),
                    points_per_segment=2,
                ),
            )

    def test__QeBandsData__rejects_qexsd_kpoint_disagreement(self) -> None:
        document = replace(
            QEXSD_FIXTURES.bands_document(),
            k_points=(
                (0.0, 0.0, 0.0),
                (0.26, 0.0, 0.0),
                (0.5, 0.0, 0.0),
            ),
        )
        qexsd = QexsdData.from_document(document)
        with self.assertRaisesRegex(ValueError, "k-points disagree"):
            _BANDS_DATA_EXTRACTOR.extract(
                qexsd,
                projection=QeBandsPathProjection(
                    PwDftBandsSimulation(
                        simulation=resolved_pw_dft_simulation(
                            qexsd.final_structure.unit_cell
                        ),
                        path=_BAND_PATH,
                    ),
                    points_per_segment=2,
                ),
            )


_BANDS_DATA_EXTRACTOR = QeBandsDataExtractor(
    coordinate_tolerance=1.0e-10,
    cell_tolerance=1.0e-7,
)
_BAND_PATH = BandPath(
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


if __name__ == "__main__":
    unittest.main()
