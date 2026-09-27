# `QeRelaxationCalculationRenderer`

For physical cell columns $H$ and fractional positions $s_i$, `render` preserves

$$
r_i=Hs_i
$$

while projecting the phase-specific generic request and native QE controls into
deterministic `pw.x` input. It performs no filesystem write or calculator
execution.
