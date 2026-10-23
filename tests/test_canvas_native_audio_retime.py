"""Public authoring of native A/V retime; media quality is a separate proof."""
import hashlib
import math
import struct
import wave
from io import BytesIO

import pytest

from ai_video.canvas_composition import compose_canvas
from ai_video.production.composition_contracts import AudioKind, AudioTrackSpec, DuckingSpec
from ai_video.production.hyperframes import materialize_hyperframes_source
from ai_video.production.models import AssetSourceKind
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
from production_project_factory import _make_audio_asset, make_loaded_project_and_spec
from test_production_video_retime import _with_video_layer
from test_native_audio_retime_contracts import attach_exact_audio_probe


def _canvas(tmp_path, *, muted):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    loaded = attach_exact_audio_probe(loaded, asset_id=loaded.registry.assets[0].asset_id)
    mapping = VideoTimeMap(contract_version="video-time-map/2", audio_policy="retime_preserve_pitch",
        points=tuple(VideoTimePoint(source_frame=s, output_frame=o)
                     for s, o in ((0, 0), (24, 12), (60, 48))))
    rows = [{"occurrence_id": layer.shot_id, "shot": {"shot_id": layer.shot_id},
             "composition": {"asset_role": layer.asset_role, "asset_id": layer.asset_id}}
            for layer in spec.layers]
    rows[0]["composition"].update(trim_start_frame=12, trim_duration_frames=60,
        muted=muted, source_time_map=mapping.model_dump(mode="json"))
    return loaded, {"shots": rows}


def _ordinary_source_audio_mix(tmp_path, *, track_kind, native_count=1, muted=False):
    loaded, direction = _canvas(tmp_path, muted=muted)
    video_id = direction["shots"][0]["composition"]["asset_id"]
    video = next(asset for asset in loaded.registry.assets if asset.asset_id == video_id)
    settings = direction["shots"][0]["composition"]
    settings.pop("source_time_map")
    settings.update(trim_start_frame=0, trim_duration_frames=48)

    assets = list(loaded.registry.assets)
    paths = dict(loaded.asset_paths)
    native_ids = set()
    for index in range(native_count):
        audio, path = _make_audio_asset(
            tmp_path,
            asset_id=f"native-source-{index}",
            audio_kind=AudioKind.SFX,
            duration_samples=192_000,
        )
        source = audio.audio_metadata.source.model_copy(update={
            "kind": AssetSourceKind.GENERATED,
            "input_artifact_ids": (),
            "input_fingerprint": video.sha256,
        })
        audio = audio.model_copy(update={
            "source_kind": AssetSourceKind.GENERATED,
            "input_artifact_ids": (),
            "input_fingerprint": video.sha256,
            "creation_receipt_id": f"generated-video-audio-{'a' * 64}",
            "audio_metadata": audio.audio_metadata.model_copy(update={"source": source}),
        })
        assets.append(audio)
        paths[audio.asset_id] = path
        native_ids.add(audio.asset_id)

    voice, voice_path = _make_audio_asset(
        tmp_path,
        asset_id="authored-post-voice",
        audio_kind=track_kind,
        duration_samples=96_000,
    )
    assets.append(voice)
    paths[voice.asset_id] = voice_path
    shot_id = direction["shots"][0]["shot"]["shot_id"]
    track = AudioTrackSpec(
        track_id="authored-post-voice-track",
        shot_id=shot_id,
        audio_kind=track_kind,
        asset_id=voice.asset_id,
        trim_start_sample=0,
        trim_duration_samples=96_000,
    )
    loaded = loaded.model_copy(update={
        "registry": loaded.registry.model_copy(update={"assets": tuple(assets)}),
        "asset_paths": paths,
    })
    return loaded, direction, track, native_ids


def _script_native_audio_match(monkeypatch, native_ids):
    """Stub the existing owner lookup while leaving composition validation live."""
    monkeypatch.setattr(
        "ai_video.canvas_composition._native_audio_matches",
        lambda _loaded, audio, _video, _shot: audio.asset_id in native_ids,
    )


