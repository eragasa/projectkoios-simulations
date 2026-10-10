# Materials Project elemental-reference integration

## Purpose

`projectkoios.integrations.materials_project` adapts externally retrieved
Materials Project entries and structures. It is an outward optional integration;
the protected `projectkoios.simulations` core does not import pymatgen, mp-api,
or this package.

The integration migrates the explicit injected-`MPRester` boundary and immediate
immutable structure-copy design from `ksdft2effmass` commit
`c47d3cfcee7d4a46b66b14426650d5d811b3848d`. The migration replaces
application-specific periodic and mass-conversion records with PhysKit unit
cells. It adds elemental convex-hull selection, which was not present in the
donor implementation.

## Elemental convex-hull selection

`MaterialsProjectElementalReferenceSelector` requests all compatible entries
for one elemental chemical system through the injected client and constructs a
pymatgen `PhaseDiagram`. It selects the entry in `PhaseDiagram.el_refs`, records
its exact Materials Project identifier, energy per atom, zero hull distance,
entry count, requested thermodynamic compatibility types, and copied structure.

For the intended defect work, selection requests are made independently for B
and P using an explicitly declared Materials Project thermodynamic compatibility
scheme. The selected material IDs must be retained from the actual API response;
the software does not hard-code an allotrope based on a human label.

A one-element convex hull selects the lowest compatible calculated elemental
entry supplied by Materials Project. It is a zero-temperature database and
compatibility-scheme result. It is not an experimental standard state, finite-
temperature phase diagram, proof of ground-state stability, or scientific
acceptance decision.

A caller with an operator-owned API key can inject the current client explicitly:

```python
from mp_api.client import MPRester

from projectkoios.integrations.materials_project import (
    MaterialsProjectElementalReferenceRequest,
    MaterialsProjectElementalReferenceSelector,
)

with MPRester() as client:
    boron = MaterialsProjectElementalReferenceSelector().action(
        client=client,
        request=MaterialsProjectElementalReferenceRequest(
            element_symbol="B",
            thermo_types=("GGA_GGA+U_R2SCAN",),
        ),
    )
    phosphorus = MaterialsProjectElementalReferenceSelector().action(
        client=client,
        request=MaterialsProjectElementalReferenceRequest(
            element_symbol="P",
            thermo_types=("GGA_GGA+U_R2SCAN",),
        ),
    )
```

The resulting records—not presumed IDs—are the authoritative selections for
that retained database response and compatibility scheme.

## Retrieval snapshot

The current implementation retains the selected ID, selected energies, entry
count, request, exact copied structure content identity, and an immutable
`MaterialsProjectQuerySnapshot` containing:

- exact query parameters and requested thermodynamic compatibility types;
- retrieval timestamp and API endpoint/version metadata;
- Materials Project database or release identifier when the service supplies
  one;
- a deterministic canonical record for every returned candidate entry;
- byte size and SHA-256 of the complete canonical candidate set;
- exact selected entry and selected structure identities; and
- client/library versions used for adaptation and hull construction.

If the service does not expose an immutable database revision, the field is
explicitly unavailable. Retrieval timestamp plus candidate-response digest is
an exact retained observation, not a claim that a later live query will be
reproducible.

`MaterialsProjectElementalReference` references this snapshot and the selected
candidate digest. `entry_count` alone is not treated as sufficient provenance
for why one allotrope was selected.

## Structure adaptation

`MaterialsProjectStructureRetriever` accepts an injected client and an exact
`mp-N` request. The returned ordered pymatgen `Structure` is copied immediately
into an immutable `PrimitiveUnitCell` or `ConventionalUnitCell`. Lattice vectors
are retained in angstrom using a unit scale of one angstrom, and sites retain
fractional coordinates. Disordered sites are rejected rather than collapsed.

The geometry status is `external_reference_not_calculation_input`. Selecting a
hull entry does not make its downloaded geometry a converged production input;
that requires a separately declared relaxation and evidence record.

## Operational boundary

The package contains no API key, creates no `MPRester`, and performs no network
request by itself. Callers own credentials and inject the client. Tests use only
synthetic local entries and structures. This integration does not authorize
calculator execution.

Install the optional `materials-project` dependency group to supply `pymatgen`
and `mp-api`.

## Architecture references

See [`implementation.md`](implementation.md) for the snapshot schema and
publication rules, [`schematics.md`](schematics.md) for retrieval and local-
energy boundaries, [`scientific.md`](scientific.md) for cited hull
qualifications, and [`numeric.md`](numeric.md) for canonical snapshot and
selection consistency.

## Upstream method references

- [Materials Project API querying](https://docs.materialsproject.org/downloading-data/using-the-api/querying-data)
- [Materials Project phase-diagram methodology](https://docs.materialsproject.org/methodology/materials-methodology/thermodynamic-stability/phase-diagrams-pds)
- [pymatgen phase-diagram API](https://pymatgen.org/pymatgen.analysis)
