# `projectkoios.integrations.lammps.inspection`

**Source:** `.../integrations/lammps/inspection.py`

## `inspect_lammps_templates(...)`

Consumes explicit `lmps_sim_type` settings plus path-keyed evidence and text.
For each setting it:

1. derives `lmp_scripts_db/<declared-directory>`;
2. collects and sorts retained file evidence below that directory;
3. requires `runsimulation.sh` evidence and text;
4. requires exactly one command matching `$LAMMPS_BIN -i INPUT > OUTPUT`, the
   braced environment-variable form, or a source-pinned absolute executable
   whose basename begins with `lmp`;
5. requires the referenced input script to exist; and
6. returns a `LammpsIntegrationObservation` with execution-disabled intents.

A historical absolute executable is never retained as authority: it is
normalized to the `LAMMPS_BIN` boundary. This interpretation agrees with the
source-pinned `pyflamestk.lammps.Simulation.run`, which invokes the retained
`runsimulation.sh`; the shell line still provides the exact input and output
names. The private `_COMMAND` regular expression recognizes only this bounded
command shape. The inspector records intent; it does not expand environment
variables, open files, invoke a shell, or execute LAMMPS.

## `inspect_lammps_data_structure(...)`

Inspects a bounded LAMMPS data structure as text. It parses the species comment,
atom and atom-type counts, orthogonal bounds, tilt factors, Atoms section, atom
style, identifiers, type indices, and finite numerical columns. It returns a
`LammpsDataStructureObservation` and never creates a calculator or simulation.
