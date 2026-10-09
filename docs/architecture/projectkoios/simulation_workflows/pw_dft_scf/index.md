# Plane-wave DFT SCF application

Scientific comparison, convergence, recipe, configuration, and workflow
behavior composed over the calculator-neutral
[`simulations.dft.pw.scf`](../../simulations/dft/pw/scf/index.md) contracts.
Terminal comparison remains a pure, qualified analysis after successful child
workflows join; it does not redefine calculator-native observations or claim
absolute-energy equivalence.

## Runtime-neutral convergence replay action

The cohesive convergence replay operation is exposed directly from
`pw_dft_scf.convergence.replay` as the typed
`PwDftScfConvergenceReplayRequest` →
`PwDftScfConvergenceReplayActionizer.action(...)` →
`PwDftScfConvergenceReplayResult` contract. Its stable action identity is
`projectkoios.applications.pw-dft-scf.convergence-replay`, version `1.0.0`.
The request carries only provider-normalized evidence. The action is pure: it
performs no calculator execution, parsing, filesystem mutation, runtime
selection, state persistence, or authority decision.

There is no parallel replayer façade or untyped entry point. A generic workflow
compiler may bind the stable action identity to one pure transition; it must not
decompose the application-owned assess/extend/accept operation into
scheduler-owned scientific steps. This package has no dependency on a workflow
runtime or engine.
