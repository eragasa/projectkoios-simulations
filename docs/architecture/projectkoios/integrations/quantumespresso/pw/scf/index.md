# `scf`

This package implements projection, native-data extraction, replay, and action
handling for Quantum ESPRESSO `pw.x` SCF calculations. Its input projection
consumes the shared components declared by `pw.inputfile.base`;
calculator-neutral SCF contracts remain under `simulations.dft.pw.scf`.
