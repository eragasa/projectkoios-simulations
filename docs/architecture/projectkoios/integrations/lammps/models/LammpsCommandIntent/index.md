# `LammpsCommandIntent`

**Implemented in:** `projectkoios.integrations.lammps.models`

Immutable description of a historical LAMMPS invocation without authority to
perform it.

## Fields and invariants

- `simulation_name` is nonempty and at most 128 characters.
- `executable_environment_variable` must be exactly `LAMMPS_BIN`.
- `input_script` and `stdout_artifact` are normalized relative paths.
- `runner_script` is the exact `SourceFileEvidence` for the observed command.
- `execution_authorized` must remain `False`.

`to_dict()` fixes `program` to `lammps`, emits arguments `[-i, input_script]`,
and preserves the protected authorization state.
