"""Stable identities for calculator integrations selected by simulations."""

from __future__ import annotations

import re
from dataclasses import dataclass

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class CalculatorIntegrationId:
    """Select one source-controlled calculator integration by stable identity."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not _IDENTIFIER.fullmatch(self.value):
            raise ValueError("integration identifier must be a lowercase slug")
