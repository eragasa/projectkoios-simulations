from __future__ import annotations

import runpy
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

import numpy as np

from projectkoios.physkit.core.data import DataObject
from projectkoios.physkit.core.results import ResultsObject
from projectkoios.physkit.periodic import DirectLattice3D
from projectkoios.physkit.periodic.unit_cell import (
    Atom,
    AtomicBasis,
    ConventionalUnitCell,
    UnitCell,
    UnitCellJsonCodec,
)
from projectkoios.physkit.units import (
    PhysicalUnit,
    ScalarQuantity,
    Unitless,
    VectorQuantity,
)
from projectkoios.simulations.structure import (
    SuperCellBuilder,
    SuperCellConstructionRequest,
    UnitCellDefectDelta,
    UnitCellDefectDeltaApplicator,
    UnitCellDefectDeltaResult,
    UnitCellSiteOrigin,
)

CONVENTIONAL_SILICON_CELL = ConventionalUnitCell(
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
            for position in (
                (0.0, 0.0, 0.0),
                (0.0, 0.5, 0.5),
                (0.5, 0.0, 0.5),
                (0.5, 0.5, 0.0),
                (0.25, 0.25, 0.25),
                (0.25, 0.75, 0.75),
                (0.75, 0.25, 0.75),
                (0.75, 0.75, 0.25),
            )
        )
    ),
)
SILICON_BULK_SUPERCELL = (
    SuperCellBuilder()
    .action(
        request=SuperCellConstructionRequest(
            source_unit_cell=CONVENTIONAL_SILICON_CELL,
            repetitions=(2, 2, 2),
        )
    )
    .supercell
)


