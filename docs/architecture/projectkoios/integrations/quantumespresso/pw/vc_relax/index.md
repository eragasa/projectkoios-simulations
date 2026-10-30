# `vc_relax`

This package projects calculator-neutral variable-cell relaxation requests into
Quantum ESPRESSO `pw.x` `calculation='vc-relax'` input. Cell dynamics, pressure,
and degrees of freedom remain explicit QE-native declarations.

The package does not select a zero-pressure policy, decide that normalized force
or pressure residuals are acceptable, or own cutoff/k-point convergence and
feedback after the cell changes. Those are provider-neutral workflow concerns.
For the planned bulk route, first-party `projectkoios.adapters` maps exact QE
observations to neutral records and `tools/pw_dft_bulk_qualification` owns
provider selection, operational configuration, and invocation.

One `vc-relax` process is one separately authorized occurrence. A predecessor
qualification never authorizes it, and its provider completion never authorizes
final-setting confirmation or a later re-relaxation.
