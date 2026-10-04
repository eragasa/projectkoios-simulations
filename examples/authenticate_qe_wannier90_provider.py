#!/usr/bin/env python3
"""Authenticate and correlate one retained QE→Wannier90 provider inventory.

The caller supplies an already parsed :class:`QeQexsdData`, explicit UPF
metadata, and an immutable manifest. This example performs no XML parsing,
artifact discovery, calculator execution, H−T subtraction, or scientific
acceptance decision.
"""

from __future__ import annotations

from pathlib import Path

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction import (
    QePlaneWaveFrameExtractor,
    QeQexsdData,
    QeWavefunctionOverlapMetric,
)
from projectkoios.integrations.quantumespresso.pw2wannier90 import (
    QeWannier90AuthenticatedParser,
    QeWannier90PlaneWaveArtifactManifest,
    QeWannier90PlaneWaveManifestVerifier,
    QeWannier90ProviderCorrelationValidator,
    QeWannier90UnkParser,
)
from projectkoios.physkit.units.quantities import ModelSystemUnit


def authenticate_retained_provider(
    *,
    run_root: Path,
    manifest: QeWannier90PlaneWaveArtifactManifest,
    qexsd: QeQexsdData,
    pseudopotentials: tuple[QePseudopotentialFile, ...],
    overlap_metric: QeWavefunctionOverlapMetric,
    eigenvalue_unit: ModelSystemUnit,
    hamiltonian_unit: ModelSystemUnit,
) -> dict[str, int]:
    """Return structural observations after every provider gate succeeds."""
    verified_paths = QeWannier90PlaneWaveManifestVerifier().verify(manifest, run_root)
    paths = dict(zip(manifest.artifacts, verified_paths, strict=True))
    frame = QePlaneWaveFrameExtractor().extract(
        qexsd,
        pseudopotentials=pseudopotentials,
        overlap_metric=overlap_metric,
        spin_channel_count=manifest.spin_channel_count,
        spinor_component_count=manifest.spinor_component_count,
    )

    parser = QeWannier90AuthenticatedParser()
    nnkp = parser.parse_nnkp(
        manifest.neighbor_interface,
        paths[manifest.neighbor_interface].read_bytes(),
    )
    eigenvalues = parser.parse_eigenvalues(
        manifest.eigenvalues,
        paths[manifest.eigenvalues].read_bytes(),
        eigenvalue_unit,
    )
    gauge = parser.parse_gauge_matrix(
        manifest.gauge_matrix,
        paths[manifest.gauge_matrix].read_bytes(),
    )
    disentanglement = parser.parse_disentanglement_matrix(
        manifest.disentanglement_matrix,
        paths[manifest.disentanglement_matrix].read_bytes(),
    )
    hamiltonian = parser.parse_hamiltonian(
        manifest.hamiltonian,
        paths[manifest.hamiltonian].read_bytes(),
        hamiltonian_unit,
    )

    unk_parser = QeWannier90UnkParser()
    unks = tuple(
        unk_parser.execute(
            artifact,
            paths[artifact].read_bytes(),
            expected_grid_shape=frame.fft_grid,
            expected_band_count=manifest.band_count,
            expected_spinor_component_count=manifest.spinor_component_count,
        )
        for artifact in manifest.unks
    )
    QeWannier90ProviderCorrelationValidator().execute(
        manifest=manifest,
        frame=frame,
        nnkp=nnkp,
        eigenvalues=eigenvalues,
        gauge=gauge,
        disentanglement=disentanglement,
        hamiltonian=hamiltonian,
        unks=unks,
    )
    return {
        "kpoint_count": nnkp.data.kpoint_count,
        "band_count": eigenvalues.data.band_count,
        "wannier_count": gauge.data.wannier_count,
        "neighbor_count": nnkp.data.neighbor_count,
        "hamiltonian_representative_count": len(hamiltonian.data.representatives),
    }
