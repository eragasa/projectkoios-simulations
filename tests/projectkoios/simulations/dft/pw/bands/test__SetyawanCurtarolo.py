from __future__ import annotations

import hashlib
import json
import math
import unittest

import numpy as np

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import Atom, AtomicBasis, UnitCell
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.dft.pw.bands import (
    BandPathDirectBasisTransform,
    PwDftBandsSimulation,
)
from projectkoios.simulations.dft.pw.settings import CalculationType, PwDftSettings
from projectkoios.simulations.dft.pw.setyawan_curtarolo_2010 import (
    SETYAWAN_CURTAROLO_CONVENTION_NAME,
    SETYAWAN_CURTAROLO_DOI,
    SETYAWAN_CURTAROLO_REVISION,
    SetyawanCurtaroloAppendixACase,
    SetyawanCurtaroloAppendixACaseSelectionRequest,
    SetyawanCurtaroloAppendixACaseSelectionResult,
    SetyawanCurtaroloAppendixACaseSelector,
    SetyawanCurtaroloBasisTransformSource,
    SetyawanCurtaroloBravaisLattice,
    SetyawanCurtaroloLattice,
    SetyawanCurtaroloPathBinder,
    SetyawanCurtaroloPathBindingRequest,
    SetyawanCurtaroloPathBindingResult,
    SetyawanCurtaroloPathDefinition,
)
from projectkoios.simulations.dft.pw.simulation import PwDftSimulation, PwMatrix3
from tests.support.repository_root import REPOSITORY_ROOT


