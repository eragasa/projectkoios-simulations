# Project Koios Simulations

`projectkoios-simulations` owns calculator-neutral simulation identities,
execution records, density-functional-theory and pseudopotential contracts, and
plane-wave SCF, NSCF, and structural-relaxation contracts under
`projectkoios.simulations`. Outward provider integrations owned by this
distribution live under `projectkoios.integrations`.

The VASP integration provides native INCAR, KPOINTS, POSCAR, and OUTCAR
representations plus projections to calculator-neutral simulation contracts. It
does not select pseudopotentials, authorize calculator execution, claim that
projected inputs are runnable, or establish numerical or scientific validation.
Workflow orchestration, convergence campaigns, recipes, and scientific
acceptance policy do not belong here.

## License and origin

Maintained Project Koios code in this repository is licensed under the
Apache License 2.0; see [`LICENSE`](LICENSE).

The original software lineage comes from the historical
[PyFlamestk](https://github.com/eragasa/pyflamestk) and
[PyPosPack](https://github.com/eragasa/pypospack) projects. Their notices and
license texts remain available in [`licenses/`](licenses/) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). The extraction from
`projectkoios-frankenstein` is bound to an exact commit and Git trees in
[`TRANSFER.toml`](TRANSFER.toml).

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

These citations describe the research lineage. They do not replace software
license notices, establish scientific validation, or imply endorsement.

## Development

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install -e '.[development]'
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check src/python tests
MYPYPATH=src/python .venv/bin/python -m mypy --strict \
  src/python/projectkoios/simulations src/python/projectkoios/integrations
.venv/bin/python -m build --wheel
```
