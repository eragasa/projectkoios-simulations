# `pw2wannier90` artifact scientific boundary

## Artifact roles

The converter bridges a Quantum ESPRESSO plane-wave Bloch frame and native
Wannier90 interface data. Its outputs have distinct meanings:

- EIG records band eigenvalues over the declared reciprocal-point inventory;
- AMN records projections from Bloch states onto declared trial functions;
- MMN records neighbor overlaps over the preprocessing topology; and
- UNK, when an explicitly supported route requests it, records native
  real-space periodic wavefunction data with reciprocal-point and spin
  semantics.

These roles are not interchangeable. Similar dimensions or a common seedname
do not establish a common artifact identity or scientific purpose.

## Ordinary localization versus UNK routes

Ordinary Wannier90 localization consumes the EIG/AMN/MMN interface associated
with an exact NNKP topology and construction input. UNK is not globally
required for that localization route.

A separate analysis may require real-space wavefunction samples—for example,
a provider-specific operator or field correlation. Such a consumer must declare
an explicit UNK-producing route, exact reciprocal-point and spin inventory,
normalization/grid conventions, storage policy, and scientific purpose. The
specialized route cannot retroactively make earlier AMN/MMN evidence incomplete.

SPN and operator-related converter artifacts likewise require named consumers
and explicit scientific semantics. They are not enabled merely because the
native converter supports similarly named flags.

## Parent and construction identity

Every converter artifact derives from one exact parent NSCF saved state, QEXSD
frame, preprocessing topology, construction declaration, prefix, seedname, and
spin branch. Changing any of those creates a different provider route identity.
A converter result does not inherit scientific acceptance from a parent
calculation merely because the saved-state bytes verify.

The provider preserves source reciprocal-point order. It must not silently sort,
symmetry-reduce, merge spin channels, or substitute a different construction.

## Projection and overlap meaning

Projection count, parent band count, and Wannier rank are distinct. AMN records
trial-function overlaps; it does not by itself prove that the trial functions
span an adequate subspace. MMN neighbor overlaps depend on the exact topology
and ordering; they do not establish reciprocal-grid convergence.

EIG/AMN/MMN dimensional agreement is necessary provider evidence but not a
scientific quality criterion. A later localization may fail or may converge to
a representation that does not reproduce withheld observables.

## UNK meaning and limits

UNK data can be large and carries additional FFT-grid, band, component,
normalization, reciprocal-point, and spin conventions. Exact cardinality and
byte authentication do not prove a correct physical normalization or an
adequate plane-wave basis. Those semantics require a separately reviewed
consumer contract and provider validation.

Missing UNK is not a defect in a route that neither requests nor consumes it.
Conversely, a declared UNK route must not fabricate, omit, reorder, or infer
files to satisfy cardinality.

## Nonclaims

Provider artifact closure does not establish SCF/NSCF convergence, parent-model
adequacy, projection/window quality, localization convergence, interpolation
accuracy, operator fidelity, experimental agreement, or scientific validation.
It does not authorize converter execution or successor localization. Process
success and exact artifact identities remain software/evidence facts.

## References

1. A. A. Mostofi *et al.*, “An updated version of wannier90: A tool for
   obtaining maximally-localised Wannier functions,” *Computer Physics
   Communications* **185**, 2309–2310 (2014),
   [doi:10.1016/j.cpc.2013.10.003](https://doi.org/10.1016/j.cpc.2013.10.003).
2. P. Giannozzi *et al.*, “Advanced capabilities for materials modelling with
   Quantum ESPRESSO,” *Journal of Physics: Condensed Matter* **29**, 465901
   (2017),
   [doi:10.1088/1361-648X/aa8f79](https://doi.org/10.1088/1361-648X/aa8f79).
