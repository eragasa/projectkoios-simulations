# Simulation library scientific schema

## Status

This document freezes the scientific content of version-one plane-wave DFT SCF
and relaxation specifications. The codec, record, request, source-reference,
projector, and consumer migration is implemented in the protected core. A
manifest-backed library now authenticates and resolves canonical record bytes.

Provider normalization is a release gate for the resulting schema, not an
excuse to derive provider-native fields first. A provider may support a proper
subset of neutral intent, but it must reject every unsupported value explicitly.

## Shared plane-wave DFT intent

`PwDftSimulation` contains only intent shared by SCF and relaxation:

- one complete exact `StructureRecord` dependency;
- one `DftExchangeCorrelationModel`;
- one `DftChargeState`;
- one `DftSpinTreatment`; and
- a symbol-sorted tuple of complete `PseudopotentialFile` dependencies.

It does not contain a decoded `UnitCell`, a calculation/stage type, an
occurrence identifier, provider configuration, execution authority, evidence,
or acceptance state. `SimulationResolution` supplies the exact matching
`StructureResolution`, decoded cell, and ordered exact pseudopotential file/path
resolutions required for calculator-input translation.

### Exchange-correlation identity

`DftExchangeCorrelationModel` has:

- `identifier_scheme`, initially the closed value `libxc-composite`;
- `identifier`, a stripped ASCII Libxc composite identifier such as
  `GGA_X_PBE+GGA_C_PBE`; and
- `pseudopotential_compatibility_label`, a stripped ASCII label that every bound
  pseudopotential must match exactly.

A translator uses a closed mapping from this neutral identity to native fields
or rejects it. It never guesses from a pseudopotential filename.

### Charge and spin

The charge convention remains:

```text
positive delta_n_electrons adds electrons
charge_state == -delta_n_electrons
```

Version one represents four closed spin modes:

1. `unpolarized`;
2. `collinear`;
3. `noncollinear`; and
4. `spin-orbit-coupled`.

Collinear intent distinguishes a spin-channel electron-difference constraint
from scalar site-moment initialization. Noncollinear and spin-orbit intent use
ordered three-component site-moment vectors. Spin-orbit intent also requires a
finite normalized quantization axis. Scalar and vector initial moments, when
present, correspond one-to-one with source-ordered structure sites. A provider
must translate a mode completely or reject it before rendering.

### Exact pseudopotential dependencies

`PseudopotentialFile` is the complete protected-core pseudopotential dependency.
It includes scientific metadata, explicit artifact format, format version where
applicable, basename, byte size, and SHA-256. Version one recognizes `upf` and
`vasp-potcar`; UPF requires an explicit UPF format version. Provider subclasses
must not appear in canonical protected-core bytes.

The existing `PseudopotentialLibrary` remains the byte-verifying deployment
resolver. No second pseudopotential record or catalog hierarchy is introduced.
QE translators require UPF and VASP translators require POTCAR artifacts.

## Shared electronic controls

Every SCF and relaxation specification contains these controls rather than
borrowing mutable provider profiles:

- `DftOccupationPolicy`;
- `PwDftElectronicConvergencePolicy`; and
- `PwDftKPointSamplingPolicy`.

`DftOccupationPolicy` has a closed method (`fixed`, `gaussian`,
`fermi-dirac`, `methfessel-paxton`, or `marzari-vanderbilt-cold`), an optional
positive finite smearing width in eV, and an optional nonnegative
Methfessel-Paxton order. Fixed occupations carry neither smearing field;
smearing methods require a width; only Methfessel-Paxton carries an order.

`PwDftElectronicConvergencePolicy` declares a positive finite neutral SCF
energy tolerance in eV and a positive maximum electronic-iteration count.
Provider mappings remain scientifically qualified because native convergence
criteria differ.

`PwDftKPointSamplingPolicy` declares a positive three-integer mesh, a
three-value half-grid shift encoded as zero-or-one integers, whether spatial
symmetry reduction is allowed, and whether time-reversal reduction is allowed.
The wavefunction cutoff is a separate positive finite eV quantity. Provider
profiles may choose algorithms, but not overwrite these scientific values.

## Provider-compatible specification identity

