"""Qualified VASP ``IBRION`` and Quantum ESPRESSO workflow alignments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from projectkoios.simulations.dft.pw.settings import AlignmentKind

_VASP_IBRION_AUTHORITY = "https://vasp.at/wiki/IBRION"
_VASP_NEB_AUTHORITY = "https://vasp.at/wiki/Nudged_elastic_bands"
_QE_PW_AUTHORITY = "https://www.quantum-espresso.org/Doc/INPUT_PW.html#id1"
_QE_NEB_AUTHORITY = "https://www.quantum-espresso.org/Doc/INPUT_NEB.html"


class VaspIbrion(IntEnum):
    """Represent every value listed by the official VASP ``IBRION`` page."""

    no_update = -1
    molecular_dynamics = 0
    rmm_diis = 1
    conjugate_gradient = 2
    damped_molecular_dynamics = 3
    finite_differences_without_symmetry = 5
    finite_differences_with_symmetry = 6
    perturbation_theory_without_symmetry = 7
    perturbation_theory_with_symmetry = 8
    interactive_standard_input = 11
    interactive_python_plugin = 12
    intrinsic_reaction_coordinate = 40
    improved_dimer_method = 44


@dataclass(frozen=True, slots=True)
class VaspIbrionAlignment:
    """Record one qualified VASP ``IBRION`` to QE workflow comparison."""

    ibrion: VaspIbrion
    purpose: str
    qe_executable: str | None
    qe_fields: tuple[str, ...]
    alignment: AlignmentKind
    algorithm_equivalent: bool
    qualification: str

    def __post_init__(self) -> None:
        if type(self.ibrion) is not VaspIbrion:
            raise TypeError("ibrion must be a VaspIbrion")
        for label, value in (
            ("purpose", self.purpose),
            ("qualification", self.qualification),
        ):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError(f"{label} must be nonempty and stripped")
        if self.qe_executable is not None and (
            type(self.qe_executable) is not str
            or not self.qe_executable
            or self.qe_executable != self.qe_executable.strip()
        ):
            raise ValueError("qe_executable must be stripped and nonempty or None")
        if type(self.qe_fields) is not tuple:
            raise TypeError("qe_fields must be a tuple")
        if any(type(field) is not str or not field for field in self.qe_fields):
            raise ValueError("qe_fields must contain nonempty strings")
        if type(self.alignment) is not AlignmentKind:
            raise TypeError("alignment must be an AlignmentKind")
        if type(self.algorithm_equivalent) is not bool:
            raise TypeError("algorithm_equivalent must be a bool")


@dataclass(frozen=True, slots=True)
class VaspNebAlignment:
    """Record the workflow-level VASP NEB to QE ``neb.x`` alignment."""

    vasp_fields: tuple[str, ...]
    qe_executable: str
    qe_fields: tuple[str, ...]
    alignment: AlignmentKind
    qualification: str

    def __post_init__(self) -> None:
        for label, fields in (
            ("vasp_fields", self.vasp_fields),
            ("qe_fields", self.qe_fields),
        ):
            if type(fields) is not tuple or not fields:
                raise ValueError(f"{label} must be a nonempty tuple")
            if any(type(field) is not str or not field for field in fields):
                raise ValueError(f"{label} must contain nonempty strings")
        if (
            type(self.qe_executable) is not str
            or not self.qe_executable
            or self.qe_executable != self.qe_executable.strip()
        ):
            raise ValueError("qe_executable must be nonempty and stripped")
        if type(self.alignment) is not AlignmentKind:
            raise TypeError("alignment must be an AlignmentKind")
        if (
            type(self.qualification) is not str
            or not self.qualification
            or self.qualification != self.qualification.strip()
        ):
            raise ValueError("qualification must be nonempty and stripped")


VASP_IBRION_ALIGNMENT_REGISTRY = (
    VaspIbrionAlignment(
        ibrion=VaspIbrion.no_update,
        purpose="Fixed ions and fixed cell",
        qe_executable="pw.x",
        qe_fields=(
            "calculation='scf'",
            "calculation='nscf'",
            "calculation='bands'",
        ),
        alignment=AlignmentKind.conditional,
        algorithm_equivalent=True,
        qualification=(
            "The QE calculation value selects the electronic workflow; fixed ionic "
            "geometry follows because no ionic or cell dynamics is requested."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.molecular_dynamics,
        purpose="Molecular dynamics",
        qe_executable="pw.x",
        qe_fields=("calculation='md'", "&IONS.ion_dynamics"),
        alignment=AlignmentKind.conditional,
        algorithm_equivalent=False,
        qualification=(
            "Both codes support molecular dynamics, but integrator, thermostat, time "
            "step, duration, and ensemble require independent explicit policy."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.rmm_diis,
        purpose="RMM-DIIS structural optimization",
        qe_executable="pw.x",
        qe_fields=("calculation='relax'", "ion_dynamics='bfgs'"),
        alignment=AlignmentKind.unsupported,
        algorithm_equivalent=False,
        qualification=(
            "QE 7.5 exposes BFGS, damped dynamics, and FIRE for relaxation but no "
            "direct RMM-DIIS ionic optimizer. BFGS is a different algorithm."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.conjugate_gradient,
        purpose="Conjugate-gradient structural optimization",
        qe_executable="pw.x",
        qe_fields=(
            "calculation='relax'",
            "ion_dynamics='bfgs'|'damp'|'fire'",
        ),
        alignment=AlignmentKind.approximate,
        algorithm_equivalent=False,
        qualification=(
            "QE 7.5 does not document ion_dynamics='cg'. Its BFGS, damped, or FIRE "
            "relaxation routes may serve the same scientific purpose but are not the "
            "same optimizer."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.damped_molecular_dynamics,
        purpose="Damped-dynamics structural optimization",
        qe_executable="pw.x",
        qe_fields=(
            "calculation='relax'",
            "ion_dynamics='damp'",
            "cell_dynamics='damp-pr'|'damp-w' for vc-relax",
        ),
        alignment=AlignmentKind.conditional,
        algorithm_equivalent=False,
        qualification=(
            "QE supports damped ionic relaxation, but its implementation and the "
            "separate variable-cell dynamics choices are not identical to VASP."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.finite_differences_without_symmetry,
        purpose="Finite-difference phonons without symmetry",
        qe_executable="ph.x",
        qe_fields=("SCF reference", "ph.x q-point input"),
        alignment=AlignmentKind.approximate,
        algorithm_equivalent=False,
        qualification=(
            "The standard QE phonon workflow uses density-functional perturbation "
            "theory rather than VASP's finite-difference IBRION=5 algorithm."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.finite_differences_with_symmetry,
        purpose="Finite-difference phonons with symmetry",
        qe_executable="ph.x",
        qe_fields=("SCF reference", "ph.x q-point input"),
        alignment=AlignmentKind.approximate,
        algorithm_equivalent=False,
        qualification=(
            "QE ph.x uses symmetry-aware DFPT, which targets phonons but is not the "
            "same finite-difference algorithm as VASP IBRION=6."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.perturbation_theory_without_symmetry,
        purpose="DFPT phonons without symmetry",
        qe_executable="ph.x",
        qe_fields=("SCF reference", "ph.x q-point input", "symmetry policy"),
        alignment=AlignmentKind.conditional,
        algorithm_equivalent=True,
        qualification=(
            "Both routes use perturbation theory, but symmetry disabling, q-point "
            "sampling, outputs, and convergence controls remain code-specific."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.perturbation_theory_with_symmetry,
        purpose="DFPT phonons with symmetry",
        qe_executable="ph.x",
        qe_fields=("SCF reference", "ph.x q-point input"),
        alignment=AlignmentKind.conditional,
        algorithm_equivalent=True,
        qualification=(
            "Both routes use symmetry-aware perturbation theory, but complete phonon "
            "workflow settings do not map through IBRION alone."
        ),
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.interactive_standard_input,
        purpose="Interactive structure updates from standard input",
        qe_executable=None,
        qe_fields=(),
        alignment=AlignmentKind.unsupported,
        algorithm_equivalent=False,
        qualification="No direct QE pw.x input-mode equivalent is recorded.",
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.interactive_python_plugin,
        purpose="Interactive structure updates from a Python plugin",
        qe_executable=None,
        qe_fields=(),
        alignment=AlignmentKind.unsupported,
        algorithm_equivalent=False,
        qualification="No direct QE pw.x Python-plugin equivalent is recorded.",
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.intrinsic_reaction_coordinate,
        purpose="Intrinsic-reaction-coordinate analysis",
        qe_executable=None,
        qe_fields=(),
        alignment=AlignmentKind.unsupported,
        algorithm_equivalent=False,
        qualification="QE neb.x is a path optimizer, not a direct IRC equivalent.",
    ),
    VaspIbrionAlignment(
        ibrion=VaspIbrion.improved_dimer_method,
        purpose="Improved dimer transition-state search",
        qe_executable=None,
        qe_fields=(),
        alignment=AlignmentKind.unsupported,
        algorithm_equivalent=False,
        qualification=(
            "IBRION=44 is VASP's improved dimer method. It is not NEB, and QE neb.x "
            "must not be represented as an algorithm-equivalent mapping."
        ),
    ),
)

VASP_NEB_ALIGNMENT = VaspNebAlignment(
    vasp_fields=("IMAGES", "SPRING", "IBRION", "NSW", "image directories"),
    qe_executable="neb.x",
    qe_fields=("&PATH", "BEGIN_POSITIONS", "SCF engine inputs"),
    alignment=AlignmentKind.conditional,
    qualification=(
        "NEB is a multi-image workflow in both codes. VASP IBRION selects an image "
        "optimizer within a workflow enabled by IMAGES and SPRING; IBRION=44 is the "
        "separate improved dimer method."
    ),
)
