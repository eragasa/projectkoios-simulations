# `projectkoios.simulations` implementation rules

## Protected-core enforcement

For dependency checks, the protected core is every production module below
`projectkoios.simulations` except `projectkoios.simulations.workflows`.
Protected-core modules must not import:

- `projectkoios.simulations.workflows`;
- `projectkoios.integrations` or `projectkoios.adapters`;
- application or downstream-domain packages; or
- generic Workflow runtime implementations.

Repository AST boundary tests must enforce these rules recursively rather than
relying on naming conventions or review alone.

## Forward namespace migration

The namespace refinement must be a forward commit after
`d4323213bffee3551b92f056b8b12f2a193ac15a`; published history must not be
amended or rewritten. The implementation slice must:

1. move `src/python/projectkoios/simulation_workflows` atomically to
   `src/python/projectkoios/simulations/workflows`;
2. move the corresponding test and mirrored architecture-documentation trees;
3. rewrite imports and current-facing documentation without changing behavior;
4. remove sibling-package discovery, typing, and mypy declarations made
   redundant by the nested package;
5. preserve all public symbols, signatures, defaults, errors, evidence
   semantics, fixtures, and validation order; and
6. prove that the old source and import paths are absent.

No alias, facade, re-export, deprecation proxy, or compatibility shim is
permitted. The replay action identity
`projectkoios.applications.pw-dft-scf.convergence-replay` remains byte-for-value
unchanged because it identifies the operation, not its Python module location.

## Documentation completeness

Mirrored architecture documentation uses:

```text
docs/architecture/<package>/<subpackage>/.../<ClassName>/
```

Every documented package, subpackage, and class node created or moved by the
forward migration must contain substantive `index.md`, `schematics.md`, and
`implementation.md` files. The migration must inventory every moved
`pw_dft_*` package/subpackage/class node and fail if any target node lacks the
trio. This architecture-first slice deliberately does not pre-create those
nodes before their code moves.

## Required proof

The forward migration requires:

- normalized old-versus-new source, test, and documentation equivalence after
  path and import rewriting;
- exact public API and error-contract equivalence;
- AST import-boundary checks for the asymmetric layer rules;
- full pytest, Ruff, formatting, configured strict-mypy, and reproducible-wheel
  gates;
- wheel smoke proving the new namespace imports and the old namespace does not;
- absence of simultaneous old and new production trees; and
- no calculator execution.

## Sequencing

After the namespace migration merges, migrate the deferred provider/example
closure directly against `projectkoios.simulations.workflows`. Only after that
separate slice merges may Applications source removal proceed. Restoration or
adaptation of the silicon predecessor must target a named post-removal base.
Historical transfer manifests remain historical facts; current-facing origins
may record the later relocation without rewriting prior provenance.
