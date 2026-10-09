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

## Workflow inventory and facade

`PwDftScfWorkflowDefinition` inventories the public place and transition names
of one SCF lifecycle. It intentionally does not duplicate arcs, guards, or token
expressions. `PwDftScfWorkflowFacade` exposes typed pending actions, accepted
events, status, and terminal outcome while hiding the selected engine.

## Authoritative local Petri net

`pw_dft_scf.cpn.net.build_dft_pw_scf_net()` is the complete executable topology
transferred byte-for-byte from Applications. Its SNAKES `PetriNet` defines the
typed places, transitions, input/output arcs, guards, and token expressions. A
conformance test binds its name sets to `PwDftScfWorkflowDefinition`.

The optional `cpn` subtree remains authoritative until WORKFLOWS extracts the
engine adapter and defines its canonical runtime-neutral plan contract. It
consumes only neutral SCF domain values and never executes a calculator.

Repository tools under `tools/pw_dft_scf` may call public QE/VASP projection or
parsing APIs. The compact example tree contains only reviewed declarations,
structures, and small demonstrations. Provider integrations and tools never
become dependencies of the neutral workflow modules.
