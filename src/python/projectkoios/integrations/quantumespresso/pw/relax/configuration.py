"""QE-native input policy for fixed-cell ``relax`` calculations."""

from __future__ import annotations

from projectkoios.integrations.quantumespresso.pw.inputfile.configuration import (  # noqa: E501
    QeRelaxationInputConfiguration,
)

QeRelaxProjectionConfiguration = QeRelaxationInputConfiguration
"""Alias the common configuration because fixed-cell relax adds no fields."""
