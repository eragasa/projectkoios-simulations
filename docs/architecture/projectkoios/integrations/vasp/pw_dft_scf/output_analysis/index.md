# VASP SCF output analysis

`VaspScfArtifactError` reports invalid evidence. `VaspScfDataExtractor`
produces `VaspScfData`, which composes common native sources, the normalized
calculator-neutral SCF observation, and mechanical OUTCAR/`vasprun.xml`
consistency results. `VaspScfOutputArtifactAnalyzer` remains a compatibility
adapter that returns only the neutral observation.
