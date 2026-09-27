# `QuantumEspressoSimulation`

Immutable simulation-file bundle with public `input_file`, `pseudopotentials`, `input_filename`, and `output_filename` fields. `input_file` is an exact `QePwInputFile` retaining the shared unit cell. Every pseudopotential is an exact `QePseudopotentialFile`; symbols and filenames must be unique, and calculator-local input and output basenames must differ.

The bundle is descriptive. It does not authorize or perform calculator execution.
