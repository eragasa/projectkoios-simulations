# QE SCF projection configuration

`QeScfSpeciesConfiguration` declares species-native inputs.
`QeScfProjectionConfiguration` declares explicit Quantum ESPRESSO policy not
implied by common scientific intent. Its `electronic_tolerance_ry` is rendered
as the native convergence threshold; its separately configurable
`electronic_atol_ry` is used only to qualify conversion from the neutral eV
specification. Version one supports only `pseudo_dir = './'` and
`outdir = './tmp/'`, matching the production executor's exact staging layout;
alternate native layouts fail closed.

The numeric and scientific distinction is specified by the
[QE SCF calculator-input translation architecture](../projection/index.md).
