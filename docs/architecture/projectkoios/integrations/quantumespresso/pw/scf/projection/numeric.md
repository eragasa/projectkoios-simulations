# QE SCF calculator-input translation numeric contract

Let

- $T_{\mathrm{eV}}$ be the neutral
  `PwDftElectronicConvergencePolicy.energy_tolerance_ev`;
- $c_{\mathrm{Ry}/\mathrm{eV}}$ be the maintained eV-to-Ry conversion factor;
- $T_{\mathrm{Ry}}$ be configured `electronic_tolerance_ry`; and
- $a_{\mathrm{Ry}}$ be configured `electronic_atol_ry`.

Translation requires

$$
\left|T_{\mathrm{eV}}c_{\mathrm{Ry}/\mathrm{eV}}-T_{\mathrm{Ry}}\right|
\le a_{\mathrm{Ry}}.
$$

The comparison has zero relative tolerance. `electronic_atol_ry` must be a
finite, nonnegative float. Zero requests exact floating-point equality after
the maintained conversion; a positive value permits only the declared absolute
round-off envelope in Ry.

The maintained QE SCF profile declares

```text
electronic_tolerance_ry = 1.0e-6 Ry
electronic_atol_ry      = 1.0e-15 Ry
```

These values have different meanings. The first is rendered as `conv_thr` and
expresses the native electronic convergence threshold. The second is used only
by the translation consistency check and never relaxes `conv_thr`.

For Gaussian occupations, neutral width $W_{\mathrm{eV}}$ is rendered as

$$
\mathtt{degauss}=W_{\mathrm{eV}}c_{\mathrm{Ry}/\mathrm{eV}}.
$$

For a species whose exact pseudopotential declares $Z_v$ valence electrons and
whose sites share initial scalar moment $m$ in μB, the adapter renders

$$
\mathtt{starting\_magnetization(i)}=m/Z_v.
$$

The normalized value must lie in $[-1,1]$. Site values for the same species must
agree within configured `magnetic_moment_atol_mu_b`; the comparison has zero
relative tolerance. Neither the initial value nor its comparison tolerance is a
final-magnetization acceptance target.

Wavefunction-cutoff conversion, charge-density-cutoff multiplication, and the
maximum-iteration mapping to `electron_maxstep` remain separate numeric
mappings. Passing any translation check does not establish SCF convergence,
numerical qualification, or scientific validation.