class SetyawanCurtaroloDataObjectActionTest(unittest.TestCase):
    def test_cross_object_policy_is_owned_only_by_actionizers(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.cub]
        definition = SetyawanCurtaroloPathDefinition(lattice)
        binding_request = SetyawanCurtaroloPathBindingRequest(
            definition=definition,
            simulation=_simulation(lattice.standard_primitive_lattice_vectors_angstrom),
        )

        self.assertIsInstance(lattice, DataObject)
        self.assertIsInstance(definition, DataObject)
        self.assertIsInstance(binding_request, DataObject)
        self.assertFalse(hasattr(SetyawanCurtaroloLattice, "from_bravais_lattice"))
        self.assertFalse(hasattr(SetyawanCurtaroloPathDefinition, "bind"))
        result = SetyawanCurtaroloPathBinder().action(request=binding_request)
        self.assertIsInstance(result, ResultsObject)
        self.assertIs(result.request, binding_request)
        self.assertIs(result.calculation.simulation, binding_request.simulation)

    def test_selects_every_metric_dependent_case_within_declared_bravais_lattice(
        self,
    ) -> None:
        for appendix_a_case, expected in _specimens().items():
            with self.subTest(appendix_a_case=appendix_a_case):
                request = SetyawanCurtaroloAppendixACaseSelectionRequest(
                    bravais_lattice=_bravais_lattice(appendix_a_case),
                    a_angstrom=expected.a_angstrom,
                    b_angstrom=expected.b_angstrom,
                    c_angstrom=expected.c_angstrom,
                    alpha_degrees=expected.alpha_degrees,
                    beta_degrees=expected.beta_degrees,
                    gamma_degrees=expected.gamma_degrees,
                )
                result = SetyawanCurtaroloAppendixACaseSelector().action(
                    request=request
                )
                actual = result.lattice
                self.assertIsInstance(request, DataObject)
                self.assertIsInstance(
                    result,
                    SetyawanCurtaroloAppendixACaseSelectionResult,
                )
                self.assertIsInstance(result, ResultsObject)
                self.assertIs(result.request, request)
                self.assertEqual(actual, expected)
                self.assertIs(actual.bravais_lattice, request.bravais_lattice)

    def test_standard_conventional_and_primitive_cell_volume_ratios(self) -> None:
        face_centered = {
            SetyawanCurtaroloAppendixACase.fcc,
            SetyawanCurtaroloAppendixACase.orcf1,
            SetyawanCurtaroloAppendixACase.orcf2,
            SetyawanCurtaroloAppendixACase.orcf3,
        }
        body_or_base_centered = {
            SetyawanCurtaroloAppendixACase.bcc,
            SetyawanCurtaroloAppendixACase.bct1,
            SetyawanCurtaroloAppendixACase.bct2,
            SetyawanCurtaroloAppendixACase.orci,
            SetyawanCurtaroloAppendixACase.orcc,
            SetyawanCurtaroloAppendixACase.mclc1,
            SetyawanCurtaroloAppendixACase.mclc2,
            SetyawanCurtaroloAppendixACase.mclc3,
            SetyawanCurtaroloAppendixACase.mclc4,
            SetyawanCurtaroloAppendixACase.mclc5,
        }
        for appendix_a_case, lattice in _specimens().items():
            with self.subTest(appendix_a_case=appendix_a_case):
                conventional_volume = abs(
                    float(
                        np.linalg.det(
                            np.asarray(
                                lattice.standard_conventional_lattice_vectors_angstrom
                            )
                        )
                    )
                )
                primitive_volume = abs(
                    float(
                        np.linalg.det(
                            np.asarray(
                                lattice.standard_primitive_lattice_vectors_angstrom
                            )
                        )
                    )
                )
                expected_ratio = (
                    4.0
                    if appendix_a_case in face_centered
                    else 2.0
                    if appendix_a_case in body_or_base_centered
                    else 1.0
                )
                self.assertAlmostEqual(
                    conventional_volume / primitive_volume,
                    expected_ratio,
                )

    def test_covers_every_appendix_a_case(self) -> None:
        specimens = _specimens()
        expected_special_point_counts = {
            SetyawanCurtaroloAppendixACase.cub: 4,
            SetyawanCurtaroloAppendixACase.fcc: 6,
            SetyawanCurtaroloAppendixACase.bcc: 4,
            SetyawanCurtaroloAppendixACase.tet: 6,
            SetyawanCurtaroloAppendixACase.bct1: 7,
            SetyawanCurtaroloAppendixACase.bct2: 9,
            SetyawanCurtaroloAppendixACase.orc: 8,
            SetyawanCurtaroloAppendixACase.orcf1: 9,
            SetyawanCurtaroloAppendixACase.orcf2: 11,
            SetyawanCurtaroloAppendixACase.orcf3: 9,
            SetyawanCurtaroloAppendixACase.orci: 13,
            SetyawanCurtaroloAppendixACase.orcc: 10,
            SetyawanCurtaroloAppendixACase.hex: 6,
            SetyawanCurtaroloAppendixACase.rhl1: 12,
            SetyawanCurtaroloAppendixACase.rhl2: 8,
            SetyawanCurtaroloAppendixACase.mcl: 16,
            SetyawanCurtaroloAppendixACase.mclc1: 17,
            SetyawanCurtaroloAppendixACase.mclc2: 17,
            SetyawanCurtaroloAppendixACase.mclc3: 17,
            SetyawanCurtaroloAppendixACase.mclc4: 17,
            SetyawanCurtaroloAppendixACase.mclc5: 19,
            SetyawanCurtaroloAppendixACase.tri1a: 8,
            SetyawanCurtaroloAppendixACase.tri1b: 8,
            SetyawanCurtaroloAppendixACase.tri2a: 8,
            SetyawanCurtaroloAppendixACase.tri2b: 8,
        }
        expected_segment_counts = {
            SetyawanCurtaroloAppendixACase.cub: 6,
            SetyawanCurtaroloAppendixACase.fcc: 10,
            SetyawanCurtaroloAppendixACase.bcc: 6,
            SetyawanCurtaroloAppendixACase.tet: 9,
            SetyawanCurtaroloAppendixACase.bct1: 9,
            SetyawanCurtaroloAppendixACase.bct2: 11,
            SetyawanCurtaroloAppendixACase.orc: 12,
            SetyawanCurtaroloAppendixACase.orcf1: 11,
            SetyawanCurtaroloAppendixACase.orcf2: 13,
            SetyawanCurtaroloAppendixACase.orcf3: 10,
            SetyawanCurtaroloAppendixACase.orci: 13,
            SetyawanCurtaroloAppendixACase.orcc: 12,
            SetyawanCurtaroloAppendixACase.hex: 9,
            SetyawanCurtaroloAppendixACase.rhl1: 9,
            SetyawanCurtaroloAppendixACase.rhl2: 9,
            SetyawanCurtaroloAppendixACase.mcl: 11,
            SetyawanCurtaroloAppendixACase.mclc1: 10,
            SetyawanCurtaroloAppendixACase.mclc2: 8,
            SetyawanCurtaroloAppendixACase.mclc3: 11,
            SetyawanCurtaroloAppendixACase.mclc4: 10,
            SetyawanCurtaroloAppendixACase.mclc5: 12,
            SetyawanCurtaroloAppendixACase.tri1a: 7,
            SetyawanCurtaroloAppendixACase.tri1b: 7,
            SetyawanCurtaroloAppendixACase.tri2a: 7,
            SetyawanCurtaroloAppendixACase.tri2b: 7,
        }

        self.assertEqual(set(specimens), set(SetyawanCurtaroloAppendixACase))
        for appendix_a_case, lattice in specimens.items():
            with self.subTest(appendix_a_case=appendix_a_case):
                definition = SetyawanCurtaroloPathDefinition(lattice)
                path = definition.path
                self.assertEqual(
                    len(definition.standard_special_points),
                    expected_special_point_counts[appendix_a_case],
                )
                self.assertEqual(
                    path.segment_count, expected_segment_counts[appendix_a_case]
                )
                self.assertIn(appendix_a_case.value, path.convention)
                self.assertIn(SETYAWAN_CURTAROLO_DOI, path.convention)
                self.assertIsNotNone(path.provenance)
                assert path.provenance is not None
                self.assertEqual(
                    path.provenance.convention_name,
                    SETYAWAN_CURTAROLO_CONVENTION_NAME,
                )
                self.assertEqual(
                    path.provenance.convention_revision,
                    SETYAWAN_CURTAROLO_REVISION,
                )
                self.assertEqual(path.provenance.source_doi, SETYAWAN_CURTAROLO_DOI)
                self.assertEqual(
                    path.provenance.bravais_lattice,
                    lattice.bravais_lattice.value,
                )
                self.assertEqual(path.provenance.appendix_a_case, appendix_a_case.value)
                self.assertEqual(
                    path.provenance.direct_basis_transform,
                    ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                )

    def test_all_cells_points_and_paths_match_the_appendix_a_golden_fixture(
        self,
    ) -> None:
        fixture = json.loads(
            (
                REPOSITORY_ROOT
                / "tests/fixtures/setyawan_curtarolo_2010/appendix_a_golden.json"
            ).read_text()
        )

        self.assertEqual(fixture["scientific_source"]["doi"], SETYAWAN_CURTAROLO_DOI)
        self.assertEqual(
            len(fixture["appendix_a_cases"]), len(SetyawanCurtaroloAppendixACase)
        )
        for expected in fixture["appendix_a_cases"]:
            appendix_a_case = SetyawanCurtaroloAppendixACase(
                expected["appendix_a_case"]
            )
            with self.subTest(appendix_a_case=appendix_a_case):
                lattice = SetyawanCurtaroloLattice(
                    appendix_a_case=appendix_a_case,
                    **expected["metrics"],
                )
                definition = SetyawanCurtaroloPathDefinition(lattice)
                self._assert_nested_floats_equal(
                    lattice.standard_conventional_lattice_vectors_angstrom,
                    expected["standard_conventional_lattice_vectors_angstrom"],
                )
                self._assert_nested_floats_equal(
                    lattice.standard_primitive_lattice_vectors_angstrom,
                    expected["standard_primitive_lattice_vectors_angstrom"],
                )
                actual_points = {
                    point.label: point.coordinates
                    for point in definition.standard_special_points
                }
                expected_points = {
                    point["label"]: point["coordinates"]
                    for point in expected["standard_special_points"]
                }
                self.assertEqual(actual_points.keys(), expected_points.keys())
                for label, coordinates in actual_points.items():
                    self._assert_nested_floats_equal(
                        coordinates,
                        expected_points[label],
                    )
                self.assertEqual(
                    tuple(
                        tuple(vertex.label for vertex in branch.vertices)
                        for branch in definition.path.branches
                    ),
                    tuple(tuple(branch) for branch in expected["branches"]),
                )

    def _assert_nested_floats_equal(
        self,
        actual: object,
        expected: object,
    ) -> None:
        if isinstance(actual, tuple):
            self.assertIsInstance(expected, list)
            assert isinstance(expected, list)
            self.assertEqual(len(actual), len(expected))
            for actual_item, expected_item in zip(actual, expected, strict=True):
                self._assert_nested_floats_equal(actual_item, expected_item)
            return
        self.assertIsInstance(actual, float)
        self.assertIsInstance(expected, float)
        assert isinstance(actual, float)
        assert isinstance(expected, float)
        self.assertAlmostEqual(actual, expected, places=12)

    def test_fcc_path_matches_appendix_a_table_3(self) -> None:
        definition = SetyawanCurtaroloPathDefinition(
            _specimens()[SetyawanCurtaroloAppendixACase.fcc]
        )

        self.assertEqual(
            tuple(vertex.label for vertex in definition.standard_special_points),
            ("Γ", "K", "L", "U", "W", "X"),
        )
        self.assertEqual(
            tuple(vertex.label for vertex in definition.path.branches[0].vertices),
            ("Γ", "X", "W", "K", "Γ", "L", "U", "W", "L", "K"),
        )
        self.assertEqual(
            definition.path.branches[0].vertices[1].coordinates,
            (0.5, 0.0, 0.5),
        )
        self.assertEqual(
            definition.path.branches[0].vertices[2].coordinates,
            (0.5, 0.25, 0.75),
        )
        self.assertEqual(
            tuple(vertex.label for vertex in definition.path.branches[1].vertices),
            ("U", "X"),
        )

    def test_parameterized_bct2_points_follow_table_7(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.bct2]
        path = SetyawanCurtaroloPathDefinition(lattice).path
        vertices = {
            vertex.label: vertex.coordinates
            for branch in path.branches
            for vertex in branch.vertices
        }
        eta = (1 + lattice.a_angstrom**2 / lattice.c_angstrom**2) / 4
        zeta = lattice.a_angstrom**2 / (2 * lattice.c_angstrom**2)

        self.assertEqual(vertices["Σ"], (-eta, eta, eta))
        self.assertEqual(vertices["Y"], (-zeta, zeta, 0.5))

    def test_binding_transforms_reciprocal_coordinates_for_cyclic_basis(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.fcc]
        standard = lattice.standard_primitive_lattice_vectors_angstrom
        cyclic = (standard[2], standard[0], standard[1])

        definition = SetyawanCurtaroloPathDefinition(lattice)
        binding = _binding(definition, _simulation(cyclic))
        calculation = binding.calculation

        self.assertIs(
            binding.basis_transform_source,
            SetyawanCurtaroloBasisTransformSource.recovered,
        )
        self.assertEqual(
            binding.direct_basis_transform,
            ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        )
        self.assertIn("basis-transformed", calculation.path.convention)
        self.assertIsNotNone(calculation.path.provenance)
        assert calculation.path.provenance is not None
        self.assertEqual(
            calculation.path.provenance.direct_basis_transform,
            ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
        )
        self.assertEqual(
            calculation.path.branches[0].vertices[1].coordinates,
            (0.5, 0.5, 0.0),
        )
        self.assertEqual(
            calculation.simulation.lattice_vectors_angstrom,
            cyclic,
        )

    def test_binding_accepts_a_global_cartesian_rotation(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.orc]
        standard = lattice.standard_primitive_lattice_vectors_angstrom
        rotated = _rotate_about_z(standard, angle_radians=0.37)
        definition = SetyawanCurtaroloPathDefinition(lattice)

        standard_calculation = _bind(definition, _simulation(standard))
        rotated_calculation = _bind(definition, _simulation(rotated))

        self.assertEqual(rotated_calculation.path, standard_calculation.path)
        self.assertEqual(
            rotated_calculation.simulation.lattice_vectors_angstrom,
            rotated,
        )

    def test_declared_basis_transform_can_be_combined_with_rotation(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.orc]
        standard = lattice.standard_primitive_lattice_vectors_angstrom
        cyclic_transform = ((0, 0, 1), (1, 0, 0), (0, 1, 0))
        cyclic = (standard[2], standard[0], standard[1])
        rotated_cyclic = _rotate_about_z(cyclic, angle_radians=0.37)
        definition = SetyawanCurtaroloPathDefinition(lattice)

        expected = _bind(definition, _simulation(cyclic))
        binding = _binding(
            definition,
            _simulation(rotated_cyclic),
            direct_basis_transform=cyclic_transform,
        )
        actual = binding.calculation

        self.assertIs(
            binding.basis_transform_source,
            SetyawanCurtaroloBasisTransformSource.declared,
        )
        self.assertEqual(binding.direct_basis_transform, cyclic_transform)
        self.assertEqual(actual.path, expected.path)
        self.assertEqual(
            actual.simulation.lattice_vectors_angstrom,
            rotated_cyclic,
        )

    def test_binding_rejects_a_nonunimodular_declared_transform(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.orc]
        standard = lattice.standard_primitive_lattice_vectors_angstrom

        with self.assertRaisesRegex(ValueError, "integer-unimodular"):
            SetyawanCurtaroloPathBindingRequest(
                definition=SetyawanCurtaroloPathDefinition(lattice),
                simulation=_simulation(standard),
                direct_basis_transform=((2, 0, 0), (0, 1, 0), (0, 0, 1)),
            )

    def test_neutral_silicon_declaration_matches_generated_fcc_path(self) -> None:
        example_directory = (
            REPOSITORY_ROOT / "examples/projectkoios/simulations/dft/pw/Si/primitive"
        )
        declaration = json.loads(
            (
                example_directory
                / "Si.primitive.setyawan-curtarolo-2010-band-path.json"
            ).read_text()
        )
        structure_bytes = (example_directory / "Si.primitive.json").read_bytes()
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.fcc]
        standard = lattice.standard_primitive_lattice_vectors_angstrom
        calculation = _bind(
            SetyawanCurtaroloPathDefinition(lattice),
            _simulation((standard[2], standard[0], standard[1])),
        )

        self.assertEqual(
            declaration["structure"]["sha256"],
            hashlib.sha256(structure_bytes).hexdigest(),
        )
        self.assertIsNotNone(calculation.path.provenance)
        assert calculation.path.provenance is not None
        self.assertEqual(
            declaration["provenance"],
            {
                "convention_name": calculation.path.provenance.convention_name,
                "convention_revision": (
                    calculation.path.provenance.convention_revision
                ),
                "source_doi": calculation.path.provenance.source_doi,
                "bravais_lattice": calculation.path.provenance.bravais_lattice,
                "appendix_a_case": calculation.path.provenance.appendix_a_case,
                "direct_basis_transform": [
                    list(row)
                    for row in calculation.path.provenance.direct_basis_transform
                ],
            },
        )
        self.assertEqual(
            tuple(
                tuple(
                    (
                        vertex["label"],
                        tuple(vertex["coordinates"]),
                    )
                    for vertex in branch["vertices"]
                )
                for branch in declaration["branches"]
            ),
            tuple(
                tuple((vertex.label, vertex.coordinates) for vertex in branch.vertices)
                for branch in calculation.path.branches
            ),
        )

    def test_binding_rejects_a_non_equivalent_simulation_cell(self) -> None:
        lattice = _specimens()[SetyawanCurtaroloAppendixACase.fcc]
        vectors = lattice.standard_primitive_lattice_vectors_angstrom
        distorted = (
            (vectors[0][0] + 0.01, vectors[0][1], vectors[0][2]),
            vectors[1],
            vectors[2],
        )

        with self.assertRaisesRegex(ValueError, "integer-unimodular basis"):
            _bind(
                SetyawanCurtaroloPathDefinition(lattice),
                _simulation(distorted),
            )

    def test_rejects_a_wrong_declared_appendix_a_case(self) -> None:
        with self.assertRaisesRegex(ValueError, "BCT1 requires c < a"):
            SetyawanCurtaroloLattice(
                appendix_a_case=SetyawanCurtaroloAppendixACase.bct1,
                a_angstrom=3.0,
                b_angstrom=3.0,
                c_angstrom=4.0,
            )


