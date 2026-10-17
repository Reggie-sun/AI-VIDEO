"""Public authoring of native A/V retime; media quality is a separate proof."""
import pytest

from ai_video.canvas_composition import compose_canvas
from ai_video.production.video_retime import VideoTimeMap, VideoTimePoint
from production_project_factory import make_loaded_project_and_spec
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
