# `projectkoios.simulations.workflows`

## Purpose

`projectkoios.simulations.workflows` is the owner-specific composition layer
inside the `projectkoios.simulations` umbrella. It turns calculator-neutral
simulation intent, results, and normalized evidence into reusable scientific
operations, workflow-shape inventories, and the migrated local SCF Petri net.

The production layer is calculator-neutral and provider-independent. It may
produce an execution handoff or consume provider-normalized observations, but
it contains no calculator-native syntax, parser, provider object, executable
path, reusable authority, or live Workflow runtime state.

## Capability catalog

### Plane-wave DFT SCF

`pw_dft_scf` owns:

- campaign and bounded local-runtime configuration;
- single-calculation, k-point, cutoff, and joint-grid recipes;
- qualified comparison of successful single-SCF results;
- convergence coordinates, observations, policies, and assessments;
- convergence-test comparison;
- assess/extend/accept/budget-exhausted controller decisions;
- typed convergence replay with the stable operation identity
  `projectkoios.applications.pw-dft-scf.convergence-replay`;
- an engine-neutral single-SCF name inventory and facade; and
- the complete optional local SNAKES `PetriNet`, currently authoritative for
  places, transitions, arcs, guards, and token expressions pending extraction
  by WORKFLOWS.

### Plane-wave DFT relaxation

`pw_dft_relaxation` owns:

- a campaign that binds neutral relaxation intent to a selected integration;
- deterministic translation of a neutral request into calculator input files
  (called input projection in the current Python API);
- a non-authorizing external-execution handoff; and
- an engine-neutral input-translation/handoff workflow-shape declaration. There
  is no
  executable relaxation Petri net in this package.

### Planned chained defect-formation composition

[`pw_dft_defect_formation`](pw_dft_defect_formation/index.md) inventories the
chained reference-convergence, host-relaxation, supercell-construction,
defect-start, staged-relaxation, final-SCF, basin-selection, formation-energy,
and size-convergence workflows required for neutral Si:P and Si:B. The
production package and executable topology do not yet exist. The documentation
does not displace the current SCF Petri-net authority.

Every child calculation is one simulation occurrence. The generic executor
handles one authorized occurrence synchronously and provides MVP live stdout
while retaining exact native output; see
[`simulations.execution`](../execution/index.md). Campaign sequencing and a
deployment-wide concurrency limit of one belong to the external Workflow
runtime rather than to a batch executor.

## Tools and examples

Operational commands live under `tools/pw_dft_scf`, outside package discovery.
They provide calculator-input rendering, replay, planning, two forms of
comparison, and visualization over public workflow and integration contracts.

The compact `examples/workflows` tree contains only reviewed campaign,
comparison, and structure declarations plus small replay and relaxation
composition demonstrations. It contains no reusable runtime or runner
infrastructure. Neither tools nor examples execute calculators.

## Distinction from generic Workflow

“Workflows” here means simulation-domain composition. This package owns typed
requests, actions or actionizers, results, policies, handoffs, and workflow
shape. For SCF, `pw_dft_scf.cpn.net.build_dft_pw_scf_net()` is the current
executable topology source. The separate `PwDftScfWorkflowDefinition` records
its public names for inspection; it does not reproduce the net's arcs, guards,
or token expressions and is not advertised as sufficient compiler input.

A future generic Workflow compiler will own extraction or translation into its
canonical CPN plans. Its runtime will own occurrence identity, queues,
idempotency, leases, retries, cancellation, reconciliation, delivery, and
execution authority. Until that extraction, the optional `cpn` subtree carries
the complete Applications-owned SNAKES adapter. It exposes no Workflow service,
scheduler, worker, persistence mechanism, or calculator authority.

## Namespace and provenance

The production capability moved atomically from the historical sibling
`projectkoios.simulation_workflows` snapshot on public main commit
`0ca21564730015dcf989200858b0a6de3f26a038`. The old import path is absent and
has no alias, shim, facade, or re-export. The combined migration accounts for
all 55 Applications workflow/example source paths, then classifies them into
production CPN code, repository tools, compact examples, tests, or consolidated
documentation.

See [`schematics.md`](schematics.md) for layer and authority flows and
[`implementation.md`](implementation.md) for dependency, packaging,
provenance, and verification rules.
