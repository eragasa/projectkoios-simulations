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
