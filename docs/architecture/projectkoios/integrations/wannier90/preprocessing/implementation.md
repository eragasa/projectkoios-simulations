# Wannier90 preprocessing implementation rules

## Current implementation boundary

The first source increment provides the immutable value object
`projectkoios.integrations.wannier90.Wannier90PreprocessingInput`. Its
constructor validates the bounded generic non-spin spectral subset from typed
native parameters. Structure is a PhysKit `UnitCell`; reciprocal-fractional
points are a unitless PhysKit `MatrixQuantity`; and energy, spread, mixing, and
comparison values use Pint-backed PhysKit `ScalarQuantity` records. Ranks,
projections, optional excluded bands and projection selection, mesh,
localization controls, and complete disentanglement controls remain explicit.

Calling `Wannier90PreprocessingInput(...).render()` deterministically produces
exact newline-terminated `.win` bytes. Calling `prepare()` authenticates those
bytes and returns an existing `CalculatorInputRecord`. Construction, rendering,
and preparation have no filesystem or process side effects.

The input object reports its seed-derived `.win` and `.nnkp` basenames.
`Wannier90PreprocessingNnkpOutput` binds exact observed
`.nnkp` bytes to the preprocessing declaration, derives the native basename
from its seed, computes byte size and SHA-256, and delegates parsing to the
existing bounded `Wannier90NnkpParser`. It does not redundantly retain the
prepared record produced deterministically by that declaration.
Its `verify_source_lattices_kpoints_and_excluded_bands()` method compares the
ordered direct lattice, derived reciprocal lattice including the native `2 pi`
convention, reciprocal-fractional k points, and excluded bands against the
source input. `verify_source_selected_projection_indices()` separately checks
that any selected projection indices address the expanded native inventory; it
does not reproduce Wannier90's projection-expansion rules. Physical direct
vectors are represented with PhysKit `DirectLattice3D`, and PhysKit
`ReciprocalLattice3D.from_direct_lattice()` owns
the reciprocal construction. Direct lengths, reciprocal lengths, and fractional
k points use separate Pint-backed PhysKit scalar tolerances supplied explicitly
to the verification call in their respective units; comparison policy is not
observation state. The observed output itself reports the seed-derived filename,
byte size, and SHA-256. Persistence belongs to the future execution-evidence
boundary.

This increment does **not** yet authenticate arbitrary caller-rendered input,
verify expanded native projection values or independently reproduce the
neighbor inventory, stage files, resolve an
executable, or run Wannier90. The typed source reference identifies the
caller-owned construction declaration and energy reference.
Validation establishes representability within the bounded input object, not
scientific suitability or production acceptance.

The existing Wannier90 parser modules remain execution-independent. They are
not relocated, re-exported, or converted into runner facades.

## Separation of rendering and execution

The first renderer subset is reusable generic non-spin spectral Wannier90 input,
not a silicon-specific profile. A consuming project supplies every exact
structure, projection, energy window, k-point mesh, rank, and localization
control. The implemented pure rendering phase:

- validates the bounded provider-native construction input in the immutable
  input constructor;
- deterministically renders exact `.win` bytes;
- reports singular seed-derived `input_filename` and `nnkp_filename` values; and
- separately prepares an authenticated calculator-input record without
  resolving or running an executable.

Reporting execution resources remains to be added before the complete
preprocessing provider boundary exists.

A separate execution phase may stage the prepared input and submit one process
only after external authorization has been supplied at the existing
single-attempt execution boundary. Render-only behavior must reject execution
resources rather than retain dormant executable paths or authorization flags.
Configuration files, examples, environment variables, test markers, and the
presence of `wannier90.x` never grant authority.

## Preflight and side-effect order

Before creating an output directory or starting a process, the future provider
implementation must verify:

- a safe seedname and exact native input basename;
- the complete prepared-input byte size and SHA-256;
- exact structure, lattice, reciprocal-point order, projection, window, rank,
  spin, and predecessor identities carried by the construction declaration;
- an absolute nonsymlink executable path, executable mode, byte size, SHA-256,
  and declared version when execution is requested;
- a new nonoverlapping output directory;
- positive finite timeout and declared resource bounds; and
- absence of placeholders, unsafe path components, duplicate physical inputs,
  or undeclared resources.

After preflight, staging writes immutable input bytes into the new occurrence
directory. The runner submits exactly one no-shell command equivalent in meaning
to `wannier90.x -pp <seedname>` through
`projectkoios.simulations.execution`. It does not loop, retry, launch a child
route, or activate `pw2wannier90.x`.

## Evidence and failure behavior

The provider occurrence retains the exact input, stdout, stderr, terminal
execution record, and every declared compact output. The native neighbor file
is authenticated by size and digest before semantic parsing. Process success,
native completion observations, parse success, and provider handoff completion
remain distinct statuses.

A timeout, signal, nonzero return code, missing output, output symlink, changed
artifact, parse failure, or semantic inconsistency produces explicit retained
failure evidence. Partial outputs remain evidence but are not relabeled as a
successful topology handoff. A retry is a new occurrence and must not overwrite
the failed directory.

## Dependency direction and neutral adaptation

A future production preprocessing module may import:

- the Python standard library;
- existing Wannier90-native parsers in the same outward integration;
- protected calculator-input, execution, and artifact/evidence contracts; and
- explicitly reviewed low-level dependencies already allowed by the
  distribution.

It must not import `projectkoios.simulations.workflows`, a consuming
application, repository tools or examples, or a live Workflow runtime. It emits
provider-native records. The ProjectKoios simulations distribution must provide
a separately reviewed first-party outward `projectkoios.adapters` surface that
reads those records and constructs neutral role observations through public
contracts from both layers. This keeps both forbidden dependency arrows absent: workflows
do not import integrations, and integrations do not import workflows.

## Verification requirements

Current execution-independent tests establish deterministic byte-exact
rendering, constructor rejection of inconsistent ranks, meshes, windows, and
controls, seed-derived input and NNKP basenames, observed NNKP byte
count and checksum calculation, bounded native
parsing, supported ordered semantic verification, and operation without
executable discovery or process startup.

Future execution tests must use deterministic native fixtures and fake
executables. They must establish:

- rejection of missing external authorization before process startup;
- at most one subprocess and no implicit retry;
- exact command arguments without a shell or interactive stdin;
- preflight failure before output-directory creation where practical;
- refusal to overwrite or follow symlinked input/output paths;
- durable timeout, nonzero-exit, missing-output, and parser-failure evidence;
- exact neighbor-artifact authentication and source-order preservation;
- no import from `projectkoios.simulations.workflows`; and
- no scientific calculator execution during ordinary repository checks.

Passing these tests would establish software behavior only. It would not
qualify a scientific construction or prove compatibility with a particular
Wannier90 deployment.