def _write_tone(asset, path, *, frequency_hz, amplitude=4_000):
    duration_samples = asset.audio_metadata.duration_samples
    sample_rate = asset.audio_metadata.sample_rate_hz
    samples = tuple(
        int(amplitude * math.sin(2 * math.pi * frequency_hz * index / sample_rate))
        for index in range(duration_samples)
    )
    buffer = BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    payload = buffer.getvalue()
    path.write_bytes(payload)
    return asset.model_copy(update={
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    })


def _tone_coefficient(stereo_samples, *, frequency_hz, start_sample, end_sample):
    rate = 48_000
    values = stereo_samples[start_sample:end_sample]
    return 2 * sum(
        left * math.sin(2 * math.pi * frequency_hz * sample / rate)
        for sample, (left, _right) in zip(
            range(start_sample, end_sample), values, strict=True
        )
    ) / len(values)


def test_canvas_preserves_native_audio_through_same_map_without_registering_another_wav(tmp_path, monkeypatch):
    loaded, direction = _canvas(tmp_path, muted=False)
    def forbid_ordinary_native_lookup(*_):
        raise AssertionError("Mapped native audio must use its VIDEO source, not another accepted WAV")
    monkeypatch.setattr("ai_video.canvas_composition._native_audio_matches", forbid_ordinary_native_lookup)
    spec, timeline = compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")
    assert spec.schema_version == timeline.schema_version == "2.4"
    span, = timeline.audio_spans
    layer = spec.layers[0]
    assert span.asset_id == layer.asset_id
    assert span.asset_sha256 == loaded.registry.assets[0].sha256
    assert span.native_audio_retime.visual_layer_id == layer.layer_id
    assert (span.source_start_sample, span.source_duration_samples, span.duration_samples) == (24000, 120000, 96000)


def test_canvas_rejects_mute_conflicting_with_explicit_native_audio_policy(tmp_path):
    loaded, direction = _canvas(tmp_path, muted=True)
    with pytest.raises(ValueError, match="muted|mute"):
        compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")


@pytest.mark.parametrize("field", ["dialogue", "narration"])
def test_canvas_keeps_authored_speech_in_the_complete_native_track(tmp_path, field):
    loaded, direction = _canvas(tmp_path, muted=False)
    shot = type(loaded.shots[0]).model_validate({
        **loaded.shots[0].model_dump(mode="python"), field: "Retain the authored source speech."
    })
    loaded = loaded.model_copy(update={"shots": (shot, *loaded.shots[1:])})

    _, timeline = compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")

    native, = timeline.audio_spans
    assert native.native_audio_retime.visual_layer_id == f"canvas-{shot.shot_id}"


def test_canvas_seals_keep_policy_in_the_composition_layer(tmp_path):
    loaded, direction = _canvas(tmp_path, muted=False)
    spec, _ = compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")
    assert spec.layers[0].source_audio_policy == "KEEP"


def test_canvas_seals_explicit_mute_instead_of_discarding_the_decision(tmp_path):
    loaded, direction = _canvas(tmp_path, muted=True)
    settings = direction["shots"][0]["composition"]
    settings.pop("source_time_map")
    settings["trim_duration_frames"] = 48
    spec, timeline = compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")
    assert spec.layers[0].source_audio_policy == "MUTE"
    assert spec.layers[0].source_audio_reason
    assert not timeline.audio_spans


def test_canvas_explicit_replace_does_not_allow_missing_replacement_audio(tmp_path):
    from ai_video.errors import AiVideoError, ErrorCode

    loaded, direction = _canvas(tmp_path, muted=False)
    settings = direction["shots"][0]["composition"]
    settings.pop("source_time_map")
    settings.update(trim_duration_frames=48, source_audio_policy="REPLACE",
                    source_audio_reason="Use the authored replacement soundtrack.")
    with pytest.raises(AiVideoError) as error:
        compose_canvas(loaded=loaded, direction=direction, renderer_version="0.7.103")
    assert error.value.code is ErrorCode.AUDIO_TIMELINE_INVALID


