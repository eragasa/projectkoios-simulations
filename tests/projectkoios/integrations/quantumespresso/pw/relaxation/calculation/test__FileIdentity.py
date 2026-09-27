from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.relaxation.calculation import (  # noqa: E501
    FileIdentity,
)


class FileIdentityTest(unittest.TestCase):
    def test_requires_positive_size_and_lowercase_sha256(self) -> None:
        valid = FileIdentity(byte_size=1, sha256="a" * 64)

        self.assertEqual(valid.byte_size, 1)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            FileIdentity(byte_size=0, sha256="a" * 64)
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            FileIdentity(byte_size=1, sha256="A" * 64)


if __name__ == "__main__":
    unittest.main()
