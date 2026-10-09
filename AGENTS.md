# projectkoios-simulations

This repository owns the `projectkoios.simulations` simulation-domain
umbrella. Its non-workflow subtrees form the protected calculator-neutral core.
Reusable SCF and relaxation capability composition belongs to the
owner-specific `projectkoios.simulations.workflows` layer. Calculator-provider
implementations remain in the outward `projectkoios.integrations` and
`projectkoios.adapters` namespaces in this same repository and distribution.

## Boundaries

- Keep the protected core—every `projectkoios.simulations` subtree except
  `projectkoios.simulations.workflows`—independent of workflows, outward
  provider namespaces, application packages, and workflow-runtime
  implementations.
- `projectkoios.simulations.workflows` may depend on protected core contracts.
  It must not depend on provider integrations, application packages, domain
  consumers, or Workflow service/scheduler/persistence implementations. The
  optional `pw_dft_scf.cpn` subtree alone may import the pinned `snakes`
  namespace pending extraction by WORKFLOWS.
- Keep calculator-native input models, parsers, and runners in outward
  integrations. Keep reusable convergence controllers, recipes, assessment,
  replay, and workflow definitions in `projectkoios.simulations.workflows`.
- Keep reusable workflow contracts free of executable paths, reusable execution
  authority, scheduler lifecycle state, and provider implementation objects.
- Keep operational workflow runners, configuration loading, visualization, and
  provider composition under `tools/pw_dft_scf`. Keep only declarations, data,
  and small demonstrations under `examples/workflows`. Neither location grants
  calculator-execution authority.
- Do not restore the removed `projectkoios.simulation_workflows` sibling or add
  aliases, re-exports, shims, or compatibility facades for its former imports.
- Keep immutable public records as frozen, slotted dataclasses unless a
  documented contract requires otherwise.
- Calculator execution always requires explicit authorization. Tests must not
  interpret a smoke marker or ordinary test invocation as execution authority.
- Preserve historical-source license notices and exact transfer provenance.
- Do not claim behavioral conformance, numerical verification, or scientific
  validation from provenance alone.
- Before public release, reconcile advertised provider capability statuses with
  the outward provider packages actually included in the distribution.

## Verification

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check src/python tools examples tests
.venv/bin/python -m mypy
.venv/bin/python -m build --wheel
```

Use concise commit messages and include a `Revision note:` in every new commit
body. Do not push without explicit authorization.
