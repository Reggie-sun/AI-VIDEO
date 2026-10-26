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



def _two_captured_dialogue_previews():
    from copy import deepcopy
    p, spec, timeline, shots = _resolved_preview_fixture()
    q, second, latter, more_shots = deepcopy(_resolved_preview_fixture())
    for asset in q.registry.assets:
        asset.asset_id += '-2'
    q.registry.assets[0].sha256 = 'e' * 64
    audio = q.registry.assets[1]
    audio.input_artifact_ids = ('captured-video-2',)
    audio.input_fingerprint = 'e' * 64
    audio.audio_metadata.source.input_artifact_ids = ('captured-video-2',)
    audio.audio_metadata.source.input_fingerprint = 'e' * 64
    second.layers[0].layer_id += '-2'
    second.layers[0].asset_id += '-2'
    second.layers[0].shot_id = 'shot-s02'
    second.audio_tracks[0].track_id += '-2'
    second.audio_tracks[0].asset_id += '-2'
    second.audio_tracks[0].shot_id = 'shot-s02'
    spec.caption_tracks[0].shot_id = 'shot-s01'
    second.caption_tracks[0].shot_id = 'shot-s02'
    second.caption_tracks[0].source_audio_track_id += '-2'
    latter.visual_spans[0].layer_id += '-2'
    latter.visual_spans[0].start_sample = 768_000
    latter.audio_spans[0].track_id += '-2'
    latter.audio_spans[0].start_sample = 768_000
    p.registry.assets += q.registry.assets
    spec.shot_ids += ('shot-s02',)
    spec.layers += second.layers
    spec.audio_tracks += second.audio_tracks
    spec.caption_tracks += second.caption_tracks
    timeline.visual_spans += latter.visual_spans
    timeline.audio_spans += latter.audio_spans
    timeline.total_samples *= 2
    shots['shot-s02'] = SimpleNamespace(shot_id='shot-s02')
    return p, spec, timeline, shots


@pytest.mark.parametrize('failure', [None, 'second_source', 'short_second_audio', 'crossed_caption', 'duplicate_shot', 'gap', 'silent_second', 'silent_second_bad_source', 'silent_second_desync', 'silent_second_trimmed'])
def test_cumulative_preview_validates_every_shots_exact_source(monkeypatch, failure):
    import ai_video.production.repair_input_admission as admission
    monkeypatch.setattr(admission, 'allows_repair_preview_layer', lambda *_: True)
    monkeypatch.setattr(admission, 'verify_repair_input', lambda *_: SimpleNamespace(
        preview_use=SimpleNamespace(scope='replacement_audio_preview')))
    p, spec, timeline, shots = _two_captured_dialogue_previews()
    if failure in {'silent_second', 'silent_second_bad_source', 'silent_second_desync', 'silent_second_trimmed'}:
        # A selected interval with no speech needs no subtitle binding, while its
        # original source audio must still receive the same identity/window checks.
        spec.caption_tracks = spec.caption_tracks[:1]
    if failure == 'silent_second_bad_source':
        p.registry.assets[-1].audio_metadata.source.input_fingerprint = 'f' * 64
    elif failure == 'silent_second_desync':
        timeline.audio_spans[-1].source_start_sample = 1
    elif failure == 'silent_second_trimmed':
        spec.layers[-1].trim_start_frame = 80
        spec.layers[-1].trim_duration_frames = 112
        spec.audio_tracks[-1].trim_start_sample = 160_000
        spec.audio_tracks[-1].trim_duration_samples = 224_000
        timeline.visual_spans[-1].duration_frames = 112
        timeline.visual_spans[-1].duration_samples = 224_000
        timeline.audio_spans[-1].source_start_sample = 160_000
        timeline.audio_spans[-1].source_duration_samples = 224_000
        timeline.audio_spans[-1].duration_samples = 224_000
        timeline.total_samples = 992_000
    if failure == 'second_source':
        p.registry.assets[-1].input_fingerprint = 'f' * 64
        p.registry.assets[-1].audio_metadata.source.input_fingerprint = 'f' * 64
    elif failure == 'short_second_audio':
        timeline.audio_spans[-1].duration_samples -= 1
    elif failure == 'crossed_caption':
        spec.caption_tracks[-1].source_audio_track_id = spec.audio_tracks[0].track_id
    elif failure == 'duplicate_shot':
        spec.audio_tracks[-1].shot_id = 'shot-s01'
    elif failure == 'gap':
        timeline.visual_spans[-1].start_sample += 1
        timeline.audio_spans[-1].start_sample += 1
    def check():
        _validate_captured_dialogue_preview(p, spec, timeline, shots,
            dialogue_tracks=spec.audio_tracks, invalid=lambda message, *_: ValueError(message))
    if failure is None or failure in {'silent_second', 'silent_second_trimmed'}:
        check()
    else:
        with pytest.raises(ValueError):
            check()


@pytest.mark.parametrize('failure', [None, 'missing_original', 'changed_source', 'gain_original', 'crossed_caption', 'title_video', 'title_speech', 'extra_speech'])
def test_captured_dialogue_preview_can_add_silent_image_title_and_score(monkeypatch, failure):
    import ai_video.production.repair_input_admission as admission
    from ai_video.production.models import VisualStrategy
    monkeypatch.setattr(admission, 'allows_repair_preview_layer', lambda *_: True)
    monkeypatch.setattr(admission, 'verify_repair_input', lambda *_: SimpleNamespace(
        preview_use=SimpleNamespace(scope='replacement_audio_preview')))
    p, spec, timeline, shots = _two_captured_dialogue_previews()
    title = SimpleNamespace(asset_id='title-image', asset_type=AssetType.IMAGE)
    p.registry.assets += (title,)
    shots['title'] = SimpleNamespace(shot_id='title', visual_strategy=VisualStrategy.STATIC_IMAGE,
                                    dialogue='', narration='')
    spec.shot_ids += ('title',)
    spec.layers += (CompositionLayerSpec(layer_id='title-layer', shot_id='title',
        asset_role='primary_visual', asset_id='title-image'),)
    music = AudioTrackSpec(track_id='score', asset_id='original-score', audio_kind=AudioKind.BGM,
                           start_sample=timeline.total_samples, trim_duration_samples=96_000)
    original = spec.audio_tracks
    spec.audio_tracks += (music,)
    timeline.visual_spans += (SimpleNamespace(layer_id='title-layer', start_sample=timeline.total_samples,
                                              duration_samples=96_000),)
    timeline.total_samples += 96_000
    if failure == 'missing_original':
        spec.audio_tracks = (original[0], music)
    elif failure == 'changed_source':
        p.registry.assets[3].audio_metadata.source.input_fingerprint = 'f' * 64
    elif failure == 'gain_original':
        original[0].gain_millidb = -1
    elif failure == 'crossed_caption':
        spec.caption_tracks[-1].source_audio_track_id = original[0].track_id
    elif failure == 'title_video':
        title.asset_type = AssetType.VIDEO
    elif failure == 'title_speech':
        shots['title'].dialogue = 'An unverified new speaker'
    elif failure == 'extra_speech':
        spec.audio_tracks += (AudioTrackSpec(track_id='added-voice', asset_id='added-voice',
            audio_kind=AudioKind.NARRATION, shot_id='title'),)
    dialogue = tuple(t for t in spec.audio_tracks if t.audio_kind is AudioKind.DIALOGUE)
    def check():
        _validate_captured_dialogue_preview(p, spec, timeline, shots,
            dialogue_tracks=dialogue, invalid=lambda message, *_: ValueError(message))
    if failure is None:
        check()
    else:
        with pytest.raises(ValueError):
            check()