A single specification is reused across providers only when every scientific
field has an explicitly compatible native mapping. Existing QE and VASP input
fixtures intentionally differ in occupation and electronic-convergence values:
QE's retained semiconductor input relies on fixed occupations and a tolerance
expressed in Ry, while the retained VASP input declares `ISMEAR = 0`, `SIGMA =
0.05`, and an eV `EDIFF`. These are distinct canonical specifications rather
than two renderings of falsely identical intent.

Cross-provider comparisons therefore retain both exact `SimulationRecord`
identities and an explicit compatibility qualification. They do not coerce one
provider profile into another specification, silently overwrite neutral
values, or claim scientific equivalence. This rule preserves the reviewed
calculator-input fixture bytes while making their scientific difference
visible in exact identity.

## SCF specification

`PwDftScfSpecification` contains, in scientific order:

1. qualified stable `simulation_id`;
2. shared `PwDftSimulation`;
3. `PwDftKPointSamplingPolicy`;
4. wavefunction cutoff in eV;
5. `DftOccupationPolicy`; and
6. `PwDftElectronicConvergencePolicy`.

Its representation discriminator is `pw-dft-scf` and its schema version is
exactly `1`. `PwDftScfRequest` contains exactly `evaluation_id` and
`specification`; the occurrence ID is excluded from specification bytes.

## Relaxation specification

`PwDftRelaxationSpecification` contains all SCF scientific controls plus:

- `PwDftRelaxationInitialization`, initially the closed value
  `from-exact-starting-structure`;
- ionic convergence controls;
- geometry degrees of freedom; and
- pressure controls when lattice degrees of freedom are active.

The exact starting geometry is always the specification's `StructureRecord`.
An imposed displacement creates another exact derived structure record rather
than hidden random or provider-side initialization.

Geometry degrees of freedom require ionic positions to be active and select one
closed cell mode:

- `fixed`;
- `volume-only`;
- `shape-at-fixed-volume`;
- `selected-components`; or
- `unrestricted-vectors`.

`selected-components` additionally carries a six-boolean symmetric strain mask
in `xx, yy, zz, yz, xz, xy` order. Other modes carry no mask. Fixed-cell
relaxation carries no pressure controls. Every active-cell mode requires finite
target pressure and positive pressure tolerance in kbar.

Its representation discriminator is `pw-dft-relaxation` and its schema version
is exactly `1`. `PwDftRelaxationRequest` likewise contains only `evaluation_id`
and `specification`.

## Exact identity and derivation

A `SimulationRecord` contains:

- `simulation_id`;
- closed `SimulationRepresentation`;
- schema version;
- byte size;
- SHA-256; and
- closed authored, transferred, or derived provenance whose `result_sha256`
  equals the record SHA-256.

Recipe coordinates that change cutoff, mesh, shift, occupation, convergence,
spin, charge, geometry, or relaxation controls create distinct canonical bytes
and a deterministic derived record. Catalog persistence is optional; truthful
content identity is not. A `CalculatorInputSourceReference` is created only
from that exact record and never from a flattened request or placeholder digest.

## Canonical version-one encoding

Both representations use strict UTF-8 JSON with:

- one prescribed field set and order per representation;
- no unknown, missing, or duplicate keys;
- JSON arrays for ordered tuples;
- symbol-sorted pseudopotentials with unique complete identities;
- finite numbers only;
- booleans rejected where integers are required;
- negative zero normalized to positive zero;
- shortest round-trippable decimal JSON numbers;
- no insignificant whitespace and no trailing newline; and
- exact representation and schema-version discriminators.

Decoding rejects malformed UTF-8, noncanonical numbers, incorrect key order,
provider subtypes, dependency substitution, and representation/type mismatch.
The implementation fixes explicit record and manifest byte limits before the
first permanent example bytes are published.

## Atomic migration and release gates

The migration order is:

1. implement these protected-core fields and validation;
2. atomically add specification codecs and records, remove shared calculation
   type, replace both request shapes, establish derived identities, return
   `CalculatorInputRecord` from projectors, and update every consumer;
3. completed: add strict manifest-backed resolution; then
4. pending: publish reviewed study catalogs and remove remaining tool-side
   scientific reconstruction.

There is no mixed old/new request interval, compatibility facade, alias, or
placeholder source identity. Before publication, all maintained QE/VASP
translators and normalization adapters must either map every supported field or
fail explicitly, the publisher must prove that evidence source identity names
the exact relaxation specification, and the minimum PhysKit release containing
base-`UnitCell` codec support must be selected as the compatible lower bound.
