"""Occurrence envelopes for reusable plane-wave DFT SCF specifications."""

from __future__ import annotations

import re
from dataclasses import dataclass

from projectkoios.simulations.dft.pw.scf.specification import PwDftScfSpecification

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class PwDftScfRequest:
    """Request one evaluation of an exact reusable SCF specification."""

    # Occurrence identity intentionally remains outside canonical specification
    # bytes so retries and repeated evaluations do not change scientific identity.
    evaluation_id: str
    specification: PwDftScfSpecification

    def __post_init__(self) -> None:
        if type(self.evaluation_id) is not str or not _IDENTIFIER.fullmatch(
            self.evaluation_id
        ):
            raise ValueError("evaluation_id must be a lowercase slug")
        if type(self.specification) is not PwDftScfSpecification:
            raise TypeError("specification must be a PwDftScfSpecification")
