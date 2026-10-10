# QE relaxation calculator-input translation numeric contract

Let

- $T_{\mathrm{eV}}$ be the neutral electronic energy tolerance;
- $c_{\mathrm{Ry}/\mathrm{eV}}$ be the maintained eV-to-Ry factor;
- $T_{\mathrm{Ry}}$ be `electronic_tolerance_ry`; and
- $a_{\mathrm{Ry}}$ be `electronic_atol_ry`.

Fixed- and variable-cell translation both require

$$
\left|T_{\mathrm{eV}}c_{\mathrm{Ry}/\mathrm{eV}}-T_{\mathrm{Ry}}\right|
\le a_{\mathrm{Ry}}.
$$

`electronic_atol_ry` must be a finite, nonnegative float. It is an absolute
quantity in Ry; it is not dimensionless and is not a relative tolerance. Zero
requires exact floating-point equality after conversion.

The maintained relaxation declarations use

```text
electronic_tolerance_ry = 1.0e-6 Ry
electronic_atol_ry      = 1.0e-15 Ry
```

Only `electronic_tolerance_ry` is rendered as `conv_thr`. The absolute tolerance
does not change the requested threshold or any observed convergence criterion.

Other relaxation conversions remain independent:

$$
E_{\mathrm{wfc,Ry}}=E_{\mathrm{wfc,eV}}c_{\mathrm{Ry}/\mathrm{eV}},
$$

$$
E_{\mathrm{ion,Ry}}=E_{\mathrm{ion,eV}}c_{\mathrm{Ry}/\mathrm{eV}},
$$

and

$$
F_{\mathrm{Ry/bohr}}=F_{\mathrm{eV/angstrom}}
 c_{\mathrm{Ry/bohr}\,/\,\mathrm{eV/angstrom}}.
$$

Agreement for one conversion cannot qualify another. Numeric translation
compatibility does not establish provider convergence or scientific acceptance.
