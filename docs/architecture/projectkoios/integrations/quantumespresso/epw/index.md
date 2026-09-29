# `projectkoios.integrations.quantumespresso.epw`

This outward provider package owns the initial adapter for Quantum ESPRESSO's
`epw.x` executable. It provides:

- typed, deterministic `&inputepw` rendering without selecting scientific
  settings;
- exact-identity staging of declared parent artifacts;
- explicit, fail-closed calculator execution through the neutral
  `CalculatorExecutor`;
- bounded captured-stream observation; and
- exact declared-artifact inspection without scientific interpretation.

The adapter never searches for `epw.x`, hard-codes a machine-local executable,
or runs a process while rendering input. An execution request must explicitly
set `execute=True` and provide the executable path, SHA-256, byte size, timeout,
and exact identities for every staged parent artifact. All supplied identities
are verified before the output directory is created. The executable is invoked
without a shell as `epw.x -in epw.in`.

EPW outputs depend strongly on the requested calculation. The artifact inspector
therefore verifies caller-declared regular files and requires canonical captured
`epw.out`, `epw.err`, and `execution.json` records; it does not infer a scientific
result schema. Stream markers such as `JOB DONE.`, the total-program timing
section, Wannierization, and electron--phonon interpolation are retained as
provider-native observations, not acceptance decisions.

## Ownership boundary

Calculator-neutral electron--phonon identities may be introduced under
`projectkoios.simulations` only as separately reviewed neutral contracts. The
provider-native namelist, executable invocation, and native artifacts remain
here. Multi-stage SCF, NSCF, phonon, `pw2wannier90.x`, Wannier90, and EPW workflow
composition belongs to `projectkoios.applications`.

This adapter does not own phonon preparation, convergence policy, mobility or
superconductivity policy, campaign state, scheduler integration, or scientific
validation. Process success does not establish that parent states are mutually
compatible or that any numerical result is scientifically acceptable.

## Software reference

EPW is distributed with Quantum ESPRESSO. Upstream documentation is maintained
at <https://docs.epw-code.org/> and the project site at
<https://epw-code.org/>. No EPW source code or executable is copied into this
repository.
