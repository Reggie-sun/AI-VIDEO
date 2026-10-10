"""Canvas static-image composition reaches the canonical HyperFrames owner."""
import hashlib
from pathlib import Path

from ai_video.canvas_production import CanvasProductionService
from ai_video.production.composition_contracts import AudioTrackSpec
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    AudioKind,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    SourceReference,
    ToolIdentity,
    VisualStrategy,
    RenderReceipt,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, ProductionStateCommitter
from production_e2e_support import DeterministicHyperFramesRunner, require_audio_toolchain
from production_project_factory import _make_audio_asset, _p7_png
from test_canvas_authoring import direction, packet


def _image_asset(asset_id: str, payload: bytes, index: int) -> AssetRecord:
    digest = hashlib.sha256(payload).hexdigest()
    return AssetRecord(
        asset_id=asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=Path(f"assets/files/{asset_id}.png"),
        sha256=digest,
        size_bytes=len(payload),
        mime_type="image/png",
        width=2,
        height=1,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="canvas-render-fixture", version="1"),
        input_fingerprint=digest,
        creation_receipt_id=f"canvas-image-{index}",
        usage_license="fixture-only",
    )


def _policy() -> QaPolicy:
    return seal_artifact(
        QaPolicy(
            artifact_id="canvas-render-qa",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id="canvas-render-qa",
            source_provenance=(
                SourceReference(kind="derived", reference="canvas-render-test"),
            ),
            policy_id="canvas-render-qa",
            policy_version="1",
            required_layers=(QaLayer.TECHNICAL,),
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
        )
    )


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)
    return path.resolve(strict=True)


def test_static_canvas_bootstrap_composes_audio_and_delivers_canonical_render(
    tmp_path, monkeypatch
):
    fixture_root = tmp_path / "fixture-assets"
    (fixture_root / "assets/files").mkdir(parents=True)
    image_payloads = (
        _p7_png(rgba=b"\x11\x22\x33\xff"),
        _p7_png(rgba=b"\x44\x55\x66\xff"),
    )
    images = (
        _image_asset("adopted-image-one", image_payloads[0], 1),
        _image_asset("adopted-image-two", image_payloads[1], 2),
    )
    audio, audio_path = _make_audio_asset(
        fixture_root,
        asset_id="adopted-room-tone",
        audio_kind=AudioKind.AMBIENCE,
        duration_samples=192_000,
    )
    asset_records = tuple(sorted((*images, audio), key=lambda item: item.asset_id))
    registry = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=asset_records,
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    asset_payloads = {
        images[0].artifact_path: image_payloads[0],
        images[1].artifact_path: image_payloads[1],
        audio.artifact_path: audio_path.read_bytes(),
    }
    prepared_assets = tuple(
        PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())
        for path, payload in asset_payloads.items()
    )

    director = direction()
    director["delivery_profile"] = {"width": 1280, "height": 720, "fps": 24}
    selected_ids = tuple(item.asset_id for item in images)
    for index, row in enumerate(director["shots"]):
        shot = row["shot"]
        shot["visual_strategy"] = VisualStrategy.STATIC_IMAGE.value
        shot.pop("generated_video_rationale", None)
        shot["duration_policy"] = {"mode": "fixed", "seconds": 2}
        shot["required_asset_roles"] = [
            {
                "role": "primary_visual",
                "asset_ids": [selected_ids[index]],
                "allowed_asset_types": [AssetType.IMAGE.value],
            }
        ]
        row["composition"] = {
            "asset_role": "primary_visual",
            "asset_id": selected_ids[index],
        }

    project_root = tmp_path / "canvas-project"
    project_root.mkdir()
    committer = ProductionStateCommitter(project_root)
    service = CanvasProductionService(
        committer=committer,
        packet=packet(),
        direction=director,
        targets=(),
    )
    bundle = service.author(registry=registry, asset_artifacts=prepared_assets)
    service.approve_authoring(
        bundle=bundle,
        attempt_id="canvas-static-bootstrap",
        qa_policy=_policy(),
    )

    assert service.targets == ()
    assert service.position().next_action == "compose"
    audio_track = AudioTrackSpec(
        track_id="room-tone",
        audio_kind=AudioKind.AMBIENCE,
        asset_id=audio.asset_id,
        start_sample=48_000,
        trim_start_sample=24_000,
        trim_duration_samples=96_000,
    )
    spec, composed_timeline = service.compose(audio_tracks=(audio_track,))
    assert spec.shot_ids == ("one", "two")
    assert [span.asset_id for span in composed_timeline.visual_spans] == list(selected_ids)
    assert [span.start_frame for span in composed_timeline.visual_spans] == [0, 48]
    assert [span.trim_start_frame for span in composed_timeline.visual_spans] == [0, 0]
    assert [span.trim_duration_frames for span in composed_timeline.visual_spans] == [None, None]
    assert len(composed_timeline.audio_spans) == 1
    audio_span = composed_timeline.audio_spans[0]
    assert (audio_span.track_id, audio_span.asset_id) == ("room-tone", audio.asset_id)
    assert (audio_span.start_sample, audio_span.duration_samples) == (48_000, 96_000)
    assert (audio_span.source_start_sample, audio_span.source_duration_samples) == (
        24_000,
        96_000,
    )

    toolchain = require_audio_toolchain()
    runner = DeterministicHyperFramesRunner(toolchain.ffmpeg_path)
    import ai_video.production.hyperframes as hyperframes

    monkeypatch.setattr(
        hyperframes,
        "_NetworkIsolatedHyperFramesRunner",
        lambda **_kwargs: runner,
    )
    tools = tmp_path / "renderer-tools"
    renderer_toolchain = {
        "binary_path": tools / "node_modules/.bin/hyperframes",
        "browser_path": _executable(tools / "chrome"),
        "unshare_path": _executable(tools / "unshare"),
        "ip_path": _executable(tools / "ip"),
        "bash_path": _executable(tools / "bash"),
        "ffmpeg_path": toolchain.ffmpeg_path,
        "ffprobe_path": toolchain.ffprobe_path,
    }
    result = service.render(
        attempt_id="canvas-static-render",
        toolchain=renderer_toolchain,
        audio_tracks=(audio_track,),
    )
    assert result.active_render_state is not None
    assert runner.render_calls == 1

    final_project, final_timeline = service.deliver()
    assert final_project.render_state is not None
    assert final_project.render_state.output.size_bytes > 0
    assert final_timeline == composed_timeline
    receipt = RenderReceipt.model_validate_json(
        (project_root / final_project.render_state.render_receipt.path).read_bytes()
    )
    assert receipt.measured.audio is not None
    assert receipt.measured.audio.stream_count == 1
    assert receipt.measured.audio.decoded_samples > 0
    assert receipt.decoded_audio_fingerprint is not None
    replayed = service.render(attempt_id="canvas-static-render", toolchain=renderer_toolchain,
                              audio_tracks=(audio_track,))
    assert replayed == result
    assert runner.render_calls == 1
