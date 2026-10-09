# Software origins and research provenance

## Maintained repository

`projectkoios-simulations` is the maintained owner of the inward
`projectkoios.simulations` namespace and the sibling
`projectkoios.simulation_workflows` capability namespace. The repository applies
Apache-2.0 to its maintained code under explicit operator and rightsholder
authority.

The initial implementation was extracted from
`projectkoios-frankenstein` commit
`3eb562f2d6167ec20d6f2c892c517509a7abf283`. Exact source, test, and
documentation Git trees and the namespace-only adaptation are recorded in
[`../../TRANSFER.toml`](../../TRANSFER.toml).

## Reusable simulation-workflow capability migration

The reusable SCF and relaxation workflow capabilities under
`projectkoios.simulation_workflows` were migrated from
`projectkoios-applications` commit
`416be52d539bfbffdbc8a27bd8e13de65404821b` (root tree
`de6257c720fa73caff21b393af4a3fb4858fd617`). The migration copied the
capability implementation, direct tests, retained normalized replay fixture,
and architecture documentation wholesale. Adaptations were limited to the
namespace and import paths plus destination documentation and package metadata.
Exact implementation, test, and documentation tree identities are recorded in
[`../../TRANSFER.toml`](../../TRANSFER.toml).

The provider-dependent examples, their tests, the provider-fingerprint fixture,
and its exact-provider probe remain authoritative in `projectkoios-applications`
until a separate provider/example migration. Their 55 exact source paths, Git
blob identities, SHA-256 digests, and byte counts are retained in
[`deferred-provider-example-main-416be52.tsv`](deferred-provider-example-main-416be52.tsv).
The mutually exclusive replay replacement from child commit
`7b687fb23b9877b744bfba3455040db2cbf94292` (root tree
`0e7c07e76d932fb3f5efc173d0835a9f8e7ba8bc`) was applied afterward as a
separate overlay. Fourteen capability paths replace the former replayer with a
typed runtime-neutral Actionizer contract. The provider-example change remains
deferred, while the two Applications-specific source-distribution inventory
paths are represented by destination build-inventory and provenance checks
rather than transplanted. The exact 17-path source delta is retained in
[`replay-7b687fb-delta-manifest.tsv`](replay-7b687fb-delta-manifest.tsv).
The stable action identity remains
`projectkoios.applications.pw-dft-scf.convergence-replay`; preserving that
literal avoids changing the identity of the migrated operation.

No calculator was executed during migration. Source provenance establishes
transfer identity only; it does not establish behavioral conformance, numerical
verification, scientific validation, or acceptance.

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

## Wannier90 native-artifact parser extraction

The outward parser bundle under `projectkoios.integrations.wannier90` was
extracted from `ksdft2effmass` commit
`7bd913151f7e61ed2bdba593df920be36573b502` (root tree
`4f7ca69afbd1381c0cb736b0efe6b8ac5431acf6`). Its implementation and test
subtrees, individual source blobs, namespace rewrite, and Apache-2.0 license
identity are recorded in [`../../TRANSFER.toml`](../../TRANSFER.toml).

The donor imported generic unit-bearing array contracts from its broad
`ksdft2effmass.operators` facade. Static closure analysis identified
`operators/quantities.py` as the only semantic dependency. Those generic
contracts are already owned by the compatible `projectkoios-physkit`
distribution. At extraction that repository and distribution were named
`physkit`; both the historical and successor identities are retained in
`TRANSFER.toml`. Commit `97032f16c9125aa124750508f8513cca9f6dab02`
identifies the implementation reviewed during extraction, not an installation
pin. Maintained imports target `projectkoios.physkit.units.quantities`, and no
operator, Hamiltonian, workflow, calculator, execution, or campaign package was
copied. The extraction-reviewed PhysKit snapshot's MIT text is retained in
[`../../licenses/PHYSKIT-MIT.txt`](../../licenses/PHYSKIT-MIT.txt); the
maintained projectkoios-physkit successor is separately distributed under
Apache-2.0.

The extracted parsers only adapt caller-supplied bytes and correlate logical
names, byte counts, and SHA-256 identities. They do not run Wannier90, perform
interpolation, normalize into universal units, judge convergence, or establish
scientific validity.

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
