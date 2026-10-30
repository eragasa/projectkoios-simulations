# Plane-wave DFT SCF convergence implementation

## Source mapping

This node mirrors `src/python/projectkoios/simulations/workflows/pw_dft_scf/convergence/__init__.py` and its sibling modules.

## Relocation contract

The source moved from the historical `projectkoios.simulation_workflows` namespace to `projectkoios.simulations.workflows.pw_dft_scf.convergence` by path and import rewriting only. Fields, signatures, defaults, validation order, errors, evidence semantics, and stable operation identities are preserved. No old-path alias, re-export, shim, or facade is permitted.

## Bulk-qualification reuse and additive correlation

The existing coordinate, observation, assessor, assessment, and controller APIs
remain unchanged. The first bulk route does require one additive typed
qualification/correlation record around them. It binds exact structure,
request/specification, neutral cutoff realization, full sampling policy,
prepared input, selected occurrence, normalized evidence bytes, artifacts,
pseudopotentials, provider-adapter mapping, every observation, the unchanged
assessment, and the highest tested mesh/cutoff corner selected only when the
correlation is accepted.

Final confirmation reruns the existing recipe and assessor with sufficient
high-side context on the exact relaxed structure and creates a new correlation.
Cross-structure evidence is rejected rather than merged. Noncubic coordinates
and independently varying the density/potential cutoff remain future,
separately reviewed work.

## Enforceable imports

The implementation may import the Python standard library, protected `projectkoios.simulations` core contracts, and modules inside `projectkoios.simulations.workflows`. Imports from provider integrations, Applications, downstream consumers, or live Workflow service/kernel/runtime objects are forbidden.

## Verification

Relevant behavior remains covered under
`tests/projectkoios/simulations/workflows/pw_dft_scf`. Outer bulk-composition
tests must prove complete typed correlation and reject mixed structures,
requests/specifications, models, pseudopotentials, neutral cutoff realizations,
provider mappings, sampling, occurrences, normalized bytes, or artifacts and
preserve exact prior evidence when a
later structure requires changed settings. Repository gates require the
complete documentation trio, normalized old-to-new equivalence, public API
signature equivalence, AST dependency checks, strict mypy, Ruff, the full test
suite, reproducible wheel construction, new-path import smoke, and absence of
the historical import path. No gate authorizes calculator execution.
