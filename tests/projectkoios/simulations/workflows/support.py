"""Application-test construction through public simulation contracts."""

from __future__ import annotations

from projectkoios.simulations.dft.pw.relaxation.base import PwDftRelaxationScope
from projectkoios.simulations.dft.pw.relaxation.request import PwDftRelaxationRequest
from projectkoios.simulations.dft.pw.scf.request import PwDftScfRequest
from tests.projectkoios.simulations.dft.pw.relaxation.support import (
    silicon_relaxation_request as _silicon_relaxation_request,
)
from tests.projectkoios.simulations.dft.pw.scf.support import (
    silicon_scf_request as _silicon_scf_request,
)


def silicon_scf_request() -> PwDftScfRequest:
    """Return one deterministic calculator-neutral silicon request fixture."""
    return _silicon_scf_request()


def silicon_relaxation_request() -> PwDftRelaxationRequest:
    """Return one deterministic fixed-cell relaxation request fixture."""
    return _silicon_relaxation_request(PwDftRelaxationScope.ATOMIC_POSITIONS)
