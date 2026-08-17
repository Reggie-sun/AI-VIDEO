from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    ActorIdentity,
    ApprovedRepairReceipt,
    AssetRegistrySnapshot,
    DependencyLifecycle,
    DependencyNodeState,
    ProductionProject,
    ProductionManifest,
    ProjectSnapshotPointer,
    QaLayoutRules,
    QaLayer,
    QaPolicy,
    QaTechnicalThresholds,
    NamedFingerprint,
    RepairAction,
    RepairAuthorization,
    RepairRequest,
    ReviewAttemptPhase,
    ReviewRequest,
    ReviewRequestPointer,
    RendererKind,
    RendererSelectionReceipt,
    RegistrySnapshotPointer,
    RegistryDependencyEvidence,
    RecoveryDisposition,
    RenderStateSnapshotPointer,
    Shot,
    SourceReference,
    StateCommitStatus,
    StateCommitAttempt,
    TechnicalReviewContext,
    ToolIdentity,
)
from ai_video.production.project import load_production_project, load_production_project_candidate
from ai_video.production.registry import load_asset_registry
from ai_video.production.registry import registry_semantic_sha256
import ai_video.production.state_commit as state_commit
from ai_video.production.state_commit import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    CommitPhase,
    NoopCrashInjector,
    PreparedArtifact,
    ProductionStateCommitter,
    RecordRenderFailureRequest,
    RenderAttemptPaths,
    StateCommitRequest,
    _NativeFileOps,
    _canonical_json_bytes,
    _canonical_yaml_bytes,
    _owned_temp_name,
    prepare_dependency_graph_transition,
)
from ai_video.production.paths import (
    canonical_render_attempt_root,
    canonical_render_output_path,
    canonical_render_receipt_path,
    canonical_render_source_asset_path,
    canonical_render_source_index_path,
    canonical_render_source_root,
    canonical_render_state_path,
    canonical_render_timeline_path,
    canonical_review_request_path,
    canonical_renderer_source_receipt_path,
)
import production_project_factory as project_factory


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def make_qa_policy(
    *, version: str = "1", repair_authorities: tuple[ActorIdentity, ...] = ()
) -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id=f"qa-policy-{version}",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=f"qa-policy-{version}",
            source_provenance=(
                SourceReference(kind="derived", reference="p6-test-fixture"),
            ),
            policy_id="qa-default",
            policy_version=version,
            required_layers=(QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.STRATEGY),
            technical_thresholds=QaTechnicalThresholds(
                black_luma_max_milli=10,
                silence_peak_max_millidb=-60_000,
                clipping_peak_min_millidb=-100,
            ),
            layout_rules=QaLayoutRules(
                safe_area_inset_milli=50,
                caption_overflow_tolerance_milli=0,
            ),
            strategy_rules_version="1",
            semantic_requirement="optional",
            repair_authorities=repair_authorities,
        )
    )


def test_p6_policy_activation_migrates_23_and_exact_replay_is_noop(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    writer = ProductionStateCommitter(tmp_path)
    committed = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=before.manifest_revision,
        attempt_id="qa-policy-1",
    )
    assert committed.schema_version == "2.4"
    assert committed.active_dependency_graph == before.active_dependency_graph
    assert committed.dependency_states == before.dependency_states
    assert committed.active_qa_policy is not None
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.qa_policy == make_qa_policy()

    replay = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=before.manifest_revision,
        attempt_id="qa-policy-1",
    )
    assert replay == committed


def test_review_request_is_consumed_once_before_analysis(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    before = read_manifest(tmp_path)
    current = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=before.manifest_revision,
        attempt_id="qa-policy-review-consume",
    )
    assert current.active_dependency_graph is not None
    assert current.active_qa_policy is not None
    render_hash = "9" * 64
    render_pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{render_hash}.json"),
        revision=1,
        content_hash=render_hash,
        file_sha256="8" * 64,
    )
    context = TechnicalReviewContext(
        render_output_sha256="7" * 64,
        timeline_fingerprint="6" * 64,
        windows=(),
        measurement_contract_version="1",
    )
    request = seal_artifact(
        ReviewRequest(
            artifact_id="review-request-once",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="review-request-once",
            source_provenance=(
                SourceReference(kind="derived", reference="p6-test-fixture"),
            ),
            request_id="review-request-once",
            base_manifest_revision=current.manifest_revision,
            dependency_graph=current.active_dependency_graph,
            dependency_states_hash=canonical_sha256(
                {"dependency_states": [
                    item.model_dump(mode="json")
                    for item in current.dependency_states
                ]}
            ),
            render_state=render_pointer,
            render_output_sha256=context.render_output_sha256,
            timeline_fingerprint=context.timeline_fingerprint,
            qa_policy=current.active_qa_policy,
            requested_layers=(QaLayer.TECHNICAL,),
            evidence_tool_identities=(ToolIdentity(name="video-analysis", version="1"),),
            technical_context=context,
        )
    )
    payload = _canonical_json_bytes(request)
    request_path = canonical_review_request_path(request.content_hash)
    absolute_request_path = tmp_path / request_path
    absolute_request_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_request_path.write_bytes(payload)
    pointer = ReviewRequestPointer(
        path=request_path,
        request_id=request.request_id,
        content_hash=request.content_hash,
        file_sha256=hashlib.sha256(payload).hexdigest(),
    )
    running = StateCommitAttempt(
        attempt_id="review-attempt-once",
        operation="review",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=current.manifest_revision,
        base_project=current.active_project,
        base_registry=current.active_registry,
        candidate_artifacts_hash="5" * 64,
        review_request=pointer,
        review_phase=ReviewAttemptPhase.REQUESTED,
        started_at="2026-08-17T00:00:00Z",
    )
    begun = current.model_copy(
        update={
            "manifest_revision": current.manifest_revision + 1,
            "attempts": current.attempts + (running,),
        }
    )
    (tmp_path / "state/manifest.json").write_text(
        begun.model_dump_json(indent=2), encoding="utf-8"
    )

    consumed = writer.consume_review_analysis_request(
        review_request=pointer,
        expected_manifest_revision=begun.manifest_revision,
    )
    after = read_manifest(tmp_path)
    assert consumed == request
    assert after.attempts[-1].review_phase.value == "evidence"

    with pytest.raises(AiVideoError) as exc_info:
        writer.consume_review_analysis_request(
            review_request=pointer,
            expected_manifest_revision=after.manifest_revision,
        )
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN


def test_unapproved_repair_is_rejected_before_any_commit_attempt(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    before_policy = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    current = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=before_policy.manifest_revision,
        attempt_id="qa-policy-1",
    )
    request = project_factory.make_revision_two_request(
        tmp_path, attempt_id="unapproved-repair"
    )
    request = replace(request, operation="repair")

    with pytest.raises(AiVideoError) as exc_info:
        writer.commit(request)

    assert exc_info.value.code is ErrorCode.REPAIR_AUTHORIZATION_REQUIRED
    after = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    assert after == current
    assert not any(item.attempt_id == "unapproved-repair" for item in after.attempts)


def test_caller_signed_repair_approval_is_rejected_without_trusted_authorizer(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    trusted = ActorIdentity(actor_id="human-reviewer", actor_kind="human")
    writer = ProductionStateCommitter(tmp_path)
    before = read_manifest(tmp_path)
    current = writer.activate_qa_policy(
        make_qa_policy(repair_authorities=(trusted,)),
        expected_manifest_revision=before.manifest_revision,
        attempt_id="qa-policy-repair-authority",
    )
    assert current.active_dependency_graph is not None
    assert current.active_qa_policy is not None
    actor = ActorIdentity(actor_id="codex", actor_kind="codex")
    action = RepairAction(kind="caption_layout", parameters_fingerprint="4" * 64)
    target = current.dependency_states[0].node_id
    scope = canonical_sha256(
        {
            "repair_id": "repair-self-signed",
            "actor": actor.model_dump(mode="json"),
            "action": action.model_dump(mode="json"),
            "target_artifact_ids": ["caption-1"],
            "target_node_ids": [target],
            "expected_invalidation_node_ids": [target],
        }
    )
    render_hash = "9" * 64
    request = seal_artifact(
        RepairRequest(
            artifact_id="repair-request-self-signed",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="repair-request-self-signed",
            source_provenance=(
                SourceReference(kind="derived", reference="p6-test-fixture"),
            ),
            repair_id="repair-self-signed",
            base_manifest_revision=current.manifest_revision,
            dependency_graph=current.active_dependency_graph,
            dependency_states_hash=canonical_sha256(
                {"dependency_states": [
                    item.model_dump(mode="json") for item in current.dependency_states
                ]}
            ),
            render_state=RenderStateSnapshotPointer(
                path=Path(f"state/render/states/{render_hash}.json"),
                revision=1,
                content_hash=render_hash,
                file_sha256="8" * 64,
            ),
            render_output_sha256="7" * 64,
            timeline_fingerprint="6" * 64,
            qa_policy=current.active_qa_policy,
            review_receipt_ids=("review-1",),
            issue_ids=("caption-overflow",),
            evidence_ids=("evidence-1",),
            root_cause_hypothesis="caption box exceeds safe area",
            selected_repair_action=action,
            exact_target_artifact_ids=("caption-1",),
            exact_target_node_ids=(target,),
            expected_invalidation_node_ids=(target,),
            actor=actor,
            authorization=RepairAuthorization(
                authorization_id="caller-signed",
                authorized=True,
                authorized_by=trusted,
                scope_fingerprint=scope,
            ),
            before_fingerprints=(
                NamedFingerprint(name="caption", fingerprint="3" * 64),
            ),
        )
    )
    receipt = seal_artifact(
        ApprovedRepairReceipt.model_validate(
            {
                **request.model_dump(mode="python"),
                "artifact_id": "approved-repair-self-signed",
                "content_hash": ZERO_HASH,
                "request_content_hash": request.content_hash,
            }
        )
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_approved_repair_receipt(
            request,
            receipt,
            expected_manifest_revision=current.manifest_revision,
            attempt_id="approve-self-signed",
        )

    assert exc_info.value.code is ErrorCode.REPAIR_AUTHORIZATION_REQUIRED
    assert read_manifest(tmp_path).active_approved_repair is None


def test_manifest_24_preserves_p5_transition_support(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    current = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="qa-policy-1",
    )
    request = project_factory.make_revision_two_request(
        tmp_path, attempt_id="manifest-24-p5-transition"
    )
    request, _ = project_factory.attach_p5_dependency_transition(tmp_path, request)

    committed = writer.commit(request)

    assert committed.schema_version == "2.4"
    assert committed.active_dependency_graph == request.dependency_graph_transition.candidate_dependency_graph
    assert committed.active_qa_policy == current.active_qa_policy


def test_recovery_reports_active_and_historical_p6_policy(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    first = writer.activate_qa_policy(
        make_qa_policy(version="1"),
        expected_manifest_revision=manifest.manifest_revision,
        attempt_id="qa-policy-1",
    )
    first_path = first.active_qa_policy.path
    second = writer.activate_qa_policy(
        make_qa_policy(version="2"),
        expected_manifest_revision=first.manifest_revision,
        attempt_id="qa-policy-2",
    )

    report = writer.recover()
    dispositions = {item.path: item.disposition for item in report.items}
    assert dispositions[second.active_qa_policy.path] is RecoveryDisposition.ACTIVE
    assert dispositions[first_path] is RecoveryDisposition.ORPHAN_PRESERVED


def test_p6_post_replace_process_interrupt_maps_to_outcome_unknown(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    before = read_manifest(tmp_path)
    writer = ProductionStateCommitter(
        tmp_path,
        crash_injector=ProcessInterruptInjector(
            CommitPhase.AFTER_MANIFEST_REPLACE, 1, KeyboardInterrupt
        ),
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.activate_qa_policy(
            make_qa_policy(),
            expected_manifest_revision=before.manifest_revision,
            attempt_id="qa-policy-post-replace-interrupt",
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert read_manifest(tmp_path).schema_version == "2.4"


def test_voice_lifecycle_api_persists_r1_then_mints_one_use_r2_permit(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)

    r1 = writer.begin_voice_generation(request, preview, authorization)
    assert r1.schema_version == "2.2"
    assert r1.manifest_revision == 2
    assert r1.attempts[-1].voice_phase == "request"

    permit = writer.record_voice_submit_intent(request, preview, authorization)
    r2 = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert r2.manifest_revision == 3
    assert r2.attempts[-1].voice_phase == "submit_intent"
    binding = {
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.voice_request_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "destination": authorization.destination,
        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
    }
    assert permit._validate_voice_submit_permit(**binding)
    assert permit._consume_voice_submit_permit(**binding)
    assert not permit._consume_voice_submit_permit(**binding)


def test_voice_submit_intent_exact_replay_cannot_remint_permit(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_voice_submit_intent(request, preview, authorization)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_voice_submit_permit_becomes_invalid_when_r2_manifest_changes(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    permit = writer.record_voice_submit_intent(request, preview, authorization)
    writer.record_voice_outcome_unknown(request.attempt_id, phase="submit_intent")
    binding = {
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.voice_request_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "destination": authorization.destination,
        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
    }

    assert not permit._validate_voice_submit_permit(**binding)
    assert not permit._consume_voice_submit_permit(**binding)


def test_voice_submit_permit_becomes_invalid_when_submit_intent_is_deleted(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    permit = writer.record_voice_submit_intent(request, preview, authorization)
    writer.voice_attempt_paths(request.attempt_id).submit_intent_path.unlink()
    binding = {
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.voice_request_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "destination": authorization.destination,
        "budget_reservation_receipt_id": authorization.budget_reservation_receipt_id,
        "egress_authorization_receipt_id": authorization.egress_authorization_receipt_id,
    }

    assert not permit._validate_voice_submit_permit(**binding)
    assert not permit._consume_voice_submit_permit(**binding)


def test_voice_submit_intent_rejects_replaced_r1_evidence_before_permit(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    r1 = writer.begin_voice_generation(request, preview, authorization)
    writer.voice_attempt_paths(request.attempt_id).preview_path.write_bytes(b"{}")

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_voice_submit_intent(request, preview, authorization)

    after = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    if isinstance(exc_info.value, AiVideoError):
        assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert after == r1
    assert after.attempts[-1].voice_phase == "request"


def test_voice_attempt_paths_are_exact_and_contained(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    paths = ProductionStateCommitter(tmp_path).voice_attempt_paths("voice-attempt")

    assert paths.attempt_root == tmp_path / "state/voice/attempts/voice-attempt"
    assert paths.audio_candidate_path == paths.attempt_root / "candidate.wav"
    assert paths.submit_intent_path == paths.attempt_root / "submit-intent.json"


def test_prepare_audio_registry_commit_is_pure_and_uses_existing_writer(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    project, registry = project_factory.load_initial_models(tmp_path)
    p4_registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=registry.assets,
    )
    revision = state_commit.registry_semantic_sha256(p4_registry)
    p4_registry = p4_registry.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )
    before = set(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    request = state_commit.prepare_audio_registry_commit(
        manifest=manifest,
        project=project,
        base_registry=registry,
        registry=p4_registry,
        attempt_id="audio-import-1",
        artifacts=(),
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path,
            (tmp_path / manifest.active_project.path).read_bytes(),
            manifest.active_project.file_sha256,
        ),
    )

    after = set(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert request.operation == "audio_import"
    assert request.next_project.content_hash == manifest.active_project.content_hash
    assert before == after


def test_prepare_audio_registry_commit_rejects_mutated_base_record(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    project, registry = project_factory.load_initial_models(tmp_path)
    forged = registry.assets[0].model_copy(update={"usage_license": "forged"})
    candidate = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=(forged, *registry.assets[1:]),
    )
    revision = state_commit.registry_semantic_sha256(candidate)
    candidate = candidate.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )

    with pytest.raises(AiVideoError) as exc_info:
        state_commit.prepare_audio_registry_commit(
            manifest=manifest,
            project=project,
            base_registry=registry,
            registry=candidate,
            attempt_id="audio-import-forged-base",
            artifacts=(),
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


@pytest.mark.parametrize(
    "asset_id",
    ("voice-dialogue", "bgm-theme", "sfx-hit", "caption-asset-1"),
)
def test_prepare_audio_registry_commit_accepts_each_p4_asset_type_including_caption_only(
    tmp_path: Path,
    asset_id: str,
) -> None:
    loaded, _ = project_factory.make_p4_composition_fixture(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    project, base_registry = project_factory.load_initial_models(tmp_path)
    record = next(item for item in loaded.registry.assets if item.asset_id == asset_id)
    candidate = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=base_registry.assets + (record,),
    )
    revision = state_commit.registry_semantic_sha256(candidate)
    candidate = candidate.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )
    artifact_paths = [record.artifact_path]
    if (
        record.caption_metadata is not None
        and record.caption_metadata.style_content_hash is not None
    ):
        artifact_paths.append(
            Path(
                f"assets/styles/{record.caption_metadata.style_content_hash}.json"
            )
        )
    artifacts = tuple(
        PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())
        for path in artifact_paths
        for payload in ((tmp_path / path).read_bytes(),)
    )

    request = state_commit.prepare_audio_registry_commit(
        manifest=manifest,
        project=project,
        base_registry=base_registry,
        registry=candidate,
        attempt_id=f"audio-import-{asset_id}",
        artifacts=artifacts,
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path,
            (tmp_path / manifest.active_project.path).read_bytes(),
            manifest.active_project.file_sha256,
        ),
    )

    registry_artifact = next(
        item for item in request.artifacts if item.relative_path == request.next_registry.path
    )
    reopened = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
    assert reopened.assets[len(base_registry.assets) :] == (record,)


def test_audio_import_upgrades_manifest_and_registry_without_downgrade(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    manifest = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    project, registry = project_factory.load_initial_models(tmp_path)
    upgraded_registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=registry.assets,
    )
    revision = state_commit.registry_semantic_sha256(upgraded_registry)
    upgraded_registry = upgraded_registry.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )
    request = state_commit.prepare_audio_registry_commit(
        manifest=manifest,
        project=project,
        base_registry=registry,
        registry=upgraded_registry,
        attempt_id="audio-import-version-upgrade",
        artifacts=(),
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path,
            (tmp_path / manifest.active_project.path).read_bytes(),
            manifest.active_project.file_sha256,
        ),
    )

    committed = ProductionStateCommitter(tmp_path).commit(request)
    assert committed.schema_version == "2.2"
    assert committed.active_project == manifest.active_project
    active_registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / committed.active_registry.path).read_bytes()
    )
    assert active_registry.schema_version == "2.1"
    assert committed.attempts[-1].operation == "audio_import"
    assert committed.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_audio_import_preserves_22_render_state_when_active_pair_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_factory.write_production_project(tmp_path)
    first = ProductionStateCommitter(tmp_path).commit(
        project_factory.make_audio_import_upgrade_request(tmp_path)
    )
    render_pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{'a' * 64}.json"),
        revision=1,
        content_hash="a" * 64,
        file_sha256="b" * 64,
    )
    with_render = first.model_copy(update={"active_render_state": render_pointer})
    (tmp_path / "state/manifest.json").write_text(
        with_render.model_dump_json(indent=2), encoding="utf-8"
    )
    request = project_factory.make_audio_import_upgrade_request(
        tmp_path, attempt_id="audio-import-same-pair"
    )
    monkeypatch.setattr(
        state_commit,
        "load_verified_render_state",
        lambda *_args, **_kwargs: object(),
    )

    committed = ProductionStateCommitter(tmp_path).commit(request)

    assert committed.schema_version == "2.2"
    assert committed.active_project == first.active_project
    assert committed.active_registry == first.active_registry
    assert committed.active_render_state == render_pointer


def test_voice_r3_r4_activation_selects_exact_registry_and_clears_render(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path, request, authorization, expected_manifest_revision=3
    )

    r4 = writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)

    assert r4.schema_version == "2.2"
    assert r4.manifest_revision == 5
    assert r4.active_registry == activation.next_registry
    assert r4.active_render_state is None
    assert r4.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert r4.attempts[-1].voice_phase == "activate"
    assert writer.activate_voice_assets(activation, audio_asset_ids=audio_ids) == r4


def test_generated_voice_caption_is_exactly_bound_and_activated(tmp_path: Path) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=3,
        include_caption=True,
    )
    caption_ids = (f"caption-{request.attempt_id}",)

    committed = writer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=caption_ids,
    )

    registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / committed.active_registry.path).read_bytes()
    )
    audio = next(item for item in registry.assets if item.asset_id == audio_ids[0])
    caption = next(item for item in registry.assets if item.asset_id == caption_ids[0])
    assert audio.egress.retention_mode == "provider_standard"
    assert audio.egress.provider_policy_snapshot_id == "fixture-policy-receipt"
    assert caption.caption_metadata is not None
    assert caption.caption_metadata.alignment_receipt_id == (
        audio.audio_metadata.alignment_receipt_id
    )


