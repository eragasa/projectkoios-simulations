# `projectkoios.integrations.wannier90`

## Current status

The implemented integration remains parser-only and execution-independent. The
planned preprocessing and localization architecture linked below does not add
production packages, public APIs, staging, subprocess behavior, or execution
authority. Those capabilities require separate reviewed implementation changes.

## Ownership

This outward integration owns execution-independent adaptation of seven
caller-supplied Wannier90 text artifacts:

- `.eig` indexed eigenvalues
- `.amn` projections
- `.mmn` neighbor-overlap matrices
- `.nnkp` neighbor lists
- `.wout` final localization observations
- `_u.mat` gauge matrices
- `_hr.dat` real-space Hamiltonian blocks

The package has no filesystem discovery, subprocess, calculator, workflow,
interpolation, convergence-policy, or scientific-acceptance behavior.

## Dependency direction

```text
projectkoios.integrations.wannier90
    -> projectkoios.physkit.units.quantities
    -> NumPy/Pint/SciPy (through projectkoios-physkit)

projectkoios.simulations -X-> projectkoios.integrations
```

Native parser records are integration-owned. The inward
`projectkoios.simulations` namespace must never import them. No new neutral
simulation record was identified during extraction.

## Planned provider execution prerequisites

- [Planned preprocessing integration](preprocessing/index.md) specifies a future
  exact-input and single-occurrence `wannier90.x -pp` provider boundary.
- [Planned localization execution](localization/index.md) specifies a future
  route-qualified input, single-occurrence localization, and native-output
  evidence boundary.

Both nodes are explicitly unimplemented. They preserve configuration versus
authority, one process per occurrence, closed native artifact sets, retained
failure evidence, and separation of provider observations from scientific
acceptance.

## Outward neutral adaptation boundary

Production integration modules return provider-native records and do not import
`projectkoios.simulations.workflows`. The neutral workflow layer likewise does
not import integration records. The ProjectKoios simulations distribution must
provide a separately reviewed first-party outward `projectkoios.adapters`
surface that imports public contracts from both sides, authenticates the
provider observation, and maps its semantic roles to neutral
`pw_dft_wannierization` roles. `tools/pw_dft_wannierization` consumes that
mapping for provider selection, operational configuration, and route invocation;
it does not own the mapping contract.

That mapping must retain exact provider artifact, parent, route-profile, schema,
and adapter-implementation identities. It must not place provider objects in
neutral records, copy scientific policy into the integration, infer execution
authority, or claim acceptance. No such adapter is implemented by these
documents.

## Public implemented surfaces

- [Artifact identity and set correlation](artifacts/index.md)
- [Parser and record inventory](parsers/index.md)
- [Provenance and scientific limits](provenance/index.md)
