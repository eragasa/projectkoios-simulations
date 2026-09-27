from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.lammps import (
    PYPOSPACK_LAMMPS_BYTE_SIZE,
    PYPOSPACK_LAMMPS_LIMITATIONS,
    PYPOSPACK_LAMMPS_PATH,
    PYPOSPACK_LAMMPS_SHA256,
    PYPOSPACK_LICENSE_SHA256,
    PYPOSPACK_RELEASE_TAG,
    PYPOSPACK_REPOSITORY_URL,
    PYPOSPACK_REVISION,
    PYPOSPACK_TREE,
    LammpsAtom,
    LammpsSimulationCell,
    PypospackLammpsProvenance,
    inspect_lammps_data_structure,
    render_lammps_data,
)
from projectkoios.integrations.lammps.models import SourceFileEvidence
from projectkoios.integrations.lammps.provenance import (
    PYPOSPACK_LICENSE_PATH,
)


def bound_source() -> PypospackLammpsProvenance:
    return PypospackLammpsProvenance(
        component="pypospack",
        repository_url=PYPOSPACK_REPOSITORY_URL,
        release_tag=PYPOSPACK_RELEASE_TAG,
        revision=PYPOSPACK_REVISION,
        tree=PYPOSPACK_TREE,
        source_path=PYPOSPACK_LAMMPS_PATH,
        source_sha256=PYPOSPACK_LAMMPS_SHA256,
        source_byte_size=PYPOSPACK_LAMMPS_BYTE_SIZE,
        license_path=PYPOSPACK_LICENSE_PATH,
        license_sha256=PYPOSPACK_LICENSE_SHA256,
        source_limitations=PYPOSPACK_LAMMPS_LIMITATIONS,
    )


def orthogonal_cell() -> LammpsSimulationCell:
    return LammpsSimulationCell(
        scale=2.0,
        lattice=(
            (1.0, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (0.0, 0.0, 3.0),
        ),
        atoms=(
            LammpsAtom("O", (0.5, 0.5, 0.5), charge=-2.0),
            LammpsAtom("Mg", (0.0, 0.0, 0.0), charge=2.0),
        ),
    )


class RenderLammpsDataTest(unittest.TestCase):
    def test_renders_stable_effect_free_charge_data(self) -> None:
        source = bound_source()
        cell = orthogonal_cell()

        first = render_lammps_data(
            cell=cell,
            species_order=("Mg", "O"),
            atom_style="charge",
            source=source,
        )
        second = render_lammps_data(
            cell=cell,
            species_order=("Mg", "O"),
            atom_style="charge",
            source=source,
        )

        self.assertEqual(first, second)
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(
            first.utf8_text,
            "# ['Mg', 'O']\n"
            "\n"
            "2 atoms\n"
            "2 atom types\n"
            "\n"
            "    0.0000     2.0000 xlo xhi\n"
            "    0.0000     4.0000 ylo yhi\n"
            "    0.0000     6.0000 zlo zhi\n"
            "\n"
            "    0.0000     0.0000     0.0000 xy xz yz\n"
            "\n"
            "Atoms\n"
            "\n"
            "1 1     2.0000     0.0000     0.0000     0.0000\n"
            "2 2    -2.0000     1.0000     2.0000     3.0000\n",
        )
        payload = first.to_dict()
        self.assertEqual(
            payload["contract"],
            "projectkoios.integrations.lammps-data",
        )
        self.assertFalse(payload["calculator_execution_authorized"])
        self.assertFalse(payload["scientific_validation_claimed"])
        self.assertNotIn("utf8_text", payload)
        self.assertEqual(first.to_dict(include_text=True)["utf8_text"], first.utf8_text)
        observation = inspect_lammps_data_structure(
            name="rendered",
            evidence=SourceFileEvidence(
                relative_path="rendered.structure",
                sha256=first.sha256,
                byte_size=len(first.utf8_text.encode("utf-8")),
            ),
            text=first.utf8_text,
        )
        self.assertEqual(observation.bounds, ((0.0, 2.0), (0.0, 4.0), (0.0, 6.0)))

    def test_rejects_unsupported_or_numerically_unsafe_cells(self) -> None:
        source = bound_source()
        triclinic = replace(
            orthogonal_cell(),
            lattice=(
                (1.0, 0.25, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 0.0, 3.0),
            ),
        )
        with self.assertRaisesRegex(ValueError, "off-diagonal"):
            render_lammps_data(
                cell=triclinic,
                species_order=("Mg", "O"),
                atom_style="atomic",
                source=source,
            )

        overflowing = LammpsSimulationCell(
            scale=1e308,
            lattice=(
                (2.0, 0.0, 0.0),
                (0.0, 2.0, 0.0),
                (0.0, 0.0, 2.0),
            ),
            atoms=(LammpsAtom("Mg", (0.0, 0.0, 0.0)),),
        )
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            render_lammps_data(
                cell=overflowing,
                species_order=("Mg",),
                atom_style="atomic",
                source=source,
            )

        rounded_to_zero = LammpsSimulationCell(
            scale=0.00001,
            lattice=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            atoms=(LammpsAtom("Mg", (0.0, 0.0, 0.0)),),
        )
        with self.assertRaisesRegex(ValueError, "serialization precision"):
            render_lammps_data(
                cell=rounded_to_zero,
                species_order=("Mg",),
                atom_style="atomic",
                source=source,
            )

    def test_rejects_missing_charges_and_incomplete_species_order(self) -> None:
        source = bound_source()
        cell = orthogonal_cell()
        without_charges = replace(
            cell,
            atoms=(LammpsAtom("Mg", (0.0, 0.0, 0.0)),),
        )
        with self.assertRaisesRegex(ValueError, "explicit charge"):
            render_lammps_data(
                cell=without_charges,
                species_order=("Mg",),
                atom_style="charge",
                source=source,
            )
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            render_lammps_data(
                cell=cell,
                species_order=("Mg",),
                atom_style="atomic",
                source=source,
            )


if __name__ == "__main__":
    unittest.main()
