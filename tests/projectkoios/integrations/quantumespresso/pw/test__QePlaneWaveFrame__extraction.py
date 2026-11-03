from __future__ import annotations

import math

import pytest

from projectkoios.integrations.quantumespresso.pseudopotential import (
    QePseudopotential,
    QePseudopotentialFile,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction import (
    QePlaneWaveFrame,
    QePlaneWaveFrameExtractor,
    QeWavefunctionOverlapMetric,
    QexsdData,
)
from tests.projectkoios.integrations.quantumespresso.resources.qexsd_fixtures import (
    QEXSD_FIXTURES,
)

_PLANE_WAVE_FRAME_EXTRACTOR = QePlaneWaveFrameExtractor(
    duality_absolute_tolerance=1.0e-10,
    kpoint_reconstruction_tolerance=1.0e-12,
)


class TestQePlaneWaveFrame:
    def _ultrasoft(
        self,
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

    def test__QePlaneWaveFrame__frame_cannot_be_constructed_without_the_qexsd_extractor(
        self,
    ) -> None:
        with pytest.raises(TypeError):
            QePlaneWaveFrame()

    def test__QePlaneWaveFrame__extracts_qexsd_frame_and_evaluates_kinetic_diagonal(
        self,
    ) -> None:
        frame = _PLANE_WAVE_FRAME_EXTRACTOR.extract(
            QexsdData.from_document(QEXSD_FIXTURES.plane_wave_frame_document()),
            pseudopotentials=self._ultrasoft(),
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
    def test__QePlaneWaveFrame__rejects_identity_metric_for_ultrasoft_upf(
        self, formalism: str
    ) -> None:
        with pytest.raises(ValueError, match="identity overlap"):
            _PLANE_WAVE_FRAME_EXTRACTOR.extract(
                QexsdData.from_document(QEXSD_FIXTURES.plane_wave_frame_document()),
                pseudopotentials=self._ultrasoft(formalism),
                overlap_metric=QeWavefunctionOverlapMetric.identity,
                spin_channel_count=1,
                spinor_component_count=1,
            )

    def test__QePlaneWaveFrame__rejects_unknown_pseudopotential_formalism(self) -> None:
        with pytest.raises(
            ValueError, match="unsupported QE pseudopotential formalism"
        ):
            _PLANE_WAVE_FRAME_EXTRACTOR.extract(
                QexsdData.from_document(QEXSD_FIXTURES.plane_wave_frame_document()),
                pseudopotentials=self._ultrasoft("mystery"),
                overlap_metric=QeWavefunctionOverlapMetric.identity,
                spin_channel_count=1,
                spinor_component_count=1,
            )

    def test__QePlaneWaveFrame__rejects_upf_label_not_bound_by_qexsd(self) -> None:
        wrong = self._ultrasoft()[0]
        wrong = QePseudopotentialFile(
            pseudopotential=wrong.pseudopotential,
            filename="other.UPF",
            sha256=wrong.sha256,
            byte_size=wrong.byte_size,
        )

        with pytest.raises(ValueError, match="labels disagree"):
            _PLANE_WAVE_FRAME_EXTRACTOR.extract(
                QexsdData.from_document(QEXSD_FIXTURES.plane_wave_frame_document()),
                pseudopotentials=(wrong,),
                overlap_metric=QeWavefunctionOverlapMetric.ultrasoft_generalized,
                spin_channel_count=1,
                spinor_component_count=1,
            )
