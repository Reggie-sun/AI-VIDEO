import pytest

from ai_video.errors import AiVideoError
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import VisualStrategy
from ai_video.production.visual_media import resolved_video_trim_duration, VisualMediaValidationError
from production_project_factory import make_loaded_project_and_spec
from test_production_composition import _with_video_layer


def test_vfr_development_preview_uses_output_clock_without_changing_metadata(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec, trim_start_frame=0,
        trim_duration_frames=288, metadata_changes=dict(fps_numerator=17340,
            fps_denominator=721, frame_count=289, duration_milliseconds=12017))
    asset, layer = loaded.registry.assets[0], spec.layers[0]
    kwargs = dict(duration_frames=288, delivery_profile=spec.delivery_profile)
    with pytest.raises(VisualMediaValidationError, match="frame rate does not match"):
        resolved_video_trim_duration(asset, layer, **kwargs)
    assert resolved_video_trim_duration(asset, layer, normal_speed_preview=True, **kwargs) == 288
    assert asset.video_metadata.fps_numerator == 17340
    with pytest.raises(VisualMediaValidationError, match="preview clock interval"):
        resolved_video_trim_duration(asset, layer.model_copy(update={"trim_start_frame": 24}),
            normal_speed_preview=True, **kwargs)


def test_static_product_image_can_be_the_complete_ad_visual(tmp_path):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded = loaded.model_copy(update={"shots": (
        loaded.shots[0].model_copy(update={"visual_strategy": VisualStrategy.STATIC_IMAGE}),
        *loaded.shots[1:])})
    spec = seal_artifact(spec.model_copy(update={"schema_version": "2.2",
        "graphic_layer_ids": (spec.layers[0].layer_id,),
        "ad_creative_plan_id": "fixture-primary-product-photo", "ad_creative_plan_hash": "1" * 64}))
    timeline = resolve_composition(loaded, spec, renderer_version="0.7.103")
    assert timeline.visual_spans[0].asset_id == spec.layers[0].asset_id
    # Declaring a video Shot still requires an actual primary video source.
    video = loaded.model_copy(update={"shots": (
        loaded.shots[0].model_copy(update={"visual_strategy": VisualStrategy.GENERATED_VIDEO}),
        *loaded.shots[1:])})
    with pytest.raises(AiVideoError, match="requires a primary visual layer"):
        resolve_composition(video, spec, renderer_version="0.7.103")
