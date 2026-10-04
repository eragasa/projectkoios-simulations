"""Fail-closed correlation across authenticated QE/Wannier90 provider data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import PurePosixPath

import numpy as np

from projectkoios.integrations.quantumespresso.pw2wannier90.authenticated import (
    QeWannier90AuthenticatedData,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.provider import (
    QeWannier90PlaneWaveArtifactManifest,
)
from projectkoios.integrations.quantumespresso.pw2wannier90.unk import (
    QeWannier90UnkData,
)
from projectkoios.integrations.wannier90.disentanglement_matrices import (
    Wannier90DisentanglementMatrixData,
)
from projectkoios.integrations.wannier90.hamiltonian_blocks import (
    Wannier90HamiltonianBlockData,
)
from projectkoios.integrations.wannier90.interface_data import (
    Wannier90EigenvalueData,
)
from projectkoios.integrations.wannier90.nnkp import Wannier90NnkpData
from projectkoios.integrations.wannier90.unitary_matrices import (
    Wannier90UnitaryMatrixData,
)

from ..pw.data_extraction import QePlaneWaveFrame

_BOHR_TO_ANGSTROM = 0.529177210903


@dataclass(frozen=True, slots=True)
class QeWannier90ProviderCorrelationValidator:
    """Correlate parsed records after their manifest bytes are authenticated.

    NNKP establishes interface lattice, k-point, projection, exclusion, and
    neighbor semantics only. It is deliberately not consulted for FFT/G-index
    mapping or UNK normalization.
    """

    coordinate_absolute_tolerance: float = 1.0e-6

    def __post_init__(self) -> None:
        if (
            type(self.coordinate_absolute_tolerance) is not float
            or not math.isfinite(self.coordinate_absolute_tolerance)
            or self.coordinate_absolute_tolerance <= 0.0
        ):
            raise ValueError(
                "coordinate_absolute_tolerance must be positive and finite"
            )

    def execute(
        self,
        *,
        manifest: QeWannier90PlaneWaveArtifactManifest,
        frame: QePlaneWaveFrame,
        nnkp: QeWannier90AuthenticatedData[Wannier90NnkpData],
        eigenvalues: QeWannier90AuthenticatedData[Wannier90EigenvalueData],
        gauge: QeWannier90AuthenticatedData[Wannier90UnitaryMatrixData],
        disentanglement: QeWannier90AuthenticatedData[
            Wannier90DisentanglementMatrixData
        ],
        hamiltonian: QeWannier90AuthenticatedData[Wannier90HamiltonianBlockData],
        unks: tuple[QeWannier90UnkData, ...],
    ) -> None:
        """Reject any break in the QEXSD→NNKP→native-artifact index chain."""
        if type(manifest) is not QeWannier90PlaneWaveArtifactManifest:
            raise TypeError("manifest has the wrong type")
        if type(frame) is not QePlaneWaveFrame:
            raise TypeError("frame has the wrong type")
        authenticated = (
            (nnkp, manifest.neighbor_interface, Wannier90NnkpData, "nnkp"),
            (
                eigenvalues,
                manifest.eigenvalues,
                Wannier90EigenvalueData,
                "eigenvalues",
            ),
            (gauge, manifest.gauge_matrix, Wannier90UnitaryMatrixData, "gauge"),
            (
                disentanglement,
                manifest.disentanglement_matrix,
                Wannier90DisentanglementMatrixData,
                "disentanglement",
            ),
            (
                hamiltonian,
                manifest.hamiltonian,
                Wannier90HamiltonianBlockData,
                "hamiltonian",
            ),
        )
        for wrapped, binding, data_type, label in authenticated:
            if type(wrapped) is not QeWannier90AuthenticatedData:
                raise TypeError(f"{label} must be authenticated parsed data")
            if wrapped.artifact != binding:
                raise ValueError(f"{label} does not match its manifest binding")
            if type(wrapped.data) is not data_type:
                raise TypeError(f"{label} has the wrong parsed data type")
        nnkp_data = nnkp.data
        eigenvalue_data = eigenvalues.data
        gauge_data = gauge.data
        disentanglement_data = disentanglement.data
        hamiltonian_data = hamiltonian.data
        if type(unks) is not tuple or any(
            type(item) is not QeWannier90UnkData for item in unks
        ):
            raise TypeError("unks must contain QeWannier90UnkData records")
        self._qexsd_identity(manifest, frame)
        self._pseudopotential_identities(manifest, frame)
        if nnkp_data.excluded_bands:
            raise ValueError("nonempty NNKP excluded-band mappings are unsupported")
        if manifest.spin_channel_count != frame.spin_channel_count:
            raise ValueError("manifest and frame spin-channel counts disagree")
        if manifest.spinor_component_count != frame.spinor_component_count:
            raise ValueError("manifest and frame spinor-component counts disagree")
        if (
            manifest.kpoint_count != len(frame.kpoints_reduced)
            or manifest.kpoint_count != nnkp_data.kpoint_count
            or manifest.kpoint_count != eigenvalue_data.kpoint_count
            or manifest.kpoint_count != gauge_data.kpoint_count
            or manifest.kpoint_count != disentanglement_data.kpoint_count
            or manifest.kpoint_count != len(unks)
        ):
            raise ValueError("provider k-point counts disagree")
        if (
            manifest.band_count != frame.band_count
            or manifest.band_count != eigenvalue_data.band_count
            or manifest.band_count != disentanglement_data.band_count
        ):
            raise ValueError("provider band counts disagree")
        if (
            manifest.wannier_count != gauge_data.wannier_count
            or manifest.wannier_count != disentanglement_data.wannier_count
            or manifest.wannier_count != hamiltonian_data.wannier_count
        ):
            raise ValueError("provider Wannier counts disagree")
        self._coordinates(frame, nnkp_data, gauge_data, disentanglement_data)
        expected_indices = tuple(range(1, manifest.kpoint_count + 1))
        if tuple(item.kpoint_index for item in unks) != expected_indices:
            raise ValueError("decoded UNKs are not in contiguous k-point order")
        for decoded, binding in zip(unks, manifest.unks, strict=True):
            if decoded.artifact != binding:
                raise ValueError("decoded UNK does not match its manifest binding")
            if (
                decoded.grid_shape != frame.fft_grid
                or decoded.band_count != manifest.band_count
                or decoded.spinor_component_count != manifest.spinor_component_count
            ):
                raise ValueError(
                    "decoded UNK dimensions disagree with the provider frame"
                )

    @staticmethod
    def _qexsd_identity(
        manifest: QeWannier90PlaneWaveArtifactManifest,
        frame: QePlaneWaveFrame,
    ) -> None:
        document = frame.qexsd.document
        if (
            getattr(document, "source_sha256", None) != manifest.qexsd.sha256
            or getattr(document, "source_byte_count", None) != manifest.qexsd.byte_size
        ):
            raise ValueError("plane-wave frame does not use the manifest QEXSD")
        source_path = getattr(document, "source_path", None)
        if type(source_path) is not str:
            raise ValueError("QEXSD source path is unavailable")
        source_parts = PurePosixPath(source_path).parts
        relative_parts = PurePosixPath(manifest.qexsd.relative_path).parts
        if source_parts[-len(relative_parts) :] != relative_parts:
            raise ValueError("QEXSD source path does not match the manifest binding")

    @staticmethod
    def _pseudopotential_identities(
        manifest: QeWannier90PlaneWaveArtifactManifest,
        frame: QePlaneWaveFrame,
    ) -> None:
        manifest_values = tuple(
            (item.basename, item.sha256, item.byte_size)
            for item in manifest.pseudopotentials
        )
        frame_values = tuple(
            (item.filename, item.sha256, item.byte_size)
            for item in frame.pseudopotentials
        )
        if manifest_values != frame_values:
            raise ValueError(
                "plane-wave frame pseudopotentials disagree with the manifest"
            )

    def _coordinates(
        self,
        frame: QePlaneWaveFrame,
        nnkp: Wannier90NnkpData,
        gauge: Wannier90UnitaryMatrixData,
        disentanglement: Wannier90DisentanglementMatrixData,
    ) -> None:
        expected_real = np.asarray(frame.direct_lattice_bohr) * _BOHR_TO_ANGSTROM
        expected_reciprocal = (
            np.asarray(frame.reciprocal_lattice_per_bohr) / _BOHR_TO_ANGSTROM
        )
        nnkp_kpoints = np.asarray(nnkp.kpoints)
        if not np.allclose(
            np.asarray(nnkp.real_lattice),
            expected_real,
            rtol=0.0,
            atol=self.coordinate_absolute_tolerance,
        ):
            raise ValueError("NNKP real lattice disagrees with QEXSD")
        if not np.allclose(
            np.asarray(nnkp.reciprocal_lattice),
            expected_reciprocal,
            rtol=0.0,
            atol=self.coordinate_absolute_tolerance,
        ):
            raise ValueError("NNKP reciprocal lattice disagrees with QEXSD")
        if not np.allclose(
            nnkp_kpoints,
            np.asarray(frame.kpoints_reduced),
            rtol=0.0,
            atol=self.coordinate_absolute_tolerance,
        ):
            raise ValueError("NNKP ordered k-points disagree with QEXSD")
        for label, observed in (
            ("u.mat", gauge.fractional_kpoints.magnitude),
            ("u_dis.mat", disentanglement.fractional_kpoints.magnitude),
        ):
            if not np.allclose(
                observed,
                nnkp_kpoints,
                rtol=0.0,
                atol=self.coordinate_absolute_tolerance,
            ):
                raise ValueError(f"{label} ordered k-points disagree with NNKP")


__all__ = ["QeWannier90ProviderCorrelationValidator"]
