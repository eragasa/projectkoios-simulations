# Third-party and historical-source notices

Maintained Project Koios code in this repository is licensed under Apache-2.0.
The following historical-source notices are retained in addition to that
license.

## PyFlamestk

- Repository: <https://github.com/eragasa/pyflamestk>
- Pinned commit: `5b8368cc88d91bc56f9cc1c8a7fa8d9ea3d6b359`
- Pinned Git tree: `02e20f61a9b554ed0dcbda15bb24adc21e942007`
- Copyright: 2015–2017 Eugene J. Ragasa
- License: BSD 2-Clause-style license
- Preserved text: [`licenses/PYFLAMESTK-BSD-2-CLAUSE.txt`](licenses/PYFLAMESTK-BSD-2-CLAUSE.txt)
- License SHA-256:
  `8e8ff7b5f5de2f4f1b48a18108d6268769739d622cfb671078565ab56bef28aa`

## PyPosPack

- Repository: <https://github.com/eragasa/pypospack>
- Release: `v0.1.0`
- Pinned commit: `be453fa7191e55a0426f66e8b5b5b0b103c8b29d`
- Pinned Git tree: `7ac9c9f255aa7731f39ce35a0e561fc113082a6f`
- Copyright: 2013–2019 Eugene Ragasa
- License: MIT, with additional bundled notices retained in the original text
- Preserved text: [`licenses/PYPOSPACK-MIT.txt`](licenses/PYPOSPACK-MIT.txt)
- License SHA-256:
  `05f25c4caf59b20bbcadbb1e3e1c33b154d273ef7daa7e7740bca8a0ed0f4c83`

## projectkoios-physkit (formerly PhysKit)

- Maintained repository: <https://github.com/eragasa/projectkoios-physkit>
- Repository name at extraction: <https://github.com/eragasa/physkit>
- Extraction-reviewed source commit: `97032f16c9125aa124750508f8513cca9f6dab02`
- Extraction-reviewed source Git tree: `3a323d2436d4b5e86fe312e810e03c5d21ce37b3`
- Runtime dependency: compatible `projectkoios-physkit>=0.1.0` distribution
- Import namespace: `projectkoios.physkit`
- Dependency at extraction: `physkit>=0.1.0`, imported as `physkit`
- Extraction-reviewed snapshot license: MIT
- Maintained successor distribution license: Apache-2.0
- Preserved extraction-snapshot text: [`licenses/PHYSKIT-MIT.txt`](licenses/PHYSKIT-MIT.txt)
- License SHA-256:
  `0c4bfe022416818496cdcd7cf6fcd39af30c12a8e982cfb92d7a565d57dcc410`

## SNAKES / projectkoios-snakes

- Maintained fork: <https://github.com/eragasa/projectkoios-snakes>
- Reviewed fork commit: `72dbb1dbf0a91349faca21ceb660923cc442a8e9`
- Reviewed fork Git tree: `1b38e523f6210aa0f37bce35a43a08b3bb909f81`
- Upstream baseline: SNAKES `0.9.33`, commit
  `2291c6e627c85fc2932a83cc2eb9b712495b5d7a`
- Distribution and import names: `SNAKES` / `snakes`
- License: GNU Lesser General Public License, version 3
- Upstream copyright: Franck Pommereau and contributors
- Reviewed license SHA-256:
  `1e950a32358912876fcd3ea0bdd975c9ea8a7822eddc3cda662817c3abe99b1c`

The maintained fork supplies Python 3.14 compatibility fixes and Project Koios
CPN boundary tests while preserving the upstream import namespace and license.
It is used only by the optional local CPN implementation pending WORKFLOWS
extraction; no SNAKES source is vendored into this repository.

## Reusable simulation-workflow capabilities

The migrated `projectkoios.simulations.workflows` modules contain no vendored
third-party source. They reuse calculator-neutral contracts already distributed
under `projectkoios.simulations`. The optional local CPN uses the maintained
SNAKES fork, while repository tools retain optional Plotly use and compose the
public Quantum ESPRESSO and VASP integrations at their outward boundary. Their original exact
inventory is recorded in
`docs/provenance/deferred-provider-example-main-416be52.tsv`; the filename
preserves the superseded initial classification. The completed destination
mapping is recorded in
`docs/provenance/workflow-runner-relocation-main-416be52.tsv`.

The commit and tree above identify the MIT-licensed PhysKit source reviewed
during extraction; they are provenance identities, not installation constraints.
The separately distributed Apache-2.0 projectkoios-physkit successor supplies
the maintained runtime namespace. The Wannier90 parser extraction reuses its
generic unit and immutable quantity contracts
rather than copying that infrastructure into the simulations distribution. The
parser donor and this repository share the exact Apache-2.0 text identified by
the wheel-carried Wannier90 `provenance.json` resource.

These notices document origin and preserve upstream terms. They do not mean the
historical projects endorse this repository, and they do not turn research
citations into software licenses.
