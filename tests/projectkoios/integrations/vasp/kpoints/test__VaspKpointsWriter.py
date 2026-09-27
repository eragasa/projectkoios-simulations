from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.kpoints import (
    VaspAutomaticKpointMesh,
    VaspKpointsWriter,
)


class VaspKpointsWriterTest(unittest.TestCase):
    def test_renders_deterministic_gamma_centered_mesh(self) -> None:
        rendered = VaspKpointsWriter().render(
            VaspAutomaticKpointMesh((8, 8, 8), (0, 0, 0))
        )

        self.assertEqual(rendered, "Automatic mesh\n0\nGamma\n8 8 8\n0 0 0\n")


if __name__ == "__main__":
    unittest.main()
