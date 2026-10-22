from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    CompositionSpec,
)
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetSourceKind,
    AudioSource,
    ToolIdentity,
)
from production_project_factory import make_loaded_project_and_spec
from production_project_factory import _make_audio_asset
from test_native_audio_retime_contracts import attach_exact_audio_probe
from test_production_composition import _with_video_layer


def _reseal_spec(spec, *, layers=None, schema_version=None, audio_tracks=None):
    candidate = spec.model_copy(
        update={
            "content_hash": "0" * 64,
            "layers": tuple(layers) if layers is not None else spec.layers,
            "schema_version": schema_version or spec.schema_version,
            "audio_tracks": tuple(audio_tracks) if audio_tracks is not None else spec.audio_tracks,
        }
    )
    return CompositionSpec.model_validate(seal_artifact(candidate).model_dump(mode="python"))


def _with_policy(spec, policy, reason=None):
    layer = spec.layers[0].model_copy(
        update={"source_audio_policy": policy, "source_audio_reason": reason}
    )
    return _reseal_spec(spec, layers=(layer, *spec.layers[1:]))


def _with_p4_audio(
    root,
    loaded,
    spec,
    video,
    *,
    asset_id="source-audio",
    source_kind=AssetSourceKind.GENERATED,
    source_ids=(),
    source_fingerprint=None,
    creation_receipt_id="generated-video-audio-fixture",
    trim_start_sample=24_000,
    trim_duration_samples=96_000,
    sample_rate_hz=48_000,
    track_shot_id="shot-1",
    track_start_sample=None,
):
    audio, path = _make_audio_asset(
        root,
        asset_id=asset_id,
        audio_kind=AudioKind.BGM,
        duration_samples=144_000,
        sample_rate_hz=sample_rate_hz,
    )
    input_ids = tuple(source_ids if source_ids is not None else (video.asset_id,))
    input_fingerprint = source_fingerprint or video.sha256
    source = AudioSource(
        kind=source_kind,
        provider_or_tool=ToolIdentity(name="fixture", version="1"),
        input_artifact_ids=input_ids,
        input_fingerprint=input_fingerprint,
    )
    metadata = audio.audio_metadata.model_copy(
        update={"source": source}
    )
    audio = audio.model_copy(
        update={
            "source_kind": source_kind,
            "input_artifact_ids": input_ids,
            "input_fingerprint": input_fingerprint,
            "creation_receipt_id": creation_receipt_id,
            "audio_metadata": metadata,
        }
    )
    loaded = loaded.model_copy(
        update={
            "registry": loaded.registry.model_copy(
                update={
                    "schema_version": "2.2",
                    "assets": (*loaded.registry.assets, audio),
                }
            ),
            "asset_paths": {**loaded.asset_paths, audio.asset_id: path},
        }
    )
    track = AudioTrackSpec(
        track_id=f"track-{asset_id}",
        audio_kind=AudioKind.BGM,
        asset_id=asset_id,
        shot_id=track_shot_id,
        start_sample=track_start_sample,
        trim_start_sample=trim_start_sample,
        trim_duration_samples=trim_duration_samples,
    )
    spec = _reseal_spec(spec, schema_version="2.1", audio_tracks=(track,))
    return loaded, spec


