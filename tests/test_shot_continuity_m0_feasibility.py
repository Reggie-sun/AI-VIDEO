from __future__ import annotations

import json

import pytest

from ai_video.production.models import ActorIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.paths import (
    canonical_m0_endpoint_feasibility_approval_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_feasibility import (
    M0EndpointFeasibilityHumanDecision,
    m0_endpoint_feasibility_scope_fingerprint,
    prepare_m0_endpoint_feasibility_approval_commit,
    reopen_m0_endpoint_feasibility_approval,
)
from ai_video.production.shot_continuity_motion_tail import (
    prepare_full_source_motion_tail_commit,
)


def _prepared_tail(tmp_path):
    from test_shot_continuity_motion_tail import _accepted_source, _motion_analysis

    root, committer, source_attempt_id, loaded = _accepted_source(tmp_path)
    source_state = next(
        item for item in loaded.manifest.attempts
        if item.attempt_id == source_attempt_id
    ).video_generation_state
    assert source_state is not None
    source_request = committer._reopen_video_request(source_state.request)
    source_asset = next(
        item for item in loaded.registry.assets
        if item.asset_id == source_request.output_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")
    prepared = prepare_full_source_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="m0-feasibility-tail-v1",
        source_attempt_id=source_attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-feasibility-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=1_000,
        provider_max_duration_milliseconds=10_000,
        motion_analysis=_motion_analysis(root, source_asset),
    )
    assert prepared.commit_request is not None
    committer.commit(prepared.commit_request)
    return root, committer, load_production_project(root / "project.yaml"), prepared


_QUALIFICATION_ATTEMPT_ID = "m0-quality-v1-attempt"
_GENERATION_ID = "m0-quality-v1-generation"
_OUTPUT_ASSET_ID = "video-shot-rainy-station-4-m0-quality-v1"
_EXECUTION_STACK_HASH = "4" * 64
_PROFILE_DOCUMENT_HASH = "2" * 64


def _prepare_approval(root, committer, project, tail):
    target = next(item for item in project.shots if item.shot_id == "rainy-station-4")
    endpoint_id = next(
        role.asset_ids[0]
        for role in target.required_asset_roles
        if role.role == "approved_endpoint"
    )
    identity_id = project.characters[0].reference_asset_ids[0]
    scope_fingerprint = m0_endpoint_feasibility_scope_fingerprint(
        project_root=root,
        project=project,
        qualification_attempt_id=_QUALIFICATION_ATTEMPT_ID,
        generation_id=_GENERATION_ID,
        output_asset_id=_OUTPUT_ASSET_ID,
        execution_stack_hash=_EXECUTION_STACK_HASH,
        profile_document_hash=_PROFILE_DOCUMENT_HASH,
        target_shot_id=target.shot_id,
        output_duration_milliseconds=5_167,
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=tail.tail_asset.asset_id,
    )
    human_decision = M0EndpointFeasibilityHumanDecision.create(
        decision_id="user-chat-a4-authorized-20260826-v1",
        reviewer=ActorIdentity(actor_id="reggie", actor_kind="human"),
        decided_at="2026-08-26T12:00:00+08:00",
        evidence_source_id="test-human-review-a4-v1",
        evidence_source_sha256=canonical_sha256(
            {"evidence": "test-only exact A4 feasibility review"}
        ),
        scope_fingerprint=scope_fingerprint,
        axis_check="PASS",
        screen_direction_check="PASS",
        subject_scale_check="PASS",
        fov_check="PASS",
        reachable_displacement_check="PASS",
        no_teleport_check="PASS",
    )
    return prepare_m0_endpoint_feasibility_approval_commit(
        project_root=root,
        committer=committer,
        project=project,
        attempt_id="m0-endpoint-feasibility-v1",
        human_decision=human_decision,
        qualification_attempt_id=_QUALIFICATION_ATTEMPT_ID,
        generation_id=_GENERATION_ID,
        output_asset_id=_OUTPUT_ASSET_ID,
        execution_stack_hash=_EXECUTION_STACK_HASH,
        profile_document_hash=_PROFILE_DOCUMENT_HASH,
        target_shot_id=target.shot_id,
        output_duration_milliseconds=5_167,
        identity_asset_id=identity_id,
        endpoint_asset_id=endpoint_id,
        motion_tail_asset_id=tail.tail_asset.asset_id,
    )


def test_m0_endpoint_approval_is_hash_bound_reopens_and_replays_zero_write(
    tmp_path,
) -> None:
    root, committer, project, tail = _prepared_tail(tmp_path)
    prepared = _prepare_approval(root, committer, project, tail)
    assert prepared.commit_request is not None
    before_project = project.manifest.active_project
    before_registry = project.manifest.active_registry
    committer.commit(prepared.commit_request)
    reopened_project = load_production_project(root / "project.yaml")
    reopened = reopen_m0_endpoint_feasibility_approval(
        root, prepared.approval.content_hash, project=reopened_project
    )

    assert reopened == prepared.approval
    assert reopened_project.manifest.active_project == before_project
    assert reopened_project.manifest.active_registry == before_registry
    revision = reopened_project.manifest.manifest_revision
    replayed = _prepare_approval(root, committer, reopened_project, tail)
    assert replayed.replayed is True
    assert replayed.commit_request is None
    assert committer._read_manifest().manifest_revision == revision


def test_m0_endpoint_approval_tamper_fails_closed(tmp_path) -> None:
    root, committer, project, tail = _prepared_tail(tmp_path)
    prepared = _prepare_approval(root, committer, project, tail)
    assert prepared.commit_request is not None
    committer.commit(prepared.commit_request)
    path = root / canonical_m0_endpoint_feasibility_approval_path(
        prepared.approval.content_hash
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["output_duration_milliseconds"] += 1
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(Exception, match="reopen"):
        reopen_m0_endpoint_feasibility_approval(
            root,
            prepared.approval.content_hash,
            project=load_production_project(root / "project.yaml"),
        )
