from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction import (
    QePlaneWaveFrame,
    QePlaneWaveFrameExtractor,
    QeQexsdData,
    QeWavefunctionOverlapMetric,
)


def _qexsd() -> QeQexsdData:
    document = SimpleNamespace(
        source_path="/test/data-file-schema.xml",
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
        species=(("Si", 28.0855, "Si.pbe-n-van.UPF"),),
        atoms=((1, "Si", (0.0, 0.0, 0.0)),),
        declared_atom_count=1,
        atomic_positions_source_label="output/atomic_structure/atomic_positions",
        k_points=((0.25, 0.0, 0.0),),
        k_point_source_label="output/band_structure/ks_energies/k_point",
        sampled_k_point_count=1,
        band_count=12,
        fft_grid=(4, 4, 4),
        exit_status=0,
    )
    return QeQexsdData.from_document(document)


def _ultrasoft(
    formalism: str = "ultrasoft",
) -> tuple[QePseudopotentialFile, ...]:
    return (
        QePseudopotentialFile(
            pseudopotential=QePseudopotential(
                symbol="Si",
                exchange_correlation="PBE",
                formalism=formalism,
                relativistic_treatment="scalar-relativistic",
                valence_electrons=4,
                upf_version="2.0.1",
            ),
            filename="Si.pbe-n-van.UPF",
            sha256="1" * 64,
            byte_size=100,
        ),
    )


def test_frame_cannot_be_constructed_without_the_qexsd_extractor() -> None:
    with pytest.raises(TypeError):
        QePlaneWaveFrame()


def test_extracts_qexsd_frame_and_evaluates_kinetic_diagonal() -> None:
    frame = QePlaneWaveFrameExtractor().extract(
        _qexsd(),
        pseudopotentials=_ultrasoft(),
        overlap_metric=QeWavefunctionOverlapMetric.ultrasoft_generalized,
        spin_channel_count=1,
        spinor_component_count=1,
    )

    assert frame.kpoints_reduced == ((0.25, 0.0, 0.0),)
    assert frame.g_reduced((0, 0, 0)) == (0, 0, 0)
    assert frame.g_reduced((3, 0, 0)) == (-1, 0, 0)
    with pytest.raises(ValueError, match="Nyquist"):
        frame.g_reduced((2, 0, 0))
    assert frame.linear_grid_index((2, 0, 0)) == 2
    assert frame.linear_grid_index((1, 1, 3)) == 53
    assert frame.kinetic_energy_hartree(0, (0, 0, 0)) == pytest.approx(
        0.5 * (0.5 * math.pi) ** 2
    )


@pytest.mark.parametrize("formalism", ["ultrasoft", "USPP", "ultra-soft"])
def test_rejects_identity_metric_for_ultrasoft_upf(formalism: str) -> None:
    with pytest.raises(ValueError, match="identity overlap"):
        QePlaneWaveFrameExtractor().extract(
            _qexsd(),
            pseudopotentials=_ultrasoft(formalism),
            overlap_metric=QeWavefunctionOverlapMetric.identity,
            spin_channel_count=1,
            spinor_component_count=1,
        )


def test_rejects_unknown_pseudopotential_formalism() -> None:
    with pytest.raises(ValueError, match="unsupported QE pseudopotential formalism"):
        QePlaneWaveFrameExtractor().extract(
            _qexsd(),
            pseudopotentials=_ultrasoft("mystery"),
            overlap_metric=QeWavefunctionOverlapMetric.identity,
            spin_channel_count=1,
            spinor_component_count=1,
        )


def test_rejects_upf_label_not_bound_by_qexsd() -> None:
    wrong = _ultrasoft()[0]
    wrong = QePseudopotentialFile(
        pseudopotential=wrong.pseudopotential,
        filename="other.UPF",
        sha256=wrong.sha256,
        byte_size=wrong.byte_size,
    )

    with pytest.raises(ValueError, match="labels disagree"):
        QePlaneWaveFrameExtractor().extract(
            _qexsd(),
            pseudopotentials=(wrong,),
            overlap_metric=QeWavefunctionOverlapMetric.ultrasoft_generalized,
            spin_channel_count=1,
            spinor_component_count=1,
        )