def test_known_source_audio_cannot_be_dropped_from_composition(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    layer = spec.layers[0]
    loaded = attach_exact_audio_probe(loaded, asset_id=layer.asset_id)

    with pytest.raises(AiVideoError) as caught:
        resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert caught.value.code is ErrorCode.AUDIO_TIMELINE_INVALID


def test_known_silent_source_does_not_require_an_audio_span(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    loaded = attach_exact_audio_probe(
        loaded, asset_id=spec.layers[0].asset_id, audio_stream_count=0
    )

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.audio_spans == ()


def test_explicit_mute_with_reason_allows_known_source_audio_to_be_dropped(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    loaded = attach_exact_audio_probe(loaded, asset_id=spec.layers[0].asset_id)
    spec = _with_policy(spec, "MUTE", "The original room audio is intentionally removed.")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.audio_spans == ()


def test_explicit_keep_unknown_source_requires_exact_linked_audio(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    spec = _with_policy(spec, "KEEP")

    with pytest.raises(AiVideoError, match="no exact source-audio evidence"):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_explicit_keep_accepts_canonical_generated_audio_without_source_probe(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(tmp_path, loaded, spec, video)
    spec = _with_policy(spec, "KEEP")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert len(timeline.audio_spans) == 1
    assert timeline.audio_spans[0].asset_id == "source-audio"


def test_arbitrary_bgm_does_not_count_as_kept_source_audio(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded = attach_exact_audio_probe(loaded, asset_id=video.asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path,
        loaded,
        spec,
        video,
        source_kind=AssetSourceKind.IMPORTED,
        source_ids=(),
        source_fingerprint="f" * 64,
        creation_receipt_id="ordinary-imported-bgm",
    )

    with pytest.raises(
        AiVideoError,
        match="no exact (source-audio evidence|native or same-source P4 span)",
    ):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_same_source_p4_audio_requires_correct_trim(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path, loaded, spec, video, trim_start_sample=0
    )
    loaded = attach_exact_audio_probe(loaded, asset_id=video.asset_id)

    with pytest.raises(AiVideoError, match="no exact native or same-source P4 span"):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_same_source_global_audio_can_cover_video_when_source_offsets_align(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, trim_start_frame=0
    )
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path,
        loaded,
        spec,
        video,
        trim_start_sample=0,
        trim_duration_samples=144_000,
        track_shot_id=None,
        track_start_sample=0,
    )
    spec = _with_policy(spec, "KEEP")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert timeline.audio_spans[0].start_sample <= timeline.visual_spans[0].start_sample
    assert (
        timeline.audio_spans[0].start_sample + timeline.audio_spans[0].duration_samples
        >= timeline.visual_spans[0].start_sample + timeline.visual_spans[0].duration_samples
    )


def test_same_source_global_audio_with_offset_trim_does_not_count_as_kept_audio(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(
        tmp_path, loaded, spec, trim_start_frame=0
    )
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path,
        loaded,
        spec,
        video,
        trim_start_sample=1_000,
        trim_duration_samples=143_000,
        track_shot_id=None,
        track_start_sample=0,
    )
    spec = _with_policy(spec, "KEEP")

    with pytest.raises(
        AiVideoError,
        match="no exact (source-audio evidence|native or same-source P4 span)",
    ):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_replace_requires_full_coverage(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path,
        loaded,
        spec,
        video,
        source_kind=AssetSourceKind.IMPORTED,
        source_ids=(),
        source_fingerprint="f" * 64,
        creation_receipt_id="replacement-music",
        trim_start_sample=0,
        trim_duration_samples=48_000,
    )
    spec = _with_policy(spec, "REPLACE", "The cut uses licensed replacement music.")

    with pytest.raises(AiVideoError, match="replacement audio span covering"):
        resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_replace_accepts_registered_audio_covering_full_visual_interval(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    video = next(item for item in loaded.registry.assets if item.asset_id == spec.layers[0].asset_id)
    loaded, spec = _with_p4_audio(
        tmp_path,
        loaded,
        spec,
        video,
        source_kind=AssetSourceKind.IMPORTED,
        source_ids=(),
        source_fingerprint="f" * 64,
        creation_receipt_id="replacement-music",
        trim_start_sample=0,
        trim_duration_samples=96_000,
    )
    spec = _with_policy(spec, "REPLACE", "The cut uses licensed replacement music.")

    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")

    assert len(timeline.audio_spans) == 1
    assert timeline.audio_spans[0].asset_id == "source-audio"


def test_absent_source_audio_policy_keeps_legacy_composition_hash(tmp_path):
    _loaded, spec = make_loaded_project_and_spec(tmp_path)

    assert "source_audio_policy" not in spec.model_dump(mode="json")["layers"][0]
    assert "source_audio_reason" not in spec.model_dump(mode="json")["layers"][0]
    assert spec.content_hash == "05cdde712778ca78f4574dfe3c560da748b041786bd91903031452083cc7acc4"


@pytest.mark.parametrize("policy", ["MUTE", "REPLACE"])
def test_model_copy_cannot_bypass_reason_for_dropping_source_audio(tmp_path, policy):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    loaded = attach_exact_audio_probe(loaded, asset_id=spec.layers[0].asset_id)
    unvalidated = spec.model_copy(update={"layers": (
        spec.layers[0].model_copy(update={"source_audio_policy": policy}),
        *spec.layers[1:],
    )})
    with pytest.raises(AiVideoError) as error:
        resolve_composition(loaded, unvalidated, "0.7.103")
    assert error.value.code is ErrorCode.COMPOSITION_INVALID


def test_multiple_native_streams_require_an_explicit_audio_decision(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    loaded = attach_exact_audio_probe(loaded, asset_id=spec.layers[0].asset_id,
                                      audio_stream_count=2)
    with pytest.raises(AiVideoError, match="multiple native audio streams"):
        resolve_composition(loaded, spec, "0.7.103")
