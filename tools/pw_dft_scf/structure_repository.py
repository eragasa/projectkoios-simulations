"""Bind the reviewed example catalog to the neutral structure library."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from projectkoios.simulations.structure.library import (
    StructureLibrary,
    StructureLibraryManifestLoader,
)


@dataclass(frozen=True, slots=True)
class WorkflowStructureLibraryLoader:
    """Load the exact manifest-backed library used by repository tools."""

    manifest_path: Path

    def load(self) -> StructureLibrary:
        """Delegate identity, integrity, schema, and provenance validation."""
        return StructureLibraryManifestLoader(manifest_path=self.manifest_path).load()