def _bravais_lattice(
    appendix_a_case: SetyawanCurtaroloAppendixACase,
) -> SetyawanCurtaroloBravaisLattice:
    bravais = SetyawanCurtaroloBravaisLattice
    groups = {
        bravais.cubic_primitive: {SetyawanCurtaroloAppendixACase.cub},
        bravais.cubic_face_centered: {SetyawanCurtaroloAppendixACase.fcc},
        bravais.cubic_body_centered: {SetyawanCurtaroloAppendixACase.bcc},
        bravais.tetragonal_primitive: {SetyawanCurtaroloAppendixACase.tet},
        bravais.tetragonal_body_centered: {
            SetyawanCurtaroloAppendixACase.bct1,
            SetyawanCurtaroloAppendixACase.bct2,
        },
        bravais.orthorhombic_primitive: {SetyawanCurtaroloAppendixACase.orc},
        bravais.orthorhombic_face_centered: {
            SetyawanCurtaroloAppendixACase.orcf1,
            SetyawanCurtaroloAppendixACase.orcf2,
            SetyawanCurtaroloAppendixACase.orcf3,
        },
        bravais.orthorhombic_body_centered: {SetyawanCurtaroloAppendixACase.orci},
        bravais.orthorhombic_base_centered: {SetyawanCurtaroloAppendixACase.orcc},
        bravais.hexagonal_primitive: {SetyawanCurtaroloAppendixACase.hex},
        bravais.rhombohedral: {
            SetyawanCurtaroloAppendixACase.rhl1,
            SetyawanCurtaroloAppendixACase.rhl2,
        },
        bravais.monoclinic_primitive: {SetyawanCurtaroloAppendixACase.mcl},
        bravais.monoclinic_base_centered: {
            SetyawanCurtaroloAppendixACase.mclc1,
            SetyawanCurtaroloAppendixACase.mclc2,
            SetyawanCurtaroloAppendixACase.mclc3,
            SetyawanCurtaroloAppendixACase.mclc4,
            SetyawanCurtaroloAppendixACase.mclc5,
        },
        bravais.triclinic_primitive: {
            SetyawanCurtaroloAppendixACase.tri1a,
            SetyawanCurtaroloAppendixACase.tri1b,
            SetyawanCurtaroloAppendixACase.tri2a,
            SetyawanCurtaroloAppendixACase.tri2b,
        },
    }
    return next(
        key
        for key, appendix_a_cases in groups.items()
        if appendix_a_case in appendix_a_cases
    )


