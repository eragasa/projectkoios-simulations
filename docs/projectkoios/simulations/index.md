# Legacy `projectkoios.simulations` documentation entry point

This path predates the repository's mirrored architecture-documentation tree.
The authoritative current architecture contract is
[`docs/architecture/projectkoios/simulations/index.md`](../../architecture/projectkoios/simulations/index.md).

The protected simulation core remains calculator-neutral: its identities,
records, resources, settings, and typed ports do not import workflow
composition, provider implementations, Applications, downstream consumers, or
live Workflow runtime objects. Calculator-specific syntax and behavior remain
under `projectkoios.integrations` and `projectkoios.adapters`.

The approved layered-umbrella architecture adds an owner-specific
`projectkoios.simulations.workflows` composition layer without weakening those
core rules. At commit `d4323213bffee3551b92f056b8b12f2a193ac15a`, the
workflow implementation still uses the sibling
`projectkoios.simulation_workflows` namespace; a later forward migration will
move it cleanly without aliases or coexistence. See the authoritative contract
for the import matrix, authority boundary, migration rules, and required proof.
