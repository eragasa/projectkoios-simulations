# Exact SCF structure catalog

`catalog.toml` publishes exact immutable structure records used by workflow and
calculator-input examples. Resolution verifies representation, schema version,
byte size, SHA-256, path containment, and provenance before exposing a PhysKit
unit cell.

## Silicon records

`Si.PrimitiveUnitCell.json` and `Si.ConventionalUnitCell.json` preserve the
reviewed Applications transfer identities recorded in the catalog.

## Materials Project nickel record

`Ni.mp-23.PrimitiveUnitCell.json` is the canonical PhysKit adaptation of the
primitive structure selected by a live Materials Project one-element Ni hull.
The request used thermodynamic compatibility type `GGA_GGA+U_R2SCAN` and
selected material `mp-23` from six returned candidates.

The complete retained observation is
`provenance/Ni.mp-23.GGA_GGA+U_R2SCAN.json`. It contains exact query criteria,
all canonical candidate documents, source order, selected-candidate identity,
client/library versions, retrieval time, and exact structure identity. The
Materials Project client exposed no immutable database-release identifier, so
the candidate-response digest—not the retrieval date or material ID alone—is
the retained query identity.

The canonical structure identity is:

```text
structure_id: materials-project.mp-23.primitive
representation: primitive
byte_size: 619
sha256: c31a42131de24116e7262fd720147eee2491b8280516bd2aed0eeda618820ade
```

The record has status `external_reference_not_calculation_input`. It does not
declare local spin, occupation, pseudopotential, cutoff, k-point, relaxation,
execution, convergence, or acceptance policy. Those belong to a separate exact
simulation specification and its evidence.
