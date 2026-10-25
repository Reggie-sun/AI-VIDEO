import json

import pytest

from ai_video.production.hashing import seal_artifact
from ai_video.production.watermark_preset import (
    WatermarkPreset, build_watermark_font, build_watermark_layers,
)
from production_project_factory import make_loaded_project_and_spec


def _spec(tmp_path, single=False):
    _, spec = make_loaded_project_and_spec(tmp_path)
    changes = {"schema_version": "2.2"}
    if single:
        changes.update(shot_ids=(spec.shot_ids[0],), transitions=())
    return seal_artifact(spec.model_copy(update=changes))


def test_saved_preset_moves_top_left_to_bottom_center_to_top_right(tmp_path):
    spec = _spec(tmp_path, single=True)
    preset = WatermarkPreset(name="V字动态水印", text="乐喜呵护商贸")
    reopened = WatermarkPreset.model_validate_json(preset.model_dump_json())
    layer, = build_watermark_layers(spec, duration_frames_by_shot={spec.shot_ids[0]: 1129}, preset=reopened)
    node = layer.text_design.nodes[0]
    start, bottom, end = node.motion
    assert (start.frame, bottom.frame, end.frame) == (0, 564, 1128)
    assert start.translate_x_px < bottom.translate_x_px < end.translate_x_px
    assert start.translate_y_px == end.translate_y_px < bottom.translate_y_px
    assert bottom.translate_y_px > spec.delivery_profile.height * .8
    assert start.opacity_milli == bottom.opacity_milli == end.opacity_milli == 550
    assert layer.text == "乐喜呵护商贸"


def test_renaming_preset_and_text_rebuilds_font_and_copy(tmp_path):
    spec = _spec(tmp_path, single=True)
    data = json.loads(WatermarkPreset(name="原名", text="乐喜呵护商贸").model_dump_json())
    data.update(name="我的水印", text="另一家店")
    preset = WatermarkPreset.model_validate_json(json.dumps(data, ensure_ascii=False))
    layer, = build_watermark_layers(spec, duration_frames_by_shot={spec.shot_ids[0]: 300}, preset=preset)
    assert layer.text == "另一家店"
    assert layer.text_design.nodes[0].runs[0].text == "另一家店"
    assert "我的水印" in layer.text_design.intent
    layer.text_design.fonts[0].require_glyphs("另一家店")


def test_path_continues_across_shot_boundary_instead_of_restarting(tmp_path):
    spec = _spec(tmp_path)
    first, second = spec.shot_ids
    preset = WatermarkPreset(name="V", text="乐喜呵护商贸")
    layers = build_watermark_layers(spec, duration_frames_by_shot={first: 564, second: 565}, preset=preset)
    first_path, second_path = (x.text_design.nodes[0].motion for x in layers)
    assert second_path[0].translate_x_px > first_path[0].translate_x_px
    assert second_path[0].translate_y_px > spec.delivery_profile.height * .8
    assert abs(second_path[0].translate_y_px - first_path[-1].translate_y_px) <= 4
    assert second_path[-1].translate_y_px == first_path[0].translate_y_px


def test_invalid_or_off_canvas_presets_fail_without_clipping(tmp_path):
    with pytest.raises(ValueError, match="increase"):
        WatermarkPreset.model_validate_json(json.dumps({"name": "bad", "text": "test", "waypoints": [
            {"time_milli": 500, "center_x_milli": 120, "center_y_milli": 70},
            {"time_milli": 1000, "center_x_milli": 880, "center_y_milli": 70}]}))
    spec = _spec(tmp_path, single=True)
    with pytest.raises(ValueError, match="leaves the canvas"):
        build_watermark_layers(spec, duration_frames_by_shot={spec.shot_ids[0]: 300},
            preset=WatermarkPreset(name="too large", text="乐喜呵护商贸", font_size_px=256))
