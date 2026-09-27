# `LammpsTemplateObservation`

**Implemented in:** `projectkoios.integrations.lammps.models`

Observation of one declared simulation template directory.

`simulation_name` identifies the declared simulation. `template_directory` is
normalized and relative. `files` must be nonempty, uniquely pathed, and already
sorted by relative path. `command_intent` binds the single observed runner
command for the same simulation.

`to_dict()` emits the simulation name, template directory, ordered file
evidence, and protected command intent.
