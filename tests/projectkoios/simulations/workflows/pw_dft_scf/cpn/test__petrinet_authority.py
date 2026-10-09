from __future__ import annotations

from projectkoios.simulations.workflows.pw_dft_scf.cpn.net import (
    build_dft_pw_scf_net,
)
from projectkoios.simulations.workflows.pw_dft_scf.workflow.definition import (
    pw_dft_scf_workflow_definition,
)


def test_authoritative_petrinet_matches_the_public_name_inventory() -> None:
    definition = pw_dft_scf_workflow_definition()
    net = build_dft_pw_scf_net("inventory-check")

    assert net.name == definition.name
    assert {place.name for place in net.place()} == set(definition.places)
    assert {transition.name for transition in net.transition()} == set(
        definition.transitions
    )
