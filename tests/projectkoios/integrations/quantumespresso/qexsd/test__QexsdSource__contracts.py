r"""Software verification of ``QexsdSource``.

Evidence profile: routine

Bounded artifact scope: explicit controlled QEXSD bytes and source identity.

Facet and represented meaning

The source binds immutable bytes to a strict path, digest, and count.

Intrinsic and cross-object scope

Only intrinsic construction and immutable value semantics are tested.

VVUQ and scientific exclusions

Controlled bytes are not calculated physical data; no scientific claim is made.
"""

from dataclasses import FrozenInstanceError

import pytest

from projectkoios.integrations.quantumespresso.qexsd.records import QexsdSource

from ..resources.qexsd_fixtures import CONTROLLED_QEXSD, QEXSD_FIXTURES

SUT = QexsdSource
pytestmark = pytest.mark.software_verification


class TestQexsdSource:
    """Own this module's maintained software-verification evidence."""

    def test__QexsdSource__constructor_source_identity_maps_exact_immutable_bytes(
        self,
    ) -> None:
        """Evidence ID: SV-PERIODIC-001

        Requirement: Valid exact bytes, canonical path, SHA-256, and count are retained.

        Acceptance: Fields equal the supplied values and frozen assignment is rejected.
        """
        digest, count = QEXSD_FIXTURES.controlled_source_bytes()
        source = QexsdSource(
            "/external/data-file-schema.xml", digest, count, CONTROLLED_QEXSD
        )
        assert source.content is CONTROLLED_QEXSD
        assert (source.sha256, source.byte_count) == (digest, count)
        with pytest.raises(FrozenInstanceError):
            source.byte_count = 0  # type: ignore[misc]

    @pytest.mark.parametrize(
        ("path", "digest", "count"),
        [
            pytest.param("relative.xml", None, None, id="relative_path"),
            pytest.param("/external/source.xml", "0" * 64, None, id="digest_mismatch"),
            pytest.param("/external/source.xml", None, 1, id="byte_count_mismatch"),
        ],
    )
    def test__QexsdSource__constructor_source_contract_rejects_invalid_identity(
        self, path: str, digest: str | None, count: int | None
    ) -> None:
        """Evidence ID: SV-PERIODIC-002

        Requirement: Path is canonical absolute POSIX and digest/count match exact
        bytes.

        Acceptance: Every named invalid partition raises ValueError.
        """
        actual_digest, actual_count = QEXSD_FIXTURES.controlled_source_bytes()
        with pytest.raises(ValueError):
            QexsdSource(
                path,
                actual_digest if digest is None else digest,
                actual_count if count is None else count,
                CONTROLLED_QEXSD,
            )

    def test__QexsdSource__constructor_semantic_types_rejects_coercible_values(
        self,
    ) -> None:
        """Evidence ID: SV-PERIODIC-003

        Requirement: Source public fields reject wrong semantic types without coercion.

        Acceptance: Digest bytes, a Boolean count, and mutable bytes each raise
        ``TypeError``.
        """
        digest, count = QEXSD_FIXTURES.controlled_source_bytes()
        with pytest.raises(TypeError):
            QexsdSource(
                "/external/source.xml",
                b"x" * 64,  # type: ignore[arg-type]
                count,
                CONTROLLED_QEXSD,
            )
        with pytest.raises(TypeError):
            QexsdSource(
                "/external/source.xml",
                digest,
                True,
                CONTROLLED_QEXSD,
            )
        with pytest.raises(TypeError):
            QexsdSource(
                "/external/source.xml",
                digest,
                count,
                bytearray(CONTROLLED_QEXSD),  # type: ignore[arg-type]
            )
