# Structure library numerical contract

## Exact bytes and floating-point values

A `StructureRecord` identifies serialized bytes exactly. SHA-256 and byte size
apply to the committed UTF-8 document, not to an approximate geometry. The codec
has one canonical ordering, unit representation, numeric rendering rule, and
trailing newline for each schema version.

Exact byte identity and geometric equivalence are different questions. The
library proves the former. A separate numerical qualification is required for
claims that independently produced coordinates or lattices are equivalent
within tolerance.

## Fractional coordinates and lattice vectors

Stored fractional positions are finite three-component values in the half-open
interval `[0, 1)`. Atom ordering is significant because defect removal indices
and provenance refer to the original ordered tuple. Periodically equivalent but
numerically different coordinates are not silently wrapped or reordered during
resolution.

Lattice vectors preserve orientation and the codec's declared vector-axis
convention. The library does not silently rotate, reduce, standardize, or change
handedness to make two cells compare equal.

## Deterministic derived cells

Supercell and ideal-defect publication must reproduce the exact expected atom
order, lattice, and positions from the declared parent and operation. The output
record stores its own digest. Reapplying a derivation to the same exact parent
must reproduce the same bytes.

A changed parent record, transformation, removal index, addition order, species,
position, or charge metadata creates a different derivation identity. Charge
metadata changes provenance and declaration identity even though it does not
change structure bytes.

## Fixed-cell relaxation

For an `ATOMIC_POSITIONS` calculation, the starting lattice is authoritative
because the cell is not an allowed degree of freedom. The normalized final
`UnitCell` uses the exact starting lattice and the observed final positions.
Any lattice printed by the calculator is retained as a consistency observation
and compared against the starting lattice under an explicit unit-aware
tolerance; it does not replace the authoritative fixed lattice.

This avoids false byte differences caused only by output precision or unit
conversion while preserving evidence of a calculator that unexpectedly changed
or reported an inconsistent cell.

## Variable-cell relaxation

For an `ATOMIC_POSITIONS_AND_CELL` calculation, the observed final lattice is
part of the new structure bytes. Publication requires finite, nonsingular,
positive-orientation lattice data, explicit units, final atomic positions, and a
qualifying pressure/stress observation when available.

The numerical qualification records lattice-volume change, vector changes, and
any pressure residual. It does not choose whether volume-only, shape-only, or
full lattice relaxation is scientifically intended; that remains an explicit
simulation/workflow declaration.

## Comparison reporting

Numerical comparisons retain raw source values, converted values, units,
tolerances, and maximum deviations. They do not round before deciding, clamp
small changes to zero, or convert tolerance-qualified equality into exact byte
identity.
