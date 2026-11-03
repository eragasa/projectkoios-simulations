"""Controlled reduced and exact external QEXSD fixtures for software verification."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from projectkoios.integrations.quantumespresso.qexsd.parsing import (
    QuantumEspressoXsdDocumentParser,
)
from projectkoios.integrations.quantumespresso.qexsd.records import (
    QexsdDocument,
    QexsdSource,
)


class QexsdFixtureResources:
    """Own identities and configured paths for the shared QEXSD test resources."""

    RESOURCE_ROOT = Path(__file__).with_name("qexsd")

    @classmethod
    def controlled_path(cls, schema_version: str) -> Path:
        """Return one exact maintained reduced-QEXSD resource path."""
        if schema_version not in {"23.03.10", "25.05.21"}:
            raise ValueError("schema_version must identify a controlled QEXSD resource")
        return cls.RESOURCE_ROOT / f"qexsd-{schema_version}.xml"

    @classmethod
    def controlled_bytes(cls, schema_version: str) -> bytes:
        """Return exact bytes from one maintained reduced-QEXSD resource."""
        return cls.controlled_path(schema_version).read_bytes()

    @classmethod
    def controlled_source_bytes(
        cls,
        content: bytes | None = None,
    ) -> tuple[str, int]:
        """Return the independent digest and count for controlled fixture bytes."""
        exact_content = cls.controlled_bytes("23.03.10") if content is None else content
        return hashlib.sha256(exact_content).hexdigest(), len(exact_content)

    @staticmethod
    def configured_external_path(environment_variable: str) -> Path:
        """Return an explicitly configured external artifact path or skip."""
        configured_path = os.environ.get(environment_variable)
        if configured_path is None:
            pytest.skip(f"set {environment_variable} to run external-artifact evidence")
        return Path(configured_path)

    @classmethod
    def controlled_document(cls, schema_version: str = "25.05.21") -> QexsdDocument:
        """Parse one maintained reduced-QEXSD resource into its native record."""
        content = cls.controlled_bytes(schema_version)
        digest, count = cls.controlled_source_bytes(content)
        return QuantumEspressoXsdDocumentParser().execute(
            QexsdSource(
                f"/controlled/qexsd-{schema_version}.xml",
                digest,
                count,
                content,
            )
        )

    @classmethod
    def actual_qexsd_path(cls) -> Path:
        """Return the configured accepted QE 7.2 QEXSD source path."""
        return cls.configured_external_path("KSDFT2EFFMASS_QE72_QEXSD_PATH")

    @classmethod
    def actual_qe75_qexsd_path(cls) -> Path:
        """Return the configured QE 7.5 smoke-test QEXSD source path."""
        return cls.configured_external_path("KSDFT2EFFMASS_QE75_QEXSD_PATH")


CONTROLLED_QEXSD = QexsdFixtureResources.controlled_bytes("23.03.10")
CONTROLLED_QEXSD_250521 = QexsdFixtureResources.controlled_bytes("25.05.21")
