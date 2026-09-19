"""Build the four exact visual contracts for the Ninebot N3 lighting ad.

Constructs EcommerceDeliveryProfile / EcommerceVisualSystemProfile /
EcommerceLayoutPlan / EcommerceProductionCompileProfile from the validated
package/2, pulling copy text, keyword emphasis, brand tokens and shot
bindings directly from the package JSON so nothing drifts by hand.
Writes four JSON files next to this script for export_runtime_handoff.py.
"""

import json
from pathlib import Path

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
    GraphicAnimation,
    GraphicKeywordEmphasis,
    GraphicRole,
    GraphicSafeAreaInsets,
    GraphicTreatment,
)
from ai_video.production.composition_contracts import FixedTransform
from ai_video.production.ad_creative_types import ProductTransformIntent
from ai_video.production.models import VisualStrategy

ROOT = Path(__file__).resolve().parent
PACKAGE = json.loads((ROOT / "ecommerce-package.json").read_text(encoding="utf-8"))
FPS = 30

SAFE_AREA = GraphicSafeAreaInsets(
    top_milli=80, right_milli=120, bottom_milli=140, left_milli=60
)

TOKENS = {
    "type-headline": EcommerceTypographyToken(
        token_id="type-headline",
        font_family="sans-serif",
        font_size_px=92,
        font_weight=800,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000066",
    ),
    "type-caption": EcommerceTypographyToken(
        token_id="type-caption",
        font_family="sans-serif",
        font_size_px=44,
        font_weight=500,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000099",
    ),
    "type-product-label": EcommerceTypographyToken(
        token_id="type-product-label",
        font_family="sans-serif",
        font_size_px=60,
        font_weight=700,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000066",
    ),
    "type-proof": EcommerceTypographyToken(
        token_id="type-proof",
        font_family="sans-serif",
        font_size_px=56,
        font_weight=700,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000066",
    ),
    "type-benefit": EcommerceTypographyToken(
        token_id="type-benefit",
        font_family="sans-serif",
        font_size_px=84,
        font_weight=800,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000066",
    ),
    "type-cta": EcommerceTypographyToken(
        token_id="type-cta",
        font_family="sans-serif",
        font_size_px=88,
        font_weight=900,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#E60023FF",
    ),
    "type-end-card": EcommerceTypographyToken(
        token_id="type-end-card",
        font_family="sans-serif",
        font_size_px=68,
        font_weight=800,
        letter_spacing_px=0,
        text_color="#FFFFFFFF",
        background_color="#00000066",
    ),
}

ROLE_TOKENS = {
    "HEADLINE": "type-headline",
    "DIALOGUE_SUBTITLE": "type-caption",
    "PRODUCT_LABEL": "type-product-label",
    "PROOF_LABEL": "type-proof",
    "BENEFIT_CALLOUT": "type-benefit",
    "CTA": "type-cta",
    "BRAND_END_CARD": "type-end-card",
}

# copy_id -> (start_frame_offset, duration_frames, x_milli, y_milli, width_milli,
#             z_index, entrance, exit, extra_brand_tokens, caption_binding_id)
LAYOUT = {
    "copy-headline": (12, 66, 60, 120, 820, 20, GraphicAnimation.SLIDE_UP, GraphicAnimation.FADE, ("ninebot-accent-red",), None),
    "copy-sub-hook": (6, 78, 60, 830, 820, 15, GraphicAnimation.FADE, GraphicAnimation.FADE, (), "caption-audio-vo-hook"),
    "copy-product-label": (20, 120, 60, 640, 820, 20, GraphicAnimation.FADE, GraphicAnimation.FADE, ("ninebot-accent-glow",), None),
    "copy-sub-intro": (6, 138, 60, 830, 820, 15, GraphicAnimation.FADE, GraphicAnimation.FADE, (), "caption-audio-vo-intro"),
    "copy-proof-65000cd": (12, 216, 60, 300, 560, 20, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, ("ninebot-accent-red",), None),
    "copy-proof-highbeam": (60, 168, 60, 384, 560, 20, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, ("ninebot-accent-glow",), None),
    "copy-proof-brighter71": (110, 118, 60, 468, 560, 20, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, ("ninebot-accent-red",), None),
    "copy-benefit": (160, 68, 60, 120, 820, 20, GraphicAnimation.FADE, GraphicAnimation.FADE, ("ninebot-accent-glow",), None),
    "copy-real-label": (12, 216, 563, 400, 300, 20, GraphicAnimation.FADE, GraphicAnimation.NONE, (), None),
    "copy-sub-demo": (6, 222, 60, 830, 820, 15, GraphicAnimation.FADE, GraphicAnimation.FADE, (), "caption-audio-vo-demo"),
    "copy-price-series": (12, 186, 60, 300, 820, 20, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, ("ninebot-accent-red",), None),
    "copy-price-n3-85c": (45, 153, 60, 392, 820, 20, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, ("ninebot-accent-red",), None),
    "copy-disclaimer": (12, 186, 60, 520, 820, 10, GraphicAnimation.FADE, GraphicAnimation.NONE, (), None),
    "copy-sub-proof": (6, 186, 60, 830, 820, 15, GraphicAnimation.FADE, GraphicAnimation.FADE, (), "caption-audio-vo-proof"),
    "copy-cta": (10, 200, 180, 480, 640, 30, GraphicAnimation.SCALE_IN, GraphicAnimation.NONE, (), None),
    "copy-end-card": (40, 170, 60, 200, 820, 25, GraphicAnimation.FADE, GraphicAnimation.NONE, ("ninebot-accent-red",), None),
    "copy-sub-close": (12, 186, 60, 830, 820, 15, GraphicAnimation.FADE, GraphicAnimation.FADE, (), "caption-audio-vo-close"),
}

