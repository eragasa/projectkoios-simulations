# `projectkoios.simulations.dft.pw`

Calculator-neutral plane-wave DFT simulation declarations and calculation-mode
contracts.

- [`settings`](settings/index.md) owns common plane-wave calculation modes and
  reviewed cross-calculator setting alignments.
- [`simulation`](simulation/index.md) binds one unit cell to plane-wave DFT
  settings.
- [`scf`](scf/index.md) owns self-consistent-field requests, observations,
  integration ports, and lifecycle contracts.
- [`nscf`](nscf/index.md) identifies the neutral NSCF namespace without
  claiming an unimplemented public contract.
- [`relaxation`](relaxation/index.md) owns structural-relaxation requests,
  capabilities, and integration ports.
