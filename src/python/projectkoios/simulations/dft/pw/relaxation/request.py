"""Occurrence envelopes for plane-wave DFT relaxation specifications."""

from __future__ import annotations

import re
from dataclasses import dataclass

from projectkoios.simulations.dft.pw.relaxation.specification import (
    PwDftRelaxationSpecification,
)

_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationRequest:
    """Request one evaluation of an exact reusable relaxation specification."""

    # This envelope is occurrence data; the nested specification alone owns the
    # stable scientific content identity used by prepared inputs and evidence.
    evaluation_id: str
    specification: PwDftRelaxationSpecification

    def __post_init__(self) -> None:
        if type(self.evaluation_id) is not str or not _IDENTIFIER.fullmatch(
            self.evaluation_id
        ):
            raise ValueError("evaluation_id must be a lowercase slug")
        if type(self.specification) is not PwDftRelaxationSpecification:
            raise TypeError("specification must be a PwDftRelaxationSpecification")
