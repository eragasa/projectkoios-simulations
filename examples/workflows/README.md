# Simulation workflow examples

These examples contain reviewed declarations and small composition demonstrations.
Reusable workflow contracts and the local SCF Petri net live in
`src/python/projectkoios/simulations/workflows`; operational commands live in
`tools/`.

- `pw_dft_scf/` contains eight QE/VASP campaigns, four comparisons, two silicon
  structures, and one normalized-evidence replay example.
- `pw_dft_relaxation/` demonstrates QE input projection and a non-authorizing
  execution handoff.

Nothing in this directory executes a calculator or grants execution authority.
