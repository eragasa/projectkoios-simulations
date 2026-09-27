# `projectkoios.integrations.quantumespresso.pw.inputfile.model`

The syntax authority is the official Quantum ESPRESSO [`pw.x` input-file documentation](https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1). `PW_INPUT_DOCUMENTATION_URL` retains that authority URL and `PW_INPUT_DOCUMENTATION_VERSION` records the reviewed version, 7.5.

`CalculationType` enumerates the seven official `&CONTROL` calculation values. `ControlBlock` owns the typed calculation selection without inventing defaults for the remaining control variables. `PwInputGroup` represents one ordered namelist or recognized Quantum ESPRESSO card. `PwInput` contains the complete ordered group sequence. `QePwInputFile` binds those groups to the exact shared unit cell from a plane-wave DFT simulation. `PwInputParser` performs bounded structural parsing through `parse`; it preserves lexical values without inventing defaults or interpreting physics. `PwInputWriter` performs deterministic normalization through `render`. `QuantumEspressoInputError` identifies malformed or unsupported input syntax.

`PW_NAMELIST_NAMES` records all seven documented namelists in required order: `&CONTROL`, `&SYSTEM`, `&ELECTRONS`, `&IONS`, `&CELL`, `&FCP`, and `&RISM`.

`PW_CARD_NAMES` records all eleven documented cards in the introduction's input structure order: `ATOMIC_SPECIES`, `ATOMIC_POSITIONS`, `K_POINTS`, `CELL_PARAMETERS`, `OCCUPATIONS`, `CONSTRAINTS`, `ATOMIC_VELOCITIES`, `ATOMIC_FORCES`, `ADDITIONAL_K_POINTS`, `SOLVENTS`, and `HUBBARD`. Unknown namelist variables and card body rows remain lexical strings.

The all-groups test fixture verifies syntax coverage only. Many cards are conditional; placing every card in one file does not establish a runnable or scientifically valid calculation.
