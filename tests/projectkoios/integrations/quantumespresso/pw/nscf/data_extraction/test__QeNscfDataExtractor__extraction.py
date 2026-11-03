from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwDataSources,
)
from projectkoios.integrations.quantumespresso.pw.nscf.data_extraction import (  # noqa: E501
    QeNscfDataExtractor,
)
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)

_NSCF_EXTRACTOR = QeNscfDataExtractor(
    expected_band_count=2,
    expected_kpoint_count=2,
    stdout_relative_path="pw.out",
    stderr_relative_path="pw.err",
)


class QeNscfDataExtractorTest(unittest.TestCase):
    def test__QeNscfDataExtractor__extracts_source_ordered_native_spectral_data(
        self,
    ) -> None:
        document = QEXSD_FIXTURES.nscf_document()

        data = _NSCF_EXTRACTOR.extract(
            stdout_payload=(b"Program PWSCF v.7.5\nnumber of k points= 2\nJOB DONE.\n"),
            stderr_payload=b"",
            qexsd_document=document,
        )

        self.assertIsInstance(data.sources, QePwDataSources)
        self.assertIs(data.document, document)
        self.assertIs(data.final_structure, data.qexsd.final_structure)
        self.assertEqual(data.band_count, 2)
        self.assertEqual(data.k_points, document.k_points)
        self.assertEqual(data.eigenvalues, document.eigenvalues)
        self.assertEqual(data.occupations, document.occupations)
        self.assertEqual(data.eigenvalue_source_label, "band_structure/ks_energies")
        self.assertTrue(data.streams.stdout.job_completed)
        self.assertTrue(data.consistency.terminal_status_matches)
        self.assertTrue(data.consistency.stdout_kpoint_count_matches)
        self.assertTrue(data.consistency.declared_band_count_matches)
        self.assertTrue(data.consistency.declared_kpoint_count_matches)

    def test__QeNscfDataExtractor__rejects_declared_band_count_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "band count disagrees"):
            QeNscfDataExtractor(
                expected_band_count=3,
                expected_kpoint_count=2,
                stdout_relative_path="pw.out",
                stderr_relative_path="pw.err",
            ).extract(
                stdout_payload=b"Program PWSCF v.7.5\n",
                stderr_payload=b"",
                qexsd_document=QEXSD_FIXTURES.nscf_document(),
            )

    def test__QeNscfDataExtractor__rejects_raw_xml(self) -> None:
        with self.assertRaisesRegex(TypeError, "QexsdDocument"):
            _NSCF_EXTRACTOR.extract(
                stdout_payload=b"Program PWSCF v.7.5\n",
                stderr_payload=b"",
                qexsd_document=b"<qes/>",  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
