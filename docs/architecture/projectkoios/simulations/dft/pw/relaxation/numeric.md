# Plane-wave DFT relaxation numerical contract

## Independent observations

The normalized result separates:

- provider terminal completion;
- electronic convergence at ionic steps;
- ionic force convergence;
- cell pressure/stress convergence;
- final-structure availability; and
- cross-artifact consistency.

No single provider flag substitutes for all of these observations.

## Fixed-cell lattice consistency

For `ATOMIC_POSITIONS`, the normalized final structure uses the exact starting
lattice. A separately parsed provider lattice is compared after unit conversion.
The consistency result records component-wise deviations, maximum deviation,
units, tolerance, and source artifacts.

A mismatch does not silently alter the fixed lattice. It marks evidence as
inconsistent and prevents relaxed-structure publication until explained.

## Variable-cell validity

For `ATOMIC_POSITIONS_AND_CELL`, the final lattice must be finite, nonsingular,
and positively oriented under the repository lattice convention. The result
records initial and final volume, lattice-vector changes, final pressure or
stress, target pressure, and pressure residual when those values are available.

The numerical contract validates the declared cell-relaxation mode but does not
select that mode. Disallowed component changes are qualification failures.

## Force and pressure criteria

Maximum force and pressure residual retain their source units and converted
canonical units. Comparisons use unrounded values and explicit inclusive or
exclusive threshold semantics. Missing force or stress data is unavailable
evidence, not zero.

An optimizer reporting completion without sufficient normalized quantities can
be retained but cannot satisfy a policy requiring those quantities. A reusable
zero-pressure assessment computes the unrounded residual
`abs(p_final - p_target)` and declares inclusive or exclusive threshold
semantics; the protected observation does not infer that decision.

## Charge and spin consistency

Every ionic step and final structure belongs to the same declared
`delta_n_electrons` and spin specification unless a separate electronic-state
transition is explicitly modeled. Prepared input records establish requested
values; normalized output records retain observed magnetization or spin-channel
data when available.

Neutral Si:P relaxation evidence is eligible for the current study only when it
is correlated with the declared spin-polarized doublet input. A changed or
collapsed spin state is retained and qualified rather than silently accepted.

## Numerical-setting lineage

The exact relaxation specification binds the wavefunction cutoff and k-point
sampling used to produce its force and stress surface. The bulk route also
binds one neutral wavefunction and density/potential cutoff realization, and
adapter evidence proves each exact provider input realizes it. Provider-native
ratios remain outside protected and neutral workflow records.

A convergence result on seed structure `S0` is scoped to `S0`. After relaxation
produces `S1`, final confirmation uses observations whose exact structure
identity is `S1`. If the selected setting changes from `Q0` to `Q1`, `S1` is not
silently relabeled as qualified under `Q1`; a new relaxation produces `S2` and a
new confirmation is assessed on `S2`. Equal displayed lattice parameters or
integer mesh tuples do not collapse those identities.

A changed lattice receives a fresh run of the existing grid-convergence recipe
and assessor. The final full `PwDftKPointSamplingPolicy` remains part of exact
specification and stable-pair identity.

## Final-energy separation

The last relaxation energy is not automatically the energy used in formation-
or relaxation-energy arithmetic. A separate final SCF on the exact published
geometry supplies the comparable energy. Numerical policies qualify both the
relaxation and final SCF and preserve their different identities. Under the
planned bulk-to-Wannier composition, a prior confirmation remains predecessor
evidence and a new parent SCF begins the five-occurrence downstream route only
after stable-pair acceptance. A matching energy is insufficient to merge their
identities.

## Precision and reporting

Parsers retain source precision. Unit conversion occurs before comparison but
not before artifact hashing. Results store raw values, converted values,
tolerances, and decision operands. Presentation rounding is applied only after
the numerical decision.
