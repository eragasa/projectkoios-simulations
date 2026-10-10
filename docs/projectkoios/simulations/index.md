# Legacy `projectkoios.simulations` documentation entry point

This path predates the repository's mirrored architecture-documentation tree.
The authoritative current architecture contract is
[`docs/architecture/projectkoios/simulations/index.md`](../../architecture/projectkoios/simulations/index.md).

The protected simulation core remains calculator-neutral: its identities,
records, resources, settings, and typed ports do not import workflow
composition, provider implementations, Applications, downstream consumers, or
live Workflow runtime objects. Calculator-specific syntax and behavior remain
under `projectkoios.integrations` and `projectkoios.adapters`. The public
[structure contracts](structure/index.md) cover exact manifest-backed records,
derived supercells, and generic ideal defect deltas.

The layered-umbrella architecture includes the owner-specific
`projectkoios.simulations.workflows` composition layer without weakening those
core rules. The implementation moved forward from the historical sibling
`projectkoios.simulation_workflows` snapshot on public main commit
`0ca21564730015dcf989200858b0a6de3f26a038`; the old production path is absent
and no alias coexists. See the authoritative contract for the import matrix,
authority boundary, relocation rules, and required proof.
