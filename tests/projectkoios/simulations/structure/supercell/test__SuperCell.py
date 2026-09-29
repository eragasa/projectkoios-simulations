from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

import numpy as np

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    ConventionalUnitCell,
    UnitCell,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.structure import (
    SuperCell,
    SuperCellBuilder,
    SuperCellConstructionRequest,
    SuperCellConstructionResult,
    SuperCellSubstitutionRequest,
    SuperCellSubstitutionResult,
    SuperCellSubstitutor,
    UnitCellSiteOrigin,
)


class SuperCellTest(unittest.TestCase):
    def test_replicates_the_conventional_silicon_cell(self) -> None:
        source = _conventional_silicon_cell()
        request = SuperCellConstructionRequest(
            source_unit_cell=source,
            repetitions=(3, 3, 3),
        )

        result = SuperCellBuilder().action(request=request)
        supercell = result.supercell

        self.assertIsInstance(request, DataObject)
        self.assertIsInstance(result, SuperCellConstructionResult)
        self.assertIsInstance(result, ResultsObject)
        self.assertIs(result.request, request)
        self.assertIsInstance(supercell, SuperCell)
        self.assertIsInstance(supercell, UnitCell)
        self.assertIs(supercell.source_unit_cell, source)
        self.assertEqual(supercell.repetitions, (3, 3, 3))
        self.assertEqual(len(supercell.atomic_basis.atoms), 216)
        self.assertEqual(len(supercell.site_origins), 216)
        np.testing.assert_array_equal(
            supercell.H.magnitude,
            np.diag([16.29, 16.29, 16.29]),
        )
        self.assertEqual(
            supercell.site_origins[:9],
            tuple(
                UnitCellSiteOrigin(
                    source_atom_index=source_atom_index,
                    translation=translation,
                )
                for translation in ((0, 0, 0), (0, 0, 1))
                for source_atom_index in range(8)
            )[:9],
        )
        self.assertTrue(
            all(atom.symbol == "Si" for atom in supercell.atomic_basis.atoms)
        )
        positions = np.asarray(
            [
                atom.position_fractional.magnitude
                for atom in supercell.atomic_basis.atoms
            ]
        )
        self.assertTrue(np.all(positions >= 0.0))
        self.assertTrue(np.all(positions < 1.0))
        self.assertEqual(len({tuple(position) for position in positions}), 216)

    def test_constructs_expected_laptop_scale_atom_counts(self) -> None:
        source = _conventional_silicon_cell()

        for repetitions, expected_count in (
            ((2, 2, 2), 64),
            ((3, 3, 3), 216),
            ((4, 4, 4), 512),
        ):
            with self.subTest(repetitions=repetitions):
                result = SuperCellBuilder().action(
                    request=SuperCellConstructionRequest(
                        source_unit_cell=source,
                        repetitions=repetitions,
                    )
                )
                self.assertEqual(
                    len(result.supercell.atomic_basis.atoms),
                    expected_count,
                )

    def test_substitutes_exactly_one_provenance_identified_site(self) -> None:
        pristine = (
            SuperCellBuilder()
            .action(
                request=SuperCellConstructionRequest(
                    source_unit_cell=_conventional_silicon_cell(),
                    repetitions=(3, 3, 3),
                )
            )
            .supercell
        )
        request = SuperCellSubstitutionRequest(
            supercell=pristine,
            source_atom_index=4,
            translation=(1, 1, 1),
            replacement_symbol="P",
        )

        result = SuperCellSubstitutor().action(request=request)

        self.assertIsInstance(request, DataObject)
        self.assertIsInstance(result, SuperCellSubstitutionResult)
        self.assertIsInstance(result, ResultsObject)
        self.assertIs(result.request, request)
        self.assertIsInstance(result.supercell, SuperCell)
        self.assertIs(result.supercell.source_unit_cell, pristine.source_unit_cell)
        self.assertIs(result.supercell.site_origins, pristine.site_origins)
        self.assertEqual(
            result.supercell.site_origins[result.substituted_atom_index],
            UnitCellSiteOrigin(
                source_atom_index=4,
                translation=(1, 1, 1),
            ),
        )
        symbols = [atom.symbol for atom in result.supercell.atomic_basis.atoms]
        self.assertEqual(symbols.count("P"), 1)
        self.assertEqual(symbols.count("Si"), 215)
        for atom_index, (before, after) in enumerate(
            zip(
                pristine.atomic_basis.atoms,
                result.supercell.atomic_basis.atoms,
                strict=True,
            )
        ):
            np.testing.assert_array_equal(
                after.position_fractional.magnitude,
                before.position_fractional.magnitude,
            )
            if atom_index != result.substituted_atom_index:
                self.assertEqual(after.symbol, before.symbol)

    def test_supports_boron_without_embedding_dopant_policy(self) -> None:
        pristine = (
            SuperCellBuilder()
            .action(
                request=SuperCellConstructionRequest(
                    source_unit_cell=_conventional_silicon_cell(),
                    repetitions=(2, 2, 2),
                )
            )
            .supercell
        )

        result = SuperCellSubstitutor().action(
            request=SuperCellSubstitutionRequest(
                supercell=pristine,
                source_atom_index=0,
                translation=(1, 1, 1),
                replacement_symbol="B",
            )
        )

        symbols = [atom.symbol for atom in result.supercell.atomic_basis.atoms]
        self.assertEqual(symbols.count("B"), 1)
        self.assertEqual(symbols.count("Si"), 63)

    def test_rejects_invalid_replication_and_site_declarations(self) -> None:
        source = _conventional_silicon_cell()
        for repetitions in ((0, 2, 2), (2, -1, 2)):
            with (
                self.subTest(repetitions=repetitions),
                self.assertRaisesRegex(ValueError, "positive"),
            ):
                SuperCellConstructionRequest(
                    source_unit_cell=source,
                    repetitions=repetitions,
                )
        with self.assertRaisesRegex(TypeError, "built-in ints"):
            SuperCellConstructionRequest(
                source_unit_cell=source,
                repetitions=(True, 2, 2),
            )

        pristine = (
            SuperCellBuilder()
            .action(
                request=SuperCellConstructionRequest(
                    source_unit_cell=source,
                    repetitions=(2, 2, 2),
                )
            )
            .supercell
        )
        with self.assertRaisesRegex(ValueError, "not present"):
            SuperCellSubstitutionRequest(
                supercell=pristine,
                source_atom_index=0,
                translation=(2, 0, 0),
                replacement_symbol="P",
            )
        with self.assertRaisesRegex(ValueError, "must differ"):
            SuperCellSubstitutionRequest(
                supercell=pristine,
                source_atom_index=0,
                translation=(0, 0, 0),
                replacement_symbol="Si",
            )

    def test_records_are_frozen_and_array_storage_is_immutable(self) -> None:
        result = SuperCellBuilder().action(
            request=SuperCellConstructionRequest(
                source_unit_cell=_conventional_silicon_cell(),
                repetitions=(2, 2, 2),
            )
        )

        with self.assertRaises(FrozenInstanceError):
            result.supercell.repetitions = (3, 3, 3)  # type: ignore[misc]
        with self.assertRaises(ValueError):
            result.supercell.A.magnitude[0, 0] = 99.0
        with self.assertRaises(ValueError):
            result.supercell.atomic_basis.atoms[0].position_fractional.magnitude[0] = (
                0.5
            )


def _conventional_silicon_cell() -> ConventionalUnitCell:
    positions = (
        (0.0, 0.0, 0.0),
        (0.0, 0.5, 0.5),
        (0.5, 0.0, 0.5),
        (0.5, 0.5, 0.0),
        (0.25, 0.25, 0.25),
        (0.25, 0.75, 0.75),
        (0.75, 0.25, 0.75),
        (0.75, 0.75, 0.25),
    )
    return ConventionalUnitCell(
        direct_lattice=DirectLattice3D(
            a1=np.array([1.0, 0.0, 0.0]),
            a2=np.array([0.0, 1.0, 0.0]),
            a3=np.array([0.0, 0.0, 1.0]),
        ),
        lattice_parameter=ScalarQuantity(5.43, PhysicalUnit("angstrom")),
        atomic_basis=AtomicBasis(
            atoms=tuple(
                Atom(
                    symbol="Si",
                    position_fractional=VectorQuantity(
                        magnitude=np.asarray(position, dtype=np.float64),
                        unit=Unitless(),
                    ),
                )
                for position in positions
            )
        ),
    )


if __name__ == "__main__":
    unittest.main()
