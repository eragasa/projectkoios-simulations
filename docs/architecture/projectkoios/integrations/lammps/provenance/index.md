# `projectkoios.integrations.lammps.provenance`

**Source:** `src/python/projectkoios/integrations/lammps/provenance.py`

This module binds the maintained LAMMPS data reconstruction to an exact external
PyPosPack source.

## Constants

- `PYPOSPACK_COMPONENT`, `PYPOSPACK_REPOSITORY_URL`,
  `PYPOSPACK_RELEASE_TAG`, `PYPOSPACK_REVISION`, and `PYPOSPACK_TREE` identify
  the upstream release and exact Git object.
- `PYPOSPACK_LAMMPS_PATH`, `PYPOSPACK_LAMMPS_SHA256`, and
  `PYPOSPACK_LAMMPS_BYTE_SIZE` identify the selected source file.
- `PYPOSPACK_LICENSE_PATH` and `PYPOSPACK_LICENSE_SHA256` identify its license.
- `PYPOSPACK_LAMMPS_LIMITATIONS` records bounded source limitations.

## API

[`PypospackLammpsProvenance`](PypospackLammpsProvenance/index.md) is the immutable
result. `verify_pypospack_lammps_checkout(checkout_root)` verifies source and
license bytes in an explicit local checkout. It performs no discovery, clone,
import, or execution.
