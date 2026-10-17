from __future__ import annotations

import hashlib
import shutil
import stat
from pathlib import Path

import pytest

pytest.importorskip("projectkoios.workflow")

from projectkoios.adapters.workflow.quantumespresso.pw.scf.saved_state_artifact_set import (  # noqa: E501
    QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND,
    QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE,
    QeScfSavedStateProjectionRequestSourceRepository,
)
from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set import (
    QeScfSavedStateArtifactSetProjectionRequest,
    QeScfSavedStateArtifactSetProjectionResult,
    QeScfSavedStateArtifactSetProjector,
    QeScfSavedStateManifestArtifactIdentity,
    QeScfSavedStateRetainedArtifact,
    QeScfSavedStateRetentionReference,
    QeScfSavedStateVerificationEvidenceIdentity,
)
from projectkoios.integrations.quantumespresso.pw.scf.saved_state_artifact_set_workflow import (  # noqa: E501
    QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR,
    QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING,
    QeScfSavedStateArtifactSetProjectorIntegration,
    QeScfSavedStateArtifactSetWorkflowFirer,
)
from projectkoios.integrations.quantumespresso.saved_state import (
    QeSavedStateArtifact,
    QeSavedStateArtifactRole,
    QeSavedStateCalculation,
    QeSavedStateManifest,
    QeSavedStateManifestJsonCodec,
    QeSavedStatePseudopotential,
)
from projectkoios.workflow.actions import (
    ExperimentalWorkflowAsciiOutputMappingDescriptor,
    ExperimentalWorkflowFiringRequestCoordinates,
    ExperimentalWorkflowPureActionInputMappingDescriptor,
    ExperimentalWorkflowSelectedBindingEncoder,
    ExperimentalWorkflowSelectedBindingEvidence,
    ExperimentalWorkflowSelectedBindingRepresentationProfileIdentity,
)
from projectkoios.workflow.compilation import (
    ExperimentalWorkflowPureActionCpnPlanFactory,
    ExperimentalWorkflowPureActionExecutionBindings,
    ExperimentalWorkflowPureActionExecutionPlan,
    ExperimentalWorkflowPureActionInputBindings,
    ExperimentalWorkflowPureActionInputPlan,
    experimental_shadow_cpn_execution_profile,
)
from projectkoios.workflow.execution import (
    ExperimentalWorkflowPureActionCommittedReplayService,
    ExperimentalWorkflowPureActionCommittedReplayStatus,
    ExperimentalWorkflowPureActionDurableCpnCommitService,
    ExperimentalWorkflowPureActionDurableCpnReplayService,
    ExperimentalWorkflowPureActionDurableCpnReplayStatus,
    ExperimentalWorkflowPureActionFiringService,
    ExperimentalWorkflowPureActionFiringStatus,
    ExperimentalWorkflowPureActionInvocationService,
    ExperimentalWorkflowPureActionInvocationStatus,
    ExperimentalWorkflowPureActionSafetyStateReadStatus,
    ExperimentalWorkflowPureActionSafetyStateReplayService,
)
from projectkoios.workflow.persistence import (
    ExperimentalSQLitePureActionReservationRepository,
)
from projectkoios.workflow.petrinet.colored import (
    ColoredPetriNetArcDefinition,
    ColoredPetriNetArcIdentity,
    ColoredPetriNetBindingSelector,
    ColoredPetriNetBindingVariableIdentity,
    ColoredPetriNetColorDefinition,
    ColoredPetriNetColorIdentity,
    ColoredPetriNetDefinition,
    ColoredPetriNetDefinitionIdentity,
    ColoredPetriNetGuardExpression,
    ColoredPetriNetGuardOperator,
    ColoredPetriNetInputInscription,
    ColoredPetriNetInputMode,
    ColoredPetriNetMarking,
    ColoredPetriNetMarkingIdentity,
    ColoredPetriNetOutputInscription,
    ColoredPetriNetPlaceDefinition,
    ColoredPetriNetPlaceIdentity,
    ColoredPetriNetPlaceMarking,
    ColoredPetriNetToken,
    ColoredPetriNetTokenPattern,
    ColoredPetriNetTokenTemplate,
    ColoredPetriNetTransitionDefinition,
    ColoredPetriNetTransitionEnabler,
    ColoredPetriNetTransitionIdentity,
    ColoredPetriNetValue,
    ColoredPetriNetValueExpression,
    ColoredPetriNetValueExpressionKind,
    ColoredPetriNetValueKind,
)
from projectkoios.workflow.runtime import (
    ExperimentalWorkflowPureActionCommitStatus,
    ExperimentalWorkflowPureActionCurrentPredecessor,
    ExperimentalWorkflowPureActionInputAuthorizationService,
    ExperimentalWorkflowPureActionInputAuthorizationStatus,
    ExperimentalWorkflowPureActionInputSourceLoadStatus,
    ExperimentalWorkflowPureActionInputSourceReference,
    ExperimentalWorkflowPureActionReservationLifecycleReadStatus,
    ExperimentalWorkflowPureActionReservationLifecycleReplayService,
    ExperimentalWorkflowPureActionReservationLifecycleState,
    ExperimentalWorkflowPureActionReservationService,
    ExperimentalWorkflowPureActionReserveStatus,
)
from projectkoios.workflow_sdk.identities import (
    WorkflowAttemptIdentity,
    WorkflowMarkingIdentity,
    WorkflowNetInstanceIdentity,
    WorkflowOccurrenceIdentity,
)

