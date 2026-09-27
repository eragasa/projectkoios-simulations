# `projectkoios.integrations.lammps.models`

**Source:** `.../integrations/lammps/models.py`

This module owns immutable observations of retained LAMMPS templates and their
protected command intent.

## Classes

- [`LammpsCommandIntent`](LammpsCommandIntent/index.md)
- [`LammpsDataStructureObservation`](LammpsDataStructureObservation/index.md)
- [`LammpsTemplateObservation`](LammpsTemplateObservation/index.md)
- [`LammpsIntegrationObservation`](LammpsIntegrationObservation/index.md)

The internal `_relative` validator requires normalized, nonempty, relative
POSIX paths without `.` or `..` components.
