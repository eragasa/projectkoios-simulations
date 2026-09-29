#!/usr/bin/env python3
"""Parse one retained seven-file Wannier90 artifact set without execution.

Adapted from the execution-free artifact assembly in ksdft2effmass commit
7bd913151f7e61ed2bdba593df920be36573b502, file
``python/tests/software_verification/ksdft2effmass/campaigns/research_monograph/
periodic_1d/test__Periodic1DWannier90NativeArtifactWorkflow.py``.

This example reports structural parser observations only. It does not run
Wannier90 or claim convergence, unitarity, Hermiticity, unit conversion, or
scientific validity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from projectkoios.integrations.wannier90 import (
    Wannier90NativeArtifact,
    Wannier90NativeArtifactSetParser,
)
from projectkoios.physkit.units.quantities import PhysicalUnit


def parse_retained_artifacts(directory: Path, seed_name: str) -> dict[str, object]:
    """Read and parse the seven supported files for one seed name."""
    names = (
        f"{seed_name}.eig",
        f"{seed_name}.amn",
        f"{seed_name}.mmn",
        f"{seed_name}.nnkp",
        f"{seed_name}.wout",
        f"{seed_name}_u.mat",
        f"{seed_name}_hr.dat",
    )
    artifacts = tuple(
        Wannier90NativeArtifact(name, (directory / name).read_bytes()) for name in names
    )
    parsed = Wannier90NativeArtifactSetParser().execute(
        seed_name,
        artifacts,
        PhysicalUnit("electron_volt"),
        PhysicalUnit("angstrom"),
    )
    return {
        "kpoint_count": parsed.eigenvalues.kpoint_count,
        "band_count": parsed.eigenvalues.band_count,
        "projection_count": parsed.projections.projection_count,
        "wannier_count": parsed.unitary_matrices.wannier_count,
        "neighbor_count": parsed.neighbor_list.neighbor_count,
        "neighbor_inventory": [list(record) for record in parsed.neighbor_list.records],
        "reported_wannierisation_iterations": list(
            parsed.localization.reported_wannierisation_iterations
        ),
        "last_reported_wannierisation_iteration": (
            parsed.localization.last_reported_wannierisation_iteration
        ),
        "hamiltonian_representative_count": len(
            parsed.hamiltonian_blocks.representatives
        ),
    }


def main() -> None:
    """Parse command-line arguments and print structural observations as JSON."""
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("directory", type=Path)
    argument_parser.add_argument("seed_name")
    arguments = argument_parser.parse_args()
    print(
        json.dumps(
            parse_retained_artifacts(arguments.directory, arguments.seed_name),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
