from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_video.production._composition_visual import (
    _validate_captured_dialogue_preview,
    resolve_preview_layer_ids,
)
from ai_video.production.artifact_contracts import SourceReference
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    CaptionStyleReference,
    CaptionTrackBinding,
    CompositionLayerSpec,
    CompositionSpec,
    DeliveryProfile,
    FixedTransform,
    ResolvedAudioSpan,
    ResolvedCaptionCue,
    ResolvedTimeline,
    ResolvedVisualSpan,
    RendererIdentity,
    RendererKind,
)
from ai_video.production.models import AssetSourceKind, AssetType


def _caption_dialogue_spec(*, source_time_map=None, caption_source="original-dialogue"):
    style_hash = "a" * 64
    layer = CompositionLayerSpec(
        layer_id="captured-video-layer",
        shot_id="shot-s01",
        asset_role="final_visual",
        asset_id="captured-video",
        trim_start_frame=0,
        trim_duration_frames=384,
        source_time_map=source_time_map,
        source_audio_policy="KEEP",
    )
    dialogue = AudioTrackSpec(
        track_id="original-dialogue",
        audio_kind=AudioKind.DIALOGUE,
        asset_id="original-dialogue-wav",
        shot_id="shot-s01",
        start_sample=0,
        trim_start_sample=0,
        trim_duration_samples=768_000,
    )
    caption = CaptionTrackBinding(
        binding_id="zh-captions",
        caption_asset_id="caption-track",
        source_audio_track_id=caption_source,
        shot_id="shot-s01",
        style_reference=CaptionStyleReference(
            artifact_id="caption-style",
            revision=1,
            content_hash=style_hash,
            path=Path(f"assets/styles/{style_hash}.json"),
        ),
    )
    return CompositionSpec(
        artifact_id="composition",
        revision=1,
        content_hash="b" * 64,
        creation_receipt_id="composition-receipt",
        source_provenance=(SourceReference(kind="derived", reference="fixture"),),
        schema_version="2.3",
        composition_id="s01-caption-preview",
        shot_ids=("shot-s01",),
        layers=(layer,),
        delivery_profile=DeliveryProfile(width=1920, height=1080, fps=24),
        audio_tracks=(dialogue,),
        caption_tracks=(caption,),
    )


def test_unmapped_captured_dialogue_composition_allows_captions():
    spec = _caption_dialogue_spec()
    assert spec.layers[0].source_time_map is None
    assert spec.caption_tracks[0].source_audio_track_id == spec.audio_tracks[0].track_id


def test_replacement_preview_allows_only_captions_bound_to_dialogue(monkeypatch, tmp_path):
    import ai_video.production.repair_input_admission as admission

    spec = _caption_dialogue_spec()
    video = SimpleNamespace(asset_id="captured-video")
    shot = SimpleNamespace(
        shot_id="shot-s01",
        required_asset_roles=(SimpleNamespace(role="final_visual", asset_ids=()),),
    )
    project = SimpleNamespace(
        root=tmp_path,
        registry=SimpleNamespace(assets=(video,)),
    )
    monkeypatch.setattr(admission, "verify_repair_input", lambda *_: SimpleNamespace(
        preview_use=SimpleNamespace(scope="replacement_audio_preview")
    ))
    monkeypatch.setattr(admission, "allows_repair_preview_layer", lambda *_: True)
    assert resolve_preview_layer_ids(
        project, spec, {shot.shot_id: shot}, invalid=lambda message, *_: ValueError(message)
    ) == {"captured-video-layer"}

    mismatched = _caption_dialogue_spec(caption_source="other-audio")
    with pytest.raises(ValueError, match="captions bound to it"):
        resolve_preview_layer_ids(
            project, mismatched, {shot.shot_id: shot},
            invalid=lambda message, *_: ValueError(message),
        )


def _resolved_preview_fixture(*, source_video_sha="d" * 64, audio_end=768_000):
    video = SimpleNamespace(
        asset_id="captured-video",
        asset_type=AssetType.VIDEO,
        sha256="d" * 64,
        video_metadata=SimpleNamespace(fps_numerator=24, fps_denominator=1),
    )
    audio_source = SimpleNamespace(
        kind=AssetSourceKind.DERIVED,
        input_artifact_ids=("captured-video",),
        input_fingerprint=source_video_sha,
    )
    audio = SimpleNamespace(
        asset_id="original-dialogue-wav",
        asset_type=AssetType.VOICE,
        source_kind=AssetSourceKind.DERIVED,
        input_artifact_ids=("captured-video",),
        input_fingerprint=source_video_sha,
        audio_metadata=SimpleNamespace(audio_kind=AudioKind.DIALOGUE, source=audio_source),
    )
    layer = SimpleNamespace(
        layer_id="captured-video-layer",
        shot_id="shot-s01",
        asset_id=video.asset_id,
        trim_start_frame=0,
        trim_duration_frames=384,
        source_time_map=None,
        source_audio_policy="KEEP",
    )
    track = SimpleNamespace(
        track_id="original-dialogue",
        audio_kind=AudioKind.DIALOGUE,
        shot_id="shot-s01",
        asset_id=audio.asset_id,
        trim_start_sample=0,
        trim_duration_samples=768_000,
        gain_millidb=0,
        fade_in_samples=0,
        fade_out_samples=0,
        ducking=None,
    )
    visual_span = SimpleNamespace(
        layer_id=layer.layer_id,
        start_sample=0,
        duration_samples=768_000,
        duration_frames=384,
    )
    audio_span = SimpleNamespace(
        track_id=track.track_id,
        start_sample=0,
        duration_samples=audio_end,
        source_start_sample=0,
        source_duration_samples=768_000,
        gain_millidb=0,
        fade_in_samples=0,
        fade_out_samples=0,
        ducking=None,
    )
    project = SimpleNamespace(
        root=Path("."),
        registry=SimpleNamespace(assets=(video, audio)),
    )
    spec = SimpleNamespace(
        schema_version="2.3",
        shot_ids=("shot-s01",),
        layers=(layer,),
        audio_tracks=(track,),
        caption_tracks=(SimpleNamespace(source_audio_track_id=track.track_id),),
        sample_rate=48_000,
    )
    timeline = SimpleNamespace(
        usage_scope="development_audio_preview",
        visual_spans=(visual_span,),
        audio_spans=(audio_span,),
        total_samples=768_000,
        delivery_profile=SimpleNamespace(fps=24),
    )
    return project, spec, timeline, {"shot-s01": SimpleNamespace(shot_id="shot-s01")}


