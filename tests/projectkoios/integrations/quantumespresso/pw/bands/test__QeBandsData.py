from __future__ import annotations

import math
import unittest
from types import SimpleNamespace

from projectkoios.integrations.quantumespresso.pw.bands.data_extraction import (
    QeBandsDataExtractor,
)
from projectkoios.integrations.quantumespresso.pw.bands.path import (
    QeBandsPathProjection,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.qexsd import (
    QeQexsdData,
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
from tests.projectkoios.simulations.dft.pw.support import (
    resolved_pw_dft_simulation,
)

_HARTREE_TO_EV = 27.211386245988
_BOHR_TO_ANGSTROM = 0.529177210903


class QeBandsDataTest(unittest.TestCase):
    def test_projects_a_bound_setyawan_curtarolo_path(self) -> None:
        qexsd = QeQexsdData.from_document(_document())
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

    def test_projects_crystal_b_path_and_extracts_full_precision_qexsd(self) -> None:
        qexsd = QeQexsdData.from_document(_document())
        projection = QeBandsPathProjection(
            _calculation(_path(), qexsd),
            points_per_segment=2,
        )

        group = projection.to_kpoints_card().to_input_group()
        data = QeBandsDataExtractor().extract(
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
        self.assertEqual(data.diagram.energies_ev[0][1], (-1.5, 1.5))
        self.assertEqual(data.diagram.shifted_energies_ev[0][0], (-3.0, 0.0))
        self.assertEqual(data.diagram.branches[0].tick_indices, (0, 2))
        self.assertEqual(data.diagram.path_coordinate, (0.0, 0.25, 0.5))
        self.assertEqual(
            data.diagram.sampled_kpoints_reciprocal_fractional,
            ((0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.5, 0.0, 0.0)),
        )
        self.assertIs(data.qexsd, qexsd)
        self.assertEqual(data.maximum_kpoint_deviation, 0.0)

    def test_keeps_discontinuous_branches_adjacent_without_adding_jump(self) -> None:
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
        document = _document()
        document.k_points = (
            (0.0, 0.0, 0.0),
            (0.25, 0.0, 0.0),
            (0.5, 0.0, 0.0),
            (0.5, 0.5, 0.0),
            (0.25, 0.25, 0.0),
            (0.0, 0.0, 0.0),
        )
        document.sampled_k_point_count = 6
        document.eigenvalues = ((0.0, 1.0),) * 6
        document.occupations = ((1.0, 0.0),) * 6

        qexsd = QeQexsdData.from_document(document)
        data = QeBandsDataExtractor().extract(
            qexsd,
            projection=QeBandsPathProjection(
                _calculation(path, qexsd),
                points_per_segment=2,
            ),
        )

        self.assertEqual(data.diagram.path_coordinate[2], 0.5)
        self.assertEqual(data.diagram.path_coordinate[3], 0.5)
        self.assertEqual(
            tuple(
                (branch.start_index, branch.stop_index)
                for branch in data.diagram.branches
            ),
            ((0, 3), (3, 6)),
        )

    def test_rejects_declared_band_count_disagreement(self) -> None:
        qexsd = QeQexsdData.from_document(_document())
        with self.assertRaisesRegex(ValueError, "band count"):
            QeBandsDataExtractor().extract(
                qexsd,
                projection=QeBandsPathProjection(
                    _calculation(_path(), qexsd),
                    points_per_segment=2,
                ),
                expected_band_count=3,
            )

    def test_rejects_qexsd_from_a_different_unit_cell(self) -> None:
        qexsd = QeQexsdData.from_document(_document())
        other_document = _document()
        other_document.direct_lattice_vectors = (
            (2.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        other_qexsd = QeQexsdData.from_document(other_document)

        with self.assertRaisesRegex(ValueError, "unit cell disagrees"):
            QeBandsDataExtractor().extract(
                qexsd,
                projection=QeBandsPathProjection(
                    _calculation(_path(), other_qexsd),
                    points_per_segment=2,
                ),
            )

    def test_rejects_qexsd_kpoint_disagreement(self) -> None:
        document = _document()
        document.k_points = (
            (0.0, 0.0, 0.0),
            (0.26, 0.0, 0.0),
            (0.5, 0.0, 0.0),
        )
        qexsd = QeQexsdData.from_document(document)
        with self.assertRaisesRegex(ValueError, "k-points disagree"):
            QeBandsDataExtractor().extract(
                qexsd,
                projection=QeBandsPathProjection(
                    _calculation(_path(), qexsd),
                    points_per_segment=2,
                ),
            )


def _document() -> SimpleNamespace:
    energies_ev = ((-2.0, 1.0), (-1.5, 1.5), (-1.0, 2.0))
    return SimpleNamespace(
        source_path="/test/data-file-schema.xml",
        source_sha256="0" * 64,
        source_byte_count=123,
        qexsd_version="25.05.21",
        producing_application="Quantum ESPRESSO",
        producing_application_version="7.5",
        declared_unit_system_label="Hartree atomic units",
        atomic_structure_alat=2.0 * math.pi / _BOHR_TO_ANGSTROM,
        direct_lattice_vectors=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        direct_lattice_source_label="output/atomic_structure/cell",
        reciprocal_lattice_coefficients=(
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        reciprocal_lattice_source_label="output/basis_set/reciprocal_lattice",
        atoms=((1, "Si", (0.0, 0.0, 0.0)),),
        declared_atom_count=1,
        atomic_positions_source_label="output/atomic_structure/atomic_positions",
        k_points=((0.0, 0.0, 0.0), (0.25, 0.0, 0.0), (0.5, 0.0, 0.0)),
        k_point_source_label="output/band_structure/ks_energies/k_point",
        eigenvalues=tuple(
            tuple(value / _HARTREE_TO_EV for value in row) for row in energies_ev
        ),
        occupations=((1.0, 0.0), (1.0, 0.0), (1.0, 0.0)),
        eigenvalue_source_label="output/band_structure/ks_energies/eigenvalues",
        sampled_k_point_count=3,
        band_count=2,
        exit_status=0,
    )


def _path() -> BandPath:
    return BandPath(
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


def _calculation(path: BandPath, qexsd: QeQexsdData) -> PwDftBandsSimulation:
    return PwDftBandsSimulation(
        simulation=resolved_pw_dft_simulation(qexsd.final_structure.unit_cell),
        path=path,
    )


if __name__ == "__main__":
    unittest.main()
