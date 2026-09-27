# `loading`

The accepted declaration language is a closed mapping

$$
D_{\mathrm{TOML}} \longmapsto C_p,
$$

where unknown or missing keys are rejected rather than ignored.
`QeRelaxationCalculationTomlLoader` owns bounded, nonsymlink TOML loading and
construction of validated calculation records. It resolves no external
resources.
