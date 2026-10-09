# `projectkoios.simulations.workflows` implementation rules

## Production source inventory

Production code resides at
`src/python/projectkoios/simulations/workflows` and contains 31 Python modules:

- `_optional_dependencies.py` guards the required neutral simulation contracts;
- `pw_dft_scf` contains configuration, recipe, comparison, convergence, replay,
  workflow-source, and optional local-CPN modules; and
- `pw_dft_relaxation` contains projection composition and workflow-source
  modules.

The umbrella uses `src/python/projectkoios/simulations/py.typed`; there is no
second typing marker for the nested workflow layer.

## Allowed and forbidden imports

Production workflow modules may import only:

- the Python standard library;
- protected `projectkoios.simulations` core contracts; and
- other modules inside `projectkoios.simulations.workflows`, respecting acyclic
  package boundaries; and
- the `snakes` namespace, only from `pw_dft_scf.cpn` and only when the optional
  `cpn` extra is installed.

Production modules must not import:

- `projectkoios.integrations` or `projectkoios.adapters`;
- Applications or downstream consumer packages;
- example modules; or
- live generic Workflow service, kernel, scheduler, worker, persistence, or
  runtime implementations.

Repository AST gates enforce both directions: protected core cannot import the
workflow layer, and the workflow layer cannot escape outward.

## Public contract rules

Immutable public records remain frozen, slotted dataclasses. Relocation
preserves fields, signatures, defaults, validation order, error types/messages,
evidence semantics, and operation identities. In particular,
`projectkoios.applications.pw-dft-scf.convergence-replay` remains unchanged
because it identifies a domain operation rather than a Python module.

No historical import alias, re-export, deprecation proxy, facade, or namespace
shim is permitted.

## Tools, examples, and optional engines

Reusable local CPN code resides in the wheel-carried `pw_dft_scf.cpn` subtree.
The `cpn` extra pins the maintained `projectkoios-snakes` fork while preserving
its `SNAKES` distribution name and `snakes` import namespace.

Operational runners reside under `tools/pw_dft_scf` and may compose public
integrations at that outward repository boundary. Plotly is isolated in the
`visualization` extra. Reviewed declarations and small demonstrations reside
under `examples/workflows`; they contain no runner framework or engine state.
The retained campaign fixture and exact-provider probe remain at
`tests/fixtures/pw_dft_scf` and `tests/support`.

## Combined migration provenance

The production namespace relocation starts from exact public Simulations commit
`0ca21564730015dcf989200858b0a6de3f26a038`. Runner/example sources start from
Applications commit `416be52d539bfbffdbc8a27bd8e13de65404821b` and use exactly
one approved example overlay from
`7b687fb23b9877b744bfba3455040db2cbf94292`.

Historical source paths and hashes remain in
`docs/provenance/deferred-provider-example-main-416be52.tsv`; its filename
records the superseded initial classification. The 55-row disposition map in
`docs/provenance/workflow-runner-relocation-main-416be52.tsv` records each final
production, tool, example, test, or documentation-consolidation outcome.

## Verification

Required gates include:

- normalized source, test, documentation, and public-API equivalence;
- exact 55-row source accounting with explicit final dispositions;
- one replay-example overlay only;
- byte-exact campaign fixture identity;
- historical commit/tree and provider-graph reconstruction;
- separate current-head rendering of all eight campaigns;
- production, tool, and example import-boundary checks;
- old-path and compatibility-facade absence;
- substantive architecture trios and valid local links;
- full pytest, Ruff, formatting, configured strict mypy, and reproducible wheel
  construction; and
- wheel/sdist inventories that distinguish wheel-carried CPN modules from
  repository tools and examples.

No gate executes a calculator. Optional local engines use synthetic events or
retained artifacts only.

Applications source removal may proceed only after this combined migration is
reviewed and merged. Any later silicon-predecessor adaptation remains a
separate authorized change.
