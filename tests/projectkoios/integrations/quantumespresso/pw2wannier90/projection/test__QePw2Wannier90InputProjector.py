from __future__ import annotations

import unittest
from dataclasses import replace

from projectkoios.integrations.quantumespresso.pw2wannier90.configuration import (  # noqa: E501
    QePw2Wannier90InputConfiguration,
    QePw2Wannier90Mode,
    QePw2Wannier90SpinComponent,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.projection import (  # noqa: E501
    QePw2Wannier90InputProjector,
)


class QePw2Wannier90InputProjectorTest(unittest.TestCase):
    def test_projects_explicit_converter_input_and_dependencies(self) -> None:
        projection = QePw2Wannier90InputProjector().project(_configuration())

        self.assertEqual(
            projection.rendered_input.text,
            "&INPUTPP\n"
            "    prefix = 'system'\n"
            "    outdir = './tmp/'\n"
            "    seedname = 'silicon'\n"
            "    spin_component = 'none'\n"
            "    wan_mode = 'standalone'\n"
            "    write_amn = .true.\n"
            "    write_mmn = .true.\n"
            "    write_unk = .false.\n"
            "    write_spn = .false.\n"
            "/\n",
        )
        self.assertEqual(projection.nnkp_filename, "silicon.nnkp")
        self.assertEqual(projection.nnkp_sha256, "a" * 64)
        self.assertEqual(projection.parent_nscf_saved_state_manifest_sha256, "b" * 64)
        self.assertEqual(
            projection.required_output_filenames,
            ("silicon.amn", "silicon.mmn", "silicon.eig"),
        )

    def test_rejects_disabled_required_overlap_output(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires AMN and MMN"):
            replace(_configuration(), write_mmn=False)

    def test_rejects_unimplemented_optional_output(self) -> None:
        with self.assertRaisesRegex(NotImplementedError, "UNK and SPN"):
            replace(_configuration(), write_unk=True)

    def test_rejects_nnkp_name_that_disagrees_with_seedname(self) -> None:
        with self.assertRaisesRegex(ValueError, "must match seedname"):
            replace(_configuration(), nnkp_filename="other.nnkp")


def _configuration() -> QePw2Wannier90InputConfiguration:
    return QePw2Wannier90InputConfiguration(
        prefix="system",
        outdir="./tmp/",
        seedname="silicon",
        spin_component=QePw2Wannier90SpinComponent.none,
        mode=QePw2Wannier90Mode.standalone,
        write_amn=True,
        write_mmn=True,
        write_unk=False,
        write_spn=False,
        input_filename="pw2wan.in",
        nnkp_filename="silicon.nnkp",
        nnkp_sha256="a" * 64,
        nnkp_byte_size=1234,
        parent_nscf_saved_state_manifest_sha256="b" * 64,
    )


if __name__ == "__main__":
    unittest.main()
