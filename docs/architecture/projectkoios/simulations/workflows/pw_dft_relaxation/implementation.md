# Plane-wave DFT relaxation workflow implementation

## Module map

- `composition.py` contains campaign, handoff, composition-result, and composer
  records.
- `workflow/base.py` contains `PwDftRelaxationWorkflowStatus`.
- `workflow/definition.py` contains the immutable workflow-shape name inventory
  and `pw_dft_relaxation_workflow_definition()` constructor.

No implemented workflow module owns terminal observation adaptation,
`SimulationEvidenceRecord` assembly, zero-pressure assessment, exact structure
publication composition, or feedback after a changed numerical setting.

## Validation behavior

Campaign identifiers remain lowercase slugs. Integration and request values
must have their exact neutral types. Handoff filename and external-input tuples
must be nonempty where required, unique, and composed of nonempty strings. The
authority requirement is fixed and rejects any attempt to replace it with an
execution-granting value.

The composer accepts only the neutral integration registry and campaign types.
It calls input projection exactly once, preserves rendered-input order, and
copies filenames and required external inputs into the handoff. It does not
resolve executables or invoke a provider runner.

## Planned bulk-qualification extensions

A separate API review must define a complete provider-neutral lifecycle and
assessment without reinterpreting the current projection result. The planned
extension must:

- consume exact normalized relaxation results and evidence through neutral
  contracts;
- bind the exact starting structure and provisional numerical qualification;
- require finite maximum force, finite scalar pressure, and complete finite
  normalized stress for variable-cell qualification and recompute the declared
  force/pressure comparisons with explicit missing-evidence behavior;
- validate the declared cell mode and final-cell consistency;
- distinguish provider completion, optimizer convergence, mechanical criterion
  satisfaction, and workflow disposition;
- compose exact relaxed-structure publication only after required mechanical
  facts pass; and
- emit non-authorizing requirements for fresh confirmation or a new relaxation
  when cross-stage composition changes the selected numerical setting.

The cross-stage feedback rule itself belongs to the planned
`pw_dft_bulk_qualification` sibling, not to provider modules or the protected
relaxation core.

## Import boundary

Production relaxation workflow modules import only protected neutral
simulation contracts and the standard library. They do not import QE, VASP,
example code, Applications, or generic Workflow runtime objects.

First-party provider-to-neutral mapping for the future lifecycle belongs under
`projectkoios.adapters`, while provider selection, operational configuration,
and invocation belong under `tools/pw_dft_bulk_qualification`. Production
relaxation workflow modules must not import either outward surface.

The QE example at `examples/workflows/pw_dft_relaxation/qe_projection.py`
composes this public production API with the public QE integration at the
outward example boundary. That dependency direction must not be reversed.

## Verification

Production tests cover campaign validation, projection composition, filename
and external-input preservation, fixed authority semantics, and intended
workflow-shape names. The migrated QE example test uses a projection integration
with no calculator execution and verifies the rendered relaxation declaration
and non-authorizing handoff.

Future lifecycle tests must additionally cover finite force/scalar-pressure/
complete-stress requirements, threshold recomputation, missing normalized
quantities, exact starting/final structure lineage, changed
settings, non-authorizing successor requirements, and distinct failed or
inconclusive outcomes. They use synthetic, retained, or fake-executable evidence
only.

Repository gates also enforce exact source relocation, old-path absence,
documentation trios, and the separation between production workflows and
outward integrations.
