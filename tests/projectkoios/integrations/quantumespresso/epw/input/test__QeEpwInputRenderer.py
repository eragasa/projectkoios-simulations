from __future__ import annotations

import math
import unittest

from projectkoios.integrations.quantumespresso.epw.input import (
    QeEpwInputAssignment,
    QeEpwInputConfiguration,
    QeEpwInputRenderer,
)


class QeEpwInputRendererTest(unittest.TestCase):
    def test_renders_typed_assignments_in_declared_order(self) -> None:
        rendered = QeEpwInputRenderer().render(
            QeEpwInputConfiguration(
                assignments=(
                    QeEpwInputAssignment("prefix", "si"),
                    QeEpwInputAssignment("outdir", "./tmp"),
                    QeEpwInputAssignment("amass(1)", 28.0855),
                    QeEpwInputAssignment("elph", True),
                    QeEpwInputAssignment("nbndsub", 4),
                    QeEpwInputAssignment("proj(1)", "Si:sp3"),
                )
            )
        )

        self.assertEqual(rendered.filename, "epw.in")
        self.assertEqual(
            rendered.text,
            "--\n"
            "&inputepw\n"
            "  prefix = 'si'\n"
            "  outdir = './tmp'\n"
            "  amass(1) = 28.0855\n"
            "  elph = .true.\n"
            "  nbndsub = 4\n"
            "  proj(1) = 'Si:sp3'\n"
            "/\n",
        )

    def test_escapes_native_string_quotes(self) -> None:
        rendered = QeEpwInputRenderer().render(
            QeEpwInputConfiguration(
                assignments=(
                    QeEpwInputAssignment("prefix", "test's"),
                    QeEpwInputAssignment("outdir", "./"),
                )
            )
        )

        self.assertIn("prefix = 'test''s'", rendered.text)

    def test_rejects_duplicate_assignment_names_case_insensitively(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            QeEpwInputConfiguration(
                assignments=(
                    QeEpwInputAssignment("prefix", "si"),
                    QeEpwInputAssignment("PREFIX", "other"),
                    QeEpwInputAssignment("outdir", "./"),
                )
            )

    def test_requires_provider_identity_assignments(self) -> None:
        with self.assertRaisesRegex(ValueError, "prefix"):
            QeEpwInputConfiguration(assignments=(QeEpwInputAssignment("outdir", "./"),))

    def test_rejects_nonfinite_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            QeEpwInputAssignment("degaussw", math.inf)


if __name__ == "__main__":
    unittest.main()