_SHA_A = "a" * 64
_SHA_B = "b" * 64
_SHA_C = "c" * 64
_SHA_D = "d" * 64


class _CountingProjectorFirer(QeScfSavedStateArtifactSetWorkflowFirer):
    __slots__ = ("calls",)

    def __init__(self) -> None:
        self.calls = 0

    def _project(
        self,
        *,
        request: QeScfSavedStateArtifactSetProjectionRequest,
    ) -> QeScfSavedStateArtifactSetProjectionResult:
        self.calls += 1
        return QeScfSavedStateArtifactSetProjector().action(request=request)


def test_owner_source_repository_retains_exact_immutable_request(
    tmp_path: Path,
) -> None:
    repository = QeScfSavedStateProjectionRequestSourceRepository(
        tmp_path / "owner-private-sources"
    )
    request = _domain_request()

    reference = repository.retain(request)
    repeated = repository.retain(request)
    loaded = repository.load(reference)

    assert repeated == reference
    assert loaded.status is ExperimentalWorkflowPureActionInputSourceLoadStatus.LOADED
    assert loaded.evidence is not None
    assert (
        loaded.evidence.payload.payload_sha256
        == hashlib.sha256(loaded.evidence.payload.payload).hexdigest()
    )
    assert reference.source_kind == QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND
    assert (
        reference.source_profile_identity
        == QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE
    )
    assert str(repository.root) not in reference.source_identity

    retained_file = next(repository.root.glob("*.json"))
    assert stat.S_IMODE(retained_file.stat().st_mode) == 0o600
    absent_reference = ExperimentalWorkflowPureActionInputSourceReference(
        source_kind=reference.source_kind,
        source_profile_identity=reference.source_profile_identity,
        source_identity=f"qe-scf-saved-state-projection-request.sha256.{'0' * 64}",
    )
    absent = repository.load(absent_reference)
    assert absent.status is ExperimentalWorkflowPureActionInputSourceLoadStatus.ABSENT
    incompatible_reference = ExperimentalWorkflowPureActionInputSourceReference(
        source_kind=reference.source_kind,
        source_profile_identity=reference.source_profile_identity,
        source_identity="other-owner-source",
    )
    incompatible = repository.load(incompatible_reference)
    assert (
        incompatible.status
        is ExperimentalWorkflowPureActionInputSourceLoadStatus.INCOMPATIBLE
    )

    retained_file.write_bytes(b"{}")
    corrupt = repository.load(reference)
    assert corrupt.status is ExperimentalWorkflowPureActionInputSourceLoadStatus.CORRUPT
    assert corrupt.evidence is None


