# `projectkoios.simulations` layered umbrella

## Purpose

`projectkoios.simulations` is the distribution-owned umbrella for reusable
simulation-domain capabilities. The umbrella contains two architectural layers:

1. the **protected core**, comprising every existing
   `projectkoios.simulations` subtree except `workflows`; and
2. the owner-specific **workflow composition layer** at
   [`projectkoios.simulations.workflows`](workflows/index.md).

The protected core owns calculator-neutral identities, immutable scientific
records, resources, settings, and simulation contracts. The workflow layer owns
provider-independent comparison, convergence, assessment, recipe, replay,
composition, and workflow-definition contracts.

This is the approved target architecture for a forward namespace migration. At
commit `d4323213bffee3551b92f056b8b12f2a193ac15a`, the workflow implementation
still resides at `projectkoios.simulation_workflows`. A later reviewed change
will move it atomically; this documentation does not create an alias or claim
that the target import path is available yet.

## Contents

- [`workflows`](workflows/index.md) defines owner-specific, runtime-neutral
  workflow composition.
- Existing `dft`, `structure`, `calculator`, `execution`, and other non-workflow
  subtrees remain members of the protected core.
- Calculator-specific syntax, parsing, artifact handling, and execution remain
  outside the umbrella under `projectkoios.integrations` or
  `projectkoios.adapters`.

## Import matrix

| Importing layer | Protected core | `simulations.workflows` | Integrations/adapters | Downstream Applications/domain consumers | Live Workflow service/kernel/runtime |
| --- | --- | --- | --- | --- | --- |
| Protected core | Allowed | Forbidden | Forbidden | Forbidden | Forbidden |
| `simulations.workflows` | Allowed | Allowed | Forbidden | Forbidden | Forbidden |
| Integrations/adapters | Allowed | Forbidden in production integration modules | Allowed within the outward layer | Forbidden | Forbidden |
| Downstream application/domain composition | Allowed | Allowed | Allowed when that layer owns provider selection | Allowed within its own outward layer | Forbidden by this contract |

The table governs production imports, not whether public consumers are allowed
to import an outward package. `projectkoios.integrations` remains public; it is
kept outside the core and workflow dependency closures. This contract grants no
direct live-runtime import to Applications, examples, or other owner packages.
A future runtime integration requires a separately reviewed external binding or
process boundary. The narrower possibility of stable, runtime-neutral Workflow
source or SDK contracts remains a separate compiler-integration decision.

## Authority boundary

Neither protected core records nor workflow contracts carry reusable calculator
execution authority, executable discovery, scheduler lifecycle ownership,
leases, retries, cancellation, or provider implementation objects. Calculator
execution remains fail-closed and requires explicit external authorization.
Domain topology and guards are stated in owner source declarations. Generic
Workflow compilation owns canonical CPN places, transitions, and plans. Generic
Workflow runtime owns lifecycle mechanisms and state. None of those ownership
assignments grants an owner package a direct import of live Workflow service,
kernel, scheduler, worker, persistence, or runtime objects.

See [`schematics.md`](schematics.md) for dependency and authority diagrams and
[`implementation.md`](implementation.md) for enforceable migration and testing
rules.