def _specimens() -> dict[SetyawanCurtaroloAppendixACase, SetyawanCurtaroloLattice]:
    appendix_a_case = SetyawanCurtaroloAppendixACase
    right = {
        "alpha_degrees": 90.0,
        "beta_degrees": 90.0,
        "gamma_degrees": 90.0,
    }
    specimens = {
        appendix_a_case.cub: _lattice(appendix_a_case.cub, 3.0, 3.0, 3.0, **right),
        appendix_a_case.fcc: _lattice(appendix_a_case.fcc, 5.43, 5.43, 5.43, **right),
        appendix_a_case.bcc: _lattice(appendix_a_case.bcc, 3.0, 3.0, 3.0, **right),
        appendix_a_case.tet: _lattice(appendix_a_case.tet, 3.0, 3.0, 4.0, **right),
        appendix_a_case.bct1: _lattice(appendix_a_case.bct1, 4.0, 4.0, 3.0, **right),
        appendix_a_case.bct2: _lattice(appendix_a_case.bct2, 3.0, 3.0, 4.0, **right),
        appendix_a_case.orc: _lattice(appendix_a_case.orc, 2.0, 3.0, 4.0, **right),
        appendix_a_case.orcf1: _lattice(appendix_a_case.orcf1, 2.0, 3.0, 4.0, **right),
        appendix_a_case.orcf2: _lattice(appendix_a_case.orcf2, 2.5, 3.0, 4.0, **right),
        appendix_a_case.orcf3: _lattice(
            appendix_a_case.orcf3,
            20.0 / math.sqrt(41.0),
            4.0,
            5.0,
            **right,
        ),
        appendix_a_case.orci: _lattice(appendix_a_case.orci, 2.0, 3.0, 4.0, **right),
        appendix_a_case.orcc: _lattice(appendix_a_case.orcc, 2.0, 3.0, 4.0, **right),
        appendix_a_case.hex: _lattice(
            appendix_a_case.hex,
            3.0,
            3.0,
            5.0,
            alpha_degrees=90.0,
            beta_degrees=90.0,
            gamma_degrees=120.0,
        ),
        appendix_a_case.rhl1: _lattice(
            appendix_a_case.rhl1,
            3.0,
            3.0,
            3.0,
            alpha_degrees=75.0,
            beta_degrees=75.0,
            gamma_degrees=75.0,
        ),
        appendix_a_case.rhl2: _lattice(
            appendix_a_case.rhl2,
            3.0,
            3.0,
            3.0,
            alpha_degrees=105.0,
            beta_degrees=105.0,
            gamma_degrees=105.0,
        ),
        appendix_a_case.mcl: _monoclinic(appendix_a_case.mcl, 2.0, 3.0, 5.0, 70.0),
        appendix_a_case.mclc1: _monoclinic(appendix_a_case.mclc1, 2.0, 3.0, 5.0, 70.0),
        appendix_a_case.mclc2: _monoclinic(
            appendix_a_case.mclc2,
            2.0,
            2.0 / math.sin(math.radians(70.0)),
            5.0,
            70.0,
        ),
        appendix_a_case.mclc3: _monoclinic(appendix_a_case.mclc3, 2.0, 2.0, 6.0, 60.0),
        appendix_a_case.mclc4: _monoclinic(appendix_a_case.mclc4, 3.0, 3.0, 6.0, 60.0),
        appendix_a_case.mclc5: _monoclinic(appendix_a_case.mclc5, 2.0, 2.0, 5.0, 70.0),
        appendix_a_case.tri1a: _triclinic(appendix_a_case.tri1a, 70.0, 70.0, 70.0),
        appendix_a_case.tri1b: _triclinic(appendix_a_case.tri1b, 110.0, 110.0, 110.0),
        appendix_a_case.tri2a: _triclinic(
            appendix_a_case.tri2a,
            70.0,
            70.0,
            math.degrees(math.acos(math.cos(math.radians(70.0)) ** 2)),
        ),
        appendix_a_case.tri2b: _triclinic(
            appendix_a_case.tri2b,
            110.0,
            110.0,
            math.degrees(math.acos(math.cos(math.radians(110.0)) ** 2)),
        ),
    }
    return specimens


