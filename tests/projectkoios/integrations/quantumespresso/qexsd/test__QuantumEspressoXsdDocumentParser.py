r"""Software verification of ``QuantumEspressoXsdDocumentParser``.

Evidence profile: routine

Bounded artifact scope: mechanical QEXSD 23.03.10 and 25.05.21 parsing from
explicit bytes.

Facet and represented meaning

The parser recognizes the bounded root/version and preserves native source order.

Intrinsic and cross-object scope

Parsing and structural relationships are tested; semantic adaptation is excluded.

VVUQ and scientific exclusions

The reduced XML is a controlled fixture, not exhaustive QEXSD support or physical data.
"""

import builtins

import pytest

from projectkoios.integrations.quantumespresso.qexsd.parsing import (
    QuantumEspressoXsdDocumentParser,
)
from projectkoios.integrations.quantumespresso.qexsd.records import QexsdSource

from ..resources.qexsd_fixtures import (
    CONTROLLED_QEXSD,
    CONTROLLED_QEXSD_250521,
    QexsdFixtureResources,
)

SUT = QuantumEspressoXsdDocumentParser
pytestmark = pytest.mark.software_verification


class TestQuantumEspressoXsdDocumentParser:
    """Own this module's maintained software-verification evidence."""

    @staticmethod
    def make_source(content: bytes = CONTROLLED_QEXSD) -> QexsdSource:
        """Build an explicit controlled source for parser evidence.

        Evidence ID: Helper owns no identifier.

        Requirement: Support the named tests without owning evidence.

        Method: Hash the supplied controlled bytes and construct the explicit source.

        Oracle: Standard-library SHA-256 and the public QexsdSource identity contract.

        Acceptance: Return deterministic controlled support data.

        Interpretation: Failure blocks the consuming parser evidence without owning a
        separate claim.

        Limitations: This helper performs no parsing or scientific interpretation.

        Provenance: Module-local controlled fixture bytes.
        """
        digest, count = QexsdFixtureResources.controlled_source_bytes(content)
        return QexsdSource("/controlled/data-file-schema.xml", digest, count, content)

    @pytest.mark.parametrize(
        ("content", "expected_qexsd_version", "expected_producer_version"),
        [
            pytest.param(
                CONTROLLED_QEXSD,
                "23.03.10",
                "7.2",
                id="qexsd_23_03_10",
            ),
            pytest.param(
                CONTROLLED_QEXSD_250521,
                "25.05.21",
                "7.5",
                id="qexsd_25_05_21",
            ),
        ],
    )
    def test_method__execute__extracts_native_order_and_dimensions(
        self,
        monkeypatch: pytest.MonkeyPatch,
        content: bytes,
        expected_qexsd_version: str,
        expected_producer_version: str,
    ) -> None:
        """Evidence ID: SV-PERIODIC-004

        Requirement: Parsing both exact supported QEXSD versions uses only supplied
        bytes and preserves all ordered native values.

        Method: Deny file opening, parse each controlled version, and compare its exact
        native observations with the fixed fixture oracle.

        Oracle: The explicit reduced QEXSD fixtures independently list every expected
        native token, order, shape, and version.

        Acceptance: Expected version, producer, source order, shapes, units, grids,
        and status are exact, and no file open occurs.

        Interpretation: Failure identifies unsupported accepted-version behavior,
        source-order drift, or an implicit file-system dependency.

        Limitations: Reduced fixtures do not exhaust either upstream QEXSD schema.

        Provenance: Controlled QEXSD 23.03.10 and 25.05.21 fixture bytes.
        """
        monkeypatch.setattr(
            builtins,
            "open",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("unexpected open")
            ),
        )
        document = QuantumEspressoXsdDocumentParser().execute(
            TestQuantumEspressoXsdDocumentParser.make_source(content)
        )
        assert QuantumEspressoXsdDocumentParser.SUPPORTED_QEXSD_VERSIONS == (
            "23.03.10",
            "25.05.21",
        )
        assert document.namespace.endswith("qes-1.0")
        assert document.qexsd_version == expected_qexsd_version
        assert document.producing_application_version == expected_producer_version
        assert document.species == (("Si", 28.086, "Si.UPF"),)
        assert tuple(atom[0] for atom in document.atoms) == (1, 2)
        assert document.direct_lattice_vectors == (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
        assert document.k_points == ((0.0, 0.0, 0.0), (0.5, 0.0, 0.0))
        assert document.k_point_weights == (0.25, 0.75)
        assert document.eigenvalues == ((-1.0, 0.0), (-0.5, 0.5))
        assert document.occupations == ((1.0, 1.0), (1.0, 0.0))
        assert document.fft_grid == document.fft_smooth == document.fft_box == (4, 5, 6)
        assert document.exit_status == 0

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param(b"<broken", id="malformed_xml"),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"qes/qes-1.0", b"qes/qes-2.0"),
                id="unsupported_namespace",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"qes:espresso", b"qes:other", 1).replace(
                    b"</qes:espresso>", b"</qes:other>"
                ),
                id="unsupported_root",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"23.03.10", b"99.00.00"),
                id="unsupported_version",
            ),
        ],
    )
    def test_method__execute__rejects_unsupported_or_malformed_xml(
        self, content: bytes
    ) -> None:
        """Evidence ID: SV-PERIODIC-005

        Requirement: Malformed XML and unsupported namespace, root, or version fail
        closed.

        Method: Parse each named malformed or unsupported controlled byte partition.

        Oracle: XML syntax and the exact public namespace, root, and supported-version
        set define the invalid partitions.

        Acceptance: Every named controlled partition raises ValueError.

        Interpretation: Failure identifies fail-open behavior at the format boundary.

        Limitations: These partitions do not enumerate every malformed XML document.

        Provenance: Module-local controlled fixture mutations.
        """
        with pytest.raises(ValueError):
            QuantumEspressoXsdDocumentParser().execute(
                TestQuantumEspressoXsdDocumentParser.make_source(content)
            )

    @pytest.mark.parametrize(
        "content",
        [
            pytest.param(
                CONTROLLED_QEXSD.replace(
                    b"<total_energy><etot>-1.25</etot></total_energy>", b""
                ),
                id="missing_required_section",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(
                    b"<exit_status>0</exit_status>",
                    b"<exit_status>0</exit_status><exit_status>0</exit_status>",
                ),
                id="duplicate_singleton",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"-1.25", b"NaN"), id="nonfinite_number"
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"<a1>1 0 0</a1>", b"<a1>1 0</a1>"),
                id="invalid_vector_dimension",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(
                    b"name='Si' index='2'", b"name='Ge' index='2'"
                ),
                id="unresolved_species",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"nat='2'", b"nat='3'"),
                id="atom_count_disagreement",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"<nks>2</nks>", b"<nks>3</nks>"),
                id="spectrum_kpoint_disagreement",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"size='2'>-0.5 0.5", b"size='3'>-0.5 0.5"),
                id="declared_band_size",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(b"nr1='4'", b"nr1='0'", 1),
                id="invalid_fft_grid",
            ),
            pytest.param(
                CONTROLLED_QEXSD.replace(
                    b"<exit_status>0</exit_status>", b"<exit_status>-1</exit_status>"
                ),
                id="invalid_exit_status",
            ),
        ],
    )
    def test_method__execute__rejects_structural_invariant_failures(
        self, content: bytes
    ) -> None:
        """Evidence ID: SV-PERIODIC-006

        Requirement: Required QEXSD structural and cardinality invariants fail
        deterministically.

        Method: Parse each named controlled invariant violation through the public
        parser.

        Oracle: The documented required-section, cardinality, numeric, reference, grid,
        and exit-status contracts define each invalid partition.

        Acceptance: Every named invalid controlled fixture raises ValueError.

        Interpretation: Failure identifies acceptance of a structurally invalid native
        document.

        Limitations: The selected partitions are bounded software-verification cases,
        not exhaustive schema conformance.

        Provenance: Module-local controlled fixture mutations.
        """
        with pytest.raises(ValueError):
            QuantumEspressoXsdDocumentParser().execute(
                TestQuantumEspressoXsdDocumentParser.make_source(content)
            )
