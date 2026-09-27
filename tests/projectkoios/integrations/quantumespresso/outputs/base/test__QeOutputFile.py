from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.outputs.base import (
    QeOutputFile,
)


class QeOutputFileTest(unittest.TestCase):
    def test_accepts_a_safe_relative_path(self) -> None:
        self.assertEqual(
            QeOutputFile(relative_path="silicon.out").relative_path, "silicon.out"
        )

    def test_rejects_path_escape(self) -> None:
        with self.assertRaisesRegex(ValueError, "safe relative path"):
            QeOutputFile(relative_path="../silicon.out")


if __name__ == "__main__":
    unittest.main()
