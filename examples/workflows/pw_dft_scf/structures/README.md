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

## Materials Project boron and phosphorus records

The same injected-client, one-element `GGA_GGA+U_R2SCAN` selection was retained
for the B and P reservoirs needed by future Si:B and Si:P formation-energy
studies. The selections are exact observations of that query, not claims that
Materials Project energies are interchangeable with future local energies.

```text
B: materials-project.mp-160.primitive
   15 candidates; 12 sites; byte_size 2115
   sha256 0c020f96271ab74c9ae073824f682568604c30c0d5004363070d0a41d295ffeb

P: materials-project.mp-568348.primitive
   15 candidates; 84 sites; byte_size 11557
   sha256 5b05d50d0072e62a19a776af0b2aa7315d216f2b39b200d4ff6c922cd0510b33
```

Their complete query snapshots and selection evidence are retained under
`provenance/`. The Materials Project client again exposed no immutable database
release, so each canonical candidate-response digest is the query identity.

All three Materials Project records have status
`external_reference_not_calculation_input`. They do not declare local spin,
occupation, pseudopotential, cutoff, k-point, relaxation, execution,
convergence, or acceptance policy. Those belong to separate exact simulation
specifications and evidence.
