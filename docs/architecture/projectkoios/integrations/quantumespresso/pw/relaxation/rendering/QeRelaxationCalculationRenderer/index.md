# `QeRelaxationCalculationRenderer`

For physical cell columns $H$ and fractional positions $s_i$, `render` preserves

$$
r_i=Hs_i
$$

while translating the phase-specific neutral request and native QE controls
into deterministic `pw.x` input. The renderer propagates the configured
`electronic_atol_ry` to the shared translation check without writing it to the
input file. It performs no filesystem write or calculator execution.
