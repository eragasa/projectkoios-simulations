# Quantum ESPRESSO integration examples

This directory mirrors the maintained Quantum ESPRESSO integration boundaries:

- `pw/scf/` owns QE `pw.x` SCF projection and retained native evidence;
- `pw/nscf/` retains the cited uniform-grid NSCF input used by the Wannier90
  interface example;
- `pw/relax/` and `pw/vc_relax/` own mode-specific input projection;
- `pw/relaxation/` owns their shared provenance-bound loading, rendering, and
  execution support;
- `pw2wannier90/` retains citation-bound native interface inputs without
  granting calculator-execution authority.

The `Si/` descendants provide concrete material examples. The
`pw2wannier90/Si/wannier90-3.1.0-example11/` input set is copied byte-for-byte
from the cited upstream Wannier90 release and is not a completed calculation.
This organization does not implement research-campaign management.
