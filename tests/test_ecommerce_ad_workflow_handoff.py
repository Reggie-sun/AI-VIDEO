from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

from ai_video.production import (
    EcommerceBeatRoleBinding,
    EcommerceDeliveryProfile,
    EcommerceGraphicRoleBinding,
    EcommerceLayoutPlan,
    EcommerceLayoutScene,
    EcommerceLayoutShot,
    EcommerceProductionCompileProfile,
    EcommerceRequirementResolution,
    EcommerceTypographyToken,
    EcommerceVisualSystemProfile,
)
from ai_video.production.ad_creative_types import (
    AdBeatRole,
    CapabilityClassification,
    ProductPresentation,
    ProductPresentationMode,
    ProductPresentationRole,
)
from ai_video.production.commercial_graphics import (
    GraphicKeywordEmphasis,
    GraphicRole,
    GraphicSafeAreaInsets,
    GraphicTreatment,
)
from ai_video.production.models import VisualStrategy


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents/skills/ecommerce-ad-workflow"
SCRIPT_DIR = SKILL_ROOT / "scripts"
EXPORTER_PATH = SCRIPT_DIR / "export_runtime_handoff.py"
HANDOFF_SCHEMA_PATH = SKILL_ROOT / "schemas/ecommerce-production-handoff.schema.json"
PACKAGE_PATH = SKILL_ROOT / "templates/30s-vertical-product-ad.package.example.json"
INPUT_PATH = SKILL_ROOT / "templates/30s-vertical-product-ad.input.example.json"


def _load_exporter():
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location(
            "ecommerce_runtime_handoff_exporter", EXPORTER_PATH
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPT_DIR))


def _reviewed_visual_contracts(package):
    delivery = EcommerceDeliveryProfile.create(
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=24,
        codec_profile="h264",
        audio_sample_rate_hz=48_000,
        platform="short-video",
        placement="vertical-feed",
        constraints=("Keep product, face, CTA, and subtitles unobstructed.",),
    )
    safe = GraphicSafeAreaInsets(
        top_milli=50,
        right_milli=50,
        bottom_milli=80,
        left_milli=50,
    )
    token = EcommerceTypographyToken(
        token_id="type-commercial",
        font_family="sans-serif",
        font_size_px=56,
        font_weight=700,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#111827CC",
    )
    roles = tuple(GraphicRole)
    visual = EcommerceVisualSystemProfile.create(
        brand_token_ids=tuple(
            item.brand_token_reference for item in package.copy_graphics_plan
        ),
        safe_area=safe,
        typography_tokens=(token,),
        role_bindings=tuple(
            EcommerceGraphicRoleBinding(
                role=role,
                typography_token_id=token.token_id,
            )
            for role in roles
        ),
    )
    geometry = {
        "copy-headline": (100, 100, 800, 0, 48),
        "copy-subtitle": (100, 790, 800, 4, 60),
        "copy-product-label": (100, 160, 800, 12, 84),
        "copy-benefit": (80, 120, 560, 12, 96),
        "copy-proof": (100, 700, 800, 12, 120),
        "copy-cta": (160, 620, 680, 24, 120),
        "copy-end-card": (100, 250, 800, 72, 96),
    }
    treatments = []
    for item in package.copy_graphics_plan:
        x, y, width, start, duration = geometry[item.copy_id]
        role = GraphicRole[item.role]
        treatments.append(
            GraphicTreatment(
                graphic_id=item.copy_id,
                role=role,
                text=item.text,
                shot_id=item.shot_id,
                start_frame_offset=start,
                duration_frames=duration,
                x_milli=x,
                y_milli=y,
                width_milli=width,
                font_size_px=token.font_size_px,
                font_weight=token.font_weight,
                letter_spacing_px=token.letter_spacing_px,
                text_color=token.text_color,
                background_color=token.background_color,
                safe_area=safe,
                avoidance_target_ids=("product", "talent"),
                keyword_emphasis=tuple(
                    GraphicKeywordEmphasis(
                        text=text,
                        brand_token_id=item.brand_token_reference,
                    )
                    for text in item.keyword_emphasis
                ),
                brand_token_ids=(item.brand_token_reference,),
                synchronized_event_id=item.beat_id,
                sound_cue_ids=tuple(
                    event_id
                    for event_id in item.synchronized_event_ids
                    if event_id.startswith("audio-")
                ),
                z_index=10,
                caption_binding_id=(
                    "caption-copy-subtitle"
                    if role is GraphicRole.DIALOGUE_SUBTITLE
                    else None
                ),
            )
        )
    truth_ids = tuple(item.source_id for item in package.product_truth.sources)
    presentations = []
    for item in package.product_presentation:
        complex_integration = (
            item.occlusion_required
            or item.lighting_shadow_required
            or item.talent_interaction == "PHYSICAL_CONTACT"
        )
        presentations.append(
            ProductPresentation(
                presentation_id=item.presentation_id,
                role=ProductPresentationRole[item.role],
                mode=(
                    ProductPresentationMode.HERO_ASSET
                    if item.mode == "DEDICATED_HERO_SHOT"
                    else ProductPresentationMode.GRAPHIC_REVEAL
                ),
                beat_id=item.beat_id,
                shot_id=item.shot_id,
                asset_id=item.product_source_asset_id,
                composition_layer_id=f"layer-{item.presentation_id}",
                product_truth_reference_ids=truth_ids,
                graphic_treatment_ids=item.copy_cue_ids,
                sound_cue_ids=item.audio_cue_ids,
                tracking_required=False,
                occlusion_required=item.occlusion_required,
                lighting_match_required=item.lighting_shadow_required,
                capability_classification=(
                    CapabilityClassification.REQUIRES_RUNTIME_CAPABILITY
                    if complex_integration
                    else CapabilityClassification.SUPPORTED_CURRENTLY
                ),
                requires_physical_interaction=(
                    item.talent_interaction == "PHYSICAL_CONTACT"
                ),
            )
        )
    beat_roles = {
        "beat-hook": AdBeatRole.PROBLEM,
        "beat-intro": AdBeatRole.PRODUCT_INTRODUCTION,
        "beat-demo": AdBeatRole.DEMONSTRATION,
        "beat-proof": AdBeatRole.HERO,
        "beat-close": AdBeatRole.BRAND_CLOSURE,
    }
    layout = EcommerceLayoutPlan.create(
        source_package_id=package.package_id,
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        scenes=(
            EcommerceLayoutScene(
                scene_id="scene-daylight-desk",
                source_set_id="set-daylight-desk",
                location=package.set_plan[0].location,
                time="day",
                mood="bright practical commercial",
                participant_ids=(package.talent_plan[0].talent_id,),
                continuity_constraints=package.set_plan[0].continuity_anchors,
            ),
        ),
        shots=tuple(
            EcommerceLayoutShot(
                shot_id=item.shot_id,
                scene_id="scene-daylight-desk",
                character_ids=(package.talent_plan[0].talent_id,),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=(item.product_state,),
            )
            for item in package.shot_intents
        ),
        beat_roles=tuple(
            EcommerceBeatRoleBinding(beat_id=item.beat_id, role=beat_roles[item.beat_id])
            for item in package.ad_beats
        ),
        graphic_treatments=tuple(treatments),
        product_presentations=tuple(presentations),
        protagonist_ids=(package.talent_plan[0].talent_id,),
    )
    compile_profile = EcommerceProductionCompileProfile.create(
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        layout_plan_id=layout.layout_plan_id,
        requirement_resolutions=(
            EcommerceRequirementResolution(
                requirement_id="req-ad-graphics",
                capability="advertising_copy_graphics",
                resolution_kind="EXACT_GRAPHIC_LAYOUT",
                evidence_ids=(
                    delivery.profile_id,
                    visual.profile_id,
                    layout.layout_plan_id,
                ),
            ),
        ),
    )
    return delivery, visual, layout, compile_profile


