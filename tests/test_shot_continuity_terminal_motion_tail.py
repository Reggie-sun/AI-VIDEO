from __future__ import annotations

import pytest

from ai_video.production.paths import (
    canonical_motion_tail_window_analysis_receipt_path,
    canonical_terminal_motion_tail_receipt_path,
    canonical_video_asset_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_motion_tail_runtime import (
    validate_motion_tail,
)
from ai_video.production.shot_continuity_terminal_motion_tail import (
    prepare_terminal_motion_tail_commit,
    reopen_terminal_motion_tail_receipt,
)


def _accepted_source(tmp_path):
    from test_shot_continuity_motion_tail import _accepted_source

    root, committer, attempt_id, loaded = _accepted_source(tmp_path)
    state = next(
        item for item in loaded.manifest.attempts if item.attempt_id == attempt_id
    ).video_generation_state
    assert state is not None
    request = committer._reopen_video_request(state.request)
    source_asset = next(
        item for item in loaded.registry.assets if item.asset_id == request.output_asset_id
    )
    return root, committer, attempt_id, loaded, source_asset


def test_terminal_motion_tail_materializes_shortest_exact_provider_window(
    tmp_path,
) -> None:
    root, committer, attempt_id, loaded, source_asset = _accepted_source(
        tmp_path
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")

    prepared = prepare_terminal_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="terminal-motion-tail-v1",
        source_attempt_id=attempt_id,
        tail_asset_id="video-shot-rainy-station-3-terminal-motion-tail-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=2_000,
        provider_max_duration_milliseconds=15_000,
    )

    receipt = prepared.receipt
    tail = prepared.tail_asset
    assert receipt.selection_rule_version == "terminal-window-frame-exact-v1"
    assert receipt.start_frame_index == 76
    assert receipt.end_frame_index == 123
    assert receipt.extracted_frame_count == 48
    assert receipt.extracted_duration_milliseconds == 2_000
    assert tail.sha256 != source_asset.sha256
    assert tail.artifact_path == canonical_video_asset_path(tail.sha256)
    assert tail.video_metadata is not None
    assert tail.video_metadata.frame_count == 48
    assert tail.video_metadata.duration_milliseconds == 2_000
    assert (
        tail.video_metadata.provenance_receipt_id
        == receipt.source_provenance_receipt_id
    )
    assert prepared.commit_request is not None
    media_artifact = next(
        item
        for item in prepared.commit_request.artifacts
        if item.relative_path == tail.artifact_path
    )
    assert media_artifact.file_sha256 == tail.sha256

    committer.commit(prepared.commit_request)
    reopened = load_production_project(root / "project.yaml")
    validated = validate_motion_tail(root, reopened, tail.asset_id)

    assert validated == receipt
    assert reopen_terminal_motion_tail_receipt(root, tail) == receipt
    c4 = validated.to_c4_motion_tail_evidence(
        registry_revision_id=reopened.registry.revision_id,
        tail_asset=tail,
    )
    assert c4.extracted_sha256 == tail.sha256
    assert c4.start_frame_index == 76
    assert c4.end_frame_index == 123

    revision = committer._read_manifest().manifest_revision
    replayed = prepare_terminal_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=reopened,
        attempt_id="terminal-motion-tail-v1",
        source_attempt_id=attempt_id,
        tail_asset_id=tail.asset_id,
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=2_000,
        provider_max_duration_milliseconds=15_000,
    )
    assert replayed.replayed is True
    assert replayed.commit_request is None
    assert committer._read_manifest().manifest_revision == revision

    analysis_path = root / canonical_motion_tail_window_analysis_receipt_path(
        receipt.motion_analysis_receipt_hash
    )
    analysis_bytes = analysis_path.read_bytes()
    analysis_path.write_bytes(analysis_bytes + b"\n")
    with pytest.raises(Exception, match="analysis"):
        validate_motion_tail(root, reopened, tail.asset_id)
    analysis_path.write_bytes(analysis_bytes)

    receipt_path = root / canonical_terminal_motion_tail_receipt_path(
        receipt.content_hash
    )
    receipt_bytes = receipt_path.read_bytes()
    receipt_path.write_bytes(receipt_bytes + b"\n")
    with pytest.raises(Exception, match="receipt"):
        validate_motion_tail(root, reopened, tail.asset_id)
    receipt_path.write_bytes(receipt_bytes)

    media_path = root / tail.artifact_path
    media_path.write_bytes(media_path.read_bytes() + b"tamper")
    with pytest.raises(Exception, match="bytes"):
        validate_motion_tail(root, reopened, tail)


def test_terminal_motion_tail_rejects_duration_that_cannot_fit_source(tmp_path) -> None:
    root, committer, attempt_id, loaded, _ = _accepted_source(tmp_path)
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")

    with pytest.raises(Exception, match="duration"):
        prepare_terminal_motion_tail_commit(
            project_root=root,
            committer=committer,
            project=loaded,
            attempt_id="terminal-motion-tail-too-long-v1",
            source_attempt_id=attempt_id,
            tail_asset_id="video-shot-rainy-station-3-terminal-motion-tail-too-long-v1",
            target_shot_id=target.shot_id,
            target_shot_revision=target.revision,
            target_shot_content_hash=target.content_hash,
            continuity_constraint_snapshot_hash="c" * 64,
            provider_min_duration_milliseconds=6_000,
            provider_max_duration_milliseconds=15_000,
        )
