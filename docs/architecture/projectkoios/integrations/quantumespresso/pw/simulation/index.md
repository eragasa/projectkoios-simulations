# `projectkoios.integrations.quantumespresso.pw.simulation`

`QuantumEspressoSimulation` bundles Quantum ESPRESSO-specific `QePseudopotentialFile` identities with one immutable `PwInput` and calculator-local filenames. The generic `PseudopotentialFile` contract is owned by
`simulations.dft.pseudopotential`; its UPF specialization is owned by
`integrations.quantumespresso.pseudopotential`.

Neither record reads, copies, downloads, stages, or executes anything.