def test_exporter_produces_deterministic_handoff_and_preserves_real_gap() -> None:
    module = _load_exporter()
    package = module.validate_file(
        "package", PACKAGE_PATH, source_input_path=INPUT_PATH
    )
    profiles = _reviewed_visual_contracts(package)

    first = module.export_runtime_handoff(
        package,
        delivery=profiles[0],
        visual=profiles[1],
        layout=profiles[2],
        compile_profile=profiles[3],
    )
    second = module.export_runtime_handoff(
        package,
        delivery=profiles[0],
        visual=profiles[1],
        layout=profiles[2],
        compile_profile=profiles[3],
    )

    assert first == second
    assert first.handoff_id == second.handoff_id
    assert tuple(item.shot_id for item in first.artifact_proposals.shots) == tuple(
        item.shot_id for item in package.shot_intents
    )
    assert "req-ad-graphics" not in {
        requirement_id
        for item in first.unsupported_gaps
        for requirement_id in item.requirement_ids
    }
    assert any(
        item.blocker_code == "ECOMMERCE_PRODUCT_INTEGRATION_UNRESOLVED"
        for item in first.unsupported_gaps
    )


def test_checked_in_handoff_schema_matches_runtime_contract() -> None:
    module = _load_exporter()

    assert HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8") == module.schema_text()


def test_exporter_rejects_stale_layout_identity() -> None:
    module = _load_exporter()
    package = module.validate_file(
        "package", PACKAGE_PATH, source_input_path=INPUT_PATH
    )
    delivery, visual, layout, compile_profile = _reviewed_visual_contracts(package)
    drifted_graphic = layout.graphic_treatments[0].model_copy(update={"x_milli": 90})
    drifted_layout = layout.model_copy(
        update={
            "graphic_treatments": (
                drifted_graphic,
                *layout.graphic_treatments[1:],
            )
        }
    )

    with pytest.raises(ValidationError, match="identity"):
        module.export_runtime_handoff(
            package,
            delivery=delivery,
            visual=visual,
            layout=drifted_layout,
            compile_profile=compile_profile,
        )
