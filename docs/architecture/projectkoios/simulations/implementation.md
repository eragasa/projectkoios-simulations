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

## Namespace relocation

The namespace refinement is a forward change after public main commit
`0ca21564730015dcf989200858b0a6de3f26a038`; published history is not amended or
rewritten. The implementation moves
`src/python/projectkoios/simulation_workflows` atomically to
`src/python/projectkoios/simulations/workflows`, together with corresponding
tests and mirrored architecture descendants. It rewrites imports and
current-facing documentation without changing behavior, removes redundant
sibling-package discovery and typing declarations, preserves public symbols,
signatures, defaults, errors, evidence semantics, fixtures, and validation
order, and proves that old source and import paths are absent.

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
relocation contains substantive `index.md`, `schematics.md`, and
`implementation.md` files. Repository checks inventory every moved `pw_dft_*`
package/subpackage/class node and fail if any target node lacks the trio.

## Required proof

The namespace relocation proof requires:

- normalized old-versus-new source, test, and documentation equivalence after
  path and import rewriting;
- exact public API and error-contract equivalence;
- AST import-boundary checks for the asymmetric layer rules;
- full pytest, Ruff, formatting, configured strict-mypy, and reproducible-wheel
  gates;
- wheel smoke proving the new namespace imports and the old namespace does not;
- absence of simultaneous old and new production trees;
- exact 55-row workflow/example source accounting with one replay overlay and
  explicit final production, tool, example, test, or consolidation outcomes;
- byte identity of the retained campaign-projection fixture;
- historical provider-graph proof separately from current-head eight-campaign
  rendering; and
- no calculator execution.

## Sequencing

The namespace relocation and complete 55-path workflow/example source closure
form one combined migration. The executable CPN is production code pending
WORKFLOWS extraction; runners and shared loading are repository tools; campaign,
comparison, structure, replay, and relaxation demonstrations are compact
examples; fixture and probe paths remain test artifacts.
Applications source removal may proceed only after this combined migration
merges. Restoration or adaptation of the silicon predecessor must target a
named post-removal base. Historical transfer manifests remain historical facts;
current-facing origins record the completed relocation without rewriting prior
provenance.
