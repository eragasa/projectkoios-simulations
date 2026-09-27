from __future__ import annotations

import unittest

from projectkoios.integrations.quantumespresso.pw.inputfile.cell import (
    QeCellDynamics,
)


class QeCellDynamicsTest(unittest.TestCase):
    def test_rejects_documented_unimplemented_value_explicitly(self) -> None:
        self.assertFalse(QeCellDynamics.STEEPEST_DESCENT.implemented)
        with self.assertRaisesRegex(NotImplementedError, "QE 7.5"):
            QeCellDynamics.STEEPEST_DESCENT.require_implemented()

    def test_accepts_implemented_value(self) -> None:
        self.assertIsNone(QeCellDynamics.BFGS.require_implemented())
