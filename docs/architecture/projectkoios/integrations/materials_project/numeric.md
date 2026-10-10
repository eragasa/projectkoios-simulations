# Materials Project elemental-reference numerical contract

## Candidate energy retention

The snapshot retains source energy fields, corrections or adjustments, corrected
energy used by the compatible entry, composition normalization, and energy per
atom without presentation rounding. It does not reconstruct missing corrections
or silently substitute a different thermo type.

## Hull-distance handling

The selected elemental reference is expected on the constructed hull. The raw
computed hull distance is retained. A schema-defined small numerical tolerance
may qualify a value as numerically zero for reporting, but the original value
and tolerance remain evidence. The record does not overwrite the raw value with
zero without retaining that qualification.

## Canonical candidate digest

Canonical snapshot encoding uses strict versioned keys, finite numbers, explicit
units, sorted candidate identity, deterministic JSON, and one trailing newline.
Changing candidate membership, energy, correction data, identity, or structure
changes the candidate-set SHA-256.

The digest does not imply the remote database is immutable. It identifies only
the retained canonical response.

## Structure conversion

Lattice vectors are converted with explicit angstrom units and fractional site
coordinates. Conversion retains source ordering, rejects disordered sites, and
does not standardize or relax the structure. The resulting structure bytes have
their own size and SHA-256 independent of the candidate-set artifact.

## Selection consistency

The selected candidate must occur exactly once in the retained set. The
recorded material ID, selected entry ID, energy per atom, hull distance, and
copied structure must correlate. Candidate count must equal the retained set
length, not merely the count reported by an unverified caller.

## Missing service metadata

Unavailable database release/version metadata is represented explicitly. A
retrieval timestamp is not numerically or semantically interchangeable with a
database revision. Tests cover both supplied and unavailable revision metadata
without network access.
