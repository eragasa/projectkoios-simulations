# Project Koios Simulations

`projectkoios-simulations` owns the `projectkoios.simulations`
simulation-domain umbrella. Its non-workflow subtrees form the protected
calculator-neutral core. Reusable SCF and relaxation composition lives in the
owner-specific `projectkoios.simulations.workflows` layer. Outward provider
integrations and adapters remain under `projectkoios.integrations` and
`projectkoios.adapters`. The protected core never imports workflows or
providers; the workflow layer may import core contracts but never provider
implementations. Its optional local SNAKES `PetriNet` is the authoritative SCF
executable topology pending extraction by WORKFLOWS and carries no calculator
authority.
The architecture contract is documented in
[`docs/architecture/projectkoios/simulations/`](docs/architecture/projectkoios/simulations/index.md).
Repository-local workflow tools live under `tools/pw_dft_scf`. Compact reviewed
campaign, comparison, structure, replay, and relaxation demonstrations live
under `examples/workflows`. Both remain calculator-free and outside wheel
package discovery.

The VASP integration provides native INCAR, KPOINTS, POSCAR, and OUTCAR
representations plus projections to calculator-neutral simulation contracts. It
does not select pseudopotentials, authorize calculator execution, claim that
projected inputs are runnable, or establish numerical or scientific validation.
The neutral band contracts include the explicitly classified standard primitive
cells, special reciprocal points, and path topologies of Setyawan and Curtarolo
[3]. They do not infer space groups or authorize calculator execution. Reusable
convergence, comparison, recipe, replay, workflow inventories, and the local
SCF Petri net live under `projectkoios.simulations.workflows` without a
compatibility facade at the former sibling namespace.

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

## Exact structures, supercells, and defect deltas

`StructureLibrary` resolves exact manifest-declared primitive and conventional
unit cells by stable identifier, representation, schema version, byte size,
SHA-256, and immutable source provenance. `SuperCellBuilder` derives diagonal
supercells with source-site provenance. `UnitCellDefectDelta` represents
vacancies, interstitials, substitutions, and complexes through simultaneous
original-index removals followed by declared additions. Applying a delta returns
a base `UnitCell`; charge state remains separate configuration metadata.

The reviewed examples include exact silicon primitive and conventional records
and concrete neutral, unrelaxed Si:P and Si:B declarations based on a `(2, 2,
2)` conventional supercell. See the
[structure architecture](docs/architecture/projectkoios/simulations/structure/index.md).
These data operations neither authorize calculator execution nor establish that
a defect model is scientifically appropriate or relaxed.

The optional
[Materials Project integration](docs/architecture/projectkoios/integrations/materials_project/index.md)
uses pymatgen convex hulls to select explicit elemental B and P reference entries
from an injected `MPRester` client. Install the `materials-project` extra for
that outward integration. It records a database- and compatibility-scheme-qualified
reference choice; it does not claim a universal finite-temperature ground state.

## Local calculator and pseudopotential deployment

[`local-execution.example.toml`](local-execution.example.toml) is the single
operator-only template for calculator executable paths and the external Quantum
ESPRESSO pseudopotential-library root. Copy it to `local-execution.toml`, which
is ignored by Git, and replace the placeholders with machine-local absolute
paths. No production parser or tool automatically consumes this file; see the
[deployment-template contract](docs/local-execution.md).

`PseudopotentialLibrary` resolves a complete `PseudopotentialFile` requirement
beneath the configured root by exact basename, byte size, and SHA-256. It does
not select a pseudopotential by element or silently substitute another
same-named file. Scientific selection remains explicit in the simulation
configuration, while deployment paths remain machine-local.

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
.venv/bin/python -m ruff format --check src/python tools examples tests
.venv/bin/python -m mypy
.venv/bin/python -m build --wheel
```
