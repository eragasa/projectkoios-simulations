# Plane-wave DFT SCF workflow capability

## Purpose

`projectkoios.simulations.workflows.pw_dft_scf` composes neutral plane-wave DFT
SCF contracts into campaign, recipe, comparison, convergence, replay, and
workflow-source capabilities. It does not define provider-native input syntax,
parse provider artifacts, or execute a calculator.

## Configuration and recipes

`PwDftScfCampaignConfiguration` binds one registered integration identity to a
scientific recipe and a bounded local-runtime configuration. Recipes preserve a
neutral base request and produce immutable requests or coordinates:

- `PwDftScfSingleCalculationRecipe` — one SCF evaluation;
- `PwDftScfKpointConvergenceRecipe` — ordered cubic k-point densities at fixed
  cutoff;
- `PwDftScfCutoffConvergenceRecipe` — ordered cutoffs at fixed cubic mesh; and
- `PwDftScfGridConvergenceRecipe` — the ordered Cartesian product of both axes.

Recipes select scientific coordinates; they do not select executable paths or
grant execution authority.

## Result comparison

`PwDftScfComparator` performs a pure ordered comparison after two child SCF
workflows have successful terminal results. Native-energy comparison remains
descriptive. Reference-aligned comparison requires explicit reference identity,
energy, and qualification. Neither mode claims general cross-calculator
absolute-energy equivalence.

## Convergence

The convergence subtree owns:

- axes, coordinates, energy observations, and assessment records;
- one-dimensional and joint-grid assessors;
- policies for thresholds, stability windows, extension steps, and budgets;
- typed controller decisions to extend, accept, or report budget exhaustion;
- qualified comparison of like-for-like convergence tests; and
- replay of already normalized convergence evidence.

The replay contract is
`PwDftScfConvergenceReplayRequest` →
`PwDftScfConvergenceReplayActionizer.action(...)` →
`PwDftScfConvergenceReplayResult`. Its stable operation identity is
`projectkoios.applications.pw-dft-scf.convergence-replay`, version `1.0.0`.
There is no parallel replayer facade or untyped entry point.

## Workflow source

`PwDftScfWorkflowDefinition` names the required places and transitions for one
SCF lifecycle. `PwDftScfWorkflowFacade` exposes typed pending actions, accepted
events, status, and terminal outcome while hiding the selected engine. These
are domain source contracts: a generic Workflow compiler and runtime retain
ownership of canonical CPN plans and lifecycle state.

## Local CPN, tools, and examples

The optional `cpn` subtree contains the local SNAKES facade implementation
transferred from Applications pending later WORKFLOWS extraction. It consumes
only neutral SCF domain values and never executes a calculator.

Repository tools under `tools/pw_dft_scf` may call public QE/VASP projection or
parsing APIs. The compact example tree contains only reviewed declarations,
structures, and small demonstrations. Provider integrations and tools never
become dependencies of the neutral workflow modules.
