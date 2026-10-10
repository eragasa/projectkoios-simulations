# QE SCF calculator-input translation scientific semantics

The electronic convergence threshold is scientific specification content. Its
calculator-neutral representation is in eV so the specification does not adopt
QE's native unit convention. The QE adapter renders that intent only when its
configured Ry threshold represents the same value within the explicitly
declared numeric comparison tolerance.

`electronic_atol_ry` is not scientific intent. It describes how strictly the
adapter compares two floating-point representations of the requested threshold.
Changing it does not create a different requested convergence threshold and
must not be reported as stronger or weaker SCF convergence. A larger value can,
however, admit a less exact provider mapping, so provider profiles and prepared
input provenance must retain the value used for qualification.

Passing the comparison proves only that the declared neutral and QE-native
thresholds are numerically compatible under that profile. It does not prove
that an SCF calculation ran, converged, reached a physically meaningful state,
or satisfied a workflow or scientific acceptance policy.

Occupation, k-point symmetry, spin, charge, cutoff, structure, and exact
pseudopotential identities remain independent scientific dimensions. Agreement
of the electronic threshold cannot compensate for an unsupported or mismatched
value in any of those dimensions.

Gaussian occupation intent maps to QE `occupations='smearing'`,
`smearing='gaussian'`, and an eV-to-Ry conversion of the declared width. A
collinear initial site moment is an authored symmetry-breaking initial condition,
not a requested final magnetic moment. QE provides one
`starting_magnetization(i)` value per species, so all sites of that species must
agree within `magnetic_moment_atol_mu_b`; the adapter divides the common moment
by the exact pseudopotential valence-electron count to obtain QE's normalized
species value.

The Si/Ni validation pair deliberately separates model and observation. The Si
control is unpolarized and therefore has exactly one spin-degenerate channel;
QE does not report a noisy magnetization for that model. The Ni calculation is
collinear with an explicit 2 μB symmetry-breaking initial value and accepts only
a converged, completed result with nonzero total and absolute magnetization. The
2 μB value is not a target or reference result, and the qualitative validation
does not establish cutoff, k-point, smearing, or thermodynamic convergence.
