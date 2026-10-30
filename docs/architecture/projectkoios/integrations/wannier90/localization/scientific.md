# Planned Wannier90 localization execution scientific boundary

## Scientific meaning

A localization occurrence applies one exact construction declaration to one
correlated native interface data set and reports provider-native observations
about the resulting candidate Wannier representation. The integration preserves
that meaning; it does not choose the construction or decide that the result is
scientifically adequate.

The consuming scientific owner selects rank, projections, outer and frozen
windows, localization controls, requested outputs, restart policy, and
acceptance criteria. The provider must not widen windows, alter rank, drop
bands, change spin branch, or enable restart merely to achieve process success.

## Input roles

For the ordinary localization route, interface eigenvalues, projections, and
neighbor overlaps play different scientific roles. The preprocessing topology
defines reciprocal-point and neighbor relationships. None is interchangeable
with real-space wavefunction samples.

UNK files represent provider-native real-space periodic wavefunction data for
specific reciprocal points and spin semantics. Converter-produced UNKs are
correlated sibling evidence for a separately declared wavefunction-sensitive
consumer; they are not ordinary AMN/MMN localization inputs. A supported native
plotting or transport mode may consume them, but only its separate declaration
may stage them into a Wannier90 occurrence. That declaration must state why,
bind the complete inventory, and preserve the additional storage and numerical
conventions.

## Disentanglement, gauge, and localization

Band selection/disentanglement, gauge choice, and localization are separate
operations. An outer space may have a different dimension from the retained
Wannier space. A frozen subspace adds constraints but does not identify a gauge
by itself. Gauge and disentanglement matrices are evidence for one exact
construction and reciprocal-point order.

Reported centers and spreads characterize a provider result. They are not, by
themselves, proof that the target physical observables are accurate or that no
alternative gauge/local minimum exists. A process return code does not establish
that the provider's localization criterion was met.

## Real-space Hamiltonian meaning

A native real-space Hamiltonian carries lattice-vector-indexed blocks,
degeneracies, orbital order, and an energy convention. It is a representation
of the selected subspace under the exact construction. It must not be compared
or subtracted from another operator until state spaces, basis/gauge, geometry,
energy reference, units, and any real-space truncation are aligned.

Generating a Hamiltonian does not establish interpolation accuracy on withheld
points, velocity or curvature accuracy, effective-mass accuracy, operator
fidelity, or adequacy of a later reduced model.

## Spin and energy conventions

Non-spin-polarized, scalar spin-channel, noncollinear, and spinor
constructions are distinct. Native files and normalized provider observations
must retain component semantics and must not merge spin channels implicitly.

Input windows, interface eigenvalues, output Hamiltonians, and reported Fermi
or reference energies require explicit units and reference conventions. Scalar
energy shifts and unitary subspace transformations are separate alignment
operations owned by downstream analysis.

## Completion, convergence, and acceptance

The future provider distinguishes:

- process termination and return code;
- required native artifact closure;
- parse success;
- provider-reported disentanglement/localization status;
- dimension, source-order, and lineage consistency; and
- consumer-owned numerical and scientific acceptance.

A route may complete mechanically while remaining nonconverged, inconsistent,
or scientifically rejected. The integration preserves those observations and
does not convert them into a generic success flag.

## Nonclaims

Localization provider evidence does not establish parent-model correctness,
finite-setting convergence, projection/window adequacy, uniqueness of the
localized solution, withheld interpolation quality, experimental agreement, or
publication readiness. The integration owns no acceptance thresholds and does
not grant calculator execution.

## References

1. N. Marzari, A. A. Mostofi, J. R. Yates, I. Souza, and D. Vanderbilt,
   “Maximally localized Wannier functions: Theory and applications,” *Reviews
   of Modern Physics* **84**, 1419–1475 (2012),
   [doi:10.1103/RevModPhys.84.1419](https://doi.org/10.1103/RevModPhys.84.1419).
2. A. A. Mostofi *et al.*, “An updated version of wannier90: A tool for
   obtaining maximally-localised Wannier functions,” *Computer Physics
   Communications* **185**, 2309–2310 (2014),
   [doi:10.1016/j.cpc.2013.10.003](https://doi.org/10.1016/j.cpc.2013.10.003).
