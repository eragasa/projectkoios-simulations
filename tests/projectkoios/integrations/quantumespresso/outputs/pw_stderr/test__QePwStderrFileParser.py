from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.outputs.pw_stderr import (
    QePwStderrFile,
    QePwStderrFileParser,
)


class QePwStderrFileParserTest(unittest.TestCase):
    def test_parse_represents_each_supported_ieee_flag_once(self) -> None:
        parsed = QePwStderrFileParser().parse(
            b"IEEE_OVERFLOW_FLAG\n"
            b"IEEE_INVALID_FLAG\n"
            b"IEEE_OVERFLOW_FLAG\n"
            b"IEEE_UNDERFLOW_FLAG\n",
            output_file=QePwStderrFile(relative_path="silicon.err"),
        )

        self.assertEqual(
            parsed.ieee_flags,
            (
                "IEEE_INVALID_FLAG",
                "IEEE_OVERFLOW_FLAG",
                "IEEE_UNDERFLOW_FLAG",
            ),
        )

    def test_parse_accepts_an_empty_stderr_file(self) -> None:
        self.assertEqual(
            QePwStderrFileParser()
            .parse(
                b"",
                output_file=QePwStderrFile(relative_path="silicon.err"),
            )
            .ieee_flags,
            (),
        )


if __name__ == "__main__":
    unittest.main()
