# `rendering`

Deterministic projection is

$$
(C_p,S)\longmapsto I_{\mathrm{QE}},
$$

where `QeRelaxationCalculationRenderer` combines a validated calculation and an
exact `StructureResolution` into one phase-specific `pw.x` input document. It
propagates both `electronic_tolerance_ry` and `electronic_atol_ry` through the
shared relaxation translation path; only the former is rendered as `conv_thr`.
Rendering has no filesystem or calculator effect.
