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

The workflow implementation now resides at
`projectkoios.simulations.workflows`. It moved forward from the historical
sibling `projectkoios.simulation_workflows` snapshot on public main commit
`0ca21564730015dcf989200858b0a6de3f26a038`. The old production import path is
absent; no alias or compatibility facade was introduced.

## Contents

- [`structure`](structure/index.md) defines exact manifest-backed structures,
  derived supercells, and generic ideal defect deltas.
- [`library`](library/index.md) specifies exact authenticated manifest-backed
  resolution of immutable SCF and relaxation specifications.
- [`calculator_input`](calculator_input/index.md) specifies exact rendered
  calculator inputs and external-file requirements without carrying execution
  authority.
- [`execution`](execution/index.md) defines one explicitly authorized,
  synchronous calculator attempt and the boundary between retained native
  artifacts, MVP console emission, and future runtime control.
- [`evidence`](evidence/index.md) specifies immutable correlation of exact
  specifications, rendered calculator input files, artifacts, and normalized
  observations.
- [`defects`](defects/index.md) specifies method-neutral chemical
  potentials, formation and relaxation energies, and mechanical size-convergence
  derivations.
- [`dft/defects`](dft/defects/index.md) specifies the plane-wave DFT
  binding for electron count, charge, spin, model compatibility, and qualified
  final-SCF evidence. It supplies inputs to `simulations.defects`; it does not
  own the equations.
- [`dft/pw/relaxation`](dft/pw/relaxation/index.md) documents neutral requests,
  normalized observations and results, and evidence-qualified relaxed-structure
  publication.
- [`workflows`](workflows/index.md) defines owner-specific, runtime-neutral
  workflow composition.
- Existing `dft`, `calculator`, and other non-workflow subtrees remain members
  of the protected core.

Calculator-specific syntax, parsing, and provider artifact handling remain
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
execution remains fail-closed, requires explicit external authorization, and
runs one synchronous simulation per executor invocation. Campaign-wide
concurrency belongs to the external Workflow runtime.

The migrated SCF SNAKES `PetriNet` currently owns its executable places,
transitions, arcs, guards, and token expressions. Its separate definition is a
name inventory only. Relaxation has a workflow-shape name inventory but no
executable Petri net. Future generic Workflow compilation may own extracted
canonical plans; generic Workflow runtime will own lifecycle mechanisms and
state. None of those ownership assignments grants an owner package a direct
import of live Workflow service, kernel, scheduler, worker, persistence, or
runtime objects.

See [`schematics.md`](schematics.md) for dependency and authority diagrams and
[`implementation.md`](implementation.md) for enforceable migration and testing
rules.
