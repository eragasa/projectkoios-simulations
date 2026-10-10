# QE SCF calculator-input translation implementation

## Boundary

`QeScfInputProjector` is an outward provider adapter. It depends on the
calculator-neutral simulation contracts; the protected
`projectkoios.simulations` namespace does not depend on this adapter.

The projector receives three independently validated inputs:

1. an occurrence-bearing `PwDftScfRequest`;
2. an exact `StructureResolution` matching the specification's
   `StructureRecord`; and
3. `QeScfProjectionConfiguration`, which declares QE-native rendering policy.

It does not locate structure or pseudopotential bytes, run `pw.x`, infer
execution authority, normalize output, or decide scientific acceptance. During
an authorized execution occurrence, the injected `PseudopotentialLibrary`
resolves each complete pseudopotential identity before staging; the workflow
never selects an artifact from the library by element or basename alone.

## Fail-closed translation

Before rendering, the projector constructs `ResolvedPwDftSimulation` so
composition-dependent charge, spin, and pseudopotential invariants are checked
against the verified structure. It translates fixed and Gaussian occupations,
unpolarized and collinear spin, constrained total magnetization, and
species-representable scalar initial moments. Disabled spatial and time-reversal
k-point reductions map independently to QE `nosym` and `noinv`; enabled values
use QE's documented false defaults and are recorded as defaults in the prepared
input mapping. The projector rejects unsupported occupation, spin,
site-distinct-within-species moment, pseudopotential-format, and filename
mappings rather than selecting approximate QE behavior.

The electronic threshold check converts the neutral eV value into Ry and
compares it with the configured native threshold using
`electronic_atol_ry`. Only after that qualification succeeds does the assembler
render `electronic_tolerance_ry` as QE `conv_thr` and the neutral maximum
iteration count as `electron_maxstep`.

`electronic_atol_ry` is configuration of the adapter's numeric comparison. It
is not part of the neutral specification, is not written to `pw.in`, and does
not alter `electronic_tolerance_ry`.

## Result contract

The implementation returns `CalculatorInputRecord` with exact rendered bytes,
canonical specification correlation, complete pseudopotential requirements, and
neutral-to-native mapping observations. The former
`PwDftScfInputProjection`/`PwDftScfRenderedInput` interval is removed. The record
grants no calculator execution authority.

Authorized QE execution stages only the prepared artifacts and exact
pseudopotentials resolved through the injected `PseudopotentialLibrary`.
Resolution failure is recorded as preflight failure before `pw.x` starts.
