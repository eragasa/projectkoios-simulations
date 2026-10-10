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

`catalog.toml` has exact identity:

- byte size: `1502`;
- SHA-256: `16a52cdd077683e5d25cfa37568f4299b99861dd1a86f1c9b648ce03531f2ffa`.

Loading or resolving these records does not locate an executable, authorize a
calculator, or execute a simulation. Machine-local pseudopotential deployment
is resolved separately by `PseudopotentialLibrary` at the input-consumption or
execution boundary.
