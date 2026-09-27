from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

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
    verify_pypospack_lammps_checkout,
)
from projectkoios.integrations.lammps.provenance import (
    PYPOSPACK_LICENSE_PATH,
)

_CHECKOUT_VALUE = os.environ.get("PYPOSPACK_CHECKOUT")
CHECKOUT = Path(_CHECKOUT_VALUE).resolve() if _CHECKOUT_VALUE else None


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


@unittest.skipUnless(CHECKOUT is not None, "PYPOSPACK_CHECKOUT is not set")
class VerifyPypospackLammpsCheckoutTest(unittest.TestCase):
    def test_verifies_explicit_external_checkout(self) -> None:
        assert CHECKOUT is not None
        self.assertEqual(verify_pypospack_lammps_checkout(CHECKOUT), bound_source())

    def test_detects_mutated_or_symlinked_source_evidence(self) -> None:
        assert CHECKOUT is not None
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            for relative_path in (PYPOSPACK_LICENSE_PATH, PYPOSPACK_LAMMPS_PATH):
                destination = checkout / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(CHECKOUT / relative_path, destination)

            source_path = checkout / PYPOSPACK_LAMMPS_PATH
            source_path.write_bytes(source_path.read_bytes() + b"\n# mutation\n")
            with self.assertRaisesRegex(ValueError, "bound source"):
                verify_pypospack_lammps_checkout(checkout)

            source_path.unlink()
            source_path.symlink_to(CHECKOUT / PYPOSPACK_LAMMPS_PATH)
            with self.assertRaisesRegex(ValueError, "regular file"):
                verify_pypospack_lammps_checkout(checkout)


if __name__ == "__main__":
    unittest.main()