@pytest.mark.parametrize("track_kind", [AudioKind.NARRATION, AudioKind.BGM])
def test_canvas_composes_unique_native_source_audio_with_post_voice_and_music(
    tmp_path, monkeypatch, track_kind
):
    loaded, direction, voice_track, native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=track_kind
    )
    _script_native_audio_match(monkeypatch, native_ids)

    spec, timeline = compose_canvas(
        loaded=loaded,
        direction=direction,
        renderer_version="0.7.103",
        audio_tracks=(voice_track,),
    )

    native_track = next(track for track in spec.audio_tracks if track.asset_id in native_ids)
    assert voice_track in spec.audio_tracks
    assert {span.asset_id for span in timeline.audio_spans} == {
        voice_track.asset_id,
        native_track.asset_id,
    }


def test_canvas_does_not_duplicate_an_already_bound_native_track_with_post_voice(
    tmp_path, monkeypatch
):
    loaded, direction, voice_track, native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=AudioKind.NARRATION
    )
    _script_native_audio_match(monkeypatch, native_ids)
    native_id = next(iter(native_ids))
    bound_native_track = AudioTrackSpec(
        track_id="already-bound-native-audio",
        shot_id=voice_track.shot_id,
        audio_kind=AudioKind.SFX,
        asset_id=native_id,
        trim_start_sample=0,
        trim_duration_samples=96_000,
    )

    spec, timeline = compose_canvas(
        loaded=loaded,
        direction=direction,
        renderer_version="0.7.103",
        audio_tracks=(voice_track, bound_native_track),
    )

    assert spec.audio_tracks.count(bound_native_track) == 1
    assert {span.track_id for span in timeline.audio_spans} == {
        voice_track.track_id,
        bound_native_track.track_id,
    }


def test_canvas_keeps_post_voice_when_source_audio_is_explicitly_muted(tmp_path):
    loaded, direction, voice_track, _native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=AudioKind.NARRATION, muted=True
    )
    spec, timeline = compose_canvas(
        loaded=loaded,
        direction=direction,
        renderer_version="0.7.103",
        audio_tracks=(voice_track,),
    )

    assert spec.layers[0].source_audio_policy == "MUTE"
    assert voice_track in spec.audio_tracks
    assert [span.asset_id for span in timeline.audio_spans] == [voice_track.asset_id]


def test_canvas_rejects_post_voice_as_a_substitute_for_missing_native_source_audio(
    tmp_path, monkeypatch
):
    loaded, direction, voice_track, _native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=AudioKind.NARRATION, native_count=0
    )
    _script_native_audio_match(monkeypatch, set())

    with pytest.raises(ValueError, match="native video audio needs its exact registered WAV"):
        compose_canvas(
            loaded=loaded,
            direction=direction,
            renderer_version="0.7.103",
            audio_tracks=(voice_track,),
        )


def test_canvas_rejects_ambiguous_native_sources_even_with_post_voice(tmp_path, monkeypatch):
    loaded, direction, voice_track, native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=AudioKind.NARRATION, native_count=2
    )
    _script_native_audio_match(monkeypatch, native_ids)

    with pytest.raises(ValueError, match="native video audio needs its exact registered WAV"):
        compose_canvas(
            loaded=loaded,
            direction=direction,
            renderer_version="0.7.103",
            audio_tracks=(voice_track,),
        )


