from __future__ import annotations

import json

import pytest

from ai_video.production.paths import (
    canonical_full_source_motion_analysis_receipt_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_motion_tail import (
    FullSourceMotionAnalysisReceipt,
    FullSourceMotionSpanMeasurement,
    analyze_full_source_motion,
    prepare_full_source_motion_tail_commit,
    reopen_full_source_motion_analysis_receipt,
    reopen_full_source_motion_tail_receipt,
    validate_full_source_motion_tail,
)


def test_motion_span_rejects_two_isolated_nonzero_transitions() -> None:
    with pytest.raises(ValueError):
        FullSourceMotionSpanMeasurement(
            span_id="frames-0-3",
            start_frame_index=0,
            end_frame_index=3,
            sample_count=4,
            nonzero_ydif_count=2,
            longest_nonzero_ydif_run=1,
            mean_ydif_millionths=1,
            measurement_output_sha256="a" * 64,
        )


def _accepted_source(tmp_path):
    from test_shot_continuity_source_operator import _reach_source_boundary_candidate

    root, committer, attempt_id, _, _, _ = _reach_source_boundary_candidate(tmp_path)
    committer.activate_video_candidate(attempt_id=attempt_id)
    return root, committer, attempt_id, load_production_project(root / "project.yaml")


def _motion_analysis(root, source_asset):
    return analyze_full_source_motion(root, source_asset)


def test_full_source_zero_copy_tail_is_a_distinct_registry_asset_and_reopens(
    tmp_path,
) -> None:
    root, committer, attempt_id, loaded = _accepted_source(tmp_path)
    source_attempt = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    )
    source_state = source_attempt.video_generation_state
    assert source_state is not None
    source_request = committer._reopen_video_request(source_state.request)
    source_asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == source_request.output_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")

    prepared = prepare_full_source_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="full-source-motion-tail-v1",
        source_attempt_id=attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=1_000,
        provider_max_duration_milliseconds=10_000,
        motion_analysis=_motion_analysis(root, source_asset),
    )

    assert prepared.tail_asset.asset_id != source_asset.asset_id
    assert prepared.tail_asset.artifact_path == source_asset.artifact_path
    assert prepared.tail_asset.sha256 == source_asset.sha256
    assert prepared.receipt.start_frame_index == 0
    assert prepared.receipt.end_frame_index == 123
    assert prepared.commit_request.dependency_graph_transition is not None

    committed = committer.commit(prepared.commit_request)
    reopened = load_production_project(root / "project.yaml")
    validated = validate_full_source_motion_tail(
        root, reopened, prepared.receipt.content_hash
    )

    assert committed.active_project == loaded.manifest.active_project
    assert reopened.manifest.active_registry == prepared.commit_request.next_registry
    assert validated == prepared.receipt
    assert (
        reopen_full_source_motion_analysis_receipt(
            root, prepared.receipt.motion_analysis_receipt_hash
        )
        == _motion_analysis(root, source_asset)
    )
    assert (
        reopen_full_source_motion_tail_receipt(root, prepared.tail_asset)
        == prepared.receipt
    )
    reopened_tail = next(
        item
        for item in reopened.registry.assets
        if item.asset_id == prepared.tail_asset.asset_id
    )
    assert reopened_tail.artifact_path == source_asset.artifact_path
    assert reopened_tail.sha256 == source_asset.sha256
    analysis_path = root / canonical_full_source_motion_analysis_receipt_path(
        prepared.receipt.motion_analysis_receipt_hash
    )
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    payload["spans"][0]["mean_ydif_millionths"] += 1
    analysis_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception, match="reopen"):
        validate_full_source_motion_tail(root, reopened, prepared.receipt.content_hash)


def test_full_source_tail_rejects_motion_analysis_for_another_source(
    tmp_path,
) -> None:
    root, committer, attempt_id, loaded = _accepted_source(tmp_path)
    source_attempt = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    )
    source_state = source_attempt.video_generation_state
    assert source_state is not None
    source_request = committer._reopen_video_request(source_state.request)
    source_asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == source_request.output_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")

    analysis = _motion_analysis(root, source_asset).model_copy(
        update={"source_video_sha256": "f" * 64}
    )
    with pytest.raises(Exception, match="analysis"):
        prepare_full_source_motion_tail_commit(
            project_root=root,
            committer=committer,
            project=loaded,
            attempt_id="full-source-motion-tail-invalid-v1",
            source_attempt_id=attempt_id,
            tail_asset_id="video-shot-rainy-station-3-motion-tail-invalid-v1",
            target_shot_id=target.shot_id,
            target_shot_revision=target.revision,
            target_shot_content_hash=target.content_hash,
            continuity_constraint_snapshot_hash="c" * 64,
            provider_min_duration_milliseconds=1_000,
            provider_max_duration_milliseconds=10_000,
            motion_analysis=analysis,
        )


def test_full_source_tail_rejects_hash_valid_fake_stats_and_arguments(tmp_path) -> None:
    root, committer, attempt_id, loaded = _accepted_source(tmp_path)
    source_state = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    ).video_generation_state
    assert source_state is not None
    source_request = committer._reopen_video_request(source_state.request)
    source_asset = next(
        item for item in loaded.registry.assets
        if item.asset_id == source_request.output_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")
    analysis = _motion_analysis(root, source_asset)
    values = analysis.model_dump(mode="python", exclude={"content_hash"})
    forged_span = analysis.spans[0].model_copy(
        update={"mean_ydif_millionths": analysis.spans[0].mean_ydif_millionths + 1}
    )
    forged = FullSourceMotionAnalysisReceipt.create(
        **{**values, "spans": (forged_span, analysis.spans[1])}
    )
    kwargs = dict(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="full-source-motion-tail-forged-v1",
        source_attempt_id=attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-forged-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=1_000,
        provider_max_duration_milliseconds=10_000,
    )
    with pytest.raises(Exception, match="fixed analyzer output"):
        prepare_full_source_motion_tail_commit(
            **kwargs,
            motion_analysis=forged,
        )
    with pytest.raises(ValueError, match="fixed contract"):
        FullSourceMotionAnalysisReceipt.create(
            **{**values, "canonical_arguments": ("caller-selected",)}
        )


def test_full_source_tail_exact_replay_reopens_without_a_commit(tmp_path) -> None:
    root, committer, attempt_id, loaded = _accepted_source(tmp_path)
    source_state = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    ).video_generation_state
    assert source_state is not None
    source_request = committer._reopen_video_request(source_state.request)
    source_asset = next(
        item for item in loaded.registry.assets
        if item.asset_id == source_request.output_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")
    values = dict(
        project_root=root,
        committer=committer,
        attempt_id="full-source-motion-tail-replay-v1",
        source_attempt_id=attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-replay-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=1_000,
        provider_max_duration_milliseconds=10_000,
        motion_analysis=_motion_analysis(root, source_asset),
    )
    prepared = prepare_full_source_motion_tail_commit(project=loaded, **values)
    assert prepared.commit_request is not None
    committer.commit(prepared.commit_request)
    revision = committer._read_manifest().manifest_revision

    replayed = prepare_full_source_motion_tail_commit(
        project=load_production_project(root / "project.yaml"), **values
    )

    assert replayed.replayed is True
    assert replayed.commit_request is None
    assert replayed.receipt == prepared.receipt
    assert committer._read_manifest().manifest_revision == revision
