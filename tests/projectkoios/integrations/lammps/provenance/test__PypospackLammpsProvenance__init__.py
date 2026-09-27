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
    PypospackLammpsProvenance,
)
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


class PypospackLammpsProvenanceInitializationTest(unittest.TestCase):
    def test_preserves_the_exact_immutable_source_contract(self) -> None:
        source = bound_source()

        self.assertEqual(source.component, "pypospack")
        self.assertEqual(source.release_tag, "v0.1.0")
        self.assertEqual(source.revision, PYPOSPACK_REVISION)
        self.assertEqual(source.source_path, PYPOSPACK_LAMMPS_PATH)
        self.assertEqual(source.source_byte_size, 3_030)
        self.assertEqual(source.to_dict()["release_tag"], "v0.1.0")
        self.assertTrue(source.source_limitations)

        with self.assertRaisesRegex(ValueError, "source size"):
            replace(source, source_byte_size=3_031)
        with self.assertRaisesRegex(ValueError, "limitations"):
            replace(source, source_limitations=("invented",))


if __name__ == "__main__":
    unittest.main()