def _lattice(
    appendix_a_case: SetyawanCurtaroloAppendixACase,
    a: float,
    b: float,
    c: float,
    *,
    alpha_degrees: float,
    beta_degrees: float,
    gamma_degrees: float,
) -> SetyawanCurtaroloLattice:
    return SetyawanCurtaroloLattice(
        appendix_a_case=appendix_a_case,
        a_angstrom=a,
        b_angstrom=b,
        c_angstrom=c,
        alpha_degrees=alpha_degrees,
        beta_degrees=beta_degrees,
        gamma_degrees=gamma_degrees,
    )


def _monoclinic(
    appendix_a_case: SetyawanCurtaroloAppendixACase,
    a: float,
    b: float,
    c: float,
    alpha: float,
) -> SetyawanCurtaroloLattice:
    return _lattice(
        appendix_a_case,
        a,
        b,
        c,
        alpha_degrees=alpha,
        beta_degrees=90.0,
        gamma_degrees=90.0,
    )


def _triclinic(
    appendix_a_case: SetyawanCurtaroloAppendixACase,
    alpha: float,
    beta: float,
    gamma: float,
) -> SetyawanCurtaroloLattice:
    return _lattice(
        appendix_a_case,
        2.0,
        3.0,
        4.0,
        alpha_degrees=alpha,
        beta_degrees=beta,
        gamma_degrees=gamma,
    )


