from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction import (
    QePlaneWaveFrameExtractor,
    QeQexsdData,
    QeWavefunctionOverlapMetric,
)
from projectkoios.integrations.quantumespresso.pw2wannier90 import (
    QeWannier90AuthenticatedData,
    QeWannier90AuthenticatedParser,
    QeWannier90PlaneWaveArtifactManifest,
    QeWannier90ProviderArtifact,
    QeWannier90ProviderArtifactRole,
    QeWannier90ProviderCorrelationValidator,
    QeWannier90UnkParser,
)
from projectkoios.physkit.units import PhysicalUnit

_BOHR_TO_ANGSTROM = 0.529177210903
_EIGENVALUE_PAYLOAD = b"1 1 0.0\n"
_GAUGE_PAYLOAD = b"gauge\n1 1 1\n0 0 0\n1 0\n"
_DISENTANGLEMENT_PAYLOAD = b"dis\n1 1 1\n0 0 0\n1 0\n"
_HAMILTONIAN_PAYLOAD = b"hr\n1\n1\n1\n0 0 0 1 1 0.0 0.0\n"


def _binding(
    role: QeWannier90ProviderArtifactRole,
    path: str,
    *,
    payload: bytes = b"x",
    kpoint_index: int | None = None,
    spin_channel_index: int | None = None,
) -> QeWannier90ProviderArtifact:
    return QeWannier90ProviderArtifact(
        role=role,
        relative_path=path,
        sha256=hashlib.sha256(payload).hexdigest(),
        byte_size=len(payload),
        kpoint_index=kpoint_index,
        spin_channel_index=spin_channel_index,
    )


def _qexsd() -> QeQexsdData:
    return QeQexsdData.from_document(
        SimpleNamespace(
            source_path="/run/work/qe/si.save/data-file-schema.xml",
            source_sha256="0" * 64,
            source_byte_count=123,
            qexsd_version="25.05.21",
            producing_application="Quantum ESPRESSO",
            producing_application_version="7.5",
            declared_unit_system_label="Hartree atomic units",
            atomic_structure_alat=1.0,
            direct_lattice_vectors=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            direct_lattice_source_label="output/atomic_structure/cell",
            reciprocal_lattice_coefficients=(
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            ),
            reciprocal_lattice_source_label="output/basis_set/reciprocal_lattice",
            species=(("Si", 28.0855, "Si.UPF"),),
            atoms=((1, "Si", (0.0, 0.0, 0.0)),),
            declared_atom_count=1,
            atomic_positions_source_label="output/atomic_structure/atomic_positions",
            k_points=((0.0, 0.0, 0.0),),
            k_point_source_label="output/band_structure/ks_energies/k_point",
            sampled_k_point_count=1,
            band_count=1,
            fft_grid=(1, 1, 1),
            exit_status=0,
        )
    )


def _pseudo() -> QePseudopotentialFile:
    return QePseudopotentialFile(
        pseudopotential=QePseudopotential(
            symbol="Si",
            exchange_correlation="PBE",
            formalism="norm-conserving",
            relativistic_treatment="scalar-relativistic",
            valence_electrons=4,
            upf_version="2.0.1",
        ),
        filename="Si.UPF",
        sha256="1" * 64,
        byte_size=100,
    )


def _unk_payload() -> bytes:
    header = struct.pack("<5i", 1, 1, 1, 1, 1)
    value = np.asarray([1.0 + 0.0j], dtype="<c16").tobytes()
    return (
        struct.pack("<i", 20)
        + header
        + struct.pack("<i", 20)
        + (struct.pack("<i", 16) + value + struct.pack("<i", 16))
    )


def _nnkp_payload(excluded_bands: str = "0") -> bytes:
    reciprocal = 2.0 * math.pi / _BOHR_TO_ANGSTROM
    return f"""generated interface
begin real_lattice
{_BOHR_TO_ANGSTROM} 0 0
0 {_BOHR_TO_ANGSTROM} 0
0 0 {_BOHR_TO_ANGSTROM}
end real_lattice
begin recip_lattice
{reciprocal} 0 0
0 {reciprocal} 0
0 0 {reciprocal}
end recip_lattice
begin kpoints
1
0 0 0
end kpoints
begin projections
0
end projections
begin nnkpts
1
1 1 0 0 0
end nnkpts
begin exclude_bands
{excluded_bands}
end exclude_bands
""".encode()


