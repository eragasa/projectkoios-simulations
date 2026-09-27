# Software origins and research provenance

## Maintained repository

`projectkoios-simulations` is the maintained owner of the
`projectkoios.simulations` namespace. The repository applies Apache-2.0 to its
maintained code under explicit operator and rightsholder authority.

The initial implementation was extracted from
`projectkoios-frankenstein` commit
`3eb562f2d6167ec20d6f2c892c517509a7abf283`. Exact source, test, and
documentation Git trees and the namespace-only adaptation are recorded in
[`../../TRANSFER.toml`](../../TRANSFER.toml).

## Historical software lineage

The original source lineage comes from two projects:

- **PyFlamestk** — `https://github.com/eragasa/pyflamestk`, pinned at commit
  `5b8368cc88d91bc56f9cc1c8a7fa8d9ea3d6b359`, Git tree
  `02e20f61a9b554ed0dcbda15bb24adc21e942007`.
- **PyPosPack** — `https://github.com/eragasa/pypospack`, release `v0.1.0`,
  pinned at commit `be453fa7191e55a0426f66e8b5b5b0b103c8b29d`, Git tree
  `7ac9c9f255aa7731f39ce35a0e561fc113082a6f`.

PyFlamestk's retained BSD-style notice is preserved as
[`../../licenses/PYFLAMESTK-BSD-2-CLAUSE.txt`](../../licenses/PYFLAMESTK-BSD-2-CLAUSE.txt).
PyPosPack's retained MIT notice, including its bundled third-party notices, is
preserved as
[`../../licenses/PYPOSPACK-MIT.txt`](../../licenses/PYPOSPACK-MIT.txt).
Apache-2.0 does not erase or replace those notices.

The maintained contracts are reconstructed and adapted Project Koios code;
they are not represented as unchanged upstream files. Historical lineage does
not by itself establish behavioral conformance, numerical verification, or
scientific validation.

## Research references

[1] E. J. Ragasa, C. J. O'Brien, R. G. Hennig, S. M. Foiles, and
S. R. Phillpot, “Multi-objective optimization of interatomic potentials with
application to MgO,” *Modelling and Simulation in Materials Science and
Engineering*, vol. 27, no. 7, article 074007, 2019.
DOI: [10.1088/1361-651X/ab28d9](https://doi.org/10.1088/1361-651X/ab28d9).

[2] E. J. Ragasa, *Machine Learning Techniques for the Rational Design of
Analytic Interatomic Potentials*, Ph.D. dissertation, Materials Science and
Engineering, University of Florida, Gainesville, FL, August 2019. ProQuest
Dissertations & Theses Global, Publication No. 22615421.
[ProQuest record](https://www.proquest.com/openview/2207f5cce947e0b1e24ca4de6edad24d/1?pq-origsite=gscholar&cbl=18750&diss=y).
[University of Florida record](https://ufdc.ufl.edu/UFE0055800/00001).
No DOI is assigned to this dissertation.

The DOI metadata for [1] was verified against Crossref and IOP Publishing. The
ProQuest and University of Florida records for [2] do not report a DOI, so none
is invented here.
