# Plane-wave DFT relaxation workflow implementation

## Module map

- `composition.py` contains campaign, handoff, composition-result, and composer
  records.
- `workflow/base.py` contains `PwDftRelaxationWorkflowStatus`.
- `workflow/definition.py` contains the immutable topology declaration and
  `pw_dft_relaxation_workflow_definition()` constructor.

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

## Import boundary

Production relaxation workflow modules import only protected neutral
simulation contracts and the standard library. They do not import QE, VASP,
example code, Applications, or generic Workflow runtime objects.

The QE example at `examples/workflows/pw_dft_relaxation/qe_projection.py`
composes this public production API with the public QE integration at the
outward example boundary. That dependency direction must not be reversed.

## Verification

Production tests cover campaign validation, projection composition, filename
and external-input preservation, fixed authority semantics, and topology source
places/transitions. The migrated QE example test uses a projection integration
with no calculator execution and verifies the rendered relaxation declaration
and non-authorizing handoff.

Repository gates also enforce exact source relocation, old-path absence,
documentation trios, and the separation between production workflows and
outward integrations.
