from __future__ import annotations

import unittest

import numpy as np

from projectkoios.integrations.quantumespresso.pw.inputfile.system.ibrav import (  # noqa: E501
    QeBravaisLattice,
    QeCelldm,
    QeCellParameters,
    QeCellParametersUnit,
    QeIbrav,
    QeLatticeParameters,
)
from projectkoios.physkit.periodic import DirectLattice3D


class QeIbravTest(unittest.TestCase):
    def test_exposes_every_documented_ibrav_identity(self) -> None:
        self.assertEqual(
            {member.value for member in QeBravaisLattice},
            {
                -13,
                -12,
                -9,
                -5,
                -3,
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                91,
            },
        )
        for member in QeBravaisLattice:
            with self.subTest(ibrav=member.value):
                self.assertEqual(member.bravais_lattice_kind.name, member.name)

    def test_ibrav_is_optional_only_when_space_group_is_set(self) -> None:
        with self.assertRaisesRegex(ValueError, "only when space_group is set"):
            QeIbrav(ibrav=None)

        declaration = QeIbrav(ibrav=None, space_group=227)

        self.assertEqual(declaration.space_group, 227)

    def test_free_lattice_requires_explicit_cell_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires CELL_PARAMETERS"):
            QeIbrav(ibrav=QeBravaisLattice.free)

        declaration = QeIbrav(
            ibrav=QeBravaisLattice.free,
            cell_parameters=_cell_parameters(),
        )

        self.assertIs(declaration.ibrav, QeBravaisLattice.free)

    def test_free_lattice_accepts_optional_true_lattice_parameter(self) -> None:
        celldm_declaration = QeIbrav(
            ibrav=QeBravaisLattice.free,
            celldm=QeCelldm(celldm1=10.26121286),
            cell_parameters=_cell_parameters(QeCellParametersUnit.alat),
        )
        angstrom_declaration = QeIbrav(
            ibrav=QeBravaisLattice.free,
            lattice_parameters=QeLatticeParameters(a=5.43),
            cell_parameters=_cell_parameters(QeCellParametersUnit.alat),
        )

        self.assertEqual(celldm_declaration.celldm.celldm1, 10.26121286)
        self.assertEqual(angstrom_declaration.lattice_parameters.a, 5.43)

    def test_free_lattice_rejects_both_lattice_parameter_families(self) -> None:
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            QeIbrav(
                ibrav=QeBravaisLattice.free,
                celldm=QeCelldm(celldm1=10.26121286),
                lattice_parameters=QeLatticeParameters(a=5.43),
                cell_parameters=_cell_parameters(),
            )

    def test_free_lattice_rejects_shape_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, r"celldm\(2\)-celldm\(6\)"):
            QeIbrav(
                ibrav=QeBravaisLattice.free,
                celldm=QeCelldm(celldm1=10.26121286, celldm2=1.0),
                cell_parameters=_cell_parameters(),
            )
        with self.assertRaisesRegex(ValueError, "only A"):
            QeIbrav(
                ibrav=QeBravaisLattice.free,
                lattice_parameters=QeLatticeParameters(a=5.43, b=5.43),
                cell_parameters=_cell_parameters(),
            )

    def test_indexed_lattice_requires_exactly_one_parameter_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one"):
            QeIbrav(ibrav=QeBravaisLattice.cubic_face_centered)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            QeIbrav(
                ibrav=QeBravaisLattice.cubic_face_centered,
                celldm=QeCelldm(celldm1=10.26121286),
                lattice_parameters=QeLatticeParameters(a=5.43),
            )

        celldm_declaration = QeIbrav(
            ibrav=QeBravaisLattice.cubic_face_centered,
            celldm=QeCelldm(celldm1=10.26121286),
        )
        angstrom_declaration = QeIbrav(
            ibrav=QeBravaisLattice.cubic_face_centered,
            lattice_parameters=QeLatticeParameters(a=5.43),
        )

        self.assertIsNotNone(celldm_declaration.celldm)
        self.assertIsNotNone(angstrom_declaration.lattice_parameters)

    def test_indexed_lattices_enforce_their_shape_parameters(self) -> None:
        QeIbrav(
            ibrav=QeBravaisLattice.hexagonal_trigonal_primitive,
            celldm=QeCelldm(celldm1=10.0, celldm3=2.0),
        )
        QeIbrav(
            ibrav=QeBravaisLattice.orthorhombic_face_centered,
            lattice_parameters=QeLatticeParameters(a=4.0, b=5.0, c=6.0),
        )
        QeIbrav(
            ibrav=QeBravaisLattice.monoclinic_primitive_unique_b,
            celldm=QeCelldm(
                celldm1=10.0,
                celldm2=1.1,
                celldm3=1.2,
                celldm5=0.1,
            ),
        )
        QeIbrav(
            ibrav=QeBravaisLattice.triclinic,
            lattice_parameters=QeLatticeParameters(
                a=4.0,
                b=5.0,
                c=6.0,
                cos_ab=0.1,
                cos_ac=0.2,
                cos_bc=0.3,
            ),
        )

        with self.assertRaisesRegex(ValueError, "missing=.*celldm3"):
            QeIbrav(
                ibrav=QeBravaisLattice.tetragonal_primitive,
                celldm=QeCelldm(celldm1=10.0),
            )
        with self.assertRaisesRegex(ValueError, "unexpected=.*celldm2"):
            QeIbrav(
                ibrav=QeBravaisLattice.cubic_primitive,
                celldm=QeCelldm(celldm1=10.0, celldm2=1.0),
            )

    def test_indexed_lattice_rejects_cell_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not specify CELL_PARAMETERS"):
            QeIbrav(
                ibrav=QeBravaisLattice.cubic_face_centered,
                lattice_parameters=QeLatticeParameters(a=5.43),
                cell_parameters=_cell_parameters(),
            )

    def test_cell_parameters_require_explicit_units_and_precision(self) -> None:
        cell_parameters = _cell_parameters()

        self.assertIs(cell_parameters.unit, QeCellParametersUnit.angstrom)
        self.assertEqual(cell_parameters.coordinate_precision, 8)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            QeCellParameters(
                vectors=_vectors(),
                unit=QeCellParametersUnit.angstrom,
                coordinate_precision=0,
            )


def _cell_parameters(
    unit: QeCellParametersUnit = QeCellParametersUnit.angstrom,
) -> QeCellParameters:
    return QeCellParameters(vectors=_vectors(), unit=unit, coordinate_precision=8)


def _vectors() -> DirectLattice3D:
    return DirectLattice3D(
        a1=np.asarray((2.715, 2.715, 0.0)),
        a2=np.asarray((2.715, 0.0, 2.715)),
        a3=np.asarray((0.0, 2.715, 2.715)),
    )


if __name__ == "__main__":
    unittest.main()
