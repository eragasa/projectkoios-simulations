"""Common calculator-projection runner for silicon single-SCF campaigns."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from projectkoios.integrations.quantumespresso.pw.scf import (
    projection as qe_projection,
)
from projectkoios.integrations.vasp.pw_dft_scf.projection import (
    VASP_SCF_INTEGRATION_ID,
    VaspScfInputProjector,
)
from projectkoios.simulations.calculator_input import CalculatorInputRecord
from tools.pw_dft_scf.environment import (
    WorkflowRunnerEnvironment,
)


@dataclass(frozen=True, slots=True)
class InputProjectionRunner:
    """Render one configured campaign through a source-controlled integration."""

    environment: WorkflowRunnerEnvironment

    def render(self, campaign_path: Path, output_directory: Path) -> tuple[Path, ...]:
        """Write deterministic calculator inputs and return their paths."""
        loaded = self.environment.loader.load(campaign_path)
        request = loaded.campaign.recipe.base_request
        integration_id = loaded.campaign.integration_id
        if integration_id == qe_projection.QE_SCF_INTEGRATION_ID:
            prepared_input = qe_projection.QeScfInputProjector(
                configuration=self.environment.loader.qe_projection_configuration(
                    loaded.projection_profile_id
                )
            ).project(request, loaded.structure)
        elif integration_id == VASP_SCF_INTEGRATION_ID:
            prepared_input = VaspScfInputProjector(
                configuration=(
                    self.environment.loader.vasp_projection_configuration(
                        loaded.projection_profile_id
                    )
                )
            ).project(request, loaded.structure)
        else:
            raise ValueError(f"unsupported integration: {integration_id.value}")
        return self._write_prepared_input(prepared_input, output_directory)

    @staticmethod
    def _write_prepared_input(
        prepared_input: CalculatorInputRecord,
        output_directory: Path,
    ) -> tuple[Path, ...]:
        """Write exact prepared inputs without resolving external dependencies."""
        output_directory.mkdir(parents=True, exist_ok=True)
        if output_directory.is_symlink():
            raise ValueError("output_directory must not be a symlink")
        paths: list[Path] = []
        for artifact in prepared_input.artifacts:
            destination = output_directory / artifact.filename
            destination.write_bytes(artifact.content)
            paths.append(destination)
        metadata_path = output_directory / "calculator-input-record.json"
        metadata_path.write_bytes(prepared_input.canonical_bytes)
        paths.append(metadata_path)
        return tuple(paths)


@dataclass(frozen=True, slots=True)
class InputProjectionRunnerCommand:
    """Parse command-line paths and invoke `InputProjectionRunner`."""

    def run(self) -> int:
        """Render one campaign selected entirely by reviewed configuration."""
        parser = argparse.ArgumentParser(
            description="Render configured silicon single-SCF calculator inputs."
        )
        parser.add_argument("campaign", type=Path)
        parser.add_argument("--runner-config", required=True, type=Path)
        parser.add_argument("--output", required=True, type=Path)
        arguments = parser.parse_args()
        environment = WorkflowRunnerEnvironment.load(arguments.runner_config.resolve())
        paths = InputProjectionRunner(environment=environment).render(
            campaign_path=arguments.campaign.resolve(),
            output_directory=arguments.output.resolve(),
        )
        for path in paths:
            print(path)
        return 0


if __name__ == "__main__":
    raise SystemExit(InputProjectionRunnerCommand().run())
