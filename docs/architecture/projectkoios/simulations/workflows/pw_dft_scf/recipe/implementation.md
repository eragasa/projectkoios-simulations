# Plane-wave DFT SCF recipes implementation

## Source mapping

This node mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/recipe.py`.

## Relocation contract

The source moved from the historical `projectkoios.simulation_workflows` namespace to `projectkoios.simulations.workflows.pw_dft_scf.recipe` by path and import rewriting only. Fields, signatures, defaults, validation order, errors, evidence semantics, and stable operation identities are preserved. No old-path alias, re-export, shim, or facade is permitted.

## Coordinate scope and bulk reuse

Current request projection changes only the cubic mesh tuple and
`wavefunction_cutoff_ev` while preserving the remaining base request. This
existing behavior is sufficient for the first bulk route. A new typed
correlation around generated child requests retains exact seed structure,
scientific model, neutral cutoff realization, full k-point policy, projected
input, selected occurrence, normalized evidence bytes, and adapter mapping.
Provider-native cutoff controls remain outward evidence.

Recipe projection alone does not establish that child evidence exists or that a
selected coordinate is qualified on another structure. Bulk confirmation reruns
the existing recipe after relaxation rather than generalizing the coordinate.

## Enforceable imports

The implementation may import the Python standard library, protected `projectkoios.simulations` core contracts, and modules inside `projectkoios.simulations.workflows`. Imports from provider integrations, Applications, downstream consumers, or live Workflow service/kernel/runtime objects are forbidden.

## Verification

Relevant behavior remains covered under
`tests/projectkoios/simulations/workflows/pw_dft_scf`. Bulk-composition tests
must add deterministic checks for neutral-to-provider cutoff realization,
distinct structure identity, complete typed child evidence, and rejection of
mixed structures or models. Repository gates require the complete documentation
trio, normalized old-to-new equivalence, public API signature equivalence, AST
dependency checks, strict mypy, Ruff, the full test suite, reproducible wheel
construction, new-path import smoke, and absence of the historical import path.
No gate authorizes calculator execution.
