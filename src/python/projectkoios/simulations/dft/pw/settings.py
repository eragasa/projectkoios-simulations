"""Calculator-neutral plane-wave DFT settings and alignment registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CalculationType(StrEnum):
    """Enumerate calculator-neutral plane-wave calculation modes."""

    scf = "scf"
    nscf = "nscf"
    bands = "bands"
    relax = "relax"
    md = "md"
    vc_relax = "vc-relax"
    vc_md = "vc-md"


class AlignmentKind(StrEnum):
    """Classify the fidelity of one calculator projection."""

    exact = "exact"
    unit_convertible = "unit-convertible"
    conditional = "conditional"
    approximate = "approximate"
    unsupported = "unsupported"


class PwDftTag(StrEnum):
    """Name calculator-neutral plane-wave DFT settings."""

    calculation_type = "calculation-type"
    wavefunction_cutoff = "wavefunction-cutoff"
    scf_tolerance = "scf-tolerance"
    occupation_method = "occupation-method"
    smearing_width = "smearing-width"
    spin_treatment = "spin-treatment"
    exchange_correlation = "exchange-correlation"
    unit_cell = "unit-cell"
    k_points = "k-points"


@dataclass(frozen=True, slots=True)
class TagAlignment:
    """Record QE and VASP projections for one calculator-neutral setting."""

    tag: PwDftTag
    qe_fields: tuple[str, ...]
    vasp_fields: tuple[str, ...]
    qe_alignment: AlignmentKind
    vasp_alignment: AlignmentKind
    qualification: str

    def __post_init__(self) -> None:
        if type(self.tag) is not PwDftTag:
            raise TypeError("tag must be a PwDftTag")
        for label, fields in (
            ("qe_fields", self.qe_fields),
            ("vasp_fields", self.vasp_fields),
        ):
            if type(fields) is not tuple or not fields:
                raise ValueError(f"{label} must be a nonempty tuple")
            if any(type(field) is not str or not field for field in fields):
                raise ValueError(f"{label} must contain nonempty strings")
        if type(self.qe_alignment) is not AlignmentKind:
            raise TypeError("qe_alignment must be an AlignmentKind")
        if type(self.vasp_alignment) is not AlignmentKind:
            raise TypeError("vasp_alignment must be an AlignmentKind")
        if (
            type(self.qualification) is not str
            or not self.qualification
            or self.qualification != self.qualification.strip()
        ):
            raise ValueError("qualification must be nonempty and stripped")


@dataclass(frozen=True, slots=True)
class PwDftSettings:
    """Hold calculator-neutral settings selected once for later projection."""

    calculation_type: CalculationType

    def __post_init__(self) -> None:
        if type(self.calculation_type) is not CalculationType:
            raise TypeError("calculation_type must be a CalculationType")


PW_DFT_TAG_ALIGNMENT_REGISTRY = (
    TagAlignment(
        tag=PwDftTag.calculation_type,
        qe_fields=("&CONTROL.calculation",),
        vasp_fields=(
            "INCAR.IBRION",
            "INCAR.NSW",
            "INCAR.ISIF",
            "INCAR.ICHARG",
            "KPOINTS",
            "run-state",
        ),
        qe_alignment=AlignmentKind.exact,
        vasp_alignment=AlignmentKind.conditional,
        qualification=(
            "VASP run type is determined by multiple tags, KPOINTS, and prior-run "
            "artifacts rather than one INCAR tag."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.wavefunction_cutoff,
        qe_fields=("&SYSTEM.ecutwfc",),
        vasp_fields=("INCAR.ENCUT",),
        qe_alignment=AlignmentKind.unit_convertible,
        vasp_alignment=AlignmentKind.unit_convertible,
        qualification=(
            "Energy units convert mechanically, but pseudopotential cutoff "
            "recommendations remain calculator-specific."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.scf_tolerance,
        qe_fields=("&ELECTRONS.conv_thr",),
        vasp_fields=("INCAR.EDIFF",),
        qe_alignment=AlignmentKind.approximate,
        vasp_alignment=AlignmentKind.approximate,
        qualification=(
            "The codes apply differently defined convergence criteria; equal energy "
            "values do not establish equal convergence behavior."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.occupation_method,
        qe_fields=("&SYSTEM.occupations", "&SYSTEM.smearing"),
        vasp_fields=("INCAR.ISMEAR",),
        qe_alignment=AlignmentKind.conditional,
        vasp_alignment=AlignmentKind.conditional,
        qualification=(
            "Supported occupation and smearing families do not map one-to-one."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.smearing_width,
        qe_fields=("&SYSTEM.degauss",),
        vasp_fields=("INCAR.SIGMA",),
        qe_alignment=AlignmentKind.unit_convertible,
        vasp_alignment=AlignmentKind.unit_convertible,
        qualification=(
            "Width units convert mechanically only after selecting compatible "
            "occupation methods."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.spin_treatment,
        qe_fields=("&SYSTEM.nspin", "&SYSTEM.noncolin", "&SYSTEM.lspinorb"),
        vasp_fields=("INCAR.ISPIN", "INCAR.LNONCOLLINEAR", "INCAR.LSORBIT"),
        qe_alignment=AlignmentKind.conditional,
        vasp_alignment=AlignmentKind.conditional,
        qualification=(
            "Collinear, noncollinear, and spin-orbit modes require joint tags."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.exchange_correlation,
        qe_fields=("&SYSTEM.input_dft",),
        vasp_fields=(
            "INCAR.GGA",
            "INCAR.METAGGA",
            "INCAR.LHFCALC",
            "POTCAR",
        ),
        qe_alignment=AlignmentKind.conditional,
        vasp_alignment=AlignmentKind.conditional,
        qualification=(
            "Functional selection must remain compatible with the chosen "
            "pseudopotentials and calculator implementation."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.unit_cell,
        qe_fields=("CELL_PARAMETERS", "ATOMIC_POSITIONS"),
        vasp_fields=("POSCAR",),
        qe_alignment=AlignmentKind.unit_convertible,
        vasp_alignment=AlignmentKind.unit_convertible,
        qualification=(
            "Both projections share one UnitCell, but coordinate and lattice units "
            "must be rendered explicitly."
        ),
    ),
    TagAlignment(
        tag=PwDftTag.k_points,
        qe_fields=("K_POINTS",),
        vasp_fields=("KPOINTS",),
        qe_alignment=AlignmentKind.conditional,
        vasp_alignment=AlignmentKind.conditional,
        qualification=(
            "Mesh, shifts, paths, weights, and symmetry treatment require a shared "
            "k-point policy rather than tag-name substitution."
        ),
    ),
)
