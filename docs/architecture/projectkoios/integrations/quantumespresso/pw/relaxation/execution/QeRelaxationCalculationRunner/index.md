# `QeRelaxationCalculationRunner`

The runner enforces

$$
\text{preflight}\prec\text{output creation}\prec\text{optional execution}.
$$

`run` loads the declaration, verifies the structure, renders input, verifies any
explicit execution resources, writes the input manifest, and only then invokes
`pw.x` when the request has `execute=True`. Calculator completion remains
separate from later output interpretation and scientific validation.