class UnitCellDefectDeltaTest(unittest.TestCase):
    def test_expresses_phosphorus_and_boron_substitutions_as_remove_add(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        removed_index = 0
        removed_position = bulk.atomic_basis.atoms[removed_index].position_fractional

        for replacement in ("P", "B"):
            with self.subTest(replacement=replacement):
                delta = UnitCellDefectDelta(
                    bulk_cell=bulk,
                    removals=(removed_index,),
                    additions=(
                        Atom(
                            symbol=replacement,
                            position_fractional=removed_position,
                        ),
                    ),
                    charge_state=0,
                )

                result = UnitCellDefectDeltaApplicator().action(request=delta)

                self.assertIsInstance(delta, DataObject)
                self.assertIsInstance(result, ResultsObject)
                self.assertIsInstance(result, UnitCellDefectDeltaResult)
                self.assertIs(result.delta, delta)
                self.assertIs(type(result.unit_cell), UnitCell)
                symbols = tuple(
                    atom.symbol for atom in result.unit_cell.atomic_basis.atoms
                )
                self.assertEqual(symbols.count(replacement), 1)
                self.assertEqual(symbols.count("Si"), 63)
                self.assertEqual(len(symbols), 64)
                np.testing.assert_array_equal(
                    result.unit_cell.atomic_basis.atoms[
                        -1
                    ].position_fractional.magnitude,
                    removed_position.magnitude,
                )

    def test_supports_removal_only_addition_only_and_complex_deltas(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        interstitial = Atom(
            symbol="H",
            position_fractional=VectorQuantity(
                magnitude=np.asarray((0.0625, 0.0625, 0.0625)),
                unit=Unitless(),
            ),
        )

        vacancy = UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(0,),
            additions=(),
            charge_state=-1,
        )
        vacancy_result = UnitCellDefectDeltaApplicator().action(request=vacancy)
        self.assertEqual(len(vacancy_result.unit_cell.atomic_basis.atoms), 63)
        self.assertEqual(vacancy_result.delta.charge_state, -1)

        addition = UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(),
            additions=(interstitial,),
            charge_state=1,
        )
        addition_result = UnitCellDefectDeltaApplicator().action(request=addition)
        self.assertEqual(len(addition_result.unit_cell.atomic_basis.atoms), 65)
        self.assertIs(addition_result.unit_cell.atomic_basis.atoms[-1], interstitial)

        complex_delta = UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(0, 3),
            additions=(
                Atom(
                    symbol="P",
                    position_fractional=VectorQuantity(
                        magnitude=np.asarray((0.0, 0.0, 0.0)),
                        unit=Unitless(),
                    ),
                ),
                Atom(
                    symbol="B",
                    position_fractional=VectorQuantity(
                        magnitude=np.asarray((0.25, 0.0, 0.0)),
                        unit=Unitless(),
                    ),
                ),
            ),
            charge_state=0,
        )
        complex_result = UnitCellDefectDeltaApplicator().action(request=complex_delta)
        self.assertEqual(
            tuple(
                atom.symbol for atom in complex_result.unit_cell.atomic_basis.atoms[-2:]
            ),
            ("P", "B"),
        )

    def test_removals_use_original_indices_and_preserve_retained_order(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        delta = UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(0, 2, 5),
            additions=(
                Atom(
                    symbol="P",
                    position_fractional=VectorQuantity(
                        magnitude=np.asarray((0.0, 0.0, 0.0)),
                        unit=Unitless(),
                    ),
                ),
            ),
        )

        result = UnitCellDefectDeltaApplicator().action(request=delta)

        expected = (
            tuple(
                atom
                for index, atom in enumerate(bulk.atomic_basis.atoms)
                if index not in {0, 2, 5}
            )
            + delta.additions
        )
        self.assertEqual(
            tuple(atom.symbol for atom in result.unit_cell.atomic_basis.atoms),
            tuple(atom.symbol for atom in expected),
        )
        for actual, declared in zip(
            result.unit_cell.atomic_basis.atoms,
            expected,
            strict=True,
        ):
            np.testing.assert_array_equal(
                actual.position_fractional.magnitude,
                declared.position_fractional.magnitude,
            )

    def test_preserves_bulk_lattice_without_claiming_a_bulk_subtype(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        delta = UnitCellDefectDelta(
            bulk_cell=bulk,
            removals=(0,),
            additions=(),
        )

        result = UnitCellDefectDeltaApplicator().action(request=delta)

        self.assertIs(type(result.unit_cell), UnitCell)
        np.testing.assert_array_equal(result.unit_cell.A.magnitude, bulk.A.magnitude)
        self.assertEqual(result.unit_cell.lattice_parameter, bulk.lattice_parameter)
        with self.assertRaises(FrozenInstanceError):
            result.delta.charge_state = 2  # type: ignore[misc]

    def test_concrete_silicon_substitutional_declarations(self) -> None:
        repository = Path(__file__).resolve().parents[5]
        declarations = runpy.run_path(
            repository / "examples/workflows/pw_dft_scf/structures/"
            "silicon_substitutional_defects.py"
        )

        self.assertEqual(declarations["SUBSTITUTION_SITE_INDEX"], 0)
        self.assertEqual(
            declarations["SUPERCELL_REPETITIONS"],
            ((2, 2, 2), (3, 3, 3), (4, 4, 4)),
        )
        codec = UnitCellJsonCodec()
        structure_root = repository / "examples/workflows/pw_dft_scf/structures"
        for atom_count in (64, 216, 512):
            bulk = declarations["SILICON_BULK_SUPERCELLS"][atom_count]
            phosphorus = declarations["SILICON_PHOSPHORUS_IDEAL_RESULTS"][atom_count]
            boron = declarations["SILICON_BORON_IDEAL_RESULTS"][atom_count]
            self.assertEqual(len(bulk.atomic_basis.atoms), atom_count)
            self.assertEqual(
                declarations["SUBSTITUTION_SITE_ORIGINS"][atom_count],
                UnitCellSiteOrigin(source_atom_index=0, translation=(0, 0, 0)),
            )
            self.assertEqual(phosphorus.delta.charge_state, 0)
            self.assertEqual(boron.delta.charge_state, 0)
            self.assertEqual(phosphorus.unit_cell.atomic_basis.atoms[-1].symbol, "P")
            self.assertEqual(boron.unit_cell.atomic_basis.atoms[-1].symbol, "B")
            self.assertEqual(len(phosphorus.unit_cell.atomic_basis.atoms), atom_count)
            self.assertEqual(len(boron.unit_cell.atomic_basis.atoms), atom_count)
            bulk_unit_cell = UnitCell(
                direct_lattice=bulk.direct_lattice,
                lattice_parameter=bulk.lattice_parameter,
                atomic_basis=bulk.atomic_basis,
            )
            for structure_id, unit_cell in (
                (f"Si.Supercell.Atoms{atom_count}", bulk_unit_cell),
                (
                    f"Si.P.Substitutional.Atoms{atom_count}.Ideal",
                    phosphorus.unit_cell,
                ),
                (
                    f"Si.B.Substitutional.Atoms{atom_count}.Ideal",
                    boron.unit_cell,
                ),
            ):
                self.assertEqual(
                    codec.dumps(unit_cell, structure_id=structure_id),
                    (structure_root / f"{structure_id}.json").read_text(
                        encoding="utf-8"
                    ),
                )

    def test_rejects_invalid_removal_and_addition_declarations(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        valid_addition = Atom(
            symbol="P",
            position_fractional=VectorQuantity(
                magnitude=np.asarray((0.125, 0.125, 0.125)),
                unit=Unitless(),
            ),
        )

        invalid_removals = (
            ((1, 1), "unique and strictly increasing"),
            ((2, 1), "unique and strictly increasing"),
            ((-1,), "outside"),
            ((64,), "outside"),
        )
        for removals, message in invalid_removals:
            with (
                self.subTest(removals=removals),
                self.assertRaisesRegex(ValueError, message),
            ):
                UnitCellDefectDelta(
                    bulk_cell=bulk,
                    removals=removals,
                    additions=(),
                )

        with self.assertRaisesRegex(TypeError, "tuple of built-in ints"):
            UnitCellDefectDelta(
                bulk_cell=bulk,
                removals=(True,),
                additions=(),
            )
        with self.assertRaisesRegex(TypeError, "tuple of Atom"):
            UnitCellDefectDelta(
                bulk_cell=bulk,
                removals=(),
                additions=(object(),),  # type: ignore[arg-type]
            )
        with self.assertRaisesRegex(ValueError, "remove or add"):
            UnitCellDefectDelta(bulk_cell=bulk, removals=(), additions=())
        with self.assertRaisesRegex(TypeError, "built-in int"):
            UnitCellDefectDelta(
                bulk_cell=bulk,
                removals=(),
                additions=(valid_addition,),
                charge_state=True,
            )

    def test_rejects_invalid_or_occupied_addition_positions(self) -> None:
        bulk = SILICON_BULK_SUPERCELL
        invalid_positions = (
            (-0.1, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (float("nan"), 0.0, 0.0),
        )
        for position in invalid_positions:
            with (
                self.subTest(position=position),
                self.assertRaisesRegex(ValueError, "half-open|finite vector"),
            ):
                UnitCellDefectDelta(
                    bulk_cell=bulk,
                    removals=(),
                    additions=(
                        Atom(
                            symbol="P",
                            position_fractional=VectorQuantity(
                                magnitude=np.asarray(position),
                                unit=Unitless(),
                            ),
                        ),
                    ),
                )

        occupied = bulk.atomic_basis.atoms[0].position_fractional
        with self.assertRaisesRegex(ValueError, "already occupied"):
            UnitCellDefectDelta(
                bulk_cell=bulk,
                removals=(),
                additions=(Atom(symbol="P", position_fractional=occupied),),
            )
        with self.assertRaisesRegex(ValueError, "positions must be unique"):
            UnitCellDefectDelta(
                bulk_cell=bulk,
                removals=(),
                additions=(
                    valid := Atom(
                        symbol="P",
                        position_fractional=VectorQuantity(
                            magnitude=np.asarray((0.0625, 0.0625, 0.0625)),
                            unit=Unitless(),
                        ),
                    ),
                    valid,
                ),
            )


if __name__ == "__main__":
    unittest.main()
