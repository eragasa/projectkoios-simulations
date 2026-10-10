# Structure library schematics

## Representation and meaning

```text
serialization representation          scientific meaning in provenance
----------------------------          --------------------------------
primitive                     +-----> transferred primitive source
conventional                  +-----> transferred conventional source
unit-cell                     +-----> pristine derived supercell
                              +-----> ideal defect cell
                              +-----> ion-relaxed observed cell
                              `-----> fully relaxed observed cell
```

A base `UnitCell` representation does not itself claim why the structure exists.

## Deterministic derivations

```text
exact conventional StructureRecord
               |
               +--> positive diagonal supercell transformation
               |                |
               |                v
               |       pristine SuperCell / UnitCell record
               |                |
               |                +--> UnitCellDefectDelta
               |                                 |
               |                                 v
               |                    ideal defect UnitCell record
               |
               `--> provenance retains every exact parent and operation
```

## Observed relaxed structures

```text
exact ideal defect StructureRecord
               |
exact relaxation SimulationRecord
               |
qualifying relaxation EvidenceRecord
               |
               v
explicit publication action
               |
               +--> ion-relaxed UnitCell record
               `--> fully relaxed UnitCell record
```

The publication role follows the exact relaxation scope. Evidence resolution
alone does not mutate the structure library.

## Provenance variants

```text
TransferredStructureProvenance
  source + immutable revision/snapshot + source path + source/result digests

DerivedStructureProvenance
  exact parent references + operation/version + canonical parameters + result digest

ObservedStructureProvenance
  exact starting reference + calculation/evidence references + scope + result digest
```

Every resulting `StructureRecord` also carries its own byte size and SHA-256.

## Dependency direction

```text
simulations.library -------------------> structure.library
simulations.evidence ------------------> structure.library
simulations.workflows -----------------> structure.library
integrations may publish through ------> structure.library contracts

structure.library -X-> simulations.library or evidence
structure.library -X-> workflows or integrations
structure.library -X-> calculator execution
```

To keep the protected core acyclic, observed provenance stores local immutable
content references containing stable ID, representation, schema version, byte
size, and SHA-256. The publication action verifies those references against
caller-supplied simulation and evidence records; the structure package does not
import their owning packages.
