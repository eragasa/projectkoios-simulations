# Plane-wave DFT relaxation workflow capability

## Purpose

`projectkoios.simulations.workflows.pw_dft_relaxation` composes a neutral
relaxation request with one selected public input-projection integration. It
stops at a deterministic, non-authorizing execution handoff.

## Composition records

- `PwDftRelaxationCampaign` binds a stable campaign slug, an integration
  identity, and a neutral `PwDftRelaxationRequest`.
- `PwDftRelaxationComposer` resolves that integration through the neutral
  registry and projects provider inputs.
- `PwDftRelaxationCompositionResult` returns the campaign, projection, and
  handoff together.
- `PwDftRelaxationExecutionHandoff` lists rendered filenames and required
  external inputs while fixing the authority requirement to
  `separate-explicit-external-authority-required`.

The handoff contains no executable path, reusable authorization, queue state,
process identity, or method that starts a calculator.

## Current limitation and planned qualification

The implemented workflow stops at deterministic input projection and a
non-authorizing handoff. It does not consume terminal provider observations,
assemble exact evidence, assess normalized force or pressure residuals, publish
a zero-pressure workflow decision, or compose re-relaxation after changed
numerical settings.

The planned
[`pw_dft_bulk_qualification`](../pw_dft_bulk_qualification/index.md) capability
requires this workflow to expose a provider-neutral relaxation lifecycle and
zero-pressure assessor. That extension will bind the exact starting structure,
provisional typed SCF grid-correlation result, neutral cutoff/sampling setting,
target pressure, force/pressure criteria, result, evidence, and exact published
structure. Variable-cell qualification requires finite maximum force, finite
scalar pressure, and complete finite normalized stress and recomputes the
criteria. Provider completion, optimizer convergence, mechanical
criterion satisfaction, workflow acceptance, and scientific validation remain
separate.

## Workflow shape

`PwDftRelaxationWorkflowDefinition` inventories intended names for campaign,
projection action, projected input, external-authority requirement, and terminal
outcome. `PwDftRelaxationWorkflowStatus` supplies the coarse application-facing
status projection. These types do not define arcs, guards, a CPN kernel, or a
generic runtime; no executable relaxation Petri net is claimed here. Any future
complete lifecycle or cross-stage feedback topology requires separate review
and does not follow from the current name inventory.

## Example composition

The compact QE example is `examples/workflows/pw_dft_relaxation/qe_projection.py`.
Provenance records its historical `execute_relaxation.py` source path. The
module exposes only `compose(campaign, registry)`, returns the same
non-authorizing handoff, and has no command-line execution option.

Future native/neutral observation mapping belongs to first-party
`projectkoios.adapters`. Provider selection, operational configuration, and bulk
qualification invocation belong to `tools/pw_dft_bulk_qualification`. Neither
surface becomes a dependency of this neutral workflow, and every relaxation
process still requires separate external admission and authorization.
