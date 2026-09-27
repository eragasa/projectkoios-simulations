# projectkoios-simulations

This repository owns calculator-neutral simulation identities, execution
records, DFT and pseudopotential contracts, and plane-wave SCF, NSCF, and
relaxation contracts under `projectkoios.simulations`. Execution-independent,
provider-native adapters may live outward under `projectkoios.integrations`.

## Boundaries

- Keep the inward `projectkoios.simulations` namespace independent of outward
  provider namespaces, application packages, and workflow implementations.
- Outward provider integrations may depend on neutral contracts; the neutral
  namespace must never import from `projectkoios.integrations`.
- Do not add calculator-native input models, parsers, runners, convergence
  controllers, campaign recipes, workflow state, or scientific acceptance
  policy under `projectkoios.simulations`.
- Keep native parsers under their outward integration owner. Parsers must not
  grow calculator execution, workflow, or scientific-acceptance behavior.
- Keep immutable public records as frozen, slotted dataclasses unless a
  documented contract requires otherwise.
- Calculator execution always requires explicit authorization. Tests must not
  interpret a smoke marker or ordinary test invocation as execution authority.
- Preserve historical-source license notices and exact transfer provenance.
- Do not claim behavioral conformance, numerical verification, or scientific
  validation from provenance alone.

## Verification

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check src/python tests
MYPYPATH=src/python .venv/bin/python -m mypy --strict \
  src/python/projectkoios/simulations src/python/projectkoios/integrations
.venv/bin/python -m build --wheel
```

Use concise commit messages and include a `Revision note:` in every new commit
body. Do not push without explicit authorization.
