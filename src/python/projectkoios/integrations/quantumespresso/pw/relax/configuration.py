"""QE-native input policy for fixed-cell ``relax`` calculations."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw.inputfile.configuration import (  # noqa: E501
    QeRelaxationInputConfiguration,
)


@dataclass(frozen=True, slots=True)
class QeRelaxProjectionConfiguration(QeRelaxationInputConfiguration):
    """Declare native choices for fixed-cell ionic relaxation."""
