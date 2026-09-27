"""Immutable native configuration for ``pw2wannier90.x``."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")


class QePw2Wannier90SpinComponent(StrEnum):
    """Represent documented converter spin-component values."""

    none = "none"
    up = "up"
    down = "down"


class QePw2Wannier90Mode(StrEnum):
    """Represent documented converter execution modes."""

    standalone = "standalone"
    library = "library"


@dataclass(frozen=True, slots=True)
class QePw2Wannier90InputConfiguration:
    """Declare reviewed converter input and exact parent identities."""

    prefix: str
    outdir: str
    seedname: str
    spin_component: QePw2Wannier90SpinComponent
    mode: QePw2Wannier90Mode
    write_amn: bool
    write_mmn: bool
    write_unk: bool
    write_spn: bool
    input_filename: str
    nnkp_filename: str
    nnkp_sha256: str
    nnkp_byte_size: int
    parent_nscf_saved_state_manifest_sha256: str

    def __post_init__(self) -> None:
        for label, value in (
            ("prefix", self.prefix),
            ("seedname", self.seedname),
        ):
            if type(value) is not str or _NAME.fullmatch(value) is None:
                raise ValueError(f"{label} must be a safe native name")
        if (
            type(self.outdir) is not str
            or not self.outdir
            or self.outdir != self.outdir.strip()
            or "'" in self.outdir
            or "\n" in self.outdir
            or "\r" in self.outdir
        ):
            raise ValueError("outdir must be nonempty, stripped, and unquoted")
        if type(self.spin_component) is not QePw2Wannier90SpinComponent:
            raise TypeError("spin_component must be a QePw2Wannier90SpinComponent")
        if type(self.mode) is not QePw2Wannier90Mode:
            raise TypeError("mode must be a QePw2Wannier90Mode")
        for label, bool_value in (
            ("write_amn", self.write_amn),
            ("write_mmn", self.write_mmn),
            ("write_unk", self.write_unk),
            ("write_spn", self.write_spn),
        ):
            if type(bool_value) is not bool:
                raise TypeError(f"{label} must be a boolean")
        if not self.write_amn or not self.write_mmn:
            raise ValueError("the maintained interface requires AMN and MMN output")
        if self.write_unk or self.write_spn:
            raise NotImplementedError(
                "UNK and SPN output are not implemented by the maintained interface"
            )
        for label, filename in (
            ("input_filename", self.input_filename),
            ("nnkp_filename", self.nnkp_filename),
        ):
            if type(filename) is not str or _NAME.fullmatch(filename) is None:
                raise ValueError(f"{label} must be a safe basename")
        if self.nnkp_filename != f"{self.seedname}.nnkp":
            raise ValueError("nnkp_filename must match seedname")
        if type(self.nnkp_byte_size) is not int or self.nnkp_byte_size <= 0:
            raise ValueError("nnkp_byte_size must be positive")
        for label, value in (
            ("nnkp_sha256", self.nnkp_sha256),
            (
                "parent_nscf_saved_state_manifest_sha256",
                self.parent_nscf_saved_state_manifest_sha256,
            ),
        ):
            if type(value) is not str or _SHA256.fullmatch(value) is None:
                raise ValueError(f"{label} must be lowercase SHA-256")
