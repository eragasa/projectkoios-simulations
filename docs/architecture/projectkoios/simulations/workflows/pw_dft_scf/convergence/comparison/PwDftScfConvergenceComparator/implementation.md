# PwDftScfConvergenceComparator implementation

## Source mapping

This node mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/comparison.py`. Public symbol: `PwDftScfConvergenceComparator`.

## Relocation contract

The source moved from the historical `projectkoios.simulation_workflows` namespace to `projectkoios.simulations.workflows.pw_dft_scf.convergence.comparison` by path and import rewriting only. Fields, signatures, defaults, validation order, errors, evidence semantics, and stable operation identities are preserved. No old-path alias, re-export, shim, or facade is permitted.

## Enforceable imports

The implementation may import the Python standard library, protected `projectkoios.simulations` core contracts, and modules inside `projectkoios.simulations.workflows`. Imports from provider integrations, Applications, downstream consumers, or live Workflow service/kernel/runtime objects are forbidden.

## Verification

Relevant behavior remains covered under `tests/projectkoios/simulations/workflows/pw_dft_scf`. Repository gates require the complete documentation trio, normalized old-to-new equivalence, public API signature equivalence, AST dependency checks, strict mypy, Ruff, the full test suite, reproducible wheel construction, new-path import smoke, and absence of the historical import path. No gate authorizes calculator execution.
