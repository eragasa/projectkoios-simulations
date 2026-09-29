# VASP data-source composition

`VaspDataSourceExtractor` reads a completed VASP run directory into immutable
`VaspDataSources`. The record keeps execution evidence, exact artifact
identities, parsed `OUTCAR`, and optional parsed `vasprun.xml` separate. Small
native siblings (`OSZICAR` and `CONTCAR`) are retained by identity. Large
`WAVECAR`, `CHGCAR`, `LOCPOT`, and `PROCAR` products are streamed only to
compute bounded post-execution identity records. Extraction counts streamed
bytes, stops at the configured bound, and rejects identity, size, or timestamp
changes observed while hashing. Their content is not loaded into a mode facade
or folded into another source.

The extractor requires a successful `execution.json`, rejects symlinks and path
escape, bounds every read, and recognizes VASP's zero-return-code
negative-lattice failure in captured stdout. Artifact SHA-256 identities are
computed only after execution has completed.

Mode facades compose this shared source record:

- `VaspScfData` retains the calculator-neutral SCF observation and mechanical
  OUTCAR/XML consistency results;
- `VaspNscfData` retains k-points, weights, eigenvalues, occupations, and the
  Fermi energy from `vasprun.xml`;
- `VaspRelaxData` retains every source-ordered ionic `calculation` element,
  including all electronic iterations, energies, structures, forces, and
  stresses.

Consistency values compare source representations mechanically. They do not
constitute convergence policy or scientific acceptance.
