# Workflow definition implementation

## Source mapping

This node mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/workflow/definition.py`.
It is a detached name inventory. The authoritative executable topology,
including arcs and guards, is `pw_dft_scf/cpn/net.py`.

## Relocation contract

The source moved from the historical `projectkoios.simulation_workflows` namespace to `projectkoios.simulations.workflows.pw_dft_scf.workflow.definition` by path and import rewriting only. Fields, signatures, defaults, validation order, errors, evidence semantics, and stable operation identities are preserved. No old-path alias, re-export, shim, or facade is permitted.

## Enforceable imports

The implementation may import the Python standard library, protected `projectkoios.simulations` core contracts, and modules inside `projectkoios.simulations.workflows`. Imports from provider integrations, Applications, downstream consumers, or live Workflow service/kernel/runtime objects are forbidden.

## Verification

Relevant behavior remains covered under `tests/projectkoios/simulations/workflows/pw_dft_scf`. A CPN conformance test requires its name, places, and transitions to match the authoritative Petri net. Repository gates additionally require the complete documentation trio, normalized old-to-new equivalence, public API signature equivalence, AST dependency checks, strict mypy, Ruff, the full test suite, reproducible wheel construction, new-path import smoke, and absence of the historical import path. No gate authorizes calculator execution.
