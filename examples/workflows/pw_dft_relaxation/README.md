# Plane-wave DFT relaxation example

`qe_projection.py` composes a neutral relaxation campaign with a caller-supplied
public QE projection integration. It returns deterministic projected inputs and
a handoff whose authority requirement is
`separate-explicit-external-authority-required`.

Despite the historical source filename `execute_relaxation.py`, this example has
no execution option, executable lookup, subprocess call, or reusable authority.
