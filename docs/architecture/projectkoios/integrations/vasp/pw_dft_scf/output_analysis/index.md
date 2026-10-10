# VASP SCF output analysis

`VaspScfArtifactError` reports invalid evidence. `VaspScfDataExtractor`
produces `VaspScfData`, which composes common native sources, the normalized
calculator-neutral SCF observation, and mechanical OUTCAR/`vasprun.xml`
consistency results. `VaspScfOutputArtifactAnalyzer` remains a compatibility
adapter that returns only the neutral observation.

## Required defect extension

Charged and spin-polarized defect analysis must correlate the exact
`CalculatorInputRecord` and normalize the native electron count, total
magnetization, spin-channel populations, total energy, completion, and SCF
convergence when present in retained VASP artifacts. Requested values and
observed values remain distinct.

The DFT defect binding rejects evidence that lacks required charge/spin
correlation or conflicts across OUTCAR and `vasprun.xml`. Parsing does not claim
scientific acceptance.