def _manifest(unk_payload: bytes) -> QeWannier90PlaneWaveArtifactManifest:
    return QeWannier90PlaneWaveArtifactManifest(
        schema_version=1,
        run_id="production-run",
        qe_prefix="si",
        seedname="silicon",
        kpoint_count=1,
        band_count=1,
        wannier_count=1,
        spin_channel_count=1,
        selected_spin_channel_index=1,
        spinor_component_count=1,
        post_nscf_state_manifest=_binding(
            QeWannier90ProviderArtifactRole.post_nscf_state_manifest,
            "manifests/post-nscf.tsv",
        ),
        qexsd=QeWannier90ProviderArtifact(
            QeWannier90ProviderArtifactRole.qexsd,
            "work/qe/si.save/data-file-schema.xml",
            "0" * 64,
            123,
        ),
        pseudopotentials=(
            QeWannier90ProviderArtifact(
                QeWannier90ProviderArtifactRole.pseudopotential,
                "pseudo/Si.UPF",
                "1" * 64,
                100,
            ),
        ),
        wannier_input=_binding(
            QeWannier90ProviderArtifactRole.wannier_input,
            "inputs/derived/silicon.win",
        ),
        neighbor_interface=_binding(
            QeWannier90ProviderArtifactRole.neighbor_interface,
            "artifacts/wannier90/preprocess/silicon.nnkp",
            payload=_nnkp_payload(),
        ),
        unks=(
            _binding(
                QeWannier90ProviderArtifactRole.unk,
                "work/qe/UNK00001.1",
                payload=unk_payload,
                kpoint_index=1,
                spin_channel_index=1,
            ),
        ),
        eigenvalues=_binding(
            QeWannier90ProviderArtifactRole.eigenvalues,
            "work/qe/silicon.eig",
            payload=_EIGENVALUE_PAYLOAD,
        ),
        gauge_matrix=_binding(
            QeWannier90ProviderArtifactRole.gauge_matrix,
            "work/qe/silicon_u.mat",
            payload=_GAUGE_PAYLOAD,
        ),
        disentanglement_matrix=_binding(
            QeWannier90ProviderArtifactRole.disentanglement_matrix,
            "work/qe/silicon_u_dis.mat",
            payload=_DISENTANGLEMENT_PAYLOAD,
        ),
        hamiltonian=_binding(
            QeWannier90ProviderArtifactRole.hamiltonian,
            "artifacts/wannier90/localization/silicon_hr.dat",
            payload=_HAMILTONIAN_PAYLOAD,
        ),
    )


def test_correlates_qexsd_nnkp_and_all_ordered_native_indices() -> None:
    pseudo = _pseudo()
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=(pseudo,),
        overlap_metric=QeWavefunctionOverlapMetric.identity,
        spin_channel_count=1,
        spinor_component_count=1,
    )
    unk_payload = _unk_payload()
    manifest = _manifest(unk_payload)
    unk = QeWannier90UnkParser().execute(
        manifest.unks[0],
        unk_payload,
        expected_grid_shape=(1, 1, 1),
        expected_band_count=1,
        expected_spinor_component_count=1,
    )
    parser = QeWannier90AuthenticatedParser()
    gauge = parser.parse_gauge_matrix(manifest.gauge_matrix, _GAUGE_PAYLOAD)
    disentanglement = parser.parse_disentanglement_matrix(
        manifest.disentanglement_matrix, _DISENTANGLEMENT_PAYLOAD
    )
    eigenvalues = parser.parse_eigenvalues(
        manifest.eigenvalues, _EIGENVALUE_PAYLOAD, PhysicalUnit("eV")
    )

    QeWannier90ProviderCorrelationValidator().execute(
        manifest=manifest,
        frame=frame,
        nnkp=parser.parse_nnkp(manifest.neighbor_interface, _nnkp_payload()),
        eigenvalues=eigenvalues,
        gauge=gauge,
        disentanglement=disentanglement,
        hamiltonian=parser.parse_hamiltonian(
            manifest.hamiltonian, _HAMILTONIAN_PAYLOAD, PhysicalUnit("eV")
        ),
        unks=(unk,),
    )


