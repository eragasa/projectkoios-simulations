# `relax`

This package projects calculator-neutral fixed-cell relaxation requests into
Quantum ESPRESSO `pw.x` `calculation='relax'` input. It consumes shared cards
and native values from `pw.inputfile` and does not emit a `&CELL` namelist.
