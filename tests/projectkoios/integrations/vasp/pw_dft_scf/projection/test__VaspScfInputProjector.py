from __future__ import annotations

import unittest
from pathlib import Path

import pytest

from projectkoios.integrations.vasp.pw_dft_scf.configuration import (
    VaspScfProjectionConfiguration,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VaspScfInputProjector,
)
from tests.projectkoios.simulations.dft.pw.scf.support import (
    silicon_scf_request,
)

pytestmark = pytest.mark.integration

_INPUT_ROOT = Path(
    "examples/projectkoios/integrations/vasp/pw_dft_scf/Si/primitive/input"
)


class VaspScfInputProjectorTest(unittest.TestCase):
    def test_reproduces_maintained_silicon_text_inputs(self) -> None:
        projection = VaspScfInputProjector(
            VaspScfProjectionConfiguration(
                system_label="Silicon SCF",
                poscar_comment="Silicon primitive cell",
            )
        ).project(silicon_scf_request())
        rendered = {item.filename: item.text for item in projection.rendered_inputs}

        for filename in ("INCAR", "KPOINTS", "POSCAR"):
            with self.subTest(filename=filename):
                self.assertEqual(
                    rendered[filename],
                    (_INPUT_ROOT / filename).read_text(encoding="ascii"),
                )
        self.assertEqual(projection.required_external_inputs, ("POTCAR",))


if __name__ == "__main__":
    unittest.main()
