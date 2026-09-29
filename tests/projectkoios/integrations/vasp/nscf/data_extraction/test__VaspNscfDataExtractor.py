from __future__ import annotations

import unittest

from projectkoios.integrations.vasp.data import (
    VaspDataSources,
    VaspExecutionData,
    VaspNativeArtifact,
)
from projectkoios.integrations.vasp.nscf.data_extraction import (
    VaspNscfDataExtractor,
)
from projectkoios.integrations.vasp.outcar import VaspOutcarParser
from projectkoios.integrations.vasp.run_xml import VaspRunXmlParser
from tests.projectkoios.integrations.vasp.outcar import (
    test__VaspOutcarParser as outcar_test,
)
from tests.projectkoios.integrations.vasp.run_xml import (
    test__VaspRunXmlParser as run_xml_test,
)


class VaspNscfDataExtractorTest(unittest.TestCase):
    def test_extracts_native_spectral_data_and_consistency(self) -> None:
        data = VaspNscfDataExtractor().extract(
            _sources(),
            expected_band_count=2,
            expected_kpoint_count=2,
        )

        self.assertEqual(data.spectral.spin_count, 1)
        self.assertEqual(data.spectral.kpoint_count, 2)
        self.assertEqual(data.spectral.band_count, 2)
        self.assertEqual(data.spectral.fermi_energy_ev, 0.1)
        self.assertTrue(data.consistency.atom_count_matches)
        self.assertFalse(data.consistency.program_version_matches)
        self.assertFalse(data.consistency.kpoint_count_matches)
        self.assertTrue(data.consistency.declared_band_count_matches)
        self.assertTrue(data.consistency.declared_kpoint_count_matches)

    def test_rejects_declared_band_count_disagreement(self) -> None:
        with self.assertRaisesRegex(ValueError, "band count"):
            VaspNscfDataExtractor().extract(
                _sources(),
                expected_band_count=3,
                expected_kpoint_count=2,
            )


def _sources() -> VaspDataSources:
    return VaspDataSources(
        execution=VaspExecutionData(
            status="succeeded",
            returncode=0,
            stdout_filename=None,
            stderr_filename=None,
        ),
        artifacts=(
            VaspNativeArtifact(
                role="outcar",
                relative_path="run/OUTCAR",
                sha256="0" * 64,
                byte_size=len(outcar_test.OUTCAR),
            ),
            VaspNativeArtifact(
                role="execution",
                relative_path="run/execution.json",
                sha256="1" * 64,
                byte_size=1,
            ),
            VaspNativeArtifact(
                role="vasprun",
                relative_path="run/vasprun.xml",
                sha256="2" * 64,
                byte_size=len(run_xml_test.VASPRUN_XML),
            ),
        ),
        outcar=VaspOutcarParser().parse(outcar_test.OUTCAR),
        vasprun=VaspRunXmlParser().parse(run_xml_test.VASPRUN_XML),
    )


if __name__ == "__main__":
    unittest.main()
