# `integrations.quantumespresso.pw.nscf`

Quantum ESPRESSO `pw.x` non-self-consistent calculation components for an
explicit downstream Wannier interface.

A closed-schema TOML configuration owns the source input, structure,
calculator, pseudopotential, parent SCF output, saved-state manifest, output,
and optional reference-output paths together with exact file identities. The
loader extracts that declaration into immutable records. `QeNscfControlBlock`
inherits `ControlBlock` because it adds NSCF diagnostics fields and enforces an
NSCF calculation invariant. Named NSCF builders validate phase-specific values
and return the common `QeSystemCard`, `QeElectronsCard`,
`QeAtomicSpeciesCard`, and `QeKpointsCard` types rather than nominal subclasses
that add no durable invariant.

`QeNscfInputProjection` is the explicit phase-owned aggregate: it retains the
specialized control block, the four common cards, and the rendered input. The
projector never passes raw TOML dictionaries to the writer. The configured
uniform grid is expanded in source order before `QePwInputFileAssembler` and
`PwInputWriter` produce deterministic native input.

`QeNscfCalculationRunner` supports rendering without execution. Execution
requires a separate request flag; configuration content never grants execution
authority. Before creating the output directory, the runner verifies the exact
calculator, pseudopotential, structure, parent manifest, and every parent SCF
saved-state artifact. A successful run produces a deterministic NSCF saved-state
manifest and a `QeNscfSavedStateHandoff` binding its exact path, root, size,
hash, and prefix for the maintained `pw2wannier90.x` interface.

`QeNscfArtifactInspector` verifies the native process files and saved-state
manifest, then selects the sole declared QEXSD artifact for semantic parsing.
Parsed QEXSD documents continue to enter through the structural protocol in
`QeNscfDataExtractor`; this package does not duplicate semantic XML parsing.
Process completion, manifest production, and dimensional consistency do not
establish convergence or scientific validation. Multi-stage workflow
composition remains application-owned.
