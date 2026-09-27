# `execution`

Every verified resource satisfies

$$
|B|=n_{\mathrm{declared}},
\qquad
\operatorname{SHA256}(B)=h_{\mathrm{declared}}.
$$

`QeRelaxationStructureOverride`, `QeRelaxationCalculationRunRequest`,
`QeRelaxationCalculationRunResult`, and `QeRelaxationCalculationRunner` own
resource preflight, render-only materialization, explicitly requested execution,
and native artifact manifests. Resource checks precede output-directory
creation.