def test_canvas_materializes_native_audio_with_narration_and_ducked_music_pcm(
    tmp_path, monkeypatch
):
    loaded, direction, voice_track, native_ids = _ordinary_source_audio_mix(
        tmp_path, track_kind=AudioKind.NARRATION
    )
    _script_native_audio_match(monkeypatch, native_ids)
    voice_track = voice_track.model_copy(update={
        "gain_millidb": -6_000,
        "fade_in_samples": 4_800,
    })

    native_id = next(iter(native_ids))
    assets = {asset.asset_id: asset for asset in loaded.registry.assets}
    native_path = loaded.asset_paths[native_id]
    assets[native_id] = _write_tone(
        assets[native_id], native_path, frequency_hz=440
    )
    voice_path = loaded.asset_paths[voice_track.asset_id]
    assets[voice_track.asset_id] = _write_tone(
        assets[voice_track.asset_id], voice_path, frequency_hz=880
    )

    music, music_path = _make_audio_asset(
        tmp_path,
        asset_id="authored-ducked-music",
        audio_kind=AudioKind.BGM,
        duration_samples=96_000,
    )
    music = _write_tone(music, music_path, frequency_hz=220)
    assets[music.asset_id] = music
    paths = {**loaded.asset_paths, music.asset_id: music_path}
    loaded = loaded.model_copy(update={
        "registry": loaded.registry.model_copy(update={"assets": tuple(assets.values())}),
        "asset_paths": paths,
    })
    music_track = AudioTrackSpec(
        track_id="authored-ducked-music-track",
        shot_id=voice_track.shot_id,
        audio_kind=AudioKind.BGM,
        asset_id=music.asset_id,
        trim_start_sample=0,
        trim_duration_samples=96_000,
        ducking=DuckingSpec(
            sidechain_track_ids=(voice_track.track_id,),
            attenuation_millidb=-12_000,
            attack_samples=0,
            release_samples=0,
        ),
    )

    spec, timeline = compose_canvas(
        loaded=loaded,
        direction=direction,
        renderer_version="0.7.103",
        audio_tracks=(voice_track, music_track),
    )
    assert voice_track in spec.audio_tracks
    assert music_track in spec.audio_tracks
    assert {span.audio_kind for span in timeline.audio_spans} >= {
        AudioKind.SFX,
        AudioKind.NARRATION,
        AudioKind.BGM,
    }

    asset_ids = {span.asset_id for span in timeline.visual_spans}
    asset_ids.update(span.asset_id for span in timeline.audio_spans)
    materialized = materialize_hyperframes_source(
        timeline,
        asset_sources={asset_id: loaded.asset_paths[asset_id] for asset_id in asset_ids},
        allowed_asset_root=tmp_path,
        staging_root=tmp_path / "materialized-source",
        allowed_staging_parent=tmp_path,
    )

    (binding,) = materialized.audio_bindings
    mixed_path = materialized.root / binding.materialized_path
    with wave.open(str(mixed_path), "rb") as mixed:
        assert mixed.getnchannels() == 2
        assert mixed.getframerate() == 48_000
        frame_count = mixed.getnframes()
        pcm = struct.unpack(f"<{frame_count * 2}h", mixed.readframes(frame_count))
    stereo_samples = tuple(zip(pcm[0::2], pcm[1::2], strict=True))

    native_amplitude = _tone_coefficient(
        stereo_samples, frequency_hz=440, start_sample=12_000, end_sample=36_000
    )
    voice_steady_amplitude = _tone_coefficient(
        stereo_samples, frequency_hz=880, start_sample=12_000, end_sample=36_000
    )
    voice_fade_amplitude = _tone_coefficient(
        stereo_samples, frequency_hz=880, start_sample=1_200, end_sample=3_600
    )
    music_ducked_amplitude = _tone_coefficient(
        stereo_samples, frequency_hz=220, start_sample=12_000, end_sample=36_000
    )

    assert native_amplitude == pytest.approx(4_000, abs=8)
    assert voice_steady_amplitude == pytest.approx(2_000, rel=0.03)
    assert voice_fade_amplitude == pytest.approx(
        voice_steady_amplitude / 2, rel=0.08
    )
    assert music_ducked_amplitude == pytest.approx(1_000, rel=0.04)
