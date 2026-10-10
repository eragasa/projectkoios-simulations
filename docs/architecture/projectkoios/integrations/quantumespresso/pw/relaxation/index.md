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
