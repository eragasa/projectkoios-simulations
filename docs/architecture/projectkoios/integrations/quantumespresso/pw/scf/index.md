# `scf`

This package implements calculator-input translation, rendering, native-output
parsing, normalization, replay, and action handling for Quantum ESPRESSO `pw.x`
SCF calculations. The current Python API calls calculator-input translation
“projection” and combines some of these architectural stages. The
[operation-boundary vocabulary](operations/) defines each responsibility and
keeps staging, execution, retention, Workflow correlation, and scientific
acceptance separate.

Input translation consumes the shared components declared by
`pw.inputfile.base`; calculator-neutral SCF contracts remain under
`simulations.dft.pw.scf`.

The [saved-state artifact-set boundary](saved_state_artifact_set/) defines an
immutable provider record, a strict canonical codec, retention-independent
logical identity derivation, and the exact candidate fragment projected from
canonical manifest bytes plus already-retained payload references. The
[saved-state candidate](saved_state_candidate/) is a path-free provider
companion to an unchanged successful child terminal outcome. Both remain
distinct from retention authority, managed-project scientific acceptance, and
later staging authority.
