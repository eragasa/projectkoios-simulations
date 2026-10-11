from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from snakes.nets import Expression, Variable
from snakes.nets import Test as SnakesTest

from projectkoios.simulations.dft.pw.scf.base import (
    PwDftScfRequestReference,
    PwDftScfWorkflowStart,
)
from projectkoios.simulations.workflows.pw_dft_scf.cpn.net import (
    build_dft_pw_scf_net,
)
from projectkoios.simulations.workflows.pw_dft_scf.workflow.definition import (
    pw_dft_scf_workflow_definition,
)

_NET_SOURCE_SHA256 = "4d580f686382851b32fccfbb7aa775782e3c44daf9e6efcf6d1cd95ca9d2d563"
_NET_SOURCE_BYTE_SIZE = 7173
_REPOSITORY_ROOT = Path(__file__).resolve().parents[6]


def test_authoritative_petrinet_source_is_the_reviewed_byte_sequence() -> None:
    source = (
        _REPOSITORY_ROOT
        / "src/python/projectkoios/simulations/workflows/pw_dft_scf/cpn/net.py"
    ).read_bytes()

    assert len(source) == _NET_SOURCE_BYTE_SIZE
    assert hashlib.sha256(source).hexdigest() == _NET_SOURCE_SHA256


def test_authoritative_petrinet_matches_the_public_name_inventory() -> None:
    definition = pw_dft_scf_workflow_definition()
    net = build_dft_pw_scf_net("inventory-check")

    assert net.name == definition.name
    assert len(net.place()) == 12
    assert len(net.transition()) == 8
    assert {place.name for place in net.place()} == set(definition.places)
    assert {transition.name for transition in net.transition()} == set(
        definition.transitions
    )


def test_constructed_topology_is_independent_of_the_evaluation_identity() -> None:
    first = build_dft_pw_scf_net("first-evaluation")
    second = build_dft_pw_scf_net("second-evaluation")

    assert _source_signature(first) == _source_signature(second)
    assert "first-evaluation" not in repr(_source_signature(first))
    assert "second-evaluation" not in repr(_source_signature(second))


def test_only_initial_tokens_vary_between_evaluation_net_instances() -> None:
    evaluation_id = "source-contract-evaluation"
    net = build_dft_pw_scf_net(evaluation_id)

    assert tuple(net.place("workflow_start").tokens) == (
        PwDftScfWorkflowStart(evaluation_id),
    )
    assert tuple(net.place("request").tokens) == (
        PwDftScfRequestReference(evaluation_id),
    )
    assert all(
        not tuple(place.tokens)
        for place in net.place()
        if place.name not in {"workflow_start", "request"}
    )


def test_constructed_net_uses_only_reviewed_snakes_annotation_kinds() -> None:
    net = build_dft_pw_scf_net("annotation-contract")

    assert all(type(transition.guard) is Expression for transition in net.transition())
    assert all(
        type(annotation) in {Expression, SnakesTest, Variable}
        for transition in net.transition()
        for _, annotation in (*transition.input(), *transition.output())
    )
    assert tuple(name for name, _ in net.globals) == (
        "RegisterPwDftScfTask",
        "SubmitPwDftScfTask",
        "AnalyzePwDftScfOutput",
        "PwDftScfResult",
        "PwDftScfWorkflowSucceeded",
        "PwDftScfWorkflowFailed",
    )


def _source_signature(net: Any) -> tuple[object, ...]:
    places = net.place()
    transitions = net.transition()
    return (
        tuple((place.name, repr(place.checker())) for place in places),
        tuple(
            (
                transition.name,
                str(transition.guard),
                tuple(
                    (place.name, type(annotation).__name__, str(annotation))
                    for place, annotation in transition.input()
                ),
                tuple(
                    (place.name, type(annotation).__name__, str(annotation))
                    for place, annotation in transition.output()
                ),
            )
            for transition in transitions
        ),
    )
