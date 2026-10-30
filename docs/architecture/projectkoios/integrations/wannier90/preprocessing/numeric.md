# Planned Wannier90 preprocessing numerical contract

## Purpose

The future provider contract must preserve exact input identity, reciprocal
source order, integer dimensions, and bounded native parsing. It does not
select scientific convergence thresholds or accept a construction.

Byte size, SHA-256, logical role, seedname, integer cardinality, and declared
source order are exact checks. Floating-point coordinate comparisons require an
explicit unit, convention, metric, and prospectively declared tolerance.

## Exact input invariants

One preprocessing occurrence binds exactly one native input identity. The
provider verifies:

- safe seedname and seed-derived basename rules;
- complete input byte size and SHA-256;
- exact construction-declaration and predecessor identities;
- one ordered lattice and atomic inventory;
- one source-ordered reciprocal-point inventory;
- finite energy-window and localization-control values where present;
- positive integer band, projection, and Wannier counts; and
- an explicit spin/component declaration.

A provider renderer must be deterministic for the same complete declaration.
Presentation whitespace participates in byte identity after rendering even when
it does not change native semantics. A caller-supplied exact input follows a
separate authenticated-input path and is not claimed to equal rendered bytes
unless exact equality is checked.

## Topology cardinality and ordering

Let `N_k` be the reciprocal-point count and `N_n(k)` the declared neighbor count
for source point `k`. A normalized topology observation must retain:

- exactly `N_k` source points in declared order;
- each ordered `(source, target, reciprocal_shift)` entry;
- valid one-based native indices mapped explicitly to neutral zero- or
  one-based conventions;
- positive bounded neighbor cardinalities; and
- explicit projection and excluded-band inventories.

Duplicate neighbor records, out-of-range indices, incomplete source groups,
malformed shifts, or trailing undeclared content are failures. Set equality is
insufficient because downstream overlap matrices depend on native ordering.

## Lattice and coordinate checks

Direct and reciprocal lattices must use declared units and conventions. The
provider observation retains native values before any comparison. A correlation
with a parent declaration must state:

- whether vectors are rows or columns;
- direct-length and reciprocal-length units;
- the reciprocal `2 pi` convention;
- coordinate wrapping policy; and
- absolute tolerance used after unit conversion.

Coordinate matching must reject ambiguity. Sorting or modulo reduction must not
be introduced after identity is established unless the exact permutation or
integer reciprocal shift is retained.

## Dimension separation

The provider keeps distinct:

```text
N_b  parent/interface band count
N_p  projection-function count
N_w  Wannier rank
N_k  reciprocal-point count
```

No general equality among `N_b`, `N_p`, and `N_w` is assumed. Equal values do
not prove a common state-space map. Excluded-band declarations change the
interface inventory and therefore the construction identity.

## Bounds and failure

Native parsing must apply positive reviewed bounds before allocating arrays or
accepting artifact totals. A future implementation should expose conservative
provider defaults while permitting stricter caller-supplied bounds. Exceeding a
bound is an explicit unsupported/failure outcome, not permission to truncate an
artifact.

Non-finite values, integer overflow, malformed exponents, incomplete records,
duplicate indices, and inconsistent cardinalities are rejected. The exact
native artifact remains retained evidence when safe, but no successful handoff
is assembled.

## Acceptance boundary

A dimensionally consistent topology does not demonstrate adequate reciprocal
sampling, projection quality, window choice, localization convergence, or
interpolation accuracy. Consumer-owned comparisons may apply tolerances later,
but no default scientific tolerance is inferred from parser precision, process
return code, or observed results. No numerical check in this document grants
calculator execution.
