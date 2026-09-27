from __future__ import annotations

from examples.projectkoios.integrations.quantumespresso.pw.scf.Si.primitive.convergence.joint.evidence import (  # noqa: E501
    RetainedObservationStage,
    RetainedQeScfEvidenceLoader,
)
from tests.support.repository_root import REPOSITORY_ROOT

_MANIFEST = (
    REPOSITORY_ROOT
    / "examples/projectkoios/integrations/quantumespresso/pw/scf/Si/primitive/"
    "convergence/joint/evidence/manifest.json"
)


def test_retained_qe_scf_evidence_has_complete_verified_byte_identities() -> None:
    evidence = RetainedQeScfEvidenceLoader(REPOSITORY_ROOT).load(_MANIFEST)

    assert len(evidence.observations) == 36
    assert (
        sum(
            item.stage is RetainedObservationStage.INITIAL_GRID
            for item in evidence.observations
        )
        == 30
    )
    assert (
        sum(
            item.stage is RetainedObservationStage.ADAPTIVE_EXTENSION
            for item in evidence.observations
        )
        == 6
    )
    assert sum(len(item.artifacts) for item in evidence.observations) == 144
    assert evidence.calculator.retained is False
    assert all(item.retained is False for item in evidence.pseudopotentials)
