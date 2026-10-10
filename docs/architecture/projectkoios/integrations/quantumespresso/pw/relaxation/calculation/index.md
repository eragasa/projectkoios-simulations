# `calculation`

For a declared phase $p\in\{\mathtt{relax},\mathtt{vc-relax}\}$, the immutable
scientific and resource declaration is

$$
C_p=(S,E_{\mathrm{wfc}},E_{\rho},K,T_{\mathrm{Ry}},a_{\mathrm{Ry}},I,L_p,P),
$$

where $S$ is the exact structure identity, $K$ is sampling,
$T_{\mathrm{Ry}}$ is the native electronic threshold, $a_{\mathrm{Ry}}$ is its
absolute conversion-comparison tolerance, $I$ is the required
`QeIonicRelaxationOptions`, $L_{\mathtt{relax}}=\varnothing$, and
$L_{\mathtt{vc-relax}}$ is the required
`QeLatticeVectorRelaxationOptions`. $P$ is the qualification set.

`QeRelaxationPhase`, `FileIdentity`, `StructureIdentity`, and
`QeRelaxationCalculationConfiguration` own the typed declaration and phase
invariants. They perform neither filesystem loading nor calculator execution.
The [relaxation translation architecture](../projection/index.md) defines the
numeric and scientific roles of $T_{\mathrm{Ry}}$ and $a_{\mathrm{Ry}}$.
