# `projectkoios.simulations.structure`

The public structure API provides immutable calculator-neutral contracts for
exact structure records, diagonal supercells, and ideal defect deltas.

## Exact structure library

- `StructureRecordReference`
- `StructureProvenanceReference`
- `TransferredStructureProvenance`
- `DerivedStructureProvenance`
- `ObservedStructureProvenance`
- `ObservedStructureScope`
- `StructureRecord`
- `StructureRepresentation`
- `StructureLibraryEntry`
- `StructureResolution`
- `StructureLibrary`
- `StructureLibraryManifestLoader`
- `StructureNotFoundError`
- `StructureConflictError`
- `StructureIntegrityError`
- `StructureManifestError`

```python
from pathlib import Path

from projectkoios.simulations.structure import StructureLibraryManifestLoader

library = StructureLibraryManifestLoader(
    manifest_path=Path("structures/catalog.toml").resolve()
).load()
record = library.require_unique("Si.ConventionalUnitCell")
resolution = library.resolve(record)
cell = resolution.unit_cell
```

`resolve()` verifies the full record declaration, path containment, nonsymlink
file, byte limit, exact size, SHA-256, schema, embedded structure ID, and exact
primitive/conventional/base-`UnitCell` representation. `resolve_unique()` is appropriate only
when the manifest declares one exact record for the stable identifier.

## Supercells

- `UnitCellSiteOrigin`
- `SuperCell`
- `SuperCellConstructionRequest`
- `SuperCellConstructionResult`
- `SuperCellBuilder`

`SuperCellBuilder` performs positive diagonal replication and preserves one
source-site origin for every generated atom.

## Defect deltas

- `UnitCellDefectDelta`
- `UnitCellDefectDeltaApplicator`
- `UnitCellDefectDeltaResult`

```python
from projectkoios.physkit.periodic.unit_cell import Atom
from projectkoios.simulations.structure import (
    UnitCellDefectDelta,
    UnitCellDefectDeltaApplicator,
)

delta = UnitCellDefectDelta(
    bulk_cell=bulk_cell,
    removals=(site_index,),
    additions=(
        Atom(symbol="P", position_fractional=removed_site.position_fractional),
    ),
    charge_state=0,
)
result = UnitCellDefectDeltaApplicator().action(request=delta)
```

Removal indices refer to the original bulk atom tuple and are simultaneous.
Retained atoms remain ordered; additions follow in declaration order. The
result is a base `UnitCell`. Charge state remains configuration metadata rather
than part of structure byte identity.

See the authoritative
[structure architecture](../../../architecture/projectkoios/simulations/structure/index.md)
for identity, validation, provenance, transformation, and authority boundaries.
