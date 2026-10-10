# QE relaxation calculator-input translation scientific semantics

The neutral relaxation specification owns the scientific electronic convergence
threshold in eV. QE's `electronic_tolerance_ry` is a native representation of
that same intent and is the value rendered as `conv_thr` during every ionic
step.

`electronic_atol_ry` has a narrower role: it bounds floating-point disagreement
when qualifying the neutral-to-native conversion. It is not a second
convergence threshold, a relaxation stopping criterion, or a scientific
acceptance policy. Changing it does not change the requested `conv_thr`, although
a wider value permits a less exact translation match and therefore belongs in
provider preparation provenance.

Electronic convergence, ionic convergence, and cell convergence are distinct:

- electronic convergence controls each electronic solve;
- ionic energy and force criteria control the structural optimizer; and
- pressure and cell criteria apply only when cell degrees of freedom are active.

Agreement of the electronic threshold cannot substitute for matching the ionic
or cell criteria. Likewise, rendered thresholds do not prove that a calculation
ran or converged.

Fixed-cell and variable-cell specifications remain scientifically different.
The former preserves the exact starting lattice; the latter changes only the
explicitly selected cell degrees of freedom under declared pressure controls.
Both use the same electronic threshold qualification, but that shared numeric
mapping does not make their geometries or energies interchangeable.

Charge, spin, occupation, symmetry, exact structure, cutoff, and
pseudopotential identity remain independent compatibility dimensions. The QE
adapter rejects unsupported intent rather than relying on implicit defaults.