@pytest.mark.parametrize(
    ("caption_updates", "corrupt_timing"),
    (
        ({"source_audio_asset_id": "wrong-audio"}, False),
        ({"source_audio_sha256": "f" * 64}, False),
        ({"script_hash": "f" * 64}, False),
        ({"transcript_hash": "f" * 64}, False),
        ({"alignment_receipt_id": "alignment-forged"}, False),
        ({"creation_receipt_id": "caption-receipt-forged"}, False),
        ({}, True),
    ),
)
def test_generated_voice_caption_rejects_unbound_identity_before_write(
    tmp_path: Path,
    caption_updates: dict[str, object],
    corrupt_timing: bool,
) -> None:
    project_factory.write_production_project(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()
    request = project_factory.make_voice_request(tmp_path)
    _, authorization = project_factory.make_voice_preview_and_authorization(request)

    expected_error = (AiVideoError, ValidationError) if corrupt_timing else AiVideoError
    with pytest.raises(expected_error) as exc_info:
        project_factory.make_voice_activation_request(
            tmp_path,
            request,
            authorization,
            expected_manifest_revision=3,
            include_caption=True,
            caption_updates=caption_updates,
            corrupt_caption_timing=corrupt_timing,
        )

    if isinstance(exc_info.value, AiVideoError):
        assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_voice_activation_rejects_forged_caption_registry_graph_before_write(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=3,
        include_caption=True,
    )
    caption_ids = (f"caption-{request.attempt_id}",)
    registry_artifact = next(
        item
        for item in activation.artifacts
        if item.relative_path == activation.next_registry.path
    )
    registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
    forged_assets = []
    for record in registry.assets:
        if record.asset_id not in caption_ids:
            forged_assets.append(record)
            continue
        assert record.caption_metadata is not None
        forged_assets.append(
            record.model_copy(
                update={
                    "caption_metadata": record.caption_metadata.model_copy(
                        update={"script_hash": "f" * 64}
                    )
                }
            )
        )
    forged_registry = registry.model_copy(
        update={
            "revision_id": ZERO_HASH,
            "content_hash": ZERO_HASH,
            "assets": tuple(forged_assets),
        }
    )
    revision_id = registry_semantic_sha256(forged_registry)
    forged_registry = forged_registry.model_copy(
        update={"revision_id": revision_id, "content_hash": revision_id}
    )
    forged_payload = _canonical_json_bytes(forged_registry)
    forged_path = Path(f"assets/registry.{revision_id}.json")
    forged_pointer = RegistrySnapshotPointer(
        path=forged_path,
        revision_id=revision_id,
        content_hash=revision_id,
        file_sha256=hashlib.sha256(forged_payload).hexdigest(),
    )
    forged_artifacts = tuple(
        PreparedArtifact(
            relative_path=forged_path,
            payload=forged_payload,
            file_sha256=forged_pointer.file_sha256,
        )
        if item.relative_path == activation.next_registry.path
        else item
        for item in activation.artifacts
    )
    forged = StateCommitRequest(
        attempt_id=activation.attempt_id,
        operation=activation.operation,
        expected_manifest_revision=activation.expected_manifest_revision,
        artifacts=forged_artifacts,
        next_project=activation.next_project,
        next_registry=forged_pointer,
    )
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        writer.activate_voice_assets(
            forged,
            audio_asset_ids=audio_ids,
            caption_asset_ids=caption_ids,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_voice_activation_rejects_duplicate_caption_ids_before_write(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=3,
        include_caption=True,
    )
    caption_id = f"caption-{request.attempt_id}"
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as exc_info:
        writer.activate_voice_assets(
            activation,
            audio_asset_ids=audio_ids,
            caption_asset_ids=(caption_id, caption_id),
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (tmp_path / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize(
    ("retention_mode", "policy_receipt_id"),
    (("provider_standard", "fixture-policy-receipt"), ("zero_retention", "zrm-policy-receipt")),
)
def test_voice_registry_persists_actual_policy_and_retention(
    tmp_path: Path, retention_mode: str, policy_receipt_id: str
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=3,
        retention_mode=retention_mode,
        policy_receipt_id=policy_receipt_id,
    )
    committed = writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)
    registry = AssetRegistrySnapshot.model_validate_json(
        (tmp_path / committed.active_registry.path).read_bytes()
    )
    record = next(item for item in registry.assets if item.asset_id == audio_ids[0])
    assert record.egress.retention_mode == retention_mode
    assert record.egress.provider_policy_snapshot_id == policy_receipt_id


@pytest.mark.parametrize("field", ("policy_receipt_id", "retention_mode"))
def test_voice_activation_rejects_forged_provider_policy_evidence_zero_activation(
    tmp_path: Path, field: str
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path, request, authorization, expected_manifest_revision=3
    )
    provenance_path = writer.voice_attempt_paths(request.attempt_id).provenance_path.relative_to(
        tmp_path
    )
    artifacts = []
    for artifact in activation.artifacts:
        if artifact.relative_path != provenance_path:
            artifacts.append(artifact)
            continue
        payload = json.loads(artifact.payload)
        payload[field] = (
            "forged-policy-receipt" if field == "policy_receipt_id" else "zero_retention"
        )
        encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
        artifacts.append(
            PreparedArtifact(provenance_path, encoded, hashlib.sha256(encoded).hexdigest())
        )
    forged = StateCommitRequest(
        attempt_id=activation.attempt_id,
        operation=activation.operation,
        expected_manifest_revision=activation.expected_manifest_revision,
        artifacts=tuple(artifacts),
        next_project=activation.next_project,
        next_registry=activation.next_registry,
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.activate_voice_assets(forged, audio_asset_ids=audio_ids)

    after = ProductionManifest.model_validate_json((tmp_path / "state/manifest.json").read_bytes())
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert after.active_registry == request.base_registry
    assert after.attempts[-1].voice_phase == "submit_intent"


def test_voice_activation_rejects_asset_id_not_in_exact_candidate_registry(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, _ = project_factory.make_voice_activation_request(
        tmp_path, request, authorization, expected_manifest_revision=3
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.activate_voice_assets(
            activation, audio_asset_ids=("not-in-candidate",)
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


@pytest.mark.parametrize("replay_state", ("candidate", "succeeded"))
def test_voice_replay_reconstructs_current_durable_graph_before_activation(
    tmp_path: Path, replay_state: str
) -> None:
    class _CrashAfterCandidate:
        def checkpoint(self, phase: CommitPhase) -> None:
            if phase is CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST:
                raise RuntimeError("stop at durable candidate")

    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path, request, authorization, expected_manifest_revision=3
    )
    if replay_state == "candidate":
        with pytest.raises(RuntimeError, match="durable candidate"):
            ProductionStateCommitter(
                tmp_path, crash_injector=_CrashAfterCandidate()
            ).activate_voice_assets(activation, audio_asset_ids=audio_ids)
    else:
        writer.activate_voice_assets(activation, audio_asset_ids=audio_ids)
    writer.voice_attempt_paths(request.attempt_id).outcome_path.write_bytes(b"tampered")
    manifest_before_replay = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).activate_voice_assets(
            activation, audio_asset_ids=audio_ids
        )

    after = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_bytes()
    )
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert after == manifest_before_replay
    if replay_state == "candidate":
        assert (after.active_project, after.active_registry) == (
            before.active_project,
            before.active_registry,
        )


def test_generate_voice_asset_is_only_transport_path_and_calls_provider_once(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    prepared = {}

    class _Provider:
        calls = 0

        def preview(self, candidate):
            assert candidate == request
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            self.calls += 1
            binding = {
                "attempt_id": candidate.attempt_id,
                "request_fingerprint": candidate.voice_request_fingerprint,
                "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                "destination": candidate_authorization.destination,
                "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
            }
            assert permit._consume_voice_submit_permit(**binding)
            return project_factory.make_voice_provider_result(
                request, preview, authorization
            )

    def _prepare(candidate, candidate_preview, candidate_authorization, result, paths):
        assert candidate == request
        assert candidate_preview == preview
        assert candidate_authorization == authorization
        assert result.provider_request_id == "fixture-provider-request"
        assert paths.audio_candidate_path.name == "candidate.wav"
        activation, audio_ids = project_factory.make_voice_activation_request(
            tmp_path, request, authorization, expected_manifest_revision=3
        )
        registry_artifact = next(
            item
            for item in activation.artifacts
            if item.relative_path == activation.next_registry.path
        )
        registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
        record = next(item for item in registry.assets if item.asset_id == audio_ids[0])
        audio_artifact = next(
            item for item in activation.artifacts if item.relative_path == record.artifact_path
        )
        from ai_video.production.audio import AudioProbeResult, PreparedAudioImport
        from ai_video.production.state_commit import PreparedVoiceCandidate

        metadata = record.audio_metadata
        assert metadata is not None
        probe = AudioProbeResult(
            mime_type="audio/wav",
            container_name="wav",
            file_sha256=record.sha256,
            size_bytes=record.size_bytes,
            file_device=0,
            file_inode=0,
            codec_name="pcm_s16le",
            duration_samples=metadata.duration_samples,
            sample_rate_hz=metadata.sample_rate_hz,
            channels=metadata.channels,
            channel_layout=metadata.channel_layout,
            decoded_pcm_sha256=record.sha256,
            loudness=metadata.loudness,
            loudness_receipt_id=record.sha256,
            ffmpeg=record.tool.model_copy(update={"name": "ffmpeg"}),
            ffprobe=record.tool.model_copy(update={"name": "ffprobe"}),
            content_fingerprint=record.sha256,
        )
        prepared["called"] = True
        return PreparedVoiceCandidate(
            audio=PreparedAudioImport(
                payload=audio_artifact.payload,
                probe=probe,
                asset_record=record,
            )
        )

    provider = _Provider()
    writer = ProductionStateCommitter(
        tmp_path, voice_candidate_preparer=_prepare
    )

    manifest = writer.generate_voice_asset(request, provider, authorization)

    assert provider.calls == 1
    assert prepared == {"called": True}
    assert manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_manifest_23_public_voice_requires_transition_preparer_before_provider(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    _, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _Provider:
        def preview(self, _request):
            raise AssertionError("2.3 preflight must reject before provider preview")

        def generate(self, *_args):
            raise AssertionError("2.3 preflight must reject before provider call")

    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError, match="transition preparer"):
        ProductionStateCommitter(tmp_path).generate_voice_asset(
            request, _Provider(), authorization
        )
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_manifest_23_public_voice_prepares_transition_after_local_candidate(
    tmp_path: Path,
) -> None:
    from ai_video.production.audio import AudioProbeResult, PreparedAudioImport
    from ai_video.production.state_commit import PreparedVoiceCandidate

    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _Provider:
        calls = 0

        def preview(self, candidate):
            assert candidate == request
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            self.calls += 1
            assert permit._consume_voice_submit_permit(
                attempt_id=candidate.attempt_id,
                request_fingerprint=candidate.voice_request_fingerprint,
                authorization_fingerprint=(
                    candidate_authorization.authorization_fingerprint
                ),
                destination=candidate_authorization.destination,
                budget_reservation_receipt_id=(
                    candidate_authorization.budget_reservation_receipt_id
                ),
                egress_authorization_receipt_id=(
                    candidate_authorization.egress_authorization_receipt_id
                ),
            )
            return project_factory.make_voice_provider_result(
                request, preview, authorization
            )

    def prepare_candidate(*_args):
        activation, audio_ids = project_factory.make_voice_activation_request(
            tmp_path,
            request,
            authorization,
            expected_manifest_revision=4,
        )
        registry_artifact = next(
            item
            for item in activation.artifacts
            if item.relative_path == activation.next_registry.path
        )
        registry = AssetRegistrySnapshot.model_validate_json(registry_artifact.payload)
        record = next(item for item in registry.assets if item.asset_id == audio_ids[0])
        artifact = next(
            item
            for item in activation.artifacts
            if item.relative_path == record.artifact_path
        )
        metadata = record.audio_metadata
        assert metadata is not None
        probe = AudioProbeResult(
            mime_type="audio/wav",
            container_name="wav",
            file_sha256=record.sha256,
            size_bytes=record.size_bytes,
            file_device=0,
            file_inode=0,
            codec_name="pcm_s16le",
            duration_samples=metadata.duration_samples,
            sample_rate_hz=metadata.sample_rate_hz,
            channels=metadata.channels,
            channel_layout=metadata.channel_layout,
            decoded_pcm_sha256=record.sha256,
            loudness=metadata.loudness,
            loudness_receipt_id=record.sha256,
            ffmpeg=record.tool.model_copy(update={"name": "ffmpeg"}),
            ffprobe=record.tool.model_copy(update={"name": "ffprobe"}),
            content_fingerprint=record.sha256,
        )
        return PreparedVoiceCandidate(
            audio=PreparedAudioImport(
                payload=artifact.payload,
                probe=probe,
                asset_record=record,
            )
        )

    provider = _Provider()
    committer = ProductionStateCommitter(
        tmp_path, voice_candidate_preparer=prepare_candidate
    )
    committed = committer.generate_voice_asset(
        request,
        provider,
        authorization,
        dependency_transition_preparer=lambda candidate: (
            project_factory.attach_p5_dependency_transition(tmp_path, candidate)[0]
        ),
    )

    assert provider.calls == 1
    assert committed.schema_version == "2.3"
    assert committed.active_dependency_graph is not None
    assert committed.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_public_voice_rechecks_manifest_23_preparer_inside_begin_lock(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _Provider:
        preview_calls = 0
        generate_calls = 0

        def preview(self, candidate):
            self.preview_calls += 1
            assert candidate == request
            return preview

        def generate(self, *_args):
            self.generate_calls += 1
            raise AssertionError("provider transport must remain gated")

    provider = _Provider()
    committer = ProductionStateCommitter(tmp_path)
    begin_voice_generation = committer.begin_voice_generation

    def migrate_then_begin(*args, **kwargs):
        project_factory.make_manifest_23_project(tmp_path)
        return begin_voice_generation(*args, **kwargs)

    committer.begin_voice_generation = migrate_then_begin  # type: ignore[method-assign]

    with pytest.raises(AiVideoError, match="dependency transition preparer"):
        committer.generate_voice_asset(request, provider, authorization)

    manifest = read_manifest(tmp_path)
    assert provider.preview_calls == 1
    assert provider.generate_calls == 0
    assert manifest.schema_version == "2.3"
    assert not manifest.attempts


def test_generate_voice_asset_rejects_untyped_provider_result_before_preparer(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    prepared_calls = 0

    class _Provider:
        def preview(self, candidate):
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            binding = {
                "attempt_id": candidate.attempt_id,
                "request_fingerprint": candidate.voice_request_fingerprint,
                "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                "destination": candidate_authorization.destination,
                "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
            }
            assert permit._consume_voice_submit_permit(**binding)
            return SimpleNamespace(provider_request_id="forged")

    def _prepare(*_args):
        nonlocal prepared_calls
        prepared_calls += 1
        raise AssertionError("untyped result reached candidate preparer")

    writer = ProductionStateCommitter(tmp_path, voice_candidate_preparer=_prepare)
    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_voice_asset(request, _Provider(), authorization)

    after = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert prepared_calls == 0
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN


@pytest.mark.parametrize("failure_stage", ("provider", "preparer"))
def test_generate_voice_asset_does_not_persist_provider_or_preparer_exception_payload(
    tmp_path: Path, failure_stage: str
) -> None:
    secret_payload = "TOP-SECRET raw provider response Exact script"
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _Provider:
        def preview(self, candidate):
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            binding = {
                "attempt_id": candidate.attempt_id,
                "request_fingerprint": candidate.voice_request_fingerprint,
                "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                "destination": candidate_authorization.destination,
                "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
            }
            assert permit._consume_voice_submit_permit(**binding)
            if failure_stage == "provider":
                raise RuntimeError(secret_payload)
            return project_factory.make_voice_provider_result(
                request, preview, authorization
            )

    def _prepare(*_args):
        raise RuntimeError(secret_payload)

    writer = ProductionStateCommitter(
        tmp_path,
        voice_candidate_preparer=_prepare if failure_stage == "preparer" else None,
    )
    with pytest.raises(RuntimeError, match="TOP-SECRET"):
        writer.generate_voice_asset(request, _Provider(), authorization)

    manifest_bytes = (tmp_path / "state/manifest.json").read_bytes()
    manifest = ProductionManifest.model_validate_json(manifest_bytes)
    attempt = manifest.attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.error_message in {
        "Voice provider outcome is unknown; blind retry is forbidden.",
        "Voice result could not be durably activated; explicit recovery is required.",
    }
    assert secret_payload.encode() not in manifest_bytes
    assert request.script_text.encode() not in manifest_bytes


def test_malformed_post_submit_response_persists_outcome_unknown(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _MalformedResponseProvider:
        def preview(self, candidate):
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            binding = {
                "attempt_id": candidate.attempt_id,
                "request_fingerprint": candidate.voice_request_fingerprint,
                "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                "destination": candidate_authorization.destination,
                "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
            }
            assert permit._consume_voice_submit_permit(**binding)
            raise AiVideoError(
                code=ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN,
                user_message="malformed response TOP-SECRET",
                technical_detail=None,
                retryable=False,
            )

    writer = ProductionStateCommitter(tmp_path)
    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_voice_asset(
            request, _MalformedResponseProvider(), authorization
        )

    manifest_bytes = (tmp_path / "state/manifest.json").read_bytes()
    attempt = ProductionManifest.model_validate_json(manifest_bytes).attempts[-1]
    assert exc_info.value.code is ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.error_code == ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN.value
    assert attempt.error_message == (
        "Voice provider outcome is unknown; blind retry is forbidden."
    )
    assert b"TOP-SECRET" not in manifest_bytes


def test_generate_voice_asset_rejects_preparer_supplied_activation_capability(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    before = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)

    class _Provider:
        def preview(self, candidate):
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            binding = {
                "attempt_id": candidate.attempt_id,
                "request_fingerprint": candidate.voice_request_fingerprint,
                "authorization_fingerprint": candidate_authorization.authorization_fingerprint,
                "destination": candidate_authorization.destination,
                "budget_reservation_receipt_id": candidate_authorization.budget_reservation_receipt_id,
                "egress_authorization_receipt_id": candidate_authorization.egress_authorization_receipt_id,
            }
            assert permit._consume_voice_submit_permit(**binding)
            return project_factory.make_voice_provider_result(
                request, preview, authorization
            )

    def _forged_prepare(*_args):
        activation, audio_ids = project_factory.make_voice_activation_request(
            tmp_path, request, authorization, expected_manifest_revision=3
        )
        return activation, audio_ids, ()

    writer = ProductionStateCommitter(
        tmp_path, voice_candidate_preparer=_forged_prepare
    )
    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_voice_asset(request, _Provider(), authorization)

    after = ProductionManifest.model_validate_json(
        (tmp_path / "state/manifest.json").read_text(encoding="utf-8")
    )
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN


class _RecordingHandle:
    def __init__(self, events: list[str], display_path: str) -> None:
        self._events = events
        self._display_path = display_path

    def __enter__(self) -> "_RecordingHandle":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def write(self, payload: bytes) -> int:
        self._events.append(f"write:{self._display_path}")
        return len(payload)

    def flush(self) -> None:
        self._events.append(f"flush:{self._display_path}")

    def fileno(self) -> int:
        return 1


class RecordingFileOps:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.events: list[str] = []

    def _display(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def open_exclusive(self, path: Path) -> _RecordingHandle:
        return _RecordingHandle(self.events, self._display(path))

    def fsync_file(self, handle: object, path: Path) -> None:
        self.events.append(f"fsync_file:{self._display(path)}")

    def replace(self, source: Path, destination: Path) -> None:
        self.events.append(f"replace:{self._display(source)}->{self._display(destination)}")

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")

    def mkdir(self, path: Path) -> bool:
        if path.exists():
            return False
        path.mkdir()
        return True


class _RecordingNativeHandle:
    def __init__(self, events: list[str], display_path: str, handle: object) -> None:
        self._events = events
        self._display_path = display_path
        self._handle = handle

    def __enter__(self) -> "_RecordingNativeHandle":
        self._handle.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        self._handle.__exit__(*args)

    def write(self, payload: bytes) -> int:
        self._events.append(f"write:{self._display_path}")
        return self._handle.write(payload)

    def flush(self) -> None:
        self._events.append(f"flush:{self._display_path}")
        self._handle.flush()

    def fileno(self) -> int:
        return self._handle.fileno()


class RecordingNativeFileOps:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.events: list[str] = []
        self._native = _NativeFileOps()

    def _display(self, path: Path) -> str:
        relative = path.relative_to(self.root)
        return relative.as_posix() if relative != Path(".") else "."

    def mkdir(self, path: Path) -> bool:
        created = self._native.mkdir(path)
        if created:
            self.events.append(f"mkdir:{self._display(path)}")
        return created

    def open_exclusive(self, path: Path) -> _RecordingNativeHandle:
        self.events.append(f"open:{self._display(path)}")
        return _RecordingNativeHandle(
            self.events, self._display(path), self._native.open_exclusive(path)
        )

    def fsync_file(self, handle: object, path: Path) -> None:
        self.events.append(f"fsync_file:{self._display(path)}")
        self._native.fsync_file(handle, path)

    def replace(self, source: Path, destination: Path) -> None:
        self.events.append(f"replace:{self._display(source)}->{self._display(destination)}")
        self._native.replace(source, destination)

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        self._native.fsync_directory(path)

    def stat(self, path: Path) -> object:
        self.events.append(f"stat:{self._display(path)}")
        return path.stat()

    def link(self, source: Path, destination: Path) -> None:
        self.events.append(f"link:{self._display(source)}->{self._display(destination)}")
        self._native.link(source, destination)

    def sha256_file(self, path: Path) -> str:
        self.events.append(f"sha:{self._display(path)}")
        return self._native.sha256_file(path)

    def unlink(self, path: Path, *, missing_ok: bool = False) -> None:
        self.events.append(f"unlink:{self._display(path)}")
        self._native.unlink(path, missing_ok=missing_ok)


class CorruptingRecordingNativeFileOps(RecordingNativeFileOps):
    def link(self, source: Path, destination: Path) -> None:
        super().link(source, destination)
        destination.write_bytes(b"corrupt")


class FailingFirstParentFsyncOps(RecordingNativeFileOps):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self._fail_next_root_fsync = True

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        if path == self.root and self._fail_next_root_fsync:
            self._fail_next_root_fsync = False
            raise OSError("injected parent fsync failure")
        self._native.fsync_directory(path)


class FailingLinkedParentFsyncOps(RecordingNativeFileOps):
    def __init__(self, root: Path, linked_parent: Path) -> None:
        super().__init__(root)
        self._linked_parent = linked_parent
        self._fail_once = True

    def fsync_directory(self, path: Path) -> None:
        self.events.append(f"fsync_dir:{self._display(path)}")
        if path == self._linked_parent and self._fail_once:
            self._fail_once = False
            raise OSError("injected linked-parent fsync failure")
        self._native.fsync_directory(path)


class _FakeFcntl:
    LOCK_EX = 1
    LOCK_NB = 2
    LOCK_UN = 8

    def __init__(
        self, *, busy: bool = False, unlock_error: BaseException | bool = False
    ) -> None:
        self.busy = busy
        self.unlock_error = unlock_error
        self.calls: list[int] = []

    def flock(self, descriptor: int, operation: int) -> None:
        self.calls.append(operation)
        if operation == self.LOCK_EX | self.LOCK_NB and self.busy:
            raise BlockingIOError("injected busy lock")
        if operation == self.LOCK_UN and self.unlock_error:
            if isinstance(self.unlock_error, BaseException):
                raise self.unlock_error
            raise OSError("injected unlock failure")


class _FakeLockHandle:
    def __init__(self, *, close_error: BaseException | bool = False) -> None:
        self.close_error = close_error
        self.closed = False

    def fileno(self) -> int:
        return 7

    def close(self) -> None:
        self.closed = True
        if self.close_error:
            if isinstance(self.close_error, BaseException):
                raise self.close_error
            raise OSError("injected close failure")


class _SwapStateAfterManifestFsync:
    def __init__(self, root: Path, outside: Path) -> None:
        self.root = root
        self.outside = outside

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is CommitPhase.AFTER_MANIFEST_FILE_FSYNC:
            temp_path = self.root / "state/.p2a-manifest.tmp"
            temp_path.unlink()
            (self.root / "state").rmdir()
            (self.root / "state").symlink_to(self.outside, target_is_directory=True)
            (self.outside / temp_path.name).write_bytes(b"external state temp")


class _SwapArtifactParentAfterFileFsync:
    def __init__(self, root: Path, outside: Path) -> None:
        self.root = root
        self.outside = outside

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is CommitPhase.AFTER_ARTIFACT_FILE_FSYNC:
            temp_path = next((self.root / "creative").glob(".p2a-*.tmp"))
            temp_path.unlink()
            (self.root / "creative").rmdir()
            (self.root / "creative").symlink_to(self.outside, target_is_directory=True)
            (self.outside / temp_path.name).write_bytes(b"external artifact temp")


class RaisingCrashInjector:
    def __init__(self, phase: CommitPhase) -> None:
        self.phase = phase

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.phase:
            raise OSError(f"injected failure at {phase.value}")


class RaisingOnOccurrence:
    def __init__(self, phase: CommitPhase, occurrence: int) -> None:
        self.phase = phase
        self.occurrence = occurrence
        self.count = 0

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.phase:
            self.count += 1
            if self.count == self.occurrence:
                raise OSError(f"injected failure at {phase.value}")


class ProcessInterruptInjector:
    def __init__(
        self, phase: CommitPhase, occurrence: int, exception_type: type[BaseException]
    ) -> None:
        self.phase = phase
        self.occurrence = occurrence
        self.exception_type = exception_type
        self.count = 0

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.phase:
            self.count += 1
            if self.count == self.occurrence:
                raise self.exception_type()


def make_manifest() -> ProductionManifest:
    return ProductionManifest(
        project_id="comic-demo",
        manifest_revision=1,
        active_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        active_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ZERO_HASH}.json"),
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
    )


def make_committer(
    tmp_path: Path, ops: object | None = None, injector: object | None = None
) -> ProductionStateCommitter:
    return ProductionStateCommitter(tmp_path, file_ops=ops, crash_injector=injector)


def read_manifest(root: Path) -> ProductionManifest:
    return ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def committed_project(tmp_path: Path) -> Path:
    project_factory.write_production_project(tmp_path)
    return tmp_path


def revision_two_request(root: Path, *, attempt_id: str = "attempt-revision-2") -> StateCommitRequest:
    return project_factory.make_revision_two_request(root, attempt_id=attempt_id)


def test_commit_contract_types_are_frozen_and_expose_all_phases() -> None:
    artifact = PreparedArtifact(Path("creative/brief.yaml"), b"brief", "x" * 64)
    request = StateCommitRequest(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        expected_manifest_revision=1,
        artifacts=(artifact,),
        next_project=make_manifest().active_project,
        next_registry=make_manifest().active_registry,
    )

    assert request.artifacts == (artifact,)
    with pytest.raises(AttributeError):
        request.operation = "other"  # type: ignore[misc]
    assert tuple(CommitPhase) == (
        CommitPhase.AFTER_ATTEMPT_STARTED,
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
        CommitPhase.AFTER_GRAPH_CANDIDATE_TEMP_WRITE,
        CommitPhase.AFTER_GRAPH_CANDIDATE_FILE_FSYNC,
        CommitPhase.AFTER_GRAPH_CANDIDATE_PROMOTION,
        CommitPhase.AFTER_GRAPH_CANDIDATE_DIRECTORY_FSYNC,
        CommitPhase.AFTER_GRAPH_CANDIDATE_VERIFICATION,
        CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.BEFORE_VOICE_SUBMIT_INTENT,
        CommitPhase.AFTER_VOICE_SUBMIT_INTENT,
        CommitPhase.AFTER_VOICE_PROVIDER_RESULT,
        CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST,
        CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE,
    )
    assert NoopCrashInjector().checkpoint(CommitPhase.AFTER_ATTEMPT_STARTED) is None


def test_render_path_contract_uses_full_hashes_and_safe_attempt_ids(tmp_path: Path) -> None:
    digest = "a" * 64
    assert canonical_render_timeline_path(digest) == Path(
        f"state/render/timelines/{digest}.json"
    )
    assert canonical_render_source_root(digest) == Path(
        f"state/render/sources/{digest}"
    )
    assert canonical_render_source_index_path(digest) == Path(
        f"state/render/sources/{digest}/index.html"
    )
    assert canonical_render_source_asset_path(digest, digest, ".png") == Path(
        f"state/render/sources/{digest}/assets/{digest}.png"
    )
    for suffix in (
        ".jpg",
        ".webp",
        ".wav",
        ".mp3",
        ".m4a",
        ".aac",
        ".flac",
        ".json",
    ):
        assert canonical_render_source_asset_path(digest, digest, suffix) == Path(
            f"state/render/sources/{digest}/assets/{digest}{suffix}"
        )
    for suffix in (".jpeg", ".ogg", ".html", ".js", ""):
        with pytest.raises(ValueError, match="unsupported"):
            canonical_render_source_asset_path(digest, digest, suffix)
    assert canonical_renderer_source_receipt_path(digest) == Path(
        f"state/render/source-receipts/{digest}.json"
    )
    assert canonical_render_receipt_path(digest) == Path(
        f"state/render/render-receipts/{digest}.json"
    )
    assert canonical_render_state_path(digest) == Path(
        f"state/render/states/{digest}.json"
    )
    assert canonical_render_output_path(digest) == Path(
        f"state/render/outputs/{digest}.mp4"
    )
    assert canonical_render_attempt_root("attempt-1") == Path(
        "state/render/attempts/attempt-1"
    )

    (tmp_path / "state").mkdir()
    paths = ProductionStateCommitter(tmp_path).render_attempt_paths("attempt-1")
    assert isinstance(paths, RenderAttemptPaths)
    assert paths.attempt_root == tmp_path.resolve() / "state/render/attempts/attempt-1"
    assert paths.source_root == paths.attempt_root / "source"
    assert paths.staged_output_path == paths.attempt_root / "output/render.mp4"
    assert paths.verification_snapshot_path == paths.attempt_root / "verified.mp4"
    assert not paths.attempt_root.exists()

    for unsafe in ("", ".", "..", "a/b", r"a\\b", "/absolute"):
        with pytest.raises(AiVideoError):
            ProductionStateCommitter(tmp_path).render_attempt_paths(unsafe)


def test_render_lifecycle_request_dataclasses_are_frozen() -> None:
    assert BeginRenderAttemptRequest.__dataclass_params__.frozen is True
    assert RecordRenderFailureRequest.__dataclass_params__.frozen is True
    assert ActivateRenderStateRequest.__dataclass_params__.frozen is True


def _render_selection(
    manifest: ProductionManifest, *, attempt_id: str = "render-1"
) -> RendererSelectionReceipt:
    return RendererSelectionReceipt(
        receipt_id=f"selection-{attempt_id}",
        attempt_id=attempt_id,
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint="a" * 64,
        current_project=manifest.active_project,
        current_registry=manifest.active_registry,
    )


def test_begin_render_attempt_migrates_20_and_exact_replay_is_idempotent(
    committed_project: Path,
) -> None:
    before = read_manifest(committed_project)
    request = BeginRenderAttemptRequest(
        expected_manifest_revision=before.manifest_revision,
        base_render_state=None,
        renderer_selection=_render_selection(before),
    )
    committer = ProductionStateCommitter(committed_project)

    begun = committer.begin_render_attempt(request)
    replay = committer.begin_render_attempt(request)

    assert begun == replay
    assert begun.schema_version == "2.1"
    assert begun.manifest_revision == before.manifest_revision + 1
    attempt = begun.attempts[-1]
    assert (attempt.operation, attempt.status, attempt.render_phase) == (
        "render_state",
        StateCommitStatus.RUNNING,
        "selection",
    )
    assert begun.active_render_state is None


def test_begin_render_attempt_preserves_22_manifest_with_succeeded_voice(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path, attempt_id="voice-before-render")
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    committer = ProductionStateCommitter(tmp_path)
    committer.begin_voice_generation(request, preview, authorization)
    committer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=3,
        include_caption=True,
    )
    voice_manifest = committer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=("caption-voice-before-render",),
    )
    assert voice_manifest.schema_version == "2.2"
    assert voice_manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED

    begun = committer.begin_render_attempt(
        BeginRenderAttemptRequest(
            voice_manifest.manifest_revision,
            voice_manifest.active_render_state,
            _render_selection(voice_manifest, attempt_id="render-after-voice"),
        )
    )

    assert begun.schema_version == "2.2"
    assert begun.attempts[-2].operation == "voice_generation"
    assert begun.attempts[-2].candidate_audio_asset_ids == audio_ids
    assert begun.attempts[-2].candidate_caption_asset_ids == (
        "caption-voice-before-render",
    )
    assert begun.attempts[-1].operation == "render_state"
    assert begun.attempts[-1].status is StateCommitStatus.RUNNING


def test_record_render_failure_is_terminal_r2_and_exact_replay_is_idempotent(
    committed_project: Path,
) -> None:
    committer = ProductionStateCommitter(committed_project)
    before = read_manifest(committed_project)
    selection = _render_selection(before)
    begun = committer.begin_render_attempt(
        BeginRenderAttemptRequest(before.manifest_revision, None, selection)
    )
    request = RecordRenderFailureRequest(
        attempt_id=selection.attempt_id,
        expected_manifest_revision=begun.manifest_revision,
        current_project=begun.active_project,
        current_registry=begun.active_registry,
        base_render_state=None,
        renderer_selection=selection,
        phase="render",
        error_code=ErrorCode.RENDER_FAILED.value,
        error_message="token=secret failed",
    )

    failed = committer.record_render_failure(request)
    replay = committer.record_render_failure(request)

    assert failed == replay
    assert failed.manifest_revision == before.manifest_revision + 2
    attempt = failed.attempts[-1]
    assert (attempt.status, attempt.render_phase) == (
        StateCommitStatus.FAILED,
        "render",
    )
    assert "secret" not in (attempt.error_message or "")
    assert failed.active_project == before.active_project
    assert failed.active_registry == before.active_registry


def test_atomic_manifest_write_orders_file_and_directory_durability(tmp_path: Path) -> None:
    (tmp_path / "state").mkdir()
    ops = RecordingFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)

    writer._write_manifest_atomic(make_manifest())

    assert ops.events == [
        "fsync_dir:.",
        "fsync_dir:.",
        "write:state/.p2a-manifest.tmp",
        "flush:state/.p2a-manifest.tmp",
        "fsync_file:state/.p2a-manifest.tmp",
        "fsync_dir:.",
        "replace:state/.p2a-manifest.tmp->state/manifest.json",
        "fsync_dir:state",
    ]


def test_first_state_directory_creation_fsyncs_project_root_before_manifest_write(
    tmp_path: Path,
) -> None:
    ops = RecordingNativeFileOps(tmp_path)

    make_committer(tmp_path, ops)._write_manifest_atomic(make_manifest())

    assert ops.events[:2] == ["mkdir:state", "fsync_dir:."]


def test_existing_directory_retries_parent_fsync_after_prior_creation_failure(
    tmp_path: Path,
) -> None:
    ops = FailingFirstParentFsyncOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    composition = tmp_path / "composition"

    with pytest.raises(AiVideoError) as exc:
        writer._ensure_parent_directory(composition)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert composition.is_dir()
    assert ops.events == ["mkdir:composition", "fsync_dir:."]

    writer._ensure_parent_directory(composition)

    assert ops.events == [
        "mkdir:composition",
        "fsync_dir:.",
        "fsync_dir:.",
    ]


def test_canonical_serialization_is_sort_stable_and_uses_required_newlines() -> None:
    manifest = make_manifest()

    assert _canonical_json_bytes(manifest) == (
        b'{"active_project":{"content_hash":"0000000000000000000000000000000000000000000000000000000000000000",'
        b'"file_sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"path":"project.yaml","revision":1},"active_registry":{"content_hash":"0000000000000000000000000000000000000000000000000000000000000000",'
        b'"file_sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
        b'"path":"assets/registry.0000000000000000000000000000000000000000000000000000000000000000.json",'
        b'"revision_id":"0000000000000000000000000000000000000000000000000000000000000000"},'
        b'"attempts":[],"manifest_revision":1,"project_id":"comic-demo","schema_version":"2.0"}\n'
    )
    assert _canonical_yaml_bytes(manifest) == (
        b"active_project:\n"
        b"  content_hash: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"  file_sha256: '1111111111111111111111111111111111111111111111111111111111111111'\n"
        b"  path: project.yaml\n"
        b"  revision: 1\n"
        b"active_registry:\n"
        b"  content_hash: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"  file_sha256: '1111111111111111111111111111111111111111111111111111111111111111'\n"
        b"  path: assets/registry.0000000000000000000000000000000000000000000000000000000000000000.json\n"
        b"  revision_id: '0000000000000000000000000000000000000000000000000000000000000000'\n"
        b"attempts: []\n"
        b"manifest_revision: 1\n"
        b"project_id: comic-demo\n"
        b"schema_version: '2.0'\n"
    )


def test_prepare_artifact_computes_sha256_from_payload(tmp_path: Path) -> None:
    artifact = make_committer(tmp_path).prepare_artifact(
        attempt_id="attempt-1",
        relative_path=Path("creative/brief.yaml"),
        payload=b"authoritative payload",
    )

    assert artifact.file_sha256 == hashlib.sha256(b"authoritative payload").hexdigest()
    assert artifact.payload == b"authoritative payload"


@pytest.mark.parametrize(
    "relative_path",
    [
        Path(""),
        Path("."),
        Path("/tmp/escape.yaml"),
        Path("creative/../escape.yaml"),
        Path("state/manifest.json"),
        Path("state/commit.lock"),
        Path("runs/forbidden.yaml"),
        Path(".workflow/forbidden.yaml"),
    ],
)
def test_prepare_artifact_rejects_unsafe_or_reserved_targets(
    tmp_path: Path, relative_path: Path
) -> None:
    with pytest.raises(AiVideoError) as exc:
        make_committer(tmp_path).prepare_artifact(
            attempt_id="attempt-1", relative_path=relative_path, payload=b"forbidden"
        )

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_prepare_artifact_rejects_symlink_component_and_containment_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "creative").symlink_to(outside, target_is_directory=True)

    with pytest.raises(AiVideoError, match="symlink") as exc:
        make_committer(tmp_path).prepare_artifact(
            attempt_id="attempt-1",
            relative_path=Path("creative/brief.yaml"),
            payload=b"project",
        )

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_owned_temp_name_sanitizes_attempt_id_in_final_parent(tmp_path: Path) -> None:
    final_path = tmp_path / "state/projects/project.2.yaml"
    temp_name = _owned_temp_name("attempt:/ 2", final_path)

    assert temp_name.startswith(".p2a-attempt___2-")
    assert temp_name.endswith(".tmp")
    assert "/" not in temp_name and ":" not in temp_name
    assert final_path.parent / temp_name == tmp_path / "state/projects" / temp_name


def test_owned_temp_name_disambiguates_sanitized_attempt_ids(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    slash_name = _owned_temp_name("attempt/a", final_path)
    colon_name = _owned_temp_name("attempt:a", final_path)
    crafted_safe_name = _owned_temp_name("attempt_a-5e93177664e1", final_path)
    safe_name = _owned_temp_name("attempt-1", final_path)

    assert slash_name != colon_name
    assert slash_name != crafted_safe_name
    assert hashlib.sha256(b"attempt-1").hexdigest()[:12] in safe_name
    assert slash_name.startswith(".p2a-attempt_a-")
    assert colon_name.startswith(".p2a-attempt_a-")
    assert slash_name.endswith("-brief.yaml.tmp")
    assert colon_name.endswith("-brief.yaml.tmp")
    assert "/" not in slash_name + colon_name
    assert ":" not in slash_name + colon_name
    assert slash_name == _owned_temp_name("attempt/a", final_path)


def test_owned_temp_name_is_bounded_for_long_attempt_and_final_names(tmp_path: Path) -> None:
    final_path = tmp_path / ("final-" + "x" * 1000 + ".yaml")
    name = _owned_temp_name("attempt-" + "a" * 1000, final_path)

    assert len(name.encode("utf-8")) <= 240
    assert name.startswith(".p2a-") and name.endswith(".tmp")
    assert "/" not in name and ":" not in name
    assert name == _owned_temp_name("attempt-" + "a" * 1000, final_path)


def test_lock_is_persistent_nonblocking_and_held_for_context_lifetime(tmp_path: Path) -> None:
    writer = make_committer(tmp_path)

    with writer._exclusive_lock() as lock_handle:
        assert lock_handle is not None
        assert (tmp_path / "state/commit.lock").is_file()
        with pytest.raises(AiVideoError) as exc:
            with make_committer(tmp_path)._exclusive_lock():
                pass
        assert exc.value.code is ErrorCode.PRODUCTION_STATE_BUSY

    with make_committer(tmp_path)._exclusive_lock():
        pass


def test_lock_maps_missing_posix_fcntl_to_unsupported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_video.production.state_commit as state_commit

    monkeypatch.setattr(state_commit, "fcntl", None)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_UNSUPPORTED


def test_lock_preserves_body_exception_when_unlock_and_close_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(unlock_error=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(RuntimeError, match="body failure") as exc:
        with make_committer(tmp_path)._exclusive_lock():
            raise RuntimeError("body failure")

    assert fake_fcntl.calls == [fake_fcntl.LOCK_EX | fake_fcntl.LOCK_NB, fake_fcntl.LOCK_UN]
    assert handle.closed is True
    assert any("unlock" in note or "close" in note for note in exc.value.__notes__)


def test_lock_acquisition_failure_skips_unlock_and_preserves_busy_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(busy=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_BUSY
    assert fake_fcntl.calls == [fake_fcntl.LOCK_EX | fake_fcntl.LOCK_NB]
    assert handle.closed is True
    assert any("close" in note for note in exc.value.__notes__)


def test_lock_cleanup_failure_after_success_is_typed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_video.production.state_commit as state_commit

    fake_fcntl = _FakeFcntl(unlock_error=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(AiVideoError) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert "lock cleanup" in exc.value.user_message.lower()


def test_lock_cleanup_process_exception_overrides_successful_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit_module

    fake_fcntl = _FakeFcntl(unlock_error=KeyboardInterrupt())
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit_module, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(KeyboardInterrupt) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            pass

    assert any("close" in note for note in exc.value.__notes__)


def test_lock_cleanup_process_exception_overrides_ordinary_body_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit_module

    fake_fcntl = _FakeFcntl(unlock_error=SystemExit())
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit_module, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(SystemExit) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            raise OSError("body failure")

    assert any("body failure" in note for note in exc.value.__notes__)
    assert any("close" in note for note in exc.value.__notes__)


def test_lock_preserves_process_body_exception_when_cleanup_is_ordinary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit_module

    fake_fcntl = _FakeFcntl(unlock_error=True)
    handle = _FakeLockHandle(close_error=True)
    monkeypatch.setattr(state_commit_module, "fcntl", fake_fcntl)
    monkeypatch.setattr(Path, "open", lambda *_args, **_kwargs: handle)

    with pytest.raises(KeyboardInterrupt) as exc:
        with make_committer(tmp_path)._exclusive_lock():
            raise KeyboardInterrupt()

    assert any("unlock" in note or "close" in note for note in exc.value.__notes__)


def test_immutable_promotion_is_idempotent_and_does_not_overwrite(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    assert writer._write_immutable_artifact(artifact, attempt_id="attempt-1") == final_path
    assert final_path.read_bytes() == b"same"
    assert writer._write_immutable_artifact(artifact, attempt_id="attempt-1") == final_path
    assert not list(final_path.parent.glob(".p2a-attempt-1-brief.yaml.tmp"))

    conflict = writer.prepare_artifact("attempt-2", Path("creative/brief.yaml"), b"different")
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(conflict, attempt_id="attempt-2")
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert final_path.read_bytes() == b"same"


def test_immutable_write_makes_each_new_parent_directory_durable_before_descending(
    tmp_path: Path,
) -> None:
    ops = RecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact(
        "attempt-1", Path("composition/generated/source.bin"), b"source"
    )
    temp_name = _owned_temp_name("attempt-1", tmp_path / "composition/generated/source.bin")

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events == [
        "mkdir:composition",
        "fsync_dir:.",
        "mkdir:composition/generated",
        "fsync_dir:composition",
        f"open:composition/generated/{temp_name}",
        f"write:composition/generated/{temp_name}",
        f"flush:composition/generated/{temp_name}",
        f"fsync_file:composition/generated/{temp_name}",
        "fsync_dir:.",
        "fsync_dir:composition",
        f"stat:composition/generated/{temp_name}",
        "stat:composition/generated",
        "fsync_dir:.",
        "fsync_dir:composition",
        f"link:composition/generated/{temp_name}->composition/generated/source.bin",
        "fsync_dir:composition/generated",
        "sha:composition/generated/source.bin",
        f"unlink:composition/generated/{temp_name}",
    ]


def test_idempotent_immutable_write_fsyncs_parent_before_success(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    final_path.write_bytes(b"same")
    ops = RecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    temp_name = _owned_temp_name("attempt-1", final_path)

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events == [
        "fsync_dir:.",
        f"open:creative/{temp_name}",
        f"write:creative/{temp_name}",
        f"flush:creative/{temp_name}",
        f"fsync_file:creative/{temp_name}",
        "fsync_dir:.",
        f"stat:creative/{temp_name}",
        "stat:creative",
        "fsync_dir:.",
        f"link:creative/{temp_name}->creative/brief.yaml",
        "sha:creative/brief.yaml",
        "fsync_dir:creative",
        "sha:creative/brief.yaml",
        f"unlink:creative/{temp_name}",
    ]
    assert "fsync_dir:creative" in ops.events


def test_immutable_retry_fsyncs_existing_final_after_prior_link_durability_failure(
    tmp_path: Path,
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    ops = FailingLinkedParentFsyncOps(tmp_path, final_path.parent)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert final_path.read_bytes() == b"same"
    first_parent_fsyncs = ops.events.count("fsync_dir:creative")

    writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert ops.events.count("fsync_dir:creative") == first_parent_fsyncs + 1


def test_manifest_replace_revalidates_swapped_state_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    writer = make_committer(
        tmp_path,
        injector=_SwapStateAfterManifestFsync(tmp_path, outside),
    )

    with pytest.raises(AiVideoError) as exc:
        writer._write_manifest_atomic(make_manifest())

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert not (outside / "manifest.json").exists()
    assert (outside / ".p2a-manifest.tmp").read_bytes() == b"external state temp"


def test_immutable_link_revalidates_swapped_parent_symlink(tmp_path: Path) -> None:
    (tmp_path / "creative").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    writer = make_committer(
        tmp_path,
        injector=_SwapArtifactParentAfterFileFsync(tmp_path, outside),
    )
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert not (outside / "brief.yaml").exists()
    assert next(outside.glob(".p2a-*.tmp")).read_bytes() == b"external artifact temp"


def test_immutable_verification_mismatch_is_typed_and_cleans_owned_temp(tmp_path: Path) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    ops = CorruptingRecordingNativeFileOps(tmp_path)
    writer = make_committer(tmp_path, ops)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    temp_name = _owned_temp_name("attempt-1", final_path)

    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert f"unlink:creative/{temp_name}" in ops.events
    assert not list(final_path.parent.glob(temp_name))


def test_immutable_promotion_rejects_cross_device_temp_before_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")
    original_stat = Path.stat

    def mismatched_stat(path: Path, *args: object, **kwargs: object) -> object:
        result = original_stat(path, *args, **kwargs)
        if path.name.startswith(".p2a-"):
            return SimpleNamespace(st_dev=result.st_dev + 1)
        return result

    monkeypatch.setattr(Path, "stat", mismatched_stat)
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_UNSUPPORTED
    assert not final_path.exists()


def test_immutable_cleanup_failure_keeps_primary_error_and_adds_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    final_path.write_bytes(b"existing")
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"different")

    import ai_video.production.state_commit as state_commit

    original_unlink = state_commit._NativeFileOps.unlink

    def failing_unlink(self: object, path: Path, *, missing_ok: bool = False) -> None:
        if path.name.startswith(".p2a-"):
            raise OSError("cleanup failed")
        original_unlink(self, path, missing_ok=missing_ok)

    monkeypatch.setattr(state_commit._NativeFileOps, "unlink", failing_unlink)
    with pytest.raises(AiVideoError) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert any("cleanup" in note.lower() for note in exc.value.__notes__)
    assert final_path.read_bytes() == b"existing"


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_mutable_cleanup_process_exception_overrides_ordinary_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception_type: type[BaseException]
) -> None:
    writer = make_committer(
        tmp_path, injector=RaisingCrashInjector(CommitPhase.AFTER_MANIFEST_FILE_FSYNC)
    )

    def interrupting_unlink(
        _self: object, _path: Path, *, missing_ok: bool = False
    ) -> None:
        raise exception_type()

    monkeypatch.setattr(state_commit._NativeFileOps, "unlink", interrupting_unlink)
    with pytest.raises(exception_type) as exc:
        writer._write_manifest_atomic(make_manifest())

    assert any("Could not write production state atomically" in note for note in exc.value.__notes__)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_immutable_cleanup_process_exception_overrides_ordinary_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception_type: type[BaseException]
) -> None:
    final_path = tmp_path / "creative/brief.yaml"
    final_path.parent.mkdir()
    final_path.write_bytes(b"existing")
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"different")

    def interrupting_unlink(
        _self: object, _path: Path, *, missing_ok: bool = False
    ) -> None:
        raise exception_type()

    monkeypatch.setattr(state_commit._NativeFileOps, "unlink", interrupting_unlink)
    with pytest.raises(exception_type) as exc:
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")

    assert any("already has different bytes" in note for note in exc.value.__notes__)


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_immutable_success_cleanup_process_exception_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception_type: type[BaseException]
) -> None:
    writer = make_committer(tmp_path)
    artifact = writer.prepare_artifact("attempt-1", Path("creative/brief.yaml"), b"same")

    def interrupting_unlink(
        _self: object, _path: Path, *, missing_ok: bool = False
    ) -> None:
        raise exception_type()

    monkeypatch.setattr(state_commit._NativeFileOps, "unlink", interrupting_unlink)
    with pytest.raises(exception_type):
        writer._write_immutable_artifact(artifact, attempt_id="attempt-1")


def test_mutable_atomic_write_uses_exclusive_temp_and_durable_replace(tmp_path: Path) -> None:
    final_path = tmp_path / "state/manifest.json"
    final_path.parent.mkdir()
    writer = make_committer(tmp_path)

    writer._write_mutable_atomic(final_path, b"first", temp_name=".p2a-manifest.tmp")
    assert final_path.read_bytes() == b"first"

    writer._write_mutable_atomic(final_path, b"second", temp_name=".p2a-manifest.tmp")
    assert final_path.read_bytes() == b"second"


def test_prepare_project_registry_commit_builds_exact_canonical_candidates(
    committed_project: Path,
) -> None:
    request = revision_two_request(committed_project)

    assert request.artifacts == tuple(sorted(request.artifacts, key=lambda item: item.relative_path))
    project, registry = project_factory.load_revision_two_models(committed_project)
    project_artifact = next(
        artifact for artifact in request.artifacts if artifact.relative_path.suffix == ".yaml"
    )
    registry_artifact = next(
        artifact for artifact in request.artifacts if artifact.relative_path.suffix == ".json"
    )
    assert project_artifact.relative_path == Path(
        f"state/projects/project.{project.revision}.{project.content_hash}.yaml"
    )
    assert registry_artifact.relative_path == Path(
        f"assets/registry.{registry.revision_id}.json"
    )
    assert project_artifact.payload == _canonical_yaml_bytes(project)
    assert registry_artifact.payload == _canonical_json_bytes(registry)
    assert project_artifact.file_sha256 == hashlib.sha256(project_artifact.payload).hexdigest()
    assert registry_artifact.file_sha256 == hashlib.sha256(registry_artifact.payload).hexdigest()


@pytest.mark.parametrize(
    "field, value",
    [
        ("project_id", "other-project"),
        ("content_hash", ZERO_HASH),
    ],
)
def test_prepare_project_registry_commit_rejects_invalid_project_candidate(
    committed_project: Path, field: str, value: str
) -> None:
    manifest = read_manifest(committed_project)
    project, registry = project_factory.load_revision_two_models(committed_project)
    with pytest.raises(AiVideoError) as exc:
        state_commit.prepare_project_registry_commit(
            manifest=manifest,
            project=project.model_copy(update={field: value}),
            registry=registry,
            attempt_id="invalid-project",
        )
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_prepare_project_registry_commit_rejects_invalid_registry_and_reused_revision(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    project, registry = project_factory.load_revision_two_models(committed_project)
    invalid_registry = registry.model_copy(update={"content_hash": ZERO_HASH})
    with pytest.raises(AiVideoError) as registry_error:
        state_commit.prepare_project_registry_commit(
            manifest=manifest,
            project=project,
            registry=invalid_registry,
            attempt_id="invalid-registry",
        )
    assert registry_error.value.code is ErrorCode.PRODUCTION_STATE_INVALID

    different_same_revision = seal_artifact(
        project.model_copy(update={"revision": 1, "title": "Different v1", "content_hash": ZERO_HASH})
    )
    with pytest.raises(AiVideoError) as reuse_error:
        state_commit.prepare_project_registry_commit(
            manifest=manifest,
            project=different_same_revision,
            registry=registry,
            attempt_id="reused-revision",
        )
    assert reuse_error.value.code is ErrorCode.PRODUCTION_STATE_INVALID

    backward = project.model_copy(update={"revision": 0})
    with pytest.raises(AiVideoError) as backward_error:
        state_commit.prepare_project_registry_commit(
            manifest=manifest,
            project=backward,
            registry=registry,
            attempt_id="backward-revision",
        )
    assert backward_error.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_prepare_project_registry_commit_allows_identical_initial_snapshot_migration(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    project, registry = project_factory.load_initial_models(committed_project)

    request = state_commit.prepare_project_registry_commit(
        manifest=manifest,
        project=project,
        registry=registry,
        attempt_id="migrate-v1",
    )

    assert request.next_project.revision == manifest.active_project.revision
    assert request.next_project.content_hash == manifest.active_project.content_hash


@pytest.mark.parametrize("pointer_kind", ["project", "registry"])
def test_commit_rejects_model_constructed_noncanonical_snapshot_pointer_before_mutation(
    committed_project: Path, pointer_kind: str
) -> None:
    before = (committed_project / "state/manifest.json").read_bytes()
    request = revision_two_request(committed_project)
    project_artifact = next(
        artifact for artifact in request.artifacts if artifact.relative_path.suffix == ".yaml"
    )
    registry_artifact = next(
        artifact for artifact in request.artifacts if artifact.relative_path.suffix == ".json"
    )
    if pointer_kind == "project":
        replacement = PreparedArtifact(
            relative_path=Path("state/projects/arbitrary.yaml"),
            payload=project_artifact.payload,
            file_sha256=project_artifact.file_sha256,
        )
        unsafe = StateCommitRequest(
            attempt_id=request.attempt_id,
            operation=request.operation,
            expected_manifest_revision=request.expected_manifest_revision,
            artifacts=(replacement, registry_artifact),
            next_project=ProjectSnapshotPointer.model_construct(
                **{
                    **request.next_project.model_dump(mode="python"),
                    "path": replacement.relative_path,
                }
            ),
            next_registry=request.next_registry,
        )
    else:
        replacement = PreparedArtifact(
            relative_path=Path("assets/arbitrary.json"),
            payload=registry_artifact.payload,
            file_sha256=registry_artifact.file_sha256,
        )
        unsafe = StateCommitRequest(
            attempt_id=request.attempt_id,
            operation=request.operation,
            expected_manifest_revision=request.expected_manifest_revision,
            artifacts=(project_artifact, replacement),
            next_project=request.next_project,
            next_registry=RegistrySnapshotPointer.model_construct(
                **{
                    **request.next_registry.model_dump(mode="python"),
                    "path": replacement.relative_path,
                }
            ),
        )

    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(unsafe)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (committed_project / "state/manifest.json").read_bytes() == before
    assert not (committed_project / replacement.relative_path).exists()


def test_commit_rejects_root_project_entrypoint_as_candidate_before_mutation(
    committed_project: Path,
) -> None:
    before = (committed_project / "state/manifest.json").read_bytes()
    root_project_before = (committed_project / "project.yaml").read_bytes()
    request = revision_two_request(committed_project)
    project_artifact = next(
        artifact for artifact in request.artifacts if artifact.relative_path.suffix == ".yaml"
    )
    root_artifact = PreparedArtifact(
        relative_path=Path("project.yaml"),
        payload=project_artifact.payload,
        file_sha256=project_artifact.file_sha256,
    )
    unsafe = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision,
        artifacts=tuple(
            root_artifact if artifact is project_artifact else artifact
            for artifact in request.artifacts
        ),
        next_project=request.next_project.model_copy(
            update={"path": root_artifact.relative_path}
        ),
        next_registry=request.next_registry,
    )

    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(unsafe)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert (committed_project / "state/manifest.json").read_bytes() == before
    assert (committed_project / "project.yaml").read_bytes() == root_project_before


def test_commit_rejects_stale_manifest_revision_under_lock(committed_project: Path) -> None:
    request = revision_two_request(committed_project)
    stale = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision - 1,
        artifacts=request.artifacts,
        next_project=request.next_project,
        next_registry=request.next_registry,
    )

    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(stale)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_commit_persists_running_attempt_before_artifacts_and_keeps_pointers(
    committed_project: Path,
) -> None:
    before = read_manifest(committed_project)
    request = revision_two_request(committed_project)
    committer = make_committer(
        committed_project, injector=RaisingCrashInjector(CommitPhase.AFTER_ATTEMPT_STARTED)
    )

    with pytest.raises(AiVideoError):
        committer.commit(request)

    after = read_manifest(committed_project)
    assert after.manifest_revision == before.manifest_revision + 2
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.FAILED
    assert after.attempts[-1].base_project == before.active_project
    assert after.attempts[-1].base_registry == before.active_registry
    assert after.attempts[-1].candidate_artifacts_hash == state_commit._candidate_artifacts_hash(
        revision_two_request(committed_project).artifacts
    )


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_ATTEMPT_STARTED,
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
    ],
)
def test_failure_before_manifest_replace_preserves_old_active_pointers(
    committed_project: Path, phase: CommitPhase
) -> None:
    before = read_manifest(committed_project)
    with pytest.raises(AiVideoError):
        make_committer(
            committed_project, injector=RaisingCrashInjector(phase)
        ).commit(revision_two_request(committed_project))
    after = read_manifest(committed_project)
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.FAILED


@pytest.mark.parametrize(
    "phase",
    [CommitPhase.AFTER_MANIFEST_TEMP_WRITE, CommitPhase.AFTER_MANIFEST_FILE_FSYNC],
)
def test_running_persistence_failure_preserves_original_manifest(
    committed_project: Path, phase: CommitPhase
) -> None:
    before_bytes = (committed_project / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError):
        make_committer(
            committed_project, injector=RaisingCrashInjector(phase)
        ).commit(revision_two_request(committed_project))
    assert (committed_project / "state/manifest.json").read_bytes() == before_bytes


@pytest.mark.parametrize(
    "phase",
    [CommitPhase.AFTER_MANIFEST_TEMP_WRITE, CommitPhase.AFTER_MANIFEST_FILE_FSYNC],
)
def test_final_manifest_pre_replace_failure_keeps_old_pointers_and_records_failed_attempt(
    committed_project: Path, phase: CommitPhase
) -> None:
    before = read_manifest(committed_project)
    request = revision_two_request(committed_project)
    with pytest.raises(AiVideoError):
        make_committer(
            committed_project, injector=RaisingOnOccurrence(phase, occurrence=2)
        ).commit(request)
    after = read_manifest(committed_project)
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.FAILED


@pytest.mark.parametrize(
    "phase",
    [CommitPhase.AFTER_MANIFEST_REPLACE, CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC],
)
def test_failure_after_final_manifest_replace_has_unknown_outcome(
    committed_project: Path, phase: CommitPhase
) -> None:
    request = revision_two_request(committed_project)
    injector = RaisingOnOccurrence(phase, occurrence=2)
    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project, injector=injector).commit(request)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    after = read_manifest(committed_project)
    assert after.active_project == request.next_project
    assert after.active_registry == request.next_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_failed_attempt_persistence_keeps_original_failure_and_adds_note(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    committer = make_committer(
        committed_project,
        injector=RaisingCrashInjector(CommitPhase.AFTER_ARTIFACT_TEMP_WRITE),
    )
    original_write = committer._write_manifest_atomic
    calls = 0

    def fail_failed_attempt(manifest: ProductionManifest, **kwargs: object) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("failed-attempt persistence unavailable")
        return original_write(manifest, **kwargs)

    monkeypatch.setattr(committer, "_write_manifest_atomic", fail_failed_attempt)
    with pytest.raises(AiVideoError) as exc:
        committer.commit(revision_two_request(committed_project))

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    assert any("failed production state attempt" in note.lower() for note in exc.value.__notes__)


def test_commit_rejects_symlink_escaped_future_artifact_parent(
    committed_project: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (committed_project / "composition").symlink_to(outside, target_is_directory=True)
    request = revision_two_request(committed_project)
    future = PreparedArtifact(
        Path("composition/source.future.json"), b"future", hashlib.sha256(b"future").hexdigest()
    )
    unsafe = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision,
        artifacts=request.artifacts + (future,),
        next_project=request.next_project,
        next_registry=request.next_registry,
    )
    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(unsafe)
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_commit_never_calls_legacy_manifest_writer(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.manifest as legacy_manifest

    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("P2A must not call the Legacy manifest writer")

    monkeypatch.setattr(legacy_manifest, "atomic_write_manifest", forbidden)
    make_committer(committed_project).commit(revision_two_request(committed_project))


def test_success_promotes_domain_verified_artifacts_and_switches_both_pointers(
    committed_project: Path,
) -> None:
    before = read_manifest(committed_project)
    request = revision_two_request(committed_project)
    result = make_committer(committed_project).commit(request)
    after = read_manifest(committed_project)

    assert after == result
    assert after.manifest_revision == before.manifest_revision + 2
    assert after.active_project == request.next_project
    assert after.active_registry == request.next_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED
    project_payload = yaml.safe_load(
        (committed_project / after.active_project.path).read_text(encoding="utf-8")
    )
    assert verify_artifact_hash(ProductionProject.model_validate(project_payload))
    registry, _ = load_asset_registry(
        after.active_registry.path, committed_project, committed_project / "assets/files"
    )
    assert registry.revision_id == after.active_registry.revision_id


def test_identical_replay_is_deterministic_and_conflicting_attempt_is_rejected(
    committed_project: Path,
) -> None:
    request = revision_two_request(committed_project)
    first = make_committer(committed_project).commit(request)
    second = make_committer(committed_project).commit(request)
    assert second == first
    assert len(second.attempts) == 1

    conflicting = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=second.manifest_revision,
        artifacts=request.artifacts,
        next_project=request.next_project,
        next_registry=RegistrySnapshotPointer(
            path=request.next_registry.path,
            revision_id=request.next_registry.revision_id,
            content_hash=request.next_registry.content_hash,
            file_sha256=ONE_HASH,
        ),
    )
    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(conflicting)
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_commit_carries_future_artifact_without_granting_new_pointer_ownership(
    committed_project: Path,
) -> None:
    request = revision_two_request(committed_project)
    future = PreparedArtifact(
        Path("composition/source.future.json"), b'{"future":true}\n', hashlib.sha256(b'{"future":true}\n').hexdigest()
    )
    request = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision,
        artifacts=request.artifacts + (future,),
        next_project=request.next_project,
        next_registry=request.next_registry,
    )

    result = make_committer(committed_project).commit(request)
    assert (committed_project / future.relative_path).read_bytes() == future.payload
    assert result.active_project == request.next_project
    assert result.active_registry == request.next_registry
    assert not hasattr(result, "active_composition")


@pytest.mark.parametrize(
    "relative_path",
    [
        Path("state/manifest.json"),
        Path("state/commit.lock"),
        Path("runs/run-1/manifest.json"),
        Path("../outside"),
        Path("/tmp/outside"),
    ],
)
def test_commit_rejects_unsafe_future_artifact_targets(
    committed_project: Path, relative_path: Path
) -> None:
    request = revision_two_request(committed_project)
    future = PreparedArtifact(relative_path, b"future", hashlib.sha256(b"future").hexdigest())
    unsafe = StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision,
        artifacts=request.artifacts + (future,),
        next_project=request.next_project,
        next_registry=request.next_registry,
    )
    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(unsafe)
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


@pytest.mark.parametrize(
    "phase",
    [CommitPhase.AFTER_MANIFEST_REPLACE, CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC],
)
def test_running_manifest_post_replace_failure_records_failed_attempt(
    committed_project: Path, phase: CommitPhase
) -> None:
    before = read_manifest(committed_project)
    with pytest.raises(AiVideoError) as exc:
        make_committer(
            committed_project, injector=RaisingOnOccurrence(phase, occurrence=1)
        ).commit(revision_two_request(committed_project))

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_COMMIT_FAILED
    after = read_manifest(committed_project)
    assert after.manifest_revision == before.manifest_revision + 2
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.FAILED


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_failed_attempt_persistence_process_exception_overrides_commit_failure(
    committed_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    writer = make_committer(
        committed_project, injector=RaisingCrashInjector(CommitPhase.AFTER_ATTEMPT_STARTED)
    )
    original_write = writer._write_manifest_atomic

    def interrupt_failed_manifest(
        manifest: ProductionManifest, *, on_replace: object = None
    ) -> Path:
        if manifest.attempts[-1].status is StateCommitStatus.FAILED:
            raise exception_type()
        return original_write(manifest, on_replace=on_replace)  # type: ignore[arg-type]

    monkeypatch.setattr(writer, "_write_manifest_atomic", interrupt_failed_manifest)
    with pytest.raises(exception_type) as exc:
        writer.commit(revision_two_request(committed_project))

    assert any("injected failure" in note for note in exc.value.__notes__)


def test_final_manifest_lock_cleanup_failure_has_unknown_outcome(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai_video.production.state_commit as state_commit_module

    fake_fcntl = _FakeFcntl(unlock_error=True)
    monkeypatch.setattr(state_commit_module, "fcntl", fake_fcntl)
    request = revision_two_request(committed_project)
    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(request)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    after = read_manifest(committed_project)
    assert after.active_project == request.next_project
    assert after.active_registry == request.next_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED


def test_final_manifest_process_lock_cleanup_preserves_exception_type_and_note(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_fcntl = _FakeFcntl(unlock_error=KeyboardInterrupt())
    monkeypatch.setattr(state_commit, "fcntl", fake_fcntl)
    request = revision_two_request(committed_project)

    with pytest.raises(KeyboardInterrupt) as exc:
        make_committer(committed_project).commit(request)

    assert any("outcome may be committed" in note.lower() for note in exc.value.__notes__)
    after = read_manifest(committed_project)
    assert after.active_project == request.next_project
    assert after.active_registry == request.next_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED


def _with_generic_artifact(request: StateCommitRequest, payload: bytes) -> StateCommitRequest:
    future = PreparedArtifact(
        Path("composition/source.future.json"), payload, hashlib.sha256(payload).hexdigest()
    )
    return StateCommitRequest(
        attempt_id=request.attempt_id,
        operation=request.operation,
        expected_manifest_revision=request.expected_manifest_revision,
        artifacts=request.artifacts + (future,),
        next_project=request.next_project,
        next_registry=request.next_registry,
    )


def test_replay_rejects_added_removed_or_changed_generic_artifact(
    committed_project: Path,
) -> None:
    base = revision_two_request(committed_project)
    original = _with_generic_artifact(base, b'{"future":true}\n')
    first = make_committer(committed_project).commit(original)
    assert make_committer(committed_project).commit(original) == first
    assert first.attempts[-1].candidate_artifacts_hash == state_commit._candidate_artifacts_hash(
        original.artifacts
    )

    added = StateCommitRequest(
        attempt_id=base.attempt_id,
        operation=base.operation,
        expected_manifest_revision=first.manifest_revision,
        artifacts=original.artifacts
        + (PreparedArtifact(Path("composition/extra.json"), b"extra", hashlib.sha256(b"extra").hexdigest()),),
        next_project=base.next_project,
        next_registry=base.next_registry,
    )
    changed = _with_generic_artifact(base, b'{"future":false}\n')
    removed = base
    for candidate in (added, changed, removed):
        with pytest.raises(AiVideoError) as exc:
            make_committer(committed_project).commit(candidate)
        assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_candidate_with_missing_creative_reference_fails_before_pointer_replace(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    project, registry = project_factory.load_revision_two_models(committed_project)
    broken_refs = project.artifacts.model_copy(
        update={"story": project.artifacts.story.model_copy(update={"path": "creative/missing.yaml"})}
    )
    broken_project = seal_artifact(
        project.model_copy(update={"artifacts": broken_refs, "content_hash": ZERO_HASH})
    )
    request = state_commit.prepare_project_registry_commit(
        manifest=manifest,
        project=broken_project,
        registry=registry,
        attempt_id="missing-creative-reference",
    )

    with pytest.raises(AiVideoError) as exc:
        make_committer(committed_project).commit(request)

    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    after = read_manifest(committed_project)
    assert after.active_project == manifest.active_project
    assert after.active_registry == manifest.active_registry
    assert after.attempts[-1].status is StateCommitStatus.FAILED


def test_candidate_strategy_reference_validation_is_run_before_pointer_replace(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    project, registry = project_factory.load_revision_two_models(committed_project)
    original_shot = Shot.model_validate(
        yaml.safe_load((committed_project / "creative/shots/shot-1.yaml").read_text())
    )
    invalid_shot = seal_artifact(
        original_shot.model_copy(update={"character_ids": ("missing-character",), "content_hash": ZERO_HASH})
    )
    invalid_path = committed_project / "creative/shots/invalid-reference.yaml"
    project_factory._write_yaml(invalid_path, invalid_shot)
    refs = project.artifacts.model_copy(
        update={"shots": (project.artifacts.shots[0].model_copy(
            update={"path": invalid_path.relative_to(committed_project), "content_hash": invalid_shot.content_hash}
        ),)}
    )
    invalid_project = seal_artifact(
        project.model_copy(update={"artifacts": refs, "content_hash": ZERO_HASH})
    )
    request = state_commit.prepare_project_registry_commit(
        manifest=manifest,
        project=invalid_project,
        registry=registry,
        attempt_id="invalid-shot-reference",
    )

    with pytest.raises(AiVideoError, match="unknown character"):
        make_committer(committed_project).commit(request)
    after = read_manifest(committed_project)
    assert after.active_project == manifest.active_project
    assert after.attempts[-1].status is StateCommitStatus.FAILED


def test_candidate_loader_allows_only_root_special_case_or_contained_versioned_snapshot(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    legacy = load_production_project_candidate(
        committed_project,
        manifest,
        Path("project.yaml"),
        manifest.active_registry.path,
    )
    assert legacy.project.revision == manifest.active_project.revision

    request = revision_two_request(committed_project)
    committed = make_committer(committed_project).commit(request)
    versioned = load_production_project_candidate(
        committed_project,
        committed,
        committed.active_project.path,
        committed.active_registry.path,
    )
    assert versioned.project.content_hash == committed.active_project.content_hash


def test_candidate_loader_rejects_versioned_path_symlink_to_root_project(
    committed_project: Path,
) -> None:
    manifest = read_manifest(committed_project)
    linked_project = committed_project / "state/projects/link.yaml"
    linked_project.parent.mkdir(parents=True, exist_ok=True)
    linked_project.symlink_to(committed_project / "project.yaml")

    with pytest.raises(AiVideoError) as exc:
        load_production_project_candidate(
            committed_project,
            manifest,
            Path("state/projects/link.yaml"),
            manifest.active_registry.path,
        )

    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


@pytest.mark.parametrize("exception_type", [KeyboardInterrupt, SystemExit])
def test_process_interrupt_before_final_replace_propagates_and_leaves_running_attempt(
    committed_project: Path, exception_type: type[BaseException]
) -> None:
    before = read_manifest(committed_project)
    with pytest.raises(exception_type):
        make_committer(
            committed_project,
            injector=ProcessInterruptInjector(
                CommitPhase.AFTER_ATTEMPT_STARTED, 1, exception_type
            ),
        ).commit(revision_two_request(committed_project))

    after = read_manifest(committed_project)
    assert after.manifest_revision == before.manifest_revision + 1
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.RUNNING


def test_keyboard_interrupt_after_final_replace_propagates_with_outcome_note(
    committed_project: Path,
) -> None:
    request = revision_two_request(committed_project)
    with pytest.raises(KeyboardInterrupt) as exc:
        make_committer(
            committed_project,
            injector=ProcessInterruptInjector(
                CommitPhase.AFTER_MANIFEST_REPLACE, 2, KeyboardInterrupt
            ),
        ).commit(request)

    assert any("outcome may be committed" in note.lower() for note in exc.value.__notes__)
    after = read_manifest(committed_project)
    assert after.active_project == request.next_project
    assert after.active_registry == request.next_registry
    assert after.attempts[-1].status is StateCommitStatus.SUCCEEDED


def _make_p5_bootstrap_transition(root: Path):
    from ai_video.production.dependency import (
        build_applied_dependency_evidence,
        build_production_dependency_graph,
        desired_fingerprints,
        resolve_dependency_state,
    )

    inputs = project_factory.make_p5_dependency_inputs(root)
    manifest = read_manifest(root).model_copy(
        update={"active_registry": inputs.project.manifest.active_registry}
    )
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    graph = build_production_dependency_graph(inputs)
    applied = build_applied_dependency_evidence(inputs, None)
    states = resolve_dependency_state(graph, applied).states
    desired = desired_fingerprints(graph)
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=manifest.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired,
    )
    return graph, transition, desired


def test_prepare_dependency_graph_transition_is_pure_and_recomputes_hashes(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    before = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    repeated = prepare_dependency_graph_transition(
        expected_manifest_revision=transition.expected_manifest_revision,
        base_dependency_graph=transition.base_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=transition.candidate_dependency_states,
        expected_desired_fingerprints=desired,
    )

    assert repeated == transition
    assert transition.candidate_dependency_graph.revision_id == graph.revision_id
    assert transition.candidate_dependency_states
    assert not (tmp_path / transition.candidate_dependency_graph.path).exists()
    after = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_prepare_dependency_graph_transition_rejects_bare_applied_fingerprint(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    selected = next(
        state
        for state in transition.candidate_dependency_states
        if state.lifecycle is DependencyLifecycle.STALE
    )
    states = tuple(
        state.model_copy(update={"applied_fingerprint": "f" * 64})
        if state.node_id == selected.node_id
        else state
        for state in transition.candidate_dependency_states
    )

    with pytest.raises(AiVideoError) as exc_info:
        prepare_dependency_graph_transition(
            expected_manifest_revision=transition.expected_manifest_revision,
            base_dependency_graph=transition.base_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=states,
            expected_desired_fingerprints=desired,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_package_root_exposes_only_reviewed_dependency_transition_surface() -> None:
    import ai_video.production as production

    assert production.prepare_dependency_graph_transition is prepare_dependency_graph_transition
    assert hasattr(production.ProductionStateCommitter, "bootstrap_dependency_graph")
    assert hasattr(production.ProductionStateCommitter, "record_dependency_node_applied")
    assert hasattr(production.ProductionStateCommitter, "record_dependency_node_failed")
    assert not hasattr(production, "GraphWriter")
    assert not hasattr(production, "write_dependency_graph_atomic")
    assert not hasattr(production, "recover_dependency_graph")


@pytest.mark.parametrize("schema_version", ["2.0", "2.1", "2.2"])
def test_bootstrap_dependency_graph_upgrades_2x_and_exact_replay_is_zero_write(
    tmp_path: Path, schema_version: str,
) -> None:
    project_factory.write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    original = read_manifest(tmp_path).model_copy(
        update={"schema_version": schema_version}
    )
    manifest_path.write_text(original.model_dump_json(indent=2), encoding="utf-8")
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    writer = ProductionStateCommitter(tmp_path)

    committed = writer.bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-1",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )

    assert committed.schema_version == "2.3"
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    assert committed.dependency_states == transition.candidate_dependency_states
    assert committed.manifest_revision == transition.expected_manifest_revision + 2
    assert committed.attempts[-1].status is StateCommitStatus.SUCCEEDED
    graph_mtime = (tmp_path / transition.candidate_dependency_graph.path).stat().st_mtime_ns
    manifest_mtime = (tmp_path / "state/manifest.json").stat().st_mtime_ns

    replayed = writer.bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-1",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )

    assert replayed == committed
    assert (tmp_path / transition.candidate_dependency_graph.path).stat().st_mtime_ns == graph_mtime
    assert (tmp_path / "state/manifest.json").stat().st_mtime_ns == manifest_mtime

    current_transition = prepare_dependency_graph_transition(
        expected_manifest_revision=committed.manifest_revision,
        base_dependency_graph=committed.active_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=committed.dependency_states,
        expected_desired_fingerprints=desired,
    )
    replayed_with_new_id = writer.bootstrap_dependency_graph(
        attempt_id=f"p5-bootstrap-{schema_version}-exact-current",
        graph=graph,
        transition=current_transition,
        expected_desired_fingerprints=desired,
    )
    assert replayed_with_new_id == committed
    assert (tmp_path / "state/manifest.json").stat().st_mtime_ns == manifest_mtime


def test_record_dependency_node_failed_preserves_precise_frontier(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    committed = writer.bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-failure",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    stale = next(
        state
        for state in committed.dependency_states
        if state.lifecycle is DependencyLifecycle.STALE
    )

    failed = writer.record_dependency_node_failed(
        expected_manifest_revision=committed.manifest_revision,
        active_dependency_graph=committed.active_dependency_graph,
        candidate_dependency_graph=committed.active_dependency_graph,
        node_id=stale.node_id,
        desired_fingerprint=stale.desired_fingerprint,
        error_code="fixture_failed",
        error_message="Fixture rebuild failed.",
    )

    failed_by_id = {state.node_id: state for state in failed.dependency_states}
    assert failed_by_id[stale.node_id].lifecycle is DependencyLifecycle.FAILED
    assert failed_by_id[stale.node_id].error_code == "fixture_failed"


def test_manifest_23_project_registry_mutation_requires_transition_before_write(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()
    request = project_factory.make_revision_two_request(
        tmp_path, attempt_id="p5-missing-transition"
    )

    with pytest.raises(AiVideoError, match="requires a dependency graph transition"):
        ProductionStateCommitter(tmp_path).commit(request)

    assert (tmp_path / "state/manifest.json").read_bytes() == before
    assert not any(
        item.attempt_id == "p5-missing-transition"
        for item in read_manifest(tmp_path).attempts
    )


def test_manifest_23_project_registry_mutation_atomically_selects_exact_graph(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    before = read_manifest(tmp_path)
    request = project_factory.make_revision_two_request(
        tmp_path, attempt_id="p5-project-transition"
    )
    request, _ = project_factory.attach_p5_dependency_transition(tmp_path, request)

    committed = ProductionStateCommitter(tmp_path).commit(request)

    transition = request.dependency_graph_transition
    assert transition is not None
    manifest_mtime = (tmp_path / "state/manifest.json").stat().st_mtime_ns
    graph_mtime = (
        tmp_path / transition.candidate_dependency_graph.path
    ).stat().st_mtime_ns
    replayed = ProductionStateCommitter(tmp_path).commit(request)
    assert replayed == committed
    assert committed.active_project == request.next_project
    assert committed.active_registry == request.next_registry
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    assert committed.dependency_states == transition.candidate_dependency_states
    assert committed.active_render_state == before.active_render_state
    fresh_assets = {
        state.node_id
        for state in committed.dependency_states
        if state.node_id.startswith("asset:")
        and state.lifecycle is DependencyLifecycle.FRESH
    }
    assert fresh_assets
    assert (tmp_path / "state/manifest.json").stat().st_mtime_ns == manifest_mtime
    assert (
        tmp_path / transition.candidate_dependency_graph.path
    ).stat().st_mtime_ns == graph_mtime


def test_manifest_23_audio_import_coactivates_registry_graph_and_states(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    request = project_factory.make_audio_import_upgrade_request(
        tmp_path, attempt_id="p5-audio-transition"
    )
    request, _ = project_factory.attach_p5_dependency_transition(tmp_path, request)

    committed = ProductionStateCommitter(tmp_path).commit(request)

    transition = request.dependency_graph_transition
    assert transition is not None
    assert committed.schema_version == "2.3"
    assert committed.active_project == request.next_project
    assert committed.active_registry == request.next_registry
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    assert committed.dependency_states == transition.candidate_dependency_states
    assert committed.attempts[-1].candidate_project is None


def test_manifest_23_project_transition_rejects_wrong_desired_before_write(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    request = project_factory.make_revision_two_request(
        tmp_path, attempt_id="p5-project-wrong-desired"
    )
    request, _ = project_factory.attach_p5_dependency_transition(tmp_path, request)
    transition = request.dependency_graph_transition
    assert transition is not None
    selected = transition.candidate_dependency_states[0]
    forged_state = selected.model_copy(update={"desired_fingerprint": "f" * 64})
    forged_states = (forged_state, *transition.candidate_dependency_states[1:])
    forged = transition.model_copy(
        update={
            "candidate_dependency_states": forged_states,
            "candidate_dependency_states_hash": state_commit._dependency_states_hash(
                forged_states
            ),
        }
    )
    request = replace(request, dependency_graph_transition=forged)
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError, match="resolved lifecycle|transition claim"):
        ProductionStateCommitter(tmp_path).commit(request)

    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_manifest_23_voice_activation_coactivates_registry_and_precise_graph(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    project_factory.make_manifest_23_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(tmp_path)
    writer.begin_voice_generation(
        request,
        preview,
        authorization,
        dependency_transition_preparer_available=True,
    )
    writer.record_voice_submit_intent(request, preview, authorization)
    manifest = read_manifest(tmp_path)
    activation, audio_ids = project_factory.make_voice_activation_request(
        tmp_path,
        request,
        authorization,
        expected_manifest_revision=manifest.manifest_revision,
        include_caption=True,
    )
    activation, _ = project_factory.attach_p5_dependency_transition(
        tmp_path, activation
    )

    committed = writer.activate_voice_assets(
        activation,
        audio_asset_ids=audio_ids,
        caption_asset_ids=("caption-voice-attempt-1",),
    )

    transition = activation.dependency_graph_transition
    assert transition is not None
    assert committed.active_registry == activation.next_registry
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    assert committed.dependency_states == transition.candidate_dependency_states
    by_id = {state.node_id: state for state in committed.dependency_states}
    assert by_id["asset:image-shot-1"].lifecycle is DependencyLifecycle.FRESH
    assert by_id["asset:bgm-theme"].lifecycle is DependencyLifecycle.FRESH

    succeeded = committed.attempts[-1]
    candidate_attempt = succeeded.model_copy(
        update={
            "status": StateCommitStatus.RUNNING,
            "voice_phase": "candidate",
            "finished_at": None,
        }
    )
    candidate_manifest = manifest.model_copy(
        update={
            "manifest_revision": committed.manifest_revision - 1,
            "attempts": tuple(
                candidate_attempt if item.attempt_id == request.attempt_id else item
                for item in manifest.attempts
            ),
        }
    )
    (tmp_path / "state/manifest.json").write_text(
        candidate_manifest.model_dump_json(indent=2), encoding="utf-8"
    )
    assert transition.candidate_dependency_graph != manifest.active_dependency_graph
    candidate_graph_path = tmp_path / transition.candidate_dependency_graph.path
    candidate_graph_payload = candidate_graph_path.read_bytes()
    candidate_graph_path.unlink()
    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).recover()
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    candidate_graph_path.write_bytes(candidate_graph_payload)
    report = ProductionStateCommitter(tmp_path).recover()
    recovered = read_manifest(tmp_path)
    assert report.manifest_revision_after == candidate_manifest.manifest_revision + 1
    assert recovered.active_registry == manifest.active_registry
    assert recovered.active_dependency_graph == manifest.active_dependency_graph
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert any(
        item.path == transition.candidate_dependency_graph.path
        and item.disposition is RecoveryDisposition.INTERRUPTED_RECORDED
        and item.sha256 == transition.candidate_dependency_graph.file_sha256
        for item in report.items
    )


def test_record_dependency_node_failed_rejects_standalone_renderer_node(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    committed = writer.bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-renderer-failure",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    renderer_state = next(
        state
        for state in committed.dependency_states
        if state.node_id.startswith(("renderer-source:", "render:"))
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_dependency_node_failed(
            expected_manifest_revision=committed.manifest_revision,
            active_dependency_graph=committed.active_dependency_graph,
            candidate_dependency_graph=committed.active_dependency_graph,
            node_id=renderer_state.node_id,
            desired_fingerprint=renderer_state.desired_fingerprint,
            error_code="renderer_failed",
            error_message="safe",
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID


def test_dependency_result_replace_failure_maps_unknown_outcome(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    committed = ProductionStateCommitter(tmp_path).bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-result-outcome",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    stale = next(
        state
        for state in committed.dependency_states
        if state.lifecycle is DependencyLifecycle.STALE
    )
    writer = make_committer(
        tmp_path,
        injector=RaisingCrashInjector(CommitPhase.AFTER_MANIFEST_REPLACE),
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.record_dependency_node_failed(
            expected_manifest_revision=committed.manifest_revision,
            active_dependency_graph=committed.active_dependency_graph,
            candidate_dependency_graph=committed.active_dependency_graph,
            node_id=stale.node_id,
            desired_fingerprint=stale.desired_fingerprint,
            error_code="fixture_failed",
            error_message="safe",
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    after = read_manifest(tmp_path)
    assert next(
        state for state in after.dependency_states if state.node_id == stale.node_id
    ).lifecycle is DependencyLifecycle.FAILED


def test_record_dependency_asset_applied_reopens_fixed_registry_owner_and_replays(
    tmp_path: Path,
) -> None:
    from ai_video.production.dependency import (
        build_dependency_graph,
        desired_fingerprints,
    )

    project_factory.write_production_project(tmp_path)
    production_graph, _, _ = _make_p5_bootstrap_transition(tmp_path)
    node = next(
        item
        for item in production_graph.nodes
        if item.node_id == "asset:image-shot-1"
    )
    graph = build_dependency_graph((node,), ())
    desired = desired_fingerprints(graph)
    manifest = read_manifest(tmp_path)
    stale = DependencyNodeState(
        node_id=node.node_id,
        graph_revision_id=graph.revision_id,
        desired_fingerprint=desired[node.node_id],
        lifecycle=DependencyLifecycle.STALE,
    )
    transition = prepare_dependency_graph_transition(
        expected_manifest_revision=manifest.manifest_revision,
        base_dependency_graph=None,
        candidate_graph=graph,
        candidate_dependency_states=(stale,),
        expected_desired_fingerprints=desired,
    )
    writer = ProductionStateCommitter(tmp_path)
    committed = writer.bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-asset-apply",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )
    evidence = RegistryDependencyEvidence(
        owner="registry_snapshot",
        pointer=committed.active_registry,
        artifact_id=node.artifact_id,
        artifact_fingerprint=desired[node.node_id],
    )

    applied = writer.record_dependency_node_applied(
        expected_manifest_revision=committed.manifest_revision,
        active_dependency_graph=committed.active_dependency_graph,
        candidate_dependency_graph=committed.active_dependency_graph,
        node_id=node.node_id,
        desired_fingerprint=desired[node.node_id],
        evidence=evidence,
    )
    manifest_mtime = (tmp_path / "state/manifest.json").stat().st_mtime_ns
    replayed = writer.record_dependency_node_applied(
        expected_manifest_revision=applied.manifest_revision,
        active_dependency_graph=applied.active_dependency_graph,
        candidate_dependency_graph=applied.active_dependency_graph,
        node_id=node.node_id,
        desired_fingerprint=desired[node.node_id],
        evidence=evidence,
    )

    assert applied.dependency_states[0].lifecycle is DependencyLifecycle.FRESH
    assert replayed == applied
    assert (tmp_path / "state/manifest.json").stat().st_mtime_ns == manifest_mtime


def test_bootstrap_dependency_graph_rejects_unverified_existing_evidence_before_write(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    selected = next(
        state
        for state in transition.candidate_dependency_states
        if isinstance(state.applied_evidence, RegistryDependencyEvidence)
    )
    assert selected.applied_evidence is not None
    bad_evidence = selected.applied_evidence.model_copy(
        update={
            "pointer": selected.applied_evidence.pointer.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    states = tuple(
        state.model_copy(update={"applied_evidence": bad_evidence})
        if state.node_id == selected.node_id
        else state
        for state in transition.candidate_dependency_states
    )
    forged = prepare_dependency_graph_transition(
        expected_manifest_revision=transition.expected_manifest_revision,
        base_dependency_graph=transition.base_dependency_graph,
        candidate_graph=graph,
        candidate_dependency_states=states,
        expected_desired_fingerprints=desired,
    )
    before = read_manifest(tmp_path)

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).bootstrap_dependency_graph(
            attempt_id="p5-bootstrap-tampered-evidence",
            graph=graph,
            transition=forged,
            expected_desired_fingerprints=desired,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert read_manifest(tmp_path) == before
    assert not (tmp_path / forged.candidate_dependency_graph.path).exists()


def test_bootstrap_dependency_graph_durably_promotes_before_final_activation(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    ops = RecordingNativeFileOps(tmp_path)

    committed = ProductionStateCommitter(tmp_path, file_ops=ops).bootstrap_dependency_graph(
        attempt_id="p5-bootstrap-order",
        graph=graph,
        transition=transition,
        expected_desired_fingerprints=desired,
    )

    graph_path = transition.candidate_dependency_graph.path.as_posix()
    graph_link = next(
        index
        for index, event in enumerate(ops.events)
        if event.startswith("link:state/") and event.endswith(f"->{graph_path}")
    )
    graph_parent_fsync = next(
        index
        for index, event in enumerate(ops.events[graph_link + 1 :], graph_link + 1)
        if event == "fsync_dir:state"
    )
    graph_reopen_hash = next(
        index
        for index, event in enumerate(
            ops.events[graph_parent_fsync + 1 :], graph_parent_fsync + 1
        )
        if event == f"sha:{graph_path}"
    )
    manifest_replaces = [
        index
        for index, event in enumerate(ops.events)
        if event == "replace:state/.p2a-manifest.tmp->state/manifest.json"
    ]

    assert len(manifest_replaces) == 2
    assert graph_link < graph_parent_fsync < graph_reopen_hash < manifest_replaces[-1]
    assert committed.active_dependency_graph == transition.candidate_dependency_graph


@pytest.mark.parametrize(
    ("phase", "candidate_is_durable"),
    [
        (CommitPhase.AFTER_ATTEMPT_STARTED, False),
        (CommitPhase.AFTER_ARTIFACT_VERIFICATION, True),
    ],
)
def test_recovery_converges_interrupted_dependency_bootstrap_without_activation(
    tmp_path: Path, phase: CommitPhase, candidate_is_durable: bool,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    writer = make_committer(
        tmp_path,
        injector=ProcessInterruptInjector(phase, 1, KeyboardInterrupt),
    )

    with pytest.raises(KeyboardInterrupt):
        writer.bootstrap_dependency_graph(
            attempt_id=f"p5-bootstrap-crash-{phase.value}",
            graph=graph,
            transition=transition,
            expected_desired_fingerprints=desired,
        )

    interrupted = read_manifest(tmp_path)
    assert interrupted.active_dependency_graph == transition.base_dependency_graph
    assert interrupted.attempts[-1].status is StateCommitStatus.RUNNING
    assert (
        tmp_path / transition.candidate_dependency_graph.path
    ).exists() is candidate_is_durable

    report = ProductionStateCommitter(tmp_path).recover()
    recovered = read_manifest(tmp_path)

    assert recovered.active_dependency_graph == transition.base_dependency_graph
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.manifest_revision == interrupted.manifest_revision + 1
    candidate_items = [
        item
        for item in report.items
        if item.path == transition.candidate_dependency_graph.path
    ]
    assert bool(candidate_items) is candidate_is_durable
    if candidate_items:
        assert candidate_items[0].disposition.value == "interrupted_recorded"


def test_recovery_reopens_active_graph_after_final_replace_process_interrupt(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    graph, transition, desired = _make_p5_bootstrap_transition(tmp_path)
    writer = make_committer(
        tmp_path,
        injector=ProcessInterruptInjector(
            CommitPhase.AFTER_MANIFEST_REPLACE, 2, KeyboardInterrupt
        ),
    )

    with pytest.raises(KeyboardInterrupt):
        writer.bootstrap_dependency_graph(
            attempt_id="p5-bootstrap-final-replace-interrupt",
            graph=graph,
            transition=transition,
            expected_desired_fingerprints=desired,
        )

    committed = read_manifest(tmp_path)
    assert committed.active_dependency_graph == transition.candidate_dependency_graph
    assert committed.attempts[-1].status is StateCommitStatus.SUCCEEDED
    report = ProductionStateCommitter(tmp_path).recover()

    assert report.manifest_revision_after == committed.manifest_revision
    assert any(
        item.path == transition.candidate_dependency_graph.path
        and item.disposition.value == "active"
        for item in report.items
    )
