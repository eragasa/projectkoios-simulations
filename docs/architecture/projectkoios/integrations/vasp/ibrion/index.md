# `ibrion`

Qualified cross-calculator workflow information implemented by `VaspIbrion`, `VaspIbrionAlignment`, `VaspNebAlignment`, `VASP_IBRION_ALIGNMENT_REGISTRY`, and `VASP_NEB_ALIGNMENT`.

Authorities:

- VASP `IBRION`: <https://vasp.at/wiki/IBRION>
- VASP NEB: <https://vasp.at/wiki/Nudged_elastic_bands>
- QE `pw.x`: <https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1>
- QE `neb.x`: <https://www.quantum-espresso.org/Doc/INPUT_NEB.html>

The registry distinguishes shared scientific purpose from algorithm equivalence. In particular, QE 7.5 does not document `ion_dynamics='cg'`, and VASP `IBRION=44` is the improved dimer method rather than NEB.

| VASP `IBRION` | VASP purpose | Qualified QE route |
|---:|---|---|
| `-1` | Fixed ions and cell | `pw.x` with `calculation='scf'`, `'nscf'`, or `'bands'`, depending on the electronic workflow |
| `0` | Molecular dynamics | `pw.x`, `calculation='md'`, plus explicit integrator and ensemble policy |
| `1` | RMM-DIIS relaxation | No algorithm-equivalent QE mode; BFGS is a distinct alternative |
| `2` | Conjugate-gradient relaxation | No QE 7.5 `ion_dynamics='cg'`; BFGS, damped dynamics, or FIRE can serve the relaxation purpose approximately |
| `3` | Damped-dynamics relaxation | `ion_dynamics='damp'`; variable-cell relaxation separately requires `cell_dynamics='damp-pr'` or `'damp-w'` |
| `5` / `6` | Finite-difference phonons | `ph.x` targets phonons using DFPT, not the same finite-difference algorithm |
| `7` / `8` | DFPT phonons | Run `ph.x` after a qualified SCF reference; symmetry and q-point policies remain explicit |
| `44` | Improved dimer transition-state search | No direct QE equivalent recorded; it must not be mapped to `neb.x` |
| VASP NEB workflow | Multi-image path optimization through `IMAGES`, `SPRING`, and an optimizer | QE `neb.x` with `&PATH`; this is a workflow mapping, not an `IBRION=44` mapping |
