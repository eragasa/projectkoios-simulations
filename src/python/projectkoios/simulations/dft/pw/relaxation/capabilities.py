"""Reviewed descriptions for calculator-selectable relaxation integrations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from projectkoios.simulations.calculator import CalculatorIntegrationId
from projectkoios.simulations.dft.pw.relaxation.base import (
    PwDftRelaxationScope,
)


class _PwDftRelaxationDescriptionValidation:
    """Own lexical validation shared by reviewed descriptions."""

    __slots__ = ()

    @staticmethod
    def text(value: str, label: str) -> None:
        if type(value) is not str or not value or value != value.strip():
            raise ValueError(f"{label} must be nonempty and stripped")


class PwDftRelaxationInputModel(StrEnum):
    """Identify each backend's native input organization."""

    QE_PW_NAMELISTS_AND_CARDS = "qe-pw-namelists-and-cards"
    VASP_NATIVE_FILES = "vasp-native-files"
    ABINIT_DATASETS_AND_VARIABLES = "abinit-datasets-and-variables"


class PwDftRelaxationImplementationStatus(StrEnum):
    """Distinguish usable integrations from described future integrations."""

    INPUT_PROJECTION_IMPLEMENTED = "input-projection-implemented"
    DESCRIBED_NOT_IMPLEMENTED = "described-not-implemented"


@dataclass(frozen=True, slots=True)
class PwDftRelaxationScopeDescription:
    """Describe one generic scope without claiming backend algorithm equivalence."""

    scope: PwDftRelaxationScope
    purpose: str
    qualification: str

    def __post_init__(self) -> None:
        if type(self.scope) is not PwDftRelaxationScope:
            raise TypeError("scope must be a PwDftRelaxationScope")
        _PwDftRelaxationDescriptionValidation.text(self.purpose, "purpose")
        _PwDftRelaxationDescriptionValidation.text(self.qualification, "qualification")


@dataclass(frozen=True, slots=True)
class PwDftRelaxationBackendDescription:
    """Describe a selectable backend and the native input family it owns."""

    integration_id: CalculatorIntegrationId
    display_name: str
    input_model: PwDftRelaxationInputModel
    status: PwDftRelaxationImplementationStatus
    supported_scopes: tuple[PwDftRelaxationScope, ...]
    authority_urls: tuple[str, ...]
    qualification: str

    def __post_init__(self) -> None:
        if type(self.integration_id) is not CalculatorIntegrationId:
            raise TypeError("integration_id must be a CalculatorIntegrationId")
        _PwDftRelaxationDescriptionValidation.text(self.display_name, "display_name")
        if type(self.input_model) is not PwDftRelaxationInputModel:
            raise TypeError("input_model must be a PwDftRelaxationInputModel")
        if type(self.status) is not PwDftRelaxationImplementationStatus:
            raise TypeError("status must be a PwDftRelaxationImplementationStatus")
        if not self.supported_scopes or len(set(self.supported_scopes)) != len(
            self.supported_scopes
        ):
            raise ValueError("supported_scopes must be nonempty and unique")
        if any(
            type(scope) is not PwDftRelaxationScope for scope in self.supported_scopes
        ):
            raise TypeError("supported_scopes must contain PwDftRelaxationScope values")
        if not self.authority_urls or any(
            type(url) is not str or not url.startswith("https://")
            for url in self.authority_urls
        ):
            raise ValueError("authority_urls must contain HTTPS URLs")
        _PwDftRelaxationDescriptionValidation.text(self.qualification, "qualification")


PW_DFT_RELAXATION_SCOPE_DESCRIPTIONS = (
    PwDftRelaxationScopeDescription(
        scope=PwDftRelaxationScope.ATOMIC_POSITIONS,
        purpose="Relax atomic positions while retaining the declared cell.",
        qualification=(
            "The backend chooses a native optimizer through its own typed input; "
            "the generic scope does not imply algorithm equivalence."
        ),
    ),
    PwDftRelaxationScopeDescription(
        scope=PwDftRelaxationScope.ATOMIC_POSITIONS_AND_CELL,
        purpose="Relax atomic positions and backend-declared cell degrees of freedom.",
        qualification=(
            "Cell degrees of freedom require a native declaration and may not map "
            "one-to-one between QE, VASP, and ABINIT."
        ),
    ),
)

PW_DFT_RELAXATION_BACKEND_DESCRIPTIONS = (
    PwDftRelaxationBackendDescription(
        integration_id=CalculatorIntegrationId("quantum-espresso"),
        display_name="Quantum ESPRESSO pw.x",
        input_model=PwDftRelaxationInputModel.QE_PW_NAMELISTS_AND_CARDS,
        status=(PwDftRelaxationImplementationStatus.INPUT_PROJECTION_IMPLEMENTED),
        supported_scopes=tuple(PwDftRelaxationScope),
        authority_urls=("https://www.quantum-espresso.org/Doc/INPUT_PW.html",),
        qualification=(
            "Projection uses typed CONTROL, SYSTEM, ELECTRONS, IONS, and CELL "
            "namelists plus QE data cards."
        ),
    ),
    PwDftRelaxationBackendDescription(
        integration_id=CalculatorIntegrationId("vasp"),
        display_name="VASP",
        input_model=PwDftRelaxationInputModel.VASP_NATIVE_FILES,
        status=PwDftRelaxationImplementationStatus.DESCRIBED_NOT_IMPLEMENTED,
        supported_scopes=tuple(PwDftRelaxationScope),
        authority_urls=(
            "https://vasp.at/wiki/IBRION",
            "https://vasp.at/wiki/ISIF",
        ),
        qualification=(
            "A future integration must compose INCAR, KPOINTS, POSCAR, and runtime "
            "state; QE variable names are not reused."
        ),
    ),
    PwDftRelaxationBackendDescription(
        integration_id=CalculatorIntegrationId("abinit"),
        display_name="ABINIT",
        input_model=PwDftRelaxationInputModel.ABINIT_DATASETS_AND_VARIABLES,
        status=PwDftRelaxationImplementationStatus.DESCRIBED_NOT_IMPLEMENTED,
        supported_scopes=tuple(PwDftRelaxationScope),
        authority_urls=("https://docs.abinit.org/variables/",),
        qualification=(
            "A future integration must own ABINIT datasets and input variables; QE "
            "cards and VASP tags are not treated as ABINIT declarations."
        ),
    ),
)
