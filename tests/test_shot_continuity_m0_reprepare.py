from __future__ import annotations

from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_reprepare import (
    RegisteredContinuityAnchor,
    reprepare_m0_qualification,
)
from ai_video.production.shot_continuity_terminal_motion_tail import (
    prepare_terminal_motion_tail_commit,
)
from ai_video.production.video_transition import ContinuityAnchorRole


def _unmaterialized_history(committer, root):
    receipt_root = root / "state/video-qualification/prepared-receipts"
    for path in sorted(receipt_root.glob("*.json")):
        content_hash = path.stem
        try:
            reopened = committer.reopen_p0_qualification_history(content_hash)
        except Exception:
            continue
        if all(
            stack.materialization_status == "unmaterialized"
            for stack in (*reopened[1], *reopened[5])
        ):
            return content_hash
    raise AssertionError("unmaterialized P0 history is missing")


def test_reprepare_binds_current_registry_and_exact_source_derivations(
    tmp_path,
) -> None:
    from test_shot_continuity_motion_tail import (
        _accepted_source,
    )

    root, committer, source_attempt_id, loaded = _accepted_source(tmp_path)
    source_attempt = next(
        item
        for item in loaded.manifest.attempts
        if item.attempt_id == source_attempt_id
    )
    source_state = source_attempt.video_generation_state
    assert source_state is not None
    terminal = committer._reopen_terminal_frame_evidence(
        source_state.terminal_frame_evidence
    )
    terminal_asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == terminal.extracted_asset_id
    )
    target = next(item for item in loaded.shots if item.shot_id == "rainy-station-4")
    prepared_tail = prepare_terminal_motion_tail_commit(
        project_root=root,
        committer=committer,
        project=loaded,
        attempt_id="full-source-motion-tail-reprepare-v1",
        source_attempt_id=source_attempt_id,
        tail_asset_id="video-shot-rainy-station-3-motion-tail-reprepare-v1",
        target_shot_id=target.shot_id,
        target_shot_revision=target.revision,
        target_shot_content_hash=target.content_hash,
        continuity_constraint_snapshot_hash="c" * 64,
        provider_min_duration_milliseconds=2_000,
        provider_max_duration_milliseconds=15_000,
    )
    assert prepared_tail.commit_request is not None
    committer.commit(prepared_tail.commit_request)
    after_tail = load_production_project(root / "project.yaml")
    historical_hash = _unmaterialized_history(committer, root)

    result = reprepare_m0_qualification(
        committer=committer,
        historical_receipt_hash=historical_hash,
        terminal_anchor=RegisteredContinuityAnchor(
            asset_id=terminal.extracted_asset_id,
            asset_sha256=terminal.extracted_sha256,
            evidence_fingerprint=terminal_asset.creation_receipt_id,
            materialization_receipt_id=terminal_asset.creation_receipt_id,
        ),
        motion_tail_anchor=RegisteredContinuityAnchor(
            asset_id=prepared_tail.tail_asset.asset_id,
            asset_sha256=prepared_tail.tail_asset.sha256,
            evidence_fingerprint=prepared_tail.receipt.content_hash,
            materialization_receipt_id=prepared_tail.receipt.content_hash,
        ),
        expected_manifest_revision=after_tail.manifest.manifest_revision,
        attempt_id="m0-reprepare-after-source-v1",
    )

    reopened = load_production_project(root / "project.yaml")
    assert result.receipt.project == reopened.manifest.active_project
    assert result.receipt.registry == reopened.manifest.active_registry
    assert reopened.manifest.active_p0_qualification_prepared is not None
    edge = next(
        item for item in result.policies if item.policy_id == "rainy-station-edge-3-4"
    )
    anchors = {item.role: item for item in edge.anchors}
    assert anchors[ContinuityAnchorRole.FIRST_FRAME].source_kind == "registered_asset"
    assert anchors[ContinuityAnchorRole.FIRST_FRAME].source_identity == (
        terminal.extracted_asset_id
    )
    assert anchors[ContinuityAnchorRole.REFERENCE_VIDEO].source_kind == (
        "registered_asset"
    )
    assert anchors[ContinuityAnchorRole.REFERENCE_VIDEO].source_identity == (
        prepared_tail.tail_asset.asset_id
    )
    revision = reopened.manifest.manifest_revision
    replayed = reprepare_m0_qualification(
        committer=committer,
        historical_receipt_hash=historical_hash,
        terminal_anchor=RegisteredContinuityAnchor(
            asset_id=terminal.extracted_asset_id,
            asset_sha256=terminal.extracted_sha256,
            evidence_fingerprint=terminal_asset.creation_receipt_id,
            materialization_receipt_id=terminal_asset.creation_receipt_id,
        ),
        motion_tail_anchor=RegisteredContinuityAnchor(
            asset_id=prepared_tail.tail_asset.asset_id,
            asset_sha256=prepared_tail.tail_asset.sha256,
            evidence_fingerprint=prepared_tail.receipt.content_hash,
            materialization_receipt_id=prepared_tail.receipt.content_hash,
        ),
        expected_manifest_revision=revision,
        attempt_id="m0-reprepare-after-source-v1",
    )
    assert replayed.receipt == result.receipt
    assert committer._read_manifest().manifest_revision == revision


def test_reprepare_rejects_unregistered_motion_tail_without_writing(tmp_path) -> None:
    from test_shot_continuity_motion_tail import _accepted_source

    root, committer, source_attempt_id, loaded = _accepted_source(tmp_path)
    source_attempt = next(
        item
        for item in loaded.manifest.attempts
        if item.attempt_id == source_attempt_id
    )
    source_state = source_attempt.video_generation_state
    assert source_state is not None
    terminal = committer._reopen_terminal_frame_evidence(
        source_state.terminal_frame_evidence
    )
    terminal_asset = next(
        item
        for item in loaded.registry.assets
        if item.asset_id == terminal.extracted_asset_id
    )
    historical_hash = _unmaterialized_history(committer, root)
    before = committer._read_manifest()

    try:
        reprepare_m0_qualification(
            committer=committer,
            historical_receipt_hash=historical_hash,
            terminal_anchor=RegisteredContinuityAnchor(
                asset_id=terminal.extracted_asset_id,
                asset_sha256=terminal.extracted_sha256,
                evidence_fingerprint=terminal_asset.creation_receipt_id,
                materialization_receipt_id=terminal_asset.creation_receipt_id,
            ),
            motion_tail_anchor=RegisteredContinuityAnchor(
                asset_id="missing-tail",
                asset_sha256="a" * 64,
                evidence_fingerprint="b" * 64,
                materialization_receipt_id="c" * 64,
            ),
            expected_manifest_revision=before.manifest_revision,
            attempt_id="m0-reprepare-invalid-v1",
        )
    except Exception as exc:
        assert "reference_video" in str(exc)
    else:
        raise AssertionError("unregistered motion tail was accepted")
    assert committer._read_manifest() == before
