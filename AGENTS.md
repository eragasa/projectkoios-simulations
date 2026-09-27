# projectkoios-simulations

This repository owns calculator-neutral simulation identities, execution
records, DFT and pseudopotential contracts, and plane-wave SCF, NSCF, and
relaxation contracts under `projectkoios.simulations`.

## Boundaries

- Keep this package independent of calculator-provider repositories,
  application packages, and workflow implementations.
- Provider integrations may depend on this package; this package must not
  depend on providers.
- Do not add calculator-native input models, parsers, runners, convergence
  controllers, campaign recipes, workflow state, or scientific acceptance
  policy.
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
  src/python/projectkoios/simulations
.venv/bin/python -m build --wheel
```

Use concise commit messages and include a `Revision note:` in every new commit
body. Do not push without explicit authorization.
