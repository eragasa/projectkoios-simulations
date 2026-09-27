# `calculation`

For a declared phase $p\in\{\mathtt{relax},\mathtt{vc-relax}\}$, the immutable
scientific and resource declaration is

$$
C_p=(S,E_{\mathrm{wfc}},E_{\rho},K,T_{\mathrm{native}},P),
$$

where $S$ is the exact structure identity, $K$ is sampling, and $P$ is the
qualification set.

`QeRelaxationPhase`, `FileIdentity`, `StructureIdentity`, and
`QeRelaxationCalculationConfiguration` own the typed declaration and phase
invariants. They perform neither filesystem loading nor calculator execution.
