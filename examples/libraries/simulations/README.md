# Exact simulation library

This directory retains canonical calculator-neutral simulation specifications
and their strict version-one manifest.

The initial catalog contains the reviewed silicon primitive-cell SCF bases used
by the repository workflow tools:

- `Si.PrimitiveUnitCell.QE.SCF.Single`;
- `Si.PrimitiveUnitCell.QE.SCF.ConvergenceBase`; and
- `Si.PrimitiveUnitCell.VASP.SCF.Single`.

The QE records deliberately differ in wavefunction cutoff. The VASP record is a
separate scientific specification because its occupation and electronic
convergence controls differ from the QE records. Each specification embeds the
complete exact structure record and pseudopotential identity.

The catalog also contains zero-pressure relaxation bases for local Si, B, and P
reference phases:

- `Si.ConventionalUnitCell.QE.Relaxation.ReferenceBase`;
- `materials-project.mp-160.primitive.QE.Relaxation.ReferenceBase`; and
- `materials-project.mp-568348.primitive.QE.Relaxation.ReferenceBase`.

They use exact SSSP 1.3.0 PBE precision-set pseudopotentials, the common maximum
recommended cutoff of 55 Ry (748.31312176467 eV), fixed occupations, and explicit
starting meshes of 6×6×6, 8×8×8, and 4×4×2. Silicon preserves cubic shape with
volume-only relaxation; the external B and P phases allow unrestricted lattice
vectors. These are reviewable starting specifications, not cutoff, k-point,
relaxation, or scientific-acceptance evidence.

`catalog.toml` has exact identity:

- byte size: `3175`;
- SHA-256: `1e013edcfd46214179190d2d2047881f45ea7d7272a2cc89cc3ad18713553d46`.

Loading or resolving these records does not locate an executable, authorize a
calculator, or execute a simulation. Machine-local pseudopotential deployment
is resolved separately by `PseudopotentialLibrary` at the input-consumption or
execution boundary.
