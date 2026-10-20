"""Expression, containment, exact source audit and compatibility boundaries."""
from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.commercial_graphics import GraphicTreatment, GraphicRole, GraphicAnimation
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import materialize_hyperframes_source, audit_hyperframes_source
from ai_video.production.text_design import TextDesign, TextVisualNode, TextRun, MotionPose, TextAvoidanceRegion
from ai_video.production.text_fonts import EmbeddedFont
from production_project_factory import make_loaded_project_and_spec


@pytest.fixture
def embedded_font():
    pytest.importorskip("fontTools")
    from fontTools import subset
    from fontTools.ttLib import TTFont
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not path.exists():
        pytest.skip("real text tests require the licensed DejaVu Sans system test font")
    font = TTFont(path, recalcTimestamp=False)
    sub = subset.Subsetter()
    sub.populate(text="Hello world主次")
    sub.subset(font)
    stream = io.BytesIO()
    font.save(stream)
    data = stream.getvalue()
    return EmbeddedFont(family="DejaVu Sans", sha256=hashlib.sha256(data).hexdigest(),
                        data_base64=base64.b64encode(data).decode(), license="DejaVu Fonts license")


def design(font, **changes):
    data = dict(intent="Reveal information while leaving the subject visible", hierarchy="one primary statement",
                reference_width_px=600, reference_height_px=180, fonts=(font,),
                nodes=(TextVisualNode(node_id="headline", purpose="primary reading entry",
                                      x_px=10, y_px=20, width_px=560, height_px=90,
                                      runs=(TextRun(text="Hello", font_family=font.family, font_size_px=48),),
                                      motion=(MotionPose(frame=0, reveal_right_milli=1000),
                                              MotionPose(frame=10))),))
    data.update(changes)
    return TextDesign(**data)


def graphic(text_design=None):
    return GraphicTreatment(graphic_id="g", role=GraphicRole.HEADLINE, text="Hello", shot_id="shot-1",
                            start_frame_offset=1, duration_frames=35, x_milli=50, y_milli=100,
                            width_milli=500, font_size_px=48, text_color="#FFFFFF", z_index=10,
                            text_design=text_design)


def composed(tmp_path, font):
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    spec = seal_artifact(spec.model_copy(update={"schema_version":"2.2", "text_layers":(graphic(design(font)),)}))
    spec = type(spec).model_validate(spec.model_dump(mode="python"))
    return loaded, spec, resolve_composition(loaded, spec, renderer_version="0.7.103")


def test_design_reaches_canonical_timeline_and_changes_fingerprint(tmp_path, embedded_font):
    loaded, spec, timeline = composed(tmp_path, embedded_font)
    assert timeline.text_layers[0].text_design == spec.text_layers[0].text_design
    assert type(timeline).model_validate_json(timeline.model_dump_json()) == timeline
    assert type(spec).model_validate_json(spec.model_dump_json()) == spec
    legacy = seal_artifact(spec.model_copy(update={"text_layers":(graphic(),)}))
    assert resolve_composition(loaded, legacy, "0.7.103").composition_fingerprint != timeline.composition_fingerprint
    assert "text_design" not in graphic().model_dump(mode="json")


def test_copy_and_motion_cannot_silently_override_intent(embedded_font):
    d = design(embedded_font)
    with pytest.raises(ValueError, match="exact graphic copy"):
        GraphicTreatment.model_validate({**graphic(d).model_dump(), "text":"world"})
    with pytest.raises(ValueError, match="legacy motion"):
        GraphicTreatment.model_validate({**graphic(d).model_dump(), "entrance":GraphicAnimation.FADE})
    with pytest.raises(ValueError, match="exceeds graphic"):
        graphic(design(embedded_font, nodes=(d.nodes[0].model_copy(update={"motion":(MotionPose(frame=0),MotionPose(frame=40))}),)))


def test_declared_subject_avoidance_and_font_identity_fail_closed(embedded_font):
    d = design(embedded_font, avoidance_regions=(TextAvoidanceRegion(
        target_id="face", x_px=40,y_px=20,width_px=100,height_px=100,end_frame_offset=35),))
    with pytest.raises(ValueError, match="avoidance target face"):
        graphic(d)
    with pytest.raises(ValueError, match="SHA-256"):
        EmbeddedFont(**{**embedded_font.model_dump(), "sha256":"0"*64})
    with pytest.raises(ValueError, match="lacks required glyphs"):
        embedded_font.require_glyphs("\U00020000")


