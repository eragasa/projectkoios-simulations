# `calculation`

For a declared phase $p\in\{\mathtt{relax},\mathtt{vc-relax}\}$, the immutable
scientific and resource declaration is

$$
C_p=(S,E_{\mathrm{wfc}},E_{\rho},K,I,L_p,P),
$$

where $S$ is the exact structure identity, $K$ is sampling, $I$ is the required
`QeIonicRelaxationOptions`, $L_{\mathtt{relax}}=\varnothing$, and
$L_{\mathtt{vc-relax}}$ is the required
`QeLatticeVectorRelaxationOptions`. $P$ is the qualification set.

`QeRelaxationPhase`, `FileIdentity`, `StructureIdentity`, and
`QeRelaxationCalculationConfiguration` own the typed declaration and phase
invariants. They perform neither filesystem loading nor calculator execution.
