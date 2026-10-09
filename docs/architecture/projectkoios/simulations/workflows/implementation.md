# `projectkoios.simulations.workflows` implementation rules

## Allowed imports

For the exact namespace migration, production workflow modules may import only:

- standard-library modules;
- protected `projectkoios.simulations` core contracts; and
- other modules within `projectkoios.simulations.workflows`, while respecting
  acyclic package boundaries.

The move introduces no new third-party dependency and no generic Workflow
dependency.

## Forbidden imports and state

Production workflow modules must not import:

- `projectkoios.integrations` or `projectkoios.adapters`;
- Applications or downstream domain packages;
- `ksdft2effmass` or other consumers; or
- live generic Workflow runtime implementations.

They must not own executable discovery, process paths, reusable calculator
authority, canonical CPN places, transitions, or plans, queues, operation or
attempt identity, leases, retries, cancellation, reconciliation, result
delivery, or provider-native parsing. Domain source declarations may state
scientific topology and guards as compiler input; generic Workflow owns their
canonical compiled representation. Repository boundary tests must enforce the
forbidden roots recursively.

A future compiler integration may depend on a stable, runtime-neutral Workflow
source or SDK contract only after a separate dependency and architecture
review. Such a change must remain free of Workflow service, kernel, scheduler,
worker, persistence, and other live runtime objects; it is not part of this
namespace move.

## Clean public import break

The forward migration changes imports from
`projectkoios.simulation_workflows...` to
`projectkoios.simulations.workflows...`. It is a clean break: no old package,
alias, re-export, facade, or import shim remains. The move changes ownership and
module paths only; public classes, functions, fields, defaults, validation
order, error behavior, evidence semantics, and fixture bytes remain unchanged.

The stable replay action identity
`projectkoios.applications.pw-dft-scf.convergence-replay` must remain unchanged.
Python namespace relocation is not a reason to change an established operation
identity.

## Tests and packaging

Tests move to `tests/projectkoios/simulations/workflows` and import only the new
namespace. Package discovery already includes `projectkoios.simulations.*`; the
migration removes redundant sibling declarations and verifies typed-package
resources in the built wheel. Configured `python -m mypy` must cover protected
core, integrations, and the nested workflow layer.

Required validation includes the repository test suite, Ruff checks, formatting,
configured strict mypy, reproducible wheel builds, import smoke, old-path
absence, normalized move equivalence, and repository import-boundary gates. No
test may infer calculator-execution authority from an ordinary invocation or a
smoke marker.

## Deferred closure

The provider/example closure remains deferred until the namespace move merges.
It must then target `projectkoios.simulations.workflows` directly and compose
public integrations only at its outward boundary. Applications source removal
and the later silicon-predecessor adaptation remain separate authorized steps.
