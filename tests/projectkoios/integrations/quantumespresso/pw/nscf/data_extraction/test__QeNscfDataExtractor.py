from __future__ import annotations

import unittest
from types import SimpleNamespace

from projectkoios.integrations.quantumespresso.pw.nscf.data_extraction import (  # noqa: E501
    QeNscfDataExtractor,
)


class QeNscfDataExtractorTest(unittest.TestCase):
    def test_extracts_source_ordered_native_spectral_data(self) -> None:
        document = _document()

        data = QeNscfDataExtractor().extract(
            stdout_payload=(b"Program PWSCF v.7.5\nnumber of k points= 2\nJOB DONE.\n"),
            stderr_payload=b"",
            qexsd_document=document,
            expected_band_count=2,
            expected_kpoint_count=2,
        )

        self.assertEqual(data.band_count, 2)
        self.assertEqual(data.k_points, document.k_points)
        self.assertEqual(data.eigenvalues, document.eigenvalues)
        self.assertEqual(data.occupations, document.occupations)
        self.assertEqual(data.eigenvalue_source_label, "band_structure/ks_energies")
        self.assertTrue(data.streams.stdout.job_completed)

    def test_rejects_declared_band_count_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "band count disagrees"):
            QeNscfDataExtractor().extract(
                stdout_payload=b"Program PWSCF v.7.5\n",
                stderr_payload=b"",
                qexsd_document=_document(),
                expected_band_count=3,
                expected_kpoint_count=2,
            )

    def test_rejects_raw_xml(self) -> None:
        with self.assertRaisesRegex(TypeError, "QuantumEspressoXsdDocumentParser"):
            QeNscfDataExtractor().extract(
                stdout_payload=b"Program PWSCF v.7.5\n",
                stderr_payload=b"",
                qexsd_document=b"<qes/>",
                expected_band_count=2,
                expected_kpoint_count=2,
            )


def _document() -> SimpleNamespace:
    return SimpleNamespace(
        source_path="/retained/data-file-schema.xml",
        source_sha256="a" * 64,
        source_byte_count=123,
        qexsd_version="25.05.21",
        producing_application="Quantum ESPRESSO",
        producing_application_version="7.5",
        declared_unit_system_label="Hartree atomic units",
        k_points=((0.0, 0.0, 0.0), (0.5, 0.0, 0.0)),
        k_point_weights=(0.5, 0.5),
        sampled_k_point_count=2,
        k_point_source_label="band_structure/ks_energies/k_point",
        eigenvalues=((-0.4, 0.2), (-0.3, 0.4)),
        occupations=((1.0, 0.0), (1.0, 0.0)),
        eigenvalue_source_label="band_structure/ks_energies",
        band_count=2,
        exit_status=0,
    )


if __name__ == "__main__":
    unittest.main()
