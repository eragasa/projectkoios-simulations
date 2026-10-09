# Plane-wave DFT SCF repository tools

These repository-local commands operate on reviewed campaign declarations. They
are not included in the wheel and never start QE or VASP.

| Module | Operation |
| --- | --- |
| `render_inputs.py` | Render deterministic QE or VASP input files |
| `replay.py` | Drive the local SCF Petri net with a declared retained artifact |
| `plan.py` | Expand a convergence recipe into ordered coordinates |
| `compare_single.py` | Compare two declared successful SCF artifacts |
| `compare_convergence.py` | Compare normalized convergence evidence |
| `plot_structure.py` | Write a standalone Plotly structure visualization |

`configuration.py`, `environment.py`, and `structure_repository.py` implement
shared bounded loading. `config/runner.toml` points to the profile catalog and
the structures under `examples/workflows/pw_dft_scf`.

Install the `cpn` extra for local Petri-net replay and the `visualization` extra
for structure plotting. Calculator execution always requires a separate
explicitly authorized owner.
