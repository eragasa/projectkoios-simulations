# Silicon Quantum ESPRESSO single-SCF integration

This directory retains a static QE-native projection for a primitive-silicon
SCF calculation. The rendered `pw.in` and `input-projection.json` files are
inspection examples; this repository does not include an application runner
that regenerates, replays, or executes them.

Application-layer campaign and replay declarations are intentionally not part
of this provider example. They are routed to the `projectkoios.applications`
composition owner in the `projectkoios-applications` repository. `pw_dft_scf`
is one composable capability there, not a standalone application. The retained
files do not establish runnable inputs, numerical verification, convergence, or
scientific validation.