def test_real_qe_owner_action_commits_and_replays_without_reinvocation(
    tmp_path: Path,
) -> None:
    definition, predecessor_marking, selected = _cpn_fixture()
    source_repository = QeScfSavedStateProjectionRequestSourceRepository(
        tmp_path / "owner-private-sources"
    )
    domain_request = _domain_request()
    source_reference = source_repository.retain(domain_request)
    assert source_reference.identity.value == (
        "03eb0408eb031e2e951b79a265048219d2c3800b3556576026e441341e75ae39"
    )
    firer = _CountingProjectorFirer()
    integration = QeScfSavedStateArtifactSetProjectorIntegration(
        package_version="0.1.0.dev0",
        distribution_sha256=(
            "a7a6a889ad660ab4ad96e452c131ac24cc98a005d36d7526a270da278529c7b9"
        ),
        firer=firer,
    )
    input_bindings = _input_bindings(integration, definition)
    assert integration.manifest.identity.value == (
        "140197dc0fd386c7c9e433f3ff47c609d5b9ddfef4dd3b3620cecf1d73bf8644"
    )
    assert input_bindings.input_plan.execution_plan.identity.value == (
        "a0f9aa9d5abd12da4e5099cc60c9f26063505cdd988d00898c3b8f1250a98271"
    )
    assert input_bindings.execution_bindings.identity.value == (
        "a54ebcbbf88998d7fd3215bc00a13c885f514790febcab40364e3b1aea02126f"
    )
    assert input_bindings.identity.value == (
        "ca98772a5cce04065134cdb4d3d57a39712c0c655aab0076b0d75812ca7493e5"
    )
    cpn_plan = ExperimentalWorkflowPureActionCpnPlanFactory().execute(
        input_plan=input_bindings.input_plan,
        definition=definition,
        execution_profile=experimental_shadow_cpn_execution_profile(),
    )
    net_identity = WorkflowNetInstanceIdentity("qe-scf-pilot.net:1")
    coordinates = ExperimentalWorkflowFiringRequestCoordinates(
        net_instance_identity=net_identity,
        predecessor_marking_identity=WorkflowMarkingIdentity(
            predecessor_marking.identity.value
        ),
        predecessor_revision=0,
        occurrence_identity=WorkflowOccurrenceIdentity("qe-scf-pilot.occurrence:1"),
        attempt_identity=WorkflowAttemptIdentity("qe-scf-pilot.attempt:1"),
        attempt_ordinal=0,
    )

    authorized_result = ExperimentalWorkflowPureActionInputAuthorizationService(
        source_repository
    ).execute(
        input_bindings=input_bindings,
        selected_binding_evidence=selected,
        coordinates=coordinates,
        source_references=(source_reference,),
    )
    assert (
        authorized_result.status
        is ExperimentalWorkflowPureActionInputAuthorizationStatus.AUTHORIZED
    )
    assert authorized_result.authorized_inputs is not None
    authorized = authorized_result.authorized_inputs
    assert authorized.identity.value == (
        "a69fcf048f90500b0b35ea7153ccd8e15a1b7553ffd36a9aab0e2d53acb09b3d"
    )

    durable_repository = ExperimentalSQLitePureActionReservationRepository(
        tmp_path / "workflow-private" / "pure-action.sqlite3",
        predecessors=(
            ExperimentalWorkflowPureActionCurrentPredecessor(
                net_instance_identity=net_identity,
                marking_identity=coordinates.predecessor_marking_identity,
                revision=coordinates.predecessor_revision,
            ),
        ),
    )
    reservation_service = ExperimentalWorkflowPureActionReservationService(
        durable_repository,
        source_repository,
    )
    reserved = reservation_service.reserve(
        authorized_inputs=authorized,
        cpn_plan=cpn_plan,
    )
    assert reserved.status is ExperimentalWorkflowPureActionReserveStatus.RESERVED
    assert reserved.reservation is not None

    invocation = ExperimentalWorkflowPureActionInvocationService(
        reservation_service
    ).execute(
        authorized_inputs=authorized,
        reservation_result=reserved,
        integration=integration,
        transition=definition.transitions[0],
    )
    assert invocation.status is ExperimentalWorkflowPureActionInvocationStatus.MAPPED
    assert firer.calls == 1

    firing = ExperimentalWorkflowPureActionFiringService(reservation_service).execute(
        authorized_inputs=authorized,
        reservation_result=reserved,
        invocation_outcome=invocation,
        cpn_plan=cpn_plan,
        definition=definition,
        predecessor_marking=predecessor_marking,
    )
    assert firing.status is ExperimentalWorkflowPureActionFiringStatus.FIRED_CANDIDATE

    committed = ExperimentalWorkflowPureActionDurableCpnCommitService(
        reservation_service,
        durable_repository,
    ).execute(
        authorized_inputs=authorized,
        reservation_result=reserved,
        cpn_plan=cpn_plan,
        invocation_outcome=invocation,
        firing_outcome=firing,
    )
    assert committed.status is ExperimentalWorkflowPureActionCommitStatus.COMMITTED
    assert committed.commit is not None
    commit = committed.commit
    assert selected.identity.value == (
        "3ca155cd09bf8fb0cd921688a894284665bbad7f284df3c1f3bd668644765bd4"
    )
    assert authorized.admitted_inputs.request.identity.value == (
        "417d0d912f96acac7a65ff5d42cc85de670d304805a50b859a01123d2162a64d"
    )
    assert cpn_plan.identity.value == (
        "3ba808794b16953f3fceb20b9f18b204912582ea6dbe3d36100bf321b81b3411"
    )
    assert cpn_plan.execution_profile.identity.value == (
        "3321f8a87314f964af4a8fb1c8cc732e80c2b7686f1f2fbe68329d708d931173"
    )
    assert reserved.reservation.identity.value == (
        "38596e52afac8f80438b5e26fdf506f3d41dc4a500a3d40ec8b8be05377fddb6"
    )
    assert invocation.identity.value == (
        "b8cf4187884dc9e087ea4de9760e51fd016378cfba7d29ce6f62df275ac7dc52"
    )
    assert firing.identity.value == (
        "4fb981884ffee5577ab25cec6e0a940a1137a8a6a99f6707a06fdef6e81288b5"
    )
    assert firing.firing_result is not None
    assert firing.firing_result.identity.value == (
        "fa47c1246ee164eab15723cd8fe9ff8ac556259e5939d4db630135911d111ccf"
    )
    assert firing.firing_result.successor_marking.identity.value == (
        "70ae79097bc2005a6992057373fbbcc7540b1167f7485d7d29c12945cdb45fb6"
    )
    assert commit.identity.value == (
        "5c58d4827f77d95a01d52484fc4ac628a385d9984ae8e1adc3db1ea684248df4"
    )

    owner_request_bytes = authorized.admitted_inputs.request.inputs[0].payload
    assert invocation.result is not None
    owner_evidence_bytes = invocation.result.evidence[0].payload
    private_owner_values = (
        str(source_repository.root).encode("utf-8"),
        domain_request.manifest_reference.value.encode("ascii"),
        *(
            artifact.payload_reference.value.encode("ascii")
            for artifact in domain_request.retained_artifacts
        ),
    )
    database_path = durable_repository.database_path
    for forbidden in (owner_request_bytes, owner_evidence_bytes, *private_owner_values):
        assert forbidden not in database_path.read_bytes()

    shutil.rmtree(source_repository.root)
    reopened_repository = ExperimentalSQLitePureActionReservationRepository(
        database_path
    )
    owner_calls = firer.calls
    compact = ExperimentalWorkflowPureActionCommittedReplayService(
        reopened_repository
    ).execute(reserved.reservation.identity)
    refired = ExperimentalWorkflowPureActionDurableCpnReplayService(
        reopened_repository
    ).execute(commit.identity)
    lifecycle = ExperimentalWorkflowPureActionReservationLifecycleReplayService(
        reopened_repository
    ).execute(reserved.reservation.identity)
    safety = ExperimentalWorkflowPureActionSafetyStateReplayService(
        reopened_repository
    ).execute(reserved.reservation.identity)

    assert (
        compact.status is ExperimentalWorkflowPureActionCommittedReplayStatus.REPLAYED
    )
    assert (
        refired.status is ExperimentalWorkflowPureActionDurableCpnReplayStatus.REPLAYED
    )
    assert (
        lifecycle.status
        is ExperimentalWorkflowPureActionReservationLifecycleReadStatus.FOUND
    )
    assert tuple(event.state for event in lifecycle.events) == (
        ExperimentalWorkflowPureActionReservationLifecycleState.RESERVED,
        ExperimentalWorkflowPureActionReservationLifecycleState.COMMITTED,
    )
    assert tuple(event.identity.value for event in lifecycle.events) == (
        "2f59dd5b34f32717b6928f27be19b449ede6d9ee2d4418b2daa0bc3e7bdced54",
        "a8fef9583c9dd56558099b8d1e1209164ce04544909ccfe9e2d2a28bcd39a103",
    )
    assert compact.event_sha256 == (
        "f6968d85a163d28563de41a287f37f91a489a88e7bf8f65307d098c68aa1a61a"
    )
    retained_reservation = lifecycle.events[0].reservation
    assert (
        retained_reservation.execution_plan_identity
        == input_bindings.input_plan.execution_plan.identity
    )
    assert (
        retained_reservation.execution_bindings_identity
        == input_bindings.execution_bindings.identity
    )
    assert safety.status is ExperimentalWorkflowPureActionSafetyStateReadStatus.FOUND
    assert safety.snapshot is not None
    assert safety.snapshot.committed_snapshot.record.commit_identity == commit.identity
    assert refired.firing_result == firing.firing_result
    assert safety.snapshot.successor_marking == firing.firing_result.successor_marking
    for forbidden in (owner_request_bytes, owner_evidence_bytes, *private_owner_values):
        assert forbidden not in database_path.read_bytes()
    assert firer.calls == owner_calls == 1