def test_exact_source_rejects_injected_or_changed_inline_font(tmp_path, embedded_font):
    loaded, _, timeline = composed(tmp_path / "project", embedded_font)
    materialized = materialize_hyperframes_source(
        timeline, asset_sources=loaded.asset_paths, allowed_asset_root=loaded.root,
        staging_root=tmp_path/"source", allowed_staging_parent=tmp_path)
    source = materialized.index_path.read_text()
    assert "<foreignObject" in source and "@font-face" in source and "clip-path:inset" in source
    audit_hyperframes_source(materialized.index_path, expected_assets=materialized.asset_bindings,
                             expected_timeline=timeline)
    materialized.index_path.write_text(source.replace(embedded_font.data_base64, base64.b64encode(b"changed").decode()))
    with pytest.raises(AiVideoError):
        audit_hyperframes_source(materialized.index_path, expected_assets=materialized.asset_bindings,
                                 expected_timeline=timeline)


def test_generic_text_preserves_caption_and_ad_authority(tmp_path, embedded_font):
    _, spec, timeline = composed(tmp_path, embedded_font)
    assert not spec.commercial_graphics and not timeline.commercial_graphics
    payload = spec.model_dump(mode="python")
    with pytest.raises(ValueError, match="AdCreativePlan"):
        type(spec).model_validate({**payload,"text_layers":(),"commercial_graphics":spec.text_layers})
    bad = graphic(design(embedded_font)).model_copy(update={"claim_reference_ids":("claim",)})
    with pytest.raises(ValueError, match="bypass"):
        type(spec).model_validate({**payload,"text_layers":(bad,)})
    with pytest.raises(ValueError, match="unique across"):
        type(spec).model_validate({**payload,"text_layers":(*spec.text_layers,*spec.text_layers)})


def test_text_layout_bounds_and_frame_projection(tmp_path, embedded_font):
    from ai_video.production._composition_text import resolve_caption_words
    from ai_video.production.models import CaptionSegment, CaptionWord
    loaded,spec,_ = composed(tmp_path,embedded_font)
    low = spec.text_layers[0].model_copy(update={"y_milli":990})
    bad = seal_artifact(spec.model_copy(update={"text_layers":(low,)}))
    with pytest.raises(AiVideoError, match="bottom safe area"):
        resolve_composition(loaded,bad,"0.7.103")
    segment = CaptionSegment(segment_id="one",text="Hello",start_sample=100,end_sample=10000,
        words=(CaptionWord(text="He",start_sample=100,end_sample=101),
               CaptionWord(text="llo",start_sample=2000,end_sample=10000)))
    words = resolve_caption_words(segment,audio_start=48000,source_start=0,sample_rate=48000,fps=24)
    assert (words[0].start_frame,words[0].end_frame_exclusive)==(25,25)
    assert (words[1].start_frame,words[1].end_frame_exclusive)==(25,29)


def test_public_resolver_revalidates_nested_typed_copies(tmp_path, embedded_font):
    loaded, spec, timeline = composed(tmp_path, embedded_font)
    original = spec.text_layers[0]
    node = original.text_design.nodes[0]
    run = node.runs[0].model_copy(update={"color":"red;position:fixed;inset:0"})
    forged = original.text_design.model_copy(update={"nodes":(node.model_copy(update={"runs":(run,)}),)})
    bad = seal_artifact(spec.model_copy(update={"text_layers":(original.model_copy(update={"text_design":forged}),)}))
    with pytest.raises(AiVideoError, match="resolved safely"):
        resolve_composition(loaded,bad,"0.7.103")
    bypass = seal_artifact(spec.model_copy(update={"text_layers":(original.model_copy(update={"claim_reference_ids":("claim",)}),)}))
    with pytest.raises(AiVideoError, match="resolved safely"):
        resolve_composition(loaded,bypass,"0.7.103")
    from ai_video.production.text_design_html import render_text_design
    with pytest.raises(ValueError):
        render_text_design(timeline.text_layers[0].model_copy(update={"text_design":forged}),
                           timeline=timeline,duration="1.500",boundary=lambda *a,**k:"0%")


def test_corrupt_font_tables_are_controlled_validation_errors():
    pytest.importorskip("fontTools")
    data = b"\x00\x01\x00\x00"
    with pytest.raises(ValueError, match="font tables are invalid"):
        EmbeddedFont(family="Broken",sha256=hashlib.sha256(data).hexdigest(),
                     data_base64=base64.b64encode(data).decode(),license="test")
