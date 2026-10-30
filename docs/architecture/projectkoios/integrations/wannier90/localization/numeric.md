# Planned Wannier90 localization execution numerical contract

## Purpose

The future provider contract closes exact native input/output identities and
checks integer dimensions, reciprocal source order, neighbor topology, matrix
shape, and finite values. It does not prescribe scientific tolerances or accept
a representation.

Exact byte identities, roles, cardinalities, indices, and source order are not
tolerance comparisons. Coordinate or matrix-property comparisons require an
explicit metric, units where applicable, and prospectively declared tolerance.

## Route-specific input dimensions

For a declared route, keep distinct:

```text
N_k       reciprocal-point count
N_b       interface/outer band count
N_p       projection-function count
N_w       Wannier rank
N_n(k)    neighbor count at source point k
N_s       spin-component count
```

The ordinary AMN/MMN route requires complete interface eigenvalue,
projection, and neighbor-overlap observations consistent with `N_k` and `N_b`.
It does not require or consume an UNK inventory. Converter-produced UNKs form a
correlated sibling profile with its own expected cardinality and per-file
reciprocal-point/spin index rules for a named downstream consumer. They enter a
Wannier90 occurrence only under a separately reviewed native plotting or
transport mode that explicitly consumes them. No optional mode may weaken the
ordinary localization role checks.

`N_b`, `N_p`, and `N_w` need not be equal. A disentanglement transformation may
be rectangular between outer and retained spaces. A square gauge matrix acts
within the retained Wannier space. Equal dimensions do not replace an explicit
state-space declaration.

## Reciprocal and neighbor ordering

Every interface and matrix observation retains the declared reciprocal-point
order. Neighbor overlap observations must match the preprocessing topology in
ordered `(source, target, reciprocal_shift)` inventory. A permutation is valid
only when explicitly represented and applied consistently to every correlated
artifact.

Set equality, independent sorting, or coordinate rounding is insufficient.
Coordinate comparisons state reciprocal basis, wrapping policy, metric, and
absolute tolerance and reject ambiguous matches.

## Output closure and dimensions

A route-qualified output manifest declares required, permitted optional, and
forbidden selected retained-evidence roles. The accepted first generic non-spin
spectral profile requires one WOUT and one real-space Hamiltonian; it requires
one unitary-matrix set and one disentanglement-matrix set exactly when the
construction declares those transformations. Correlation checks as applicable:

- final centers and spreads contain exactly `N_w` ordered functions;
- every reported localization iteration has a complete consistent function
  inventory;
- gauge observations contain `N_k` matrices with retained-space dimensions;
- disentanglement observations contain `N_k` transformations compatible with
  the outer band inventory and `N_w`;
- real-space Hamiltonian blocks are `N_w x N_w` in declared orbital order;
- one positive degeneracy is present for each real-space representative where
  required by the native format; and
- seedname, spin semantics, parent identity, and construction identity agree
  across all outputs.

An optional output is not accepted merely because a file with an expected
basename exists. Its role, exact bytes, producer occurrence, and dimensions are
bound explicitly.

## Finite values and bounds

Native parsers reject non-finite required values, malformed indices, duplicate
records, incomplete inventories, trailing undeclared content, and checked-size
overflow before dense allocation. Provider limits bound artifact count, byte
size, dimensions, and numeric records. Exceeding a bound is an unsupported or
failed observation, not permission to truncate.

Source precision and native units are retained. Presentation rounding never
changes stored evidence or route decisions.

## Process and convergence values

Timeout, return code, native iteration count, provider convergence marker,
centers, spreads, and objective components are separate observations. A zero
return code does not substitute for a convergence marker. A convergence marker
does not substitute for route-level dimensions or downstream accuracy tests.

A consumer may define additional numerical checks—unitarity, Hermiticity,
construction/withheld interpolation residuals, velocities, curvatures, or
operator differences—but their metrics and thresholds remain outside this
provider execution contract.

## Failure and acceptance boundary

Missing required roles, extra roles in a closed set, changed bytes, mixed
parents, inconsistent dimensions, source-order disagreement, non-finite values,
or reported nonconvergence produce explicit failed or inconclusive evidence.
They do not authorize retry or scientific acceptance. No numerical rule in this
document grants execution authority or establishes validation.