def _input_bindings(
    integration: QeScfSavedStateArtifactSetProjectorIntegration,
    definition: ColoredPetriNetDefinition,
) -> ExperimentalWorkflowPureActionInputBindings:
    mapping = ExperimentalWorkflowAsciiOutputMappingDescriptor(
        transition_binding=QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING,
        firer_descriptor=QE_SCF_SAVED_STATE_ARTIFACT_SET_FIRER_DESCRIPTOR,
        output_role="artifact_set_identity",
        external_variable_identity=ColoredPetriNetBindingVariableIdentity(
            "artifact_set_identity"
        ),
        external_value_kind=ColoredPetriNetValueKind.STRING,
        mapping_version="qe-scf-saved-state-artifact-set:0",
    )
    plan = ExperimentalWorkflowPureActionExecutionPlan(
        selected_binding_profile_identity=(
            ExperimentalWorkflowSelectedBindingRepresentationProfileIdentity(
                ExperimentalWorkflowSelectedBindingEncoder().profile_identity
            )
        ),
        output_mapping_descriptor=mapping,
    )
    bindings = ExperimentalWorkflowPureActionExecutionBindings(
        execution_plan=plan,
        integration_manifest=integration.manifest,
    )
    input_plan = ExperimentalWorkflowPureActionInputPlan(
        execution_plan=plan,
        input_mappings=(
            ExperimentalWorkflowPureActionInputMappingDescriptor(
                input_role="projection_request",
                source_kind=QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_KIND,
                source_profile_identity=(
                    QE_SCF_SAVED_STATE_PROJECTION_REQUEST_SOURCE_PROFILE
                ),
                mapping_version="qe-scf-saved-state-projection-request:0",
            ),
        ),
    )
    assert definition.identity.value == (
        QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING.definition_identity.value
    )
    return ExperimentalWorkflowPureActionInputBindings(
        input_plan=input_plan,
        execution_bindings=bindings,
    )