EMPHASIS_TOKENS = {
    "看清": "ninebot-accent-red",
    "九号 N3 85C": "ninebot-accent-glow",
    "ALC全境光幕照明系统": "ninebot-accent-glow",
    "65000cd": "ninebot-accent-red",
    "远光": "ninebot-accent-glow",
    "71%": "ninebot-accent-red",
    "更亮": "ninebot-accent-glow",
    "¥3499": "ninebot-accent-red",
    "¥4199": "ninebot-accent-red",
    "试灯试驾": "ninebot-cta",
    "浩口九号智能电动车": "ninebot-accent-red",
}


def build_treatments() -> tuple[GraphicTreatment, ...]:
    treatments = []
    for copy in PACKAGE["copy_graphics_plan"]:
        copy_id = copy["copy_id"]
        start, duration, x, y, width, z, entrance, exit_, extra_tokens, caption_binding = LAYOUT[copy_id]
        token = TOKENS[ROLE_TOKENS[copy["role"]]]
        brand_tokens = tuple(
            dict.fromkeys((copy["brand_token_reference"], *extra_tokens))
        )
        emphasis = tuple(
            GraphicKeywordEmphasis(text=text, brand_token_id=EMPHASIS_TOKENS[text])
            for text in copy["keyword_emphasis"]
        )
        sound_cues = tuple(
            event_id
            for event_id in copy["synchronized_event_ids"]
            if event_id.startswith("audio-")
        )
        treatments.append(
            GraphicTreatment(
                graphic_id=copy_id,
                role=GraphicRole(copy["role"].lower()),
                text=copy["text"],
                shot_id=copy["shot_id"],
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
                safe_area=SAFE_AREA,
                keyword_emphasis=emphasis,
                brand_token_ids=brand_tokens,
                sound_cue_ids=sound_cues,
                entrance=entrance,
                exit=exit_,
                z_index=z,
                caption_binding_id=caption_binding,
            )
        )
    return tuple(treatments)


def build_presentations() -> tuple[ProductPresentation, ...]:
    def _presentation(
        presentation_id: str,
        role: ProductPresentationRole,
        mode: ProductPresentationMode,
        beat_id: str,
        shot_id: str,
        asset_id: str,
        layer_id: str,
        truth_ids: tuple[str, ...],
        graphic_ids: tuple[str, ...],
        cue_ids: tuple[str, ...],
        entrance: GraphicAnimation = GraphicAnimation.NONE,
        transform: FixedTransform | None = None,
    ) -> ProductPresentation:
        return ProductPresentation(
            presentation_id=presentation_id,
            role=role,
            mode=mode,
            beat_id=beat_id,
            shot_id=shot_id,
            asset_id=asset_id,
            composition_layer_id=layer_id,
            product_truth_reference_ids=truth_ids,
            graphic_treatment_ids=graphic_ids,
            sound_cue_ids=cue_ids,
            capability_classification=CapabilityClassification.SUPPORTED_CURRENTLY,
            entrance=entrance,
            transform_intent=(
                ProductTransformIntent(transform=transform)
                if transform is not None
                else ProductTransformIntent()
            ),
        )

    return (
        _presentation(
            "presentation-intro",
            ProductPresentationRole.INTRO,
            ProductPresentationMode.GRAPHIC_REVEAL,
            "beat-intro",
            "shot-intro",
            "asset-n3-85c-front",
            "layer-product-intro",
            ("source-n3-85c-pricetag",),
            ("copy-product-label",),
            ("audio-vo-intro",),
            entrance=GraphicAnimation.FADE,
        ),
        _presentation(
            "presentation-demo",
            ProductPresentationRole.DEMONSTRATION,
            ProductPresentationMode.HERO_ASSET,
            "beat-demo",
            "shot-demo",
            "asset-night-pov-video",
            "layer-demo-video",
            ("source-night-pov-video",),
            (
                "copy-proof-65000cd",
                "copy-proof-highbeam",
                "copy-proof-brighter71",
                "copy-real-label",
            ),
            ("audio-vo-demo",),
            transform=FixedTransform(
                translate_x_px=608,
                translate_y_px=832,
                scale_x_milli=400,
                scale_y_milli=400,
            ),
        ),
        _presentation(
            "presentation-hero",
            ProductPresentationRole.HERO_SHOT,
            ProductPresentationMode.HERO_ASSET,
            "beat-proof",
            "shot-proof",
            "asset-n3-85c-front",
            "layer-hero",
            ("source-n3-85c-pricetag",),
            ("copy-price-series", "copy-price-n3-85c", "copy-disclaimer"),
            ("audio-vo-proof",),
        ),
        _presentation(
            "presentation-cta",
            ProductPresentationRole.CTA_SUPPORT,
            ProductPresentationMode.GRAPHIC_REVEAL,
            "beat-close",
            "shot-close",
            "asset-n3-85c-front",
            "layer-cta",
            ("source-n3-85c-pricetag",),
            ("copy-cta", "copy-end-card"),
            ("audio-vo-close",),
            entrance=GraphicAnimation.FADE,
        ),
    )


