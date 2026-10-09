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

## Workflow shape

`PwDftRelaxationWorkflowDefinition` inventories intended names for campaign,
projection action, projected input, external-authority requirement, and terminal
outcome. `PwDftRelaxationWorkflowStatus` supplies the coarse application-facing
status projection. These types do not define arcs, guards, a CPN kernel, or a
generic runtime; no executable relaxation Petri net is claimed here.

## Example composition

The compact QE example is `examples/workflows/pw_dft_relaxation/qe_projection.py`.
Provenance records its historical `execute_relaxation.py` source path. The
module exposes only `compose(campaign, registry)`, returns the same
non-authorizing handoff, and has no command-line execution option.