def _cpn_fixture() -> tuple[
    ColoredPetriNetDefinition,
    ColoredPetriNetMarking,
    ExperimentalWorkflowSelectedBindingEvidence,
]:
    color = ColoredPetriNetColorDefinition(
        ColoredPetriNetColorIdentity("qe-scf-pilot.identity"),
        (ColoredPetriNetValueKind.STRING,),
    )
    pending = ColoredPetriNetPlaceDefinition(
        ColoredPetriNetPlaceIdentity("qe-scf-pilot.pending"),
        (color.identity,),
    )
    projected = ColoredPetriNetPlaceDefinition(
        ColoredPetriNetPlaceIdentity("qe-scf-pilot.projected"),
        (color.identity,),
    )
    candidate = ColoredPetriNetBindingVariableIdentity("candidate")
    artifact_set_identity = ColoredPetriNetBindingVariableIdentity(
        "artifact_set_identity"
    )
    transition = ColoredPetriNetTransitionDefinition(
        identity=ColoredPetriNetTransitionIdentity(
            QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING.transition_identity.value
        ),
        input_variable_identities=(candidate,),
        external_output_variable_identities=(artifact_set_identity,),
        guard=ColoredPetriNetGuardExpression(ColoredPetriNetGuardOperator.TRUE),
    )
    definition = ColoredPetriNetDefinition(
        identity=ColoredPetriNetDefinitionIdentity(
            QE_SCF_SAVED_STATE_ARTIFACT_SET_TRANSITION_BINDING.definition_identity.value
        ),
        colors=(color,),
        places=(pending, projected),
        transitions=(transition,),
        arcs=(
            ColoredPetriNetArcDefinition(
                identity=ColoredPetriNetArcIdentity("qe-scf-pilot.consume"),
                place_identity=pending.identity,
                transition_identity=transition.identity,
                input_inscription=ColoredPetriNetInputInscription(
                    mode=ColoredPetriNetInputMode.CONSUME,
                    patterns=(
                        ColoredPetriNetTokenPattern(
                            variable_identity=candidate,
                            allowed_color_identities=(color.identity,),
                        ),
                    ),
                ),
            ),
            ColoredPetriNetArcDefinition(
                identity=ColoredPetriNetArcIdentity("qe-scf-pilot.produce"),
                place_identity=projected.identity,
                transition_identity=transition.identity,
                output_inscription=ColoredPetriNetOutputInscription(
                    templates=(
                        ColoredPetriNetTokenTemplate(
                            color_identity=color.identity,
                            value_expression=ColoredPetriNetValueExpression(
                                kind=ColoredPetriNetValueExpressionKind.VARIABLE,
                                variable_identity=artifact_set_identity,
                            ),
                        ),
                    ),
                ),
            ),
        ),
        transition_priority=(transition.identity,),
    )
    marking = ColoredPetriNetMarking(
        identity=ColoredPetriNetMarkingIdentity("qe-scf-pilot.marking:0"),
        definition_identity=definition.identity,
        places=(
            ColoredPetriNetPlaceMarking(
                place_identity=pending.identity,
                tokens=(
                    ColoredPetriNetToken(
                        color_identity=color.identity,
                        value=ColoredPetriNetValue(
                            kind=ColoredPetriNetValueKind.STRING,
                            value="qe-scf-saved-state-candidate",
                        ),
                    ),
                ),
            ),
            ColoredPetriNetPlaceMarking(
                place_identity=projected.identity,
                tokens=(),
            ),
        ),
    )
    enabled = ColoredPetriNetTransitionEnabler().execute(definition, marking)
    selected = ColoredPetriNetBindingSelector().execute(definition, enabled)
    return (
        definition,
        marking,
        ExperimentalWorkflowSelectedBindingEvidence(
            enablement_result=enabled,
            selection_result=selected,
        ),
    )


