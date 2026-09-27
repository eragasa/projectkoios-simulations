"""Render deterministic ``pw2wannier90.x`` native input."""

from __future__ import annotations

from dataclasses import dataclass

from projectkoios.integrations.quantumespresso.pw2wannier90.configuration import (  # noqa: E501
    QePw2Wannier90InputConfiguration,
)


def _logical(value: bool) -> str:
    return ".true." if value else ".false."


@dataclass(frozen=True, slots=True)
class QePw2Wannier90RenderedInput:
    """Represent one deterministic converter input file."""

    filename: str
    text: str

    def __post_init__(self) -> None:
        if type(self.filename) is not str or not self.filename:
            raise ValueError("filename must be nonempty")
        if type(self.text) is not str or not self.text.endswith("\n"):
            raise ValueError("text must be a newline-terminated string")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90InputProjection:
    """Bind rendered input to required NNKP and NSCF saved-state identities."""

    rendered_input: QePw2Wannier90RenderedInput
    prefix: str
    outdir: str
    seedname: str
    nnkp_filename: str
    nnkp_sha256: str
    nnkp_byte_size: int
    parent_nscf_saved_state_manifest_sha256: str
    required_output_filenames: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.rendered_input) is not QePw2Wannier90RenderedInput:
            raise TypeError("rendered_input must be a QePw2Wannier90RenderedInput")
        if type(self.required_output_filenames) is not tuple or not (
            self.required_output_filenames
        ):
            raise ValueError("required_output_filenames must be nonempty")
        if len(set(self.required_output_filenames)) != len(
            self.required_output_filenames
        ):
            raise ValueError("required output filenames must be unique")


@dataclass(frozen=True, slots=True)
class QePw2Wannier90InputProjector:
    """Project reviewed converter controls without executing the calculator."""

    def project(
        self,
        configuration: QePw2Wannier90InputConfiguration,
    ) -> QePw2Wannier90InputProjection:
        """Return deterministic ``&INPUTPP`` text and exact dependencies."""
        if type(configuration) is not QePw2Wannier90InputConfiguration:
            raise TypeError("configuration must be a QePw2Wannier90InputConfiguration")
        lines = (
            "&INPUTPP",
            f"    prefix = '{configuration.prefix}'",
            f"    outdir = '{configuration.outdir}'",
            f"    seedname = '{configuration.seedname}'",
            f"    spin_component = '{configuration.spin_component.value}'",
            f"    wan_mode = '{configuration.mode.value}'",
            f"    write_amn = {_logical(configuration.write_amn)}",
            f"    write_mmn = {_logical(configuration.write_mmn)}",
            f"    write_unk = {_logical(configuration.write_unk)}",
            f"    write_spn = {_logical(configuration.write_spn)}",
            "/",
        )
        required_outputs = [
            f"{configuration.seedname}.amn",
            f"{configuration.seedname}.mmn",
            f"{configuration.seedname}.eig",
        ]
        return QePw2Wannier90InputProjection(
            rendered_input=QePw2Wannier90RenderedInput(
                filename=configuration.input_filename,
                text="\n".join(lines) + "\n",
            ),
            prefix=configuration.prefix,
            outdir=configuration.outdir,
            seedname=configuration.seedname,
            nnkp_filename=configuration.nnkp_filename,
            nnkp_sha256=configuration.nnkp_sha256,
            nnkp_byte_size=configuration.nnkp_byte_size,
            parent_nscf_saved_state_manifest_sha256=(
                configuration.parent_nscf_saved_state_manifest_sha256
            ),
            required_output_filenames=tuple(required_outputs),
        )
