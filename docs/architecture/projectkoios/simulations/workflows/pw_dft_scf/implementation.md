# Plane-wave DFT SCF workflow implementation

## Module map

- `configuration.py` — campaign and bounded local-runtime records.
- `recipe.py` — single, k-point, cutoff, and joint-grid recipe projection.
- `comparison.py` — qualified comparison of successful SCF results.
- `convergence/base.py` — coordinates, observations, and assessments.
- `convergence/policy.py` — scientific threshold, window, extension, and budget
  declarations.
- `convergence/assessment.py` — pure axis and grid assessment.
- `convergence/controller.py` — extend/accept/budget-exhausted decisions.
- `convergence/comparison.py` — like-for-like convergence-test comparison.
- `convergence/replay/` — typed replay identity, request, evidence, actionizer,
  result, and error contracts.
- `workflow/base.py`, `definition.py`, and `facade.py` — status, topology source,
  and engine-hiding interface.
- `cpn/net.py`, `runtime.py`, and `workflow.py` — optional local SNAKES net,
  bounded firing wrapper, and facade implementation.

## Contract preservation

Public records are frozen, slotted dataclasses rooted in neutral SCF contracts.
Recipes retain request identity construction, coordinate ordering, numeric
validation, and exact failure behavior. Comparators retain ordered left/right
semantics and explicit interpretation qualifications. The convergence replay
keeps its established operation identity even though its Python namespace moved.

The old `PwDftScfConvergenceReplayer` and flat `pw_dft_scf.replay` module remain
absent. Only the typed convergence replay Actionizer contract exists.

## Import boundary

Production SCF workflow modules may import standard-library modules, protected
`projectkoios.simulations` core records, and sibling workflow modules. They may not import QE, VASP, other integrations, repository tools,
Applications, or a live generic Workflow runtime. The optional `cpn` subtree
alone imports the pinned `snakes` namespace.

Provider selection, input projection, and artifact parsing occur only in
repository tools. The local SNAKES CPN is isolated in the optional `cpn`
subtree; no other production module imports it. Tools consume public workflow
and integration records rather than being imported by production code.

## Validation and tests

Direct tests cover:

- recipe coordinates and request projection;
- single-result comparison and energy alignment;
- axis/grid convergence assessment;
- controller extension, acceptance, and budget exhaustion;
- convergence-test comparison;
- replay identity, evidence, action, results, errors, and retained QE evidence;
- topology source declarations; and
- the local CPN workflow and eight-campaign rendering in their production/tool
  test suites.

Repository tests additionally prove normalized namespace equivalence, public
API signatures, absence of the old import path, dependency boundaries, one
replay overlay only, exact fixture identity, and calculator-free execution.

## Documentation map

Every documented production package, subpackage, and public class node under
this SCF capability has an `index.md`, `schematics.md`, and `implementation.md`
trio. The wheel-carried CPN has its own architecture nodes. Repository tools and
compact examples use concise READMEs rather than misleading production-style
class documentation.