def _binding(
    definition: SetyawanCurtaroloPathDefinition,
    simulation: PwDftSimulation,
    *,
    direct_basis_transform: BandPathDirectBasisTransform | None = None,
) -> SetyawanCurtaroloPathBindingResult:
    request = SetyawanCurtaroloPathBindingRequest(
        definition=definition,
        simulation=simulation,
        direct_basis_transform=direct_basis_transform,
    )
    return SetyawanCurtaroloPathBinder().action(request=request)


def _bind(
    definition: SetyawanCurtaroloPathDefinition,
    simulation: PwDftSimulation,
    *,
    direct_basis_transform: BandPathDirectBasisTransform | None = None,
) -> PwDftBandsSimulation:
    return _binding(
        definition,
        simulation,
        direct_basis_transform=direct_basis_transform,
    ).calculation


def _rotate_about_z(vectors: PwMatrix3, *, angle_radians: float) -> PwMatrix3:
    cosine = math.cos(angle_radians)
    sine = math.sin(angle_radians)
    rotation: PwMatrix3 = (
        (cosine, sine, 0.0),
        (-sine, cosine, 0.0),
        (0.0, 0.0, 1.0),
    )
    return tuple(
        tuple(
            sum(vector[index] * rotation[index][column] for index in range(3))
            for column in range(3)
        )
        for vector in vectors
    )  # type: ignore[return-value]


def _simulation(vectors: PwMatrix3) -> PwDftSimulation:
    return PwDftSimulation(
        unit_cell=UnitCell(
            direct_lattice=DirectLattice3D(
                a1=np.asarray(vectors[0]),
                a2=np.asarray(vectors[1]),
                a3=np.asarray(vectors[2]),
            ),
            lattice_parameter=ScalarQuantity(1.0, PhysicalUnit("angstrom")),
            atomic_basis=AtomicBasis(
                atoms=(
                    Atom(
                        symbol="Si",
                        position_fractional=VectorQuantity(np.zeros(3), Unitless()),
                    ),
                )
            ),
        ),
        settings=PwDftSettings(CalculationType.bands),
    )


if __name__ == "__main__":
    unittest.main()
