# Project Koios Simulations

`projectkoios-simulations` owns the `projectkoios.simulations`
simulation-domain umbrella. Existing non-workflow subtrees form its protected
calculator-neutral core. Reusable SCF and relaxation composition is approved to
move from the currently published sibling `projectkoios.simulation_workflows`
namespace into the owner-specific `projectkoios.simulations.workflows` layer in
a separate forward migration. Outward provider integrations and adapters remain
under `projectkoios.integrations` and `projectkoios.adapters`. The protected
core never imports workflows or providers; the workflow layer may import core
contracts but never provider implementations or live workflow-runtime objects.
The architecture contract is documented in
[`docs/architecture/projectkoios/simulations/`](docs/architecture/projectkoios/simulations/index.md).

The VASP integration provides native INCAR, KPOINTS, POSCAR, and OUTCAR
representations plus projections to calculator-neutral simulation contracts. It
does not select pseudopotentials, authorize calculator execution, claim that
projected inputs are runnable, or establish numerical or scientific validation.
The neutral band contracts include the explicitly classified standard primitive
cells, special reciprocal points, and path topologies of Setyawan and Curtarolo
[3]. They do not infer space groups or authorize calculator execution. Reusable
convergence, comparison, recipe, replay, and workflow-definition contracts are
the owner-specific composition layer: they currently live under
`projectkoios.simulation_workflows` and will move cleanly to
`projectkoios.simulations.workflows` without a compatibility facade.

The LAMMPS package is a provenance-bound reconstruction scaffold for inspecting
retained templates and data text and for rendering bounded data artifacts. It
does not run LAMMPS, parse calculator results, control convergence, or claim
behavioral conformance, numerical verification, or scientific validation.
Workflow orchestration, campaigns, recipes, and scientific acceptance policy do
not belong in the LAMMPS integration package.

The Quantum ESPRESSO integration provides native input, output, saved-state,
SCF, NSCF, relaxation, `pw2wannier90.x`, and initial `epw.x` contracts. The EPW
adapter renders typed namelist assignments, stages exact declared parent
artifacts, observes captured streams, and verifies declared outputs. Calculator
execution is fail-closed and requires explicit authorization; process success
does not imply parent-state compatibility, numerical verification, convergence,
or scientific validation. Workflow orchestration, campaigns, recipes, and
scientific acceptance policy do not belong in the Quantum ESPRESSO integration
package.

`projectkoios.integrations.wannier90` authenticates and parses retained native
Wannier90 text artifacts without filesystem access or calculator execution.
The protected simulation core and owner-specific workflow layer never import
this outward integration. Workflow orchestration, calculator execution,
convergence campaigns, recipes, and scientific acceptance policy do not belong
in the parser bundle.

## Execution-independent provider example

[`examples/authenticate_qe_wannier90_provider.py`](examples/authenticate_qe_wannier90_provider.py)
shows the read-only QEXSD → manifest verification → authenticated native parsing →
correlation sequence. The caller supplies an already parsed QEXSD record and
explicit immutable artifact identities. The example does not discover or run a
calculator, infer scientific metadata, or copy the authoritative production run.

## License and origin

Maintained Project Koios code in this repository is licensed under the
Apache License 2.0; see [`LICENSE`](LICENSE).

The original software lineage comes from the historical
[PyFlamestk](https://github.com/eragasa/pyflamestk) and
[PyPosPack](https://github.com/eragasa/pypospack) projects. Their notices and
license texts remain available in [`licenses/`](licenses/) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). The extractions from
`projectkoios-frankenstein`, the provenance-bound Wannier90 parser donor, and
the reusable workflow migration from `projectkoios-applications` are bound to
exact commits and Git trees in [`TRANSFER.toml`](TRANSFER.toml).
Installed Wannier parser provenance is available as the machine-readable
package resource `projectkoios.integrations.wannier90/provenance.json`.

Research provenance is documented in [`CITATIONS.md`](CITATIONS.md) and
[`docs/provenance/origins.md`](docs/provenance/origins.md). In particular:

[1] E. J. Ragasa, C. J. O'Brien, R. G. Hennig, S. M. Foiles, and
S. R. Phillpot, “Multi-objective optimization of interatomic potentials with
application to MgO,” *Modelling and Simulation in Materials Science and
Engineering*, vol. 27, no. 7, article 074007, 2019.
[https://doi.org/10.1088/1361-651X/ab28d9](https://doi.org/10.1088/1361-651X/ab28d9).

[2] E. J. Ragasa, *Machine Learning Techniques for the Rational Design of
Analytic Interatomic Potentials*, Ph.D. dissertation, Materials Science and
Engineering, University of Florida, Gainesville, FL, August 2019. ProQuest
Dissertations & Theses Global, Publication No. 22615421.
[ProQuest record](https://www.proquest.com/openview/2207f5cce947e0b1e24ca4de6edad24d/1?pq-origsite=gscholar&cbl=18750&diss=y).
No DOI is assigned to this dissertation.

[3] W. Setyawan and S. Curtarolo, “High-throughput electronic band structure
calculations: Challenges and tools,” *Computational Materials Science*, vol. 49,
no. 2, pp. 299--312, 2010.
[https://doi.org/10.1016/j.commatsci.2010.05.010](https://doi.org/10.1016/j.commatsci.2010.05.010).

These citations describe research lineage and implemented scientific methods.
They do not replace software
license notices, establish scientific validation, or imply endorsement.

## Development

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -e '.[development]'
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check src/python tests
.venv/bin/python -m mypy
.venv/bin/python -m build --wheel
```
