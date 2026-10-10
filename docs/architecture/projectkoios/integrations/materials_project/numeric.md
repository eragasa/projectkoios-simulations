# Materials Project elemental-reference numerical contract

## Candidate energy retention

The snapshot retains source energy fields, corrections or adjustments, corrected
energy used by the compatible entry, composition normalization, and energy per
atom without presentation rounding. It does not reconstruct missing corrections
or silently substitute a different thermo type.

## Hull-distance handling

`PhaseDiagram.el_refs` supplies an entry on the constructed one-element hull.
The selector computes its hull distance and normalizes an absolute value no
greater than `1.0e-12` eV to `0.0` eV. The complete candidate entries,
compatibility scheme, response identity, and pymatgen version remain available
to reconstruct and audit that calculation. No nonzero value outside this fixed
tolerance is rewritten.

## Canonical candidate digest

Canonical snapshot encoding uses strict versioned keys, finite numbers, explicit
units, sorted candidate identity, deterministic JSON, and one trailing newline.
Changing candidate membership, energy, correction data, identity, or structure
changes the candidate-set SHA-256.

The digest does not imply the remote database is immutable. It identifies only
the retained canonical response.

## Structure conversion

Lattice vectors are converted with explicit angstrom units and fractional site
coordinates. Conversion retains source ordering, normalizes IEEE signed zero,
rejects disordered sites, and does not standardize or relax the structure. The
resulting structure bytes have
their own size and SHA-256 independent of the candidate-set artifact.

## Selection consistency

The selected candidate must occur exactly once in the retained set. The
recorded material ID, selected candidate digest, energy per atom, hull distance,
and copied structure must correlate. Candidate count must equal the retained set
length, not merely the count reported by an unverified caller.

## Missing service metadata

Unavailable database release/version metadata is represented explicitly. A
retrieval timestamp is not numerically or semantically interchangeable with a
database revision. Tests cover both supplied and unavailable revision metadata
without network access.
