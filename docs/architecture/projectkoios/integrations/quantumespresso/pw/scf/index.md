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

QE projection maps the neutral wavefunction cutoff to `ecutwfc` and uses an
explicit provider configuration ratio to render `ecutrho`. Those names and the
ratio remain provider evidence. A first-party adapter proves that each exact QE
input realizes the neutral wavefunction and density/potential cutoff setting
referenced by bulk qualification. This integration does not select convergence
policy or import the SCF workflow.

The [saved-state artifact-set boundary](saved_state_artifact_set/) defines an
immutable provider record, a strict canonical codec, retention-independent
logical identity derivation, and the exact candidate fragment projected from
canonical manifest bytes plus already-retained payload references. The
[saved-state candidate](saved_state_candidate/) is a path-free provider
companion to an unchanged successful child terminal outcome. Both remain
distinct from retention authority, managed-project scientific acceptance, and
later staging authority.

For planned bulk qualification, production QE modules continue to return
provider-native inputs, outputs, and observations. A first-party outward
`projectkoios.adapters` surface maps those public records to exact
structure-scoped neutral evidence. `tools/pw_dft_bulk_qualification` owns
provider selection, operational configuration, and route invocation. Neither
the integration nor adapter decides convergence, schedules relaxation, grants a
successor authority, or claims that a provisional seed-structure result
transfers to a relaxed structure.