def test_rejects_u_matrix_kpoint_not_matching_nnkp() -> None:
    pseudo = _pseudo()
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=(pseudo,),
        overlap_metric=QeWavefunctionOverlapMetric.identity,
        spin_channel_count=1,
        spinor_component_count=1,
    )
    unk_payload = _unk_payload()
    manifest = _manifest(unk_payload)
    wrong_gauge_payload = b"gauge\n1 1 1\n0.25 0 0\n1 0\n"
    manifest = replace(
        manifest,
        gauge_matrix=_binding(
            QeWannier90ProviderArtifactRole.gauge_matrix,
            "work/qe/silicon_u.mat",
            payload=wrong_gauge_payload,
        ),
    )
    unk = QeWannier90UnkParser().execute(
        manifest.unks[0],
        unk_payload,
        expected_grid_shape=(1, 1, 1),
        expected_band_count=1,
        expected_spinor_component_count=1,
    )
    parser = QeWannier90AuthenticatedParser()
    wrong_gauge = parser.parse_gauge_matrix(manifest.gauge_matrix, wrong_gauge_payload)

    with pytest.raises(ValueError, match="u.mat ordered k-points"):
        QeWannier90ProviderCorrelationValidator().execute(
            manifest=manifest,
            frame=frame,
            nnkp=parser.parse_nnkp(manifest.neighbor_interface, _nnkp_payload()),
            eigenvalues=parser.parse_eigenvalues(
                manifest.eigenvalues, _EIGENVALUE_PAYLOAD, PhysicalUnit("eV")
            ),
            gauge=wrong_gauge,
            disentanglement=parser.parse_disentanglement_matrix(
                manifest.disentanglement_matrix, _DISENTANGLEMENT_PAYLOAD
            ),
            hamiltonian=parser.parse_hamiltonian(
                manifest.hamiltonian, _HAMILTONIAN_PAYLOAD, PhysicalUnit("eV")
            ),
            unks=(unk,),
        )


def test_rejects_hamiltonian_wannier_dimension_mismatch() -> None:
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=(_pseudo(),),
        overlap_metric=QeWavefunctionOverlapMetric.identity,
        spin_channel_count=1,
        spinor_component_count=1,
    )
    wrong_hamiltonian_payload = (
        b"hr\n2\n1\n1\n"
        b"0 0 0 1 1 0.0 0.0\n"
        b"0 0 0 1 2 0.0 0.0\n"
        b"0 0 0 2 1 0.0 0.0\n"
        b"0 0 0 2 2 0.0 0.0\n"
    )
    unk_payload = _unk_payload()
    manifest = replace(
        _manifest(unk_payload),
        hamiltonian=_binding(
            QeWannier90ProviderArtifactRole.hamiltonian,
            "artifacts/wannier90/localization/silicon_hr.dat",
            payload=wrong_hamiltonian_payload,
        ),
    )
    parser = QeWannier90AuthenticatedParser()
    unk = QeWannier90UnkParser().execute(
        manifest.unks[0],
        unk_payload,
        expected_grid_shape=(1, 1, 1),
        expected_band_count=1,
        expected_spinor_component_count=1,
    )

    with pytest.raises(ValueError, match="Wannier counts disagree"):
        QeWannier90ProviderCorrelationValidator().execute(
            manifest=manifest,
            frame=frame,
            nnkp=parser.parse_nnkp(manifest.neighbor_interface, _nnkp_payload()),
            eigenvalues=parser.parse_eigenvalues(
                manifest.eigenvalues, _EIGENVALUE_PAYLOAD, PhysicalUnit("eV")
            ),
            gauge=parser.parse_gauge_matrix(manifest.gauge_matrix, _GAUGE_PAYLOAD),
            disentanglement=parser.parse_disentanglement_matrix(
                manifest.disentanglement_matrix, _DISENTANGLEMENT_PAYLOAD
            ),
            hamiltonian=parser.parse_hamiltonian(
                manifest.hamiltonian,
                wrong_hamiltonian_payload,
                PhysicalUnit("eV"),
            ),
            unks=(unk,),
        )


