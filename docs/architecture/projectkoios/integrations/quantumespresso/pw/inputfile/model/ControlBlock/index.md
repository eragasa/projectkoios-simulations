# `ControlBlock`

Immutable typed portion of the Quantum ESPRESSO `&CONTROL` namelist. Its required public `calculation_type` field is an exact `CalculationType`. Optional public `prefix`, `pseudo_dir`, and `outdir` fields make run identity and resource locations explicit without calculator-specific compiled defaults. Other `&CONTROL` variables remain lexical until their typed ownership and requirements are introduced.
