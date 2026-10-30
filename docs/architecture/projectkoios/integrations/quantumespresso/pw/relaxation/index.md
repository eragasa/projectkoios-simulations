# `relaxation`

This support package owns provenance-bound calculation loading, typed
[ionic and lattice-vector options](options/index.md), deterministic rendering
dispatch, explicitly authorized execution, native output observation, and
final-structure extraction shared by the `relax` and `vc_relax` mode packages.

Both modes return the unified [`QeRelaxData`](data/index.md) facade. It retains
stdout, stderr, the stdout-observed trajectory, the supplied parsed QEXSD
document record, interpreted final structure, optional execution record, exact
artifact identities, and mechanical consistency observations without defining
scientific acceptance policy. `QeRelaxData.normalize()` requires the exact
starting `StructureResolution` and interpreted QEXSD final structure, preserves
the exact starting lattice for fixed-cell relaxation, and converts terminal
energy, maximum force, stress,
pressure, magnetization, convergence state, ionic-step count, and provider
version into `PwDftRelaxationObservation`. QE compression-positive
`Ry/bohr³` stress is converted explicitly to tension-positive pascals while the
native stream record remains unchanged.

The package does not define a third QE calculation mode or duplicate QEXSD XML
parsing.

## Planned bulk-qualification boundary

This integration owns QE-native preparation, one-process execution,
authentication, parsing, and normalization only. It does not decide that a
structure is zero-pressure qualified, choose force or pressure thresholds,
transfer a cutoff/k-point result between structures, schedule final-setting
confirmation, or request re-relaxation after a changed setting.

QE relaxation configuration represents explicit `ecutwfc` and `ecutrho`
values. These remain provider evidence. A first-party outward
`projectkoios.adapters` surface proves the exact native input realizes the
neutral wavefunction and density/potential cutoff setting and maps authenticated
QE observations to public neutral contracts. `tools/pw_dft_bulk_qualification`
owns provider selection, operational configuration, and route invocation.

Every `relax` or `vc-relax` process remains one separately admitted occurrence
requiring external authorization. A preceding SCF qualification or subsequent
confirmation requirement supplies no execution authority.