def test_captured_dialogue_must_match_video_provenance_and_full_visual_window(monkeypatch):
    import ai_video.production.repair_input_admission as admission

    monkeypatch.setattr(admission, "allows_repair_preview_layer", lambda *_: True)
    monkeypatch.setattr(
        admission,
        "verify_repair_input",
        lambda *_: SimpleNamespace(
            preview_use=SimpleNamespace(scope="replacement_audio_preview")
        ),
    )

    project, spec, timeline, shots = _resolved_preview_fixture()
    _validate_captured_dialogue_preview(
        project, spec, timeline, shots,
        dialogue_tracks=spec.audio_tracks,
        invalid=lambda message, *_: ValueError(message),
    )

    project, spec, timeline, shots = _resolved_preview_fixture(source_video_sha="e" * 64)
    with pytest.raises(ValueError, match="exact captured video bytes"):
        _validate_captured_dialogue_preview(
            project, spec, timeline, shots,
            dialogue_tracks=spec.audio_tracks,
            invalid=lambda message, *_: ValueError(message),
        )

    project, spec, timeline, shots = _resolved_preview_fixture(audio_end=767_999)
    with pytest.raises(ValueError, match="exact unmodified visual source interval"):
        _validate_captured_dialogue_preview(
            project, spec, timeline, shots,
            dialogue_tracks=spec.audio_tracks,
            invalid=lambda message, *_: ValueError(message),
        )


def test_resolved_development_audio_preview_can_carry_captions():
    visual = ResolvedVisualSpan(
        layer_id="visual",
        shot_id="shot-s01",
        asset_role="final_visual",
        asset_id="video",
        asset_sha256="d" * 64,
        asset_mime_type="video/mp4",
        materialized_path=Path("assets/video.mp4"),
        start_frame=0,
        duration_frames=24,
        start_sample=0,
        duration_samples=48_000,
        trim_start_frame=0,
        trim_duration_frames=24,
        transform=FixedTransform(),
        opacity_milli=1000,
        z_index=0,
    )
    audio = ResolvedAudioSpan(
        track_id="dialogue",
        audio_kind=AudioKind.DIALOGUE,
        asset_id="dialogue-wav",
        asset_sha256="e" * 64,
        start_sample=0,
        duration_samples=48_000,
        source_start_sample=0,
        source_duration_samples=48_000,
        gain_millidb=0,
        fade_in_samples=0,
        fade_out_samples=0,
    )
    caption = ResolvedCaptionCue(
        caption_asset_id="caption",
        caption_asset_sha256="f" * 64,
        caption_track_id="zh-track",
        caption_timing_fingerprint="a" * 64,
        segment_id="line-1",
        text="慢点，里面烫。",
        start_sample=2_000,
        end_sample=6_000,
        start_frame=1,
        end_frame_exclusive=3,
    )
    timeline = ResolvedTimeline(
        artifact_id="timeline",
        schema_version="2.3",
        revision=1,
        content_hash="b" * 64,
        creation_receipt_id="timeline-receipt",
        source_provenance=(SourceReference(kind="derived", reference="fixture"),),
        usage_scope="development_audio_preview",
        timeline_id="timeline-id",
        composition_spec_id="composition",
        composition_spec_revision=1,
        composition_spec_hash="c" * 64,
        delivery_profile=DeliveryProfile(width=1920, height=1080, fps=24),
        sample_rate=48_000,
        renderer=RendererIdentity(kind=RendererKind.HYPERFRAMES, version="0.7.103"),
        visual_spans=(visual,),
        audio_spans=(audio,),
        caption_cues=(caption,),
        total_frames=24,
        total_samples=48_000,
        composition_fingerprint="d" * 64,
    )
    assert timeline.caption_cues == (caption,)
    assert timeline.audio_spans[0].audio_kind is AudioKind.DIALOGUE