def _domain_request() -> QeScfSavedStateArtifactSetProjectionRequest:
    pseudopotential = QeSavedStatePseudopotential(
        symbol="Si",
        filename="Si.upf",
        sha256=_SHA_D,
        byte_size=4,
    )
    manifest = QeSavedStateManifest(
        schema_version=1,
        prefix="si",
        calculation=QeSavedStateCalculation.scf,
        producer_program="pw.x",
        producer_version="7.5",
        executable_sha256="f" * 64,
        input_sha256="1" * 64,
        structure_id="Si.PrimitiveUnitCell",
        structure_sha256="2" * 64,
        pseudopotentials=(pseudopotential,),
        artifacts=(
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.qexsd,
                relative_path="si.save/data-file-schema.xml",
                sha256=_SHA_A,
                byte_size=1,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.charge_density,
                relative_path="si.save/charge-density.dat",
                sha256=_SHA_B,
                byte_size=2,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.wavefunction,
                relative_path="si.save/wfc1.dat",
                sha256=_SHA_C,
                byte_size=3,
            ),
            QeSavedStateArtifact(
                role=QeSavedStateArtifactRole.pseudopotential,
                relative_path="si.save/Si.upf",
                sha256=_SHA_D,
                byte_size=4,
            ),
        ),
    )
    manifest_payload = QeSavedStateManifestJsonCodec().dumps(manifest)
    retained = tuple(
        QeScfSavedStateRetainedArtifact(
            role=artifact.role,
            relative_path=artifact.relative_path,
            sha256=artifact.sha256,
            byte_size=artifact.byte_size,
            payload_reference=QeScfSavedStateRetentionReference(
                f"pilot.retention.artifact:{index}"
            ),
        )
        for index, artifact in enumerate(manifest.artifacts)
    )
    return QeScfSavedStateArtifactSetProjectionRequest(
        manifest=manifest,
        manifest_payload=manifest_payload,
        manifest_reference=QeScfSavedStateRetentionReference(
            "pilot.retention.manifest"
        ),
        manifest_artifact_identity=QeScfSavedStateManifestArtifactIdentity(
            "pilot.manifest.identity"
        ),
        retained_artifacts=retained,
        source_verification_evidence_identity=(
            QeScfSavedStateVerificationEvidenceIdentity("pilot.verification.evidence")
        ),
    )