def main() -> None:
    delivery = EcommerceDeliveryProfile.create(
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=FPS,
        codec_profile="h264",
        audio_sample_rate_hz=48_000,
        platform="douyin",
        placement="vertical-feed",
        constraints=tuple(PACKAGE["product_truth"]["required_disclaimers"])
        + ("关键文字与价格信息保持在竖屏中央安全区内",),
    )
    visual = EcommerceVisualSystemProfile.create(
        brand_token_ids=(
            "ninebot-heading-primary",
            "caption-default",
            "ninebot-product-label",
            "ninebot-proof-label",
            "ninebot-callout",
            "ninebot-price-tag",
            "ninebot-disclaimer",
            "ninebot-cta",
            "ninebot-end-card",
            "ninebot-accent-red",
            "ninebot-accent-glow",
        ),
        safe_area=SAFE_AREA,
        typography_tokens=tuple(TOKENS.values()),
        role_bindings=tuple(
            EcommerceGraphicRoleBinding(
                role=GraphicRole(role.lower()), typography_token_id=token_id
            )
            for role, token_id in ROLE_TOKENS.items()
        ),
    )
    layout = EcommerceLayoutPlan.create(
        source_package_id=PACKAGE["package_id"],
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        scenes=(
            EcommerceLayoutScene(
                scene_id="scene-night-street",
                source_set_id="set-night-street",
                location="夜间道路（demo 段为门店实拍 POV，hook/intro 为生成场景）",
                time="night",
                mood="安静、黑暗环境中光幕为唯一主角",
                participant_ids=("talent-n3-85c",),
                continuity_constraints=("白色车身", "ALC 光幕大灯形态一致"),
            ),
            EcommerceLayoutScene(
                scene_id="scene-showroom",
                source_set_id="set-showroom",
                location="门店展厅（延续实拍质感）",
                time="interior",
                mood="干净商业感",
                participant_ids=("talent-n3-85c",),
                continuity_constraints=("N3 85C 正面车头", "价格信息准确"),
            ),
        ),
        shots=(
            EcommerceLayoutShot(
                shot_id="shot-hook",
                scene_id="scene-night-street",
                character_ids=("talent-n3-85c",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("车身剪影与车灯点亮瞬间一致",),
            ),
            EcommerceLayoutShot(
                shot_id="shot-intro",
                scene_id="scene-night-street",
                character_ids=("talent-n3-85c",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("白色车身与车标一致",),
            ),
            EcommerceLayoutShot(
                shot_id="shot-demo",
                scene_id="scene-night-street",
                character_ids=("talent-n3-85c",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("光幕形态与实拍素材一致",),
            ),
            EcommerceLayoutShot(
                shot_id="shot-proof",
                scene_id="scene-showroom",
                character_ids=("talent-n3-85c",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("车头灯特写的车型 identity 一致",),
            ),
            EcommerceLayoutShot(
                shot_id="shot-close",
                scene_id="scene-showroom",
                character_ids=("talent-n3-85c",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("定妆画面与 hero 一致",),
            ),
        ),
        beat_roles=(
            EcommerceBeatRoleBinding(beat_id="beat-hook", role=AdBeatRole.PROBLEM),
            EcommerceBeatRoleBinding(
                beat_id="beat-intro", role=AdBeatRole.PRODUCT_INTRODUCTION
            ),
            EcommerceBeatRoleBinding(
                beat_id="beat-demo", role=AdBeatRole.DEMONSTRATION
            ),
            EcommerceBeatRoleBinding(beat_id="beat-proof", role=AdBeatRole.PROOF),
            EcommerceBeatRoleBinding(
                beat_id="beat-close", role=AdBeatRole.BRAND_CLOSURE
            ),
        ),
        graphic_treatments=build_treatments(),
        product_presentations=build_presentations(),
        protagonist_ids=("talent-n3-85c",),
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
    outputs = {
        "delivery-profile.json": delivery,
        "visual-system-profile.json": visual,
        "layout-plan.json": layout,
        "compile-profile.json": compile_profile,
    }
    for name, model in outputs.items():
        (ROOT / name).write_text(
            json.dumps(model.model_dump(mode="json"), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        print(name, model.model_dump(mode="json")[
            "profile_id" if "profile" in name or "delivery" in name else "layout_plan_id"
        ])


if __name__ == "__main__":
    main()
