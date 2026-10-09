# projectkoios-simulations

This repository owns calculator-neutral simulation identities, execution
records, DFT and pseudopotential contracts, and plane-wave SCF, NSCF, and
relaxation contracts under `projectkoios.simulations`. Reusable SCF and
relaxation capability composition belongs to the sibling
`projectkoios.simulation_workflows` namespace. Calculator-provider
implementations belong to outward `projectkoios.integrations` and
`projectkoios.adapters` namespaces in this same repository and distribution.

## Boundaries

- Keep the inward `projectkoios.simulations` namespace independent of outward
  provider namespaces, application packages, and workflow implementations.
- Workflow capabilities, outward provider integrations, and adapters may depend
  on `projectkoios.simulations`; the neutral namespace must not depend on them.
- Keep `projectkoios.simulation_workflows` independent of provider integrations,
  application packages, and workflow-runtime implementations.
- Do not add calculator-native input models, parsers, runners, convergence
  controllers, campaign recipes, workflow state, or scientific acceptance
  policy under `projectkoios.simulations`.
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
.venv/bin/python -m ruff format --check src/python tests
MYPYPATH=src/python .venv/bin/python -m mypy --strict \
  src/python/projectkoios/simulations \
  src/python/projectkoios/simulation_workflows
.venv/bin/python -m build --wheel
```

Use concise commit messages and include a `Revision note:` in every new commit
body. Do not push without explicit authorization.
