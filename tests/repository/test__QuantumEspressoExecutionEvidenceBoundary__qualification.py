from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path
from typing import TypedDict, cast

from projectkoios.integrations.quantumespresso.outputs.pw_stderr import (
    QePwStderrFileParser,
    QePwStderrFileResult,
)
from projectkoios.integrations.quantumespresso.outputs.pw_stdout import (
    QePwStdoutFileParser,
    QePwStdoutFileResult,
)
from projectkoios.integrations.quantumespresso.pw.bands.data_extraction import (
    QeBandsData,
)
from projectkoios.integrations.quantumespresso.pw.data_extraction.base import (
    QePwDataSources,
    QePwExecutionData,
    QePwNativeArtifact,
)
from projectkoios.integrations.quantumespresso.pw.execution import QeSimulationExecutor
from projectkoios.integrations.quantumespresso.pw.inputfile.model import (
    PwInputWriter,
    QePwInputFile,
)
from projectkoios.integrations.quantumespresso.pw.nscf.data_extraction import (
    QeNscfData,
)
from projectkoios.integrations.quantumespresso.pw.scf.data_extraction import QeScfData
from projectkoios.integrations.quantumespresso.saved_state import QeSavedStateManifest
from projectkoios.simulations.calculator.input import (
    CalculatorExternalInputRequirement,
    CalculatorInputArtifact,
    CalculatorInputRecord,
)
from projectkoios.simulations.execution import (
    CalculatorExecutableBinding,
    CalculatorExecutableIdentity,
    CalculatorExecutablePreparationFailure,
    CalculatorExecutablePreparer,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorExecutor,
    CalculatorPreparedExecutable,
    ExecutionStatus,
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_CROSSWALK = (
    _REPOSITORY_ROOT
    / "docs/provenance/quantumespresso-execution-evidence-boundary.json"
)


class _Capability(TypedDict):
    id: str
    disposition: str
    ksd_owners: list[str]
    upstream_symbols: list[str]
    owned_semantics: list[str]
    excluded_semantics: list[str]


class _SourceInventory(TypedDict):
    repository: str
    commit: str
    audit_date: str
    classification: str
    modules: dict[str, int]


class _Manifest(TypedDict):
    schema_version: int
    audit_owner_count: int
    source_inventory: _SourceInventory
    claim_boundary: list[str]
    capabilities: list[_Capability]
    immutable_record_symbols: list[str]
    next_reusable_tranches: list[str]


# Keep the owner registry explicit rather than resolving arbitrary dotted names with
# ``getattr``. This makes each accepted nominal boundary visible during review and
# ensures a renamed or removed owner fails collection instead of passing structurally.
_SYMBOLS: dict[str, type] = {
    "projectkoios.simulations.execution."
    "CalculatorExecutableBinding": CalculatorExecutableBinding,
    "projectkoios.simulations.execution."
    "CalculatorExecutableIdentity": CalculatorExecutableIdentity,
    "projectkoios.simulations.execution.CalculatorExecutablePreparationFailure": (
        CalculatorExecutablePreparationFailure
    ),
    "projectkoios.simulations.execution."
    "CalculatorExecutablePreparer": CalculatorExecutablePreparer,
    "projectkoios.simulations.execution."
    "CalculatorPreparedExecutable": CalculatorPreparedExecutable,
    "projectkoios.integrations.quantumespresso.outputs.pw_stderr."
    "QePwStderrFileParser": QePwStderrFileParser,
    "projectkoios.integrations.quantumespresso.outputs.pw_stderr."
    "QePwStderrFileResult": QePwStderrFileResult,
    "projectkoios.integrations.quantumespresso.outputs.pw_stdout."
    "QePwStdoutFileParser": QePwStdoutFileParser,
    "projectkoios.integrations.quantumespresso.outputs.pw_stdout."
    "QePwStdoutFileResult": QePwStdoutFileResult,
    "projectkoios.integrations.quantumespresso.pw.bands.data_extraction."
    "QeBandsData": QeBandsData,
    "projectkoios.integrations.quantumespresso.pw.data_extraction.base."
    "QePwDataSources": QePwDataSources,
    "projectkoios.integrations.quantumespresso.pw.data_extraction.base."
    "QePwExecutionData": QePwExecutionData,
    "projectkoios.integrations.quantumespresso.pw.data_extraction.base."
    "QePwNativeArtifact": QePwNativeArtifact,
    "projectkoios.integrations.quantumespresso.pw.execution."
    "QeSimulationExecutor": QeSimulationExecutor,
    "projectkoios.integrations.quantumespresso.pw.inputfile.model."
    "PwInputWriter": PwInputWriter,
    "projectkoios.integrations.quantumespresso.pw.inputfile.model."
    "QePwInputFile": QePwInputFile,
    "projectkoios.integrations.quantumespresso.pw.nscf.data_extraction."
    "QeNscfData": QeNscfData,
    "projectkoios.integrations.quantumespresso.pw.scf.data_extraction."
    "QeScfData": QeScfData,
    "projectkoios.integrations.quantumespresso.saved_state."
    "QeSavedStateManifest": QeSavedStateManifest,
    "projectkoios.simulations.calculator.input."
    "CalculatorExternalInputRequirement": CalculatorExternalInputRequirement,
    "projectkoios.simulations.calculator.input."
    "CalculatorInputArtifact": CalculatorInputArtifact,
    "projectkoios.simulations.calculator.input."
    "CalculatorInputRecord": CalculatorInputRecord,
    "projectkoios.simulations.execution."
    "CalculatorExecutionRecord": CalculatorExecutionRecord,
    "projectkoios.simulations.execution."
    "CalculatorExecutionRequest": CalculatorExecutionRequest,
    "projectkoios.simulations.execution.CalculatorExecutor": CalculatorExecutor,
    "projectkoios.simulations.execution.ExecutionStatus": ExecutionStatus,
}


class TestQuantumEspressoExecutionEvidenceBoundary:
    """Qualify the reusable QE evidence boundary against its source inventory.

    Notes
    -----
    These tests establish ownership, immutability, and dependency facts only. They
    do not execute Quantum ESPRESSO or establish numerical or scientific validity.
    """

    def _manifest(self) -> _Manifest:
        """Load the reviewed machine-readable boundary declaration.

        Returns
        -------
        _Manifest
            Typed view of the committed execution-evidence crosswalk.
        """
        return cast(_Manifest, json.loads(_CROSSWALK.read_text(encoding="utf-8")))

    def test__QuantumEspressoExecutionEvidenceBoundary__accounts_for_inventory(
        self,
    ) -> None:
        """Account for every audited duplicate exactly once."""
        manifest = self._manifest()
        capabilities = manifest["capabilities"]
        # Flattening the groups makes omissions and duplicate dispositions observable;
        # a matching total alone would not detect one owner counted twice.
        owners = [owner for item in capabilities for owner in item["ksd_owners"]]

        source_inventory = manifest["source_inventory"]
        assert manifest["schema_version"] == 1
        assert manifest["audit_owner_count"] == 101
        assert source_inventory == {
            "repository": "ksdft2effmass",
            "commit": "aa4098b3d32fe05436a1ba8dab18903a4347b20d",
            "audit_date": "2026-11-03",
            "classification": "UPSTREAM_DUPLICATE",
            "modules": {
                "contracts.py": 38,
                "diagnostics.py": 5,
                "effects.py": 32,
                "execution.py": 17,
                "outcomes.py": 1,
                "process.py": 6,
                "pw_input.py": 2,
            },
        }
        assert sum(source_inventory["modules"].values()) == 101
        assert len(owners) == len(set(owners)) == 101
        assert Counter(item["disposition"] for item in capabilities) == {
            "PARTIAL_UPSTREAM_OWNER": 5,
            "MISSING_REUSABLE_UPSTREAM_OWNER": 1,
            "KSD_ADAPTER_REQUIRED": 1,
        }
        assert all(item["excluded_semantics"] for item in capabilities)
        assert len(manifest["claim_boundary"]) == 3
        assert len(manifest["next_reusable_tranches"]) == 4

    def test__QuantumEspressoExecutionEvidenceBoundary__resolves_upstream_owners(
        self,
    ) -> None:
        """Keep every declared upstream owner nominally resolvable."""
        manifest = self._manifest()
        declared = {
            symbol
            for item in manifest["capabilities"]
            for symbol in item["upstream_symbols"]
        } | set(manifest["immutable_record_symbols"])

        assert declared == set(_SYMBOLS)

    def test__QuantumEspressoExecutionEvidenceBoundary__retains_immutable_records(
        self,
    ) -> None:
        """Keep mapped public records frozen and slotted."""
        manifest = self._manifest()

        # The boundary promises operational immutability, so check the dataclass
        # configuration itself rather than relying on mutation attempts in examples.
        for symbol in manifest["immutable_record_symbols"]:
            owner = _SYMBOLS[symbol]
            parameters = getattr(owner, "__dataclass_params__", None)
            assert parameters is not None, symbol
            assert parameters.frozen, symbol
            assert "__slots__" in owner.__dict__, symbol

    def test__QuantumEspressoExecutionEvidenceBoundary__excludes_ksd_dependencies(
        self,
    ) -> None:
        """Keep Simulations production code independent of KSD."""
        invalid: list[Path] = []
        source_root = _REPOSITORY_ROOT / "src/python"

        # Parse imports instead of searching raw text so documentation strings and
        # claim-boundary prose cannot create false dependency violations.
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(
                    item.name == "ksdft2effmass"
                    or item.name.startswith("ksdft2effmass.")
                    for item in node.names
                ):
                    invalid.append(path.relative_to(_REPOSITORY_ROOT))
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module is not None
                    and (
                        node.module == "ksdft2effmass"
                        or node.module.startswith("ksdft2effmass.")
                    )
                ):
                    invalid.append(path.relative_to(_REPOSITORY_ROOT))

        assert invalid == []
