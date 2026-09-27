# `LammpsDataStructureObservation`

`LammpsDataStructureObservation` is an immutable, execution-disabled summary of
a source-pinned LAMMPS data structure. Its public fields are `name`, `evidence`,
`species_order`, `atom_count`, `atom_type_count`, `atom_style`, `bounds`, and
`tilt_factors`.

Construction requires unique species, consistent atom-type counts, atomic or
charge style, three finite increasing bounds, and three finite tilt factors.
`to_dict()` emits only the bounded observation and explicitly denies calculator
execution and scientific-validation claims.