def test_authenticated_data_cannot_be_constructed_directly() -> None:
    with pytest.raises(TypeError):
        QeWannier90AuthenticatedData()


def test_authenticated_parser_rejects_substituted_matrix_bytes() -> None:
    manifest = _manifest(_unk_payload())

    with pytest.raises(ValueError, match="mismatch"):
        QeWannier90AuthenticatedParser().parse_gauge_matrix(
            manifest.gauge_matrix,
            b"gauge\n1 1 1\n0.5 0 0\n1 0\n",
        )


def test_correlation_rejects_frame_manifest_spinor_mismatch() -> None:
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=(_pseudo(),),
        overlap_metric=QeWavefunctionOverlapMetric.identity,
        spin_channel_count=1,
        spinor_component_count=2,
    )
    unk_payload = _unk_payload()
    manifest = _manifest(unk_payload)
    parser = QeWannier90AuthenticatedParser()
    unk = QeWannier90UnkParser().execute(
        manifest.unks[0],
        unk_payload,
        expected_grid_shape=(1, 1, 1),
        expected_band_count=1,
        expected_spinor_component_count=1,
    )

    with pytest.raises(ValueError, match="spinor-component counts"):
        QeWannier90ProviderCorrelationValidator().execute(
            manifest=manifest,
            frame=frame,
            nnkp=parser.parse_nnkp(manifest.neighbor_interface, _nnkp_payload()),
            eigenvalues=parser.parse_eigenvalues(
                manifest.eigenvalues, _EIGENVALUE_PAYLOAD, PhysicalUnit("eV")
            ),
            gauge=parser.parse_gauge_matrix(manifest.gauge_matrix, _GAUGE_PAYLOAD),
            disentanglement=parser.parse_disentanglement_matrix(
                manifest.disentanglement_matrix, _DISENTANGLEMENT_PAYLOAD
            ),
            hamiltonian=parser.parse_hamiltonian(
                manifest.hamiltonian, _HAMILTONIAN_PAYLOAD, PhysicalUnit("eV")
            ),
            unks=(unk,),
        )


def test_correlation_fails_closed_on_excluded_band_mapping() -> None:
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=(_pseudo(),),
        overlap_metric=QeWavefunctionOverlapMetric.identity,
        spin_channel_count=1,
        spinor_component_count=1,
    )
    unk_payload = _unk_payload()
    excluded_nnkp = _nnkp_payload("1\n1")
    manifest = _manifest(unk_payload)
    manifest = replace(
        manifest,
        neighbor_interface=_binding(
            QeWannier90ProviderArtifactRole.neighbor_interface,
            "artifacts/wannier90/preprocess/silicon.nnkp",
            payload=excluded_nnkp,
        ),
    )
    parser = QeWannier90AuthenticatedParser()
    unk = QeWannier90UnkParser().execute(
        manifest.unks[0],
        unk_payload,
        expected_grid_shape=(1, 1, 1),
        expected_band_count=1,
        expected_spinor_component_count=1,
    )

    with pytest.raises(ValueError, match="excluded-band mappings"):
        QeWannier90ProviderCorrelationValidator().execute(
            manifest=manifest,
            frame=frame,
            nnkp=parser.parse_nnkp(manifest.neighbor_interface, excluded_nnkp),
            eigenvalues=parser.parse_eigenvalues(
                manifest.eigenvalues, _EIGENVALUE_PAYLOAD, PhysicalUnit("eV")
            ),
            gauge=parser.parse_gauge_matrix(manifest.gauge_matrix, _GAUGE_PAYLOAD),
            disentanglement=parser.parse_disentanglement_matrix(
                manifest.disentanglement_matrix, _DISENTANGLEMENT_PAYLOAD
            ),
            hamiltonian=parser.parse_hamiltonian(
                manifest.hamiltonian, _HAMILTONIAN_PAYLOAD, PhysicalUnit("eV")
            ),
            unks=(unk,),
        )
