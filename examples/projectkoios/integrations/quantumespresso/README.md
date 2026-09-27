# Quantum ESPRESSO integration examples

This directory mirrors the maintained Quantum ESPRESSO integration boundaries:

- `pw/scf/` owns QE `pw.x` SCF projection and retained native evidence;
- `pw/relax/` and `pw/vc_relax/` own mode-specific input projection;
- `pw/relaxation/` owns their shared provenance-bound loading, rendering, and
  execution support.

The `Si/primitive/` descendants provide the concrete material example. This
organization does not implement research-campaign management.
