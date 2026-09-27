# `LammpsIntegrationObservation`

**Implemented in:** `projectkoios.integrations.lammps.models`

Aggregate whose `templates` field contains one or more LAMMPS template
observations.

Simulation names must be unique and `external_execution_authorized` must remain
`False`. `to_dict()` identifies the calculator as `lammps`, preserves template
order, and explicitly emits false execution, numerical-verification, and
scientific-validation claims.
