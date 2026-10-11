from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import pytest

from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwCapturedStreamData,
    QePwDataSources,
    QePwExecutionData,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.scf import (
    data_extraction as qe_data_extraction,
)
from tests.projectkoios.integrations.quantumespresso.pw.scf import (
    support as qe_support,
)

pytestmark = pytest.mark.integration


class QeScfPureOutputPipelineTest(unittest.TestCase):
    def test_parser_binds_exact_supplied_bytes_without_io(self) -> None:
        request = _parsing_request()

        with (
            mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("parser must not read files"),
            ),
            mock.patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("parser must not start processes"),
            ),
        ):
            result = qe_data_extraction.QeScfOutputParser().action(request=request)

        self.assertIs(result.request, request)
        self.assertEqual(
            result.streams.stdout_artifact.sha256,
            hashlib.sha256(request.stdout_payload).hexdigest(),
        )
        self.assertEqual(
            result.streams.stderr_artifact.sha256,
            hashlib.sha256(request.stderr_payload).hexdigest(),
        )
        self.assertEqual(result.streams.stdout_artifact.relative_path, "run/pw.out")
        self.assertEqual(result.streams.stderr_artifact.relative_path, "run/pw.err")
        self.assertEqual(
            result.streams.stdout.total_energy_ry,
            qe_support.EXPECTED_TOTAL_ENERGY_RY,
        )

    def test_parsing_result_rejects_streams_from_different_bytes(self) -> None:
        request = _parsing_request()
        result = qe_data_extraction.QeScfOutputParser().action(request=request)
        changed_request = replace(
            request,
            stdout_payload=b"x" * len(request.stdout_payload),
        )

        with self.assertRaisesRegex(ValueError, "digest does not match"):
            qe_data_extraction.QeScfOutputParsingResult(
                request=changed_request,
                streams=result.streams,
            )

    def test_parser_request_rejects_oversized_or_unsafe_streams(self) -> None:
        with self.assertRaisesRegex(
            qe_data_extraction.QeScfArtifactError,
            "stdout exceeds byte limit",
        ):
            qe_data_extraction.QeScfOutputParsingRequest(
                stdout_payload=b"12",
                stderr_payload=b"",
                maximum_stream_bytes=1,
            )

        with self.assertRaisesRegex(ValueError, "safe relative POSIX path"):
            qe_data_extraction.QeScfOutputParsingRequest(
                stdout_payload=b"",
                stderr_payload=b"",
                stdout_relative_path="../pw.out",
            )

    def test_normalizer_maps_parsed_facts_without_io_or_processes(self) -> None:
        parsing = qe_data_extraction.QeScfOutputParser().action(
            request=_parsing_request()
        )
        sources = _sources(parsing.streams)
        request = qe_data_extraction.QeScfNormalizationRequest(sources=sources)

        with (
            mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("normalizer must not read files"),
            ),
            mock.patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("normalizer must not start processes"),
            ),
        ):
            result = qe_data_extraction.QeScfNormalizer().action(request=request)

        self.assertIs(result.request, request)
        self.assertIs(result.data.sources, sources)
        self.assertEqual(result.data.atom_count, qe_support.EXPECTED_ATOM_COUNT)
        self.assertEqual(
            result.data.observation.native_artifact.sha256,
            parsing.streams.stdout_artifact.sha256,
        )
        self.assertEqual(
            tuple(item.native_artifact.sha256 for item in result.data.diagnostics),
            (parsing.streams.stderr_artifact.sha256,) * 4,
        )

    def test_normalization_result_requires_exact_requested_sources(self) -> None:
        parsing = qe_data_extraction.QeScfOutputParser().action(
            request=_parsing_request()
        )
        sources = _sources(parsing.streams)
        result = qe_data_extraction.QeScfNormalizer().action(
            request=qe_data_extraction.QeScfNormalizationRequest(sources=sources)
        )
        equal_but_distinct_sources = replace(sources)
        self.assertEqual(equal_but_distinct_sources, sources)
        self.assertIsNot(equal_but_distinct_sources, sources)

        with self.assertRaisesRegex(ValueError, "exact requested sources"):
            qe_data_extraction.QeScfNormalizationResult(
                request=qe_data_extraction.QeScfNormalizationRequest(
                    sources=equal_but_distinct_sources
                ),
                data=result.data,
            )

    def test_normalizer_rejects_incomplete_scf_observations(self) -> None:
        parsing = qe_data_extraction.QeScfOutputParser().action(
            request=qe_data_extraction.QeScfOutputParsingRequest(
                stdout_payload=qe_support.QE_PW_OUTPUT.replace(
                    "!    total energy              =     -22.83930406 Ry\n",
                    "",
                ).encode("utf-8"),
                stderr_payload=b"",
                stdout_relative_path="run/pw.out",
                stderr_relative_path="run/pw.err",
            )
        )

        with self.assertRaisesRegex(
            qe_data_extraction.QeScfArtifactError,
            "lacks required SCF observations",
        ):
            qe_data_extraction.QeScfNormalizer().action(
                request=qe_data_extraction.QeScfNormalizationRequest(
                    sources=_sources(parsing.streams)
                )
            )

    def test_extractor_delegates_to_the_same_pure_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run = root / "run"
            run.mkdir()
            stdout_payload = qe_support.QE_PW_OUTPUT.encode("utf-8")
            stderr_payload = qe_support.QE_STDERR.encode("utf-8")
            execution_payload = json.dumps(
                qe_support.QE_SUCCESSFUL_EXECUTION_RECORD
            ).encode("utf-8")
            (run / "pw.out").write_bytes(stdout_payload)
            (run / "pw.err").write_bytes(stderr_payload)
            (run / "execution.json").write_bytes(execution_payload)

            extracted = qe_data_extraction.QeScfDataExtractor(
                artifact_root=root
            ).extract("run/pw.out")

        parsing = qe_data_extraction.QeScfOutputParser().action(
            request=qe_data_extraction.QeScfOutputParsingRequest(
                stdout_payload=stdout_payload,
                stderr_payload=stderr_payload,
                stdout_relative_path="run/pw.out",
                stderr_relative_path="run/pw.err",
            )
        )
        direct_sources = QePwDataSources(
            streams=parsing.streams,
            execution=QePwExecutionData(
                status="succeeded",
                returncode=0,
                stdout_filename="pw.out",
                stderr_filename="pw.err",
            ),
            execution_artifact=QePwNativeArtifact(
                relative_path="run/execution.json",
                sha256=hashlib.sha256(execution_payload).hexdigest(),
                byte_size=len(execution_payload),
            ),
        )
        direct = (
            qe_data_extraction.QeScfNormalizer()
            .action(
                request=qe_data_extraction.QeScfNormalizationRequest(
                    sources=direct_sources
                )
            )
            .data
        )

        self.assertEqual(direct, extracted)


def _parsing_request() -> qe_data_extraction.QeScfOutputParsingRequest:
    return qe_data_extraction.QeScfOutputParsingRequest(
        stdout_payload=qe_support.QE_PW_OUTPUT.encode("utf-8"),
        stderr_payload=qe_support.QE_STDERR.encode("utf-8"),
        stdout_relative_path="run/pw.out",
        stderr_relative_path="run/pw.err",
    )


def _sources(streams: QePwCapturedStreamData) -> QePwDataSources:
    return QePwDataSources(
        streams=streams,
        execution=QePwExecutionData(
            status="succeeded",
            returncode=0,
            stdout_filename="pw.out",
            stderr_filename="pw.err",
        ),
        execution_artifact=QePwNativeArtifact(
            relative_path="run/execution.json",
            sha256="0" * 64,
            byte_size=0,
        ),
    )


if __name__ == "__main__":
    unittest.main()
