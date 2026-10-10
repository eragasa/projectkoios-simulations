"""Common configured environment for silicon SCF repository tools."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from projectkoios.simulations.library import SimulationLibraryManifestLoader
from tools.pw_dft_scf.configuration import (
    WorkflowRunnerConfigurationLoader,
)
from tools.pw_dft_scf.structure_repository import (
    WorkflowStructureLibraryLoader,
)


@dataclass(frozen=True, slots=True)
class WorkflowRunnerEnvironment:
    """Resolve runner-owned repositories from one reviewed configuration file."""

    configuration_path: Path
    loader: WorkflowRunnerConfigurationLoader

    @classmethod
    def load(cls, configuration_path: Path) -> WorkflowRunnerEnvironment:
        """Construct the common environment from bounded relative paths."""
        if not configuration_path.is_file() or configuration_path.is_symlink():
            raise ValueError("runner configuration must be a regular file")
        if configuration_path.stat().st_size > 100_000:
            raise ValueError("runner configuration exceeds the byte limit")
        payload = tomllib.loads(configuration_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError("unsupported runner configuration schema")
        root = configuration_path.parent.resolve()
        catalog_path = cls._resolve_file(
            root,
            cls._string(payload, "catalog"),
        )
        structure_catalog_path = cls._resolve_file(
            root,
            cls._string(payload, "structure_catalog"),
        )
        simulation_catalog_path = cls._resolve_file(
            root,
            cls._string(payload, "simulation_catalog"),
        )
        return cls(
            configuration_path=configuration_path.resolve(),
            loader=WorkflowRunnerConfigurationLoader(
                catalog_path=catalog_path,
                structure_library=WorkflowStructureLibraryLoader(
                    manifest_path=structure_catalog_path
                ).load(),
                simulation_library=SimulationLibraryManifestLoader(
                    manifest_path=simulation_catalog_path,
                    expected_sha256=cls._string(
                        payload,
                        "simulation_catalog_sha256",
                    ),
                    expected_byte_size=cls._integer(
                        payload,
                        "simulation_catalog_byte_size",
                    ),
                ).load(),
            ),
        )

    @staticmethod
    def _resolve_file(root: Path, value: str) -> Path:
        """Resolve one regular file beneath the repository root."""
        path = (root / value).resolve()
        if not path.is_relative_to(root.parent.parent.parent):
            raise ValueError("runner file path escapes the repository root")
        if not path.is_file() or path.is_symlink():
            raise ValueError("runner file path must identify a regular file")
        return path

    @staticmethod
    def _integer(payload: dict[str, object], key: str) -> int:
        """Require one positive built-in integer."""
        value = payload.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"{key} must be a positive integer")
        return value

    @staticmethod
    def _string(payload: dict[str, object], key: str) -> str:
        """Require one nonempty relative-path string."""
        value = payload.get(key)
        if type(value) is not str or not value or value != value.strip():
            raise ValueError(f"{key} must be a nonempty stripped string")
        if Path(value).is_absolute():
            raise ValueError(f"{key} must be relative")
        return value
