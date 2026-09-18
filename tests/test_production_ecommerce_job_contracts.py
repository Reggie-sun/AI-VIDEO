from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production import (
    EcommerceBeatRoleBinding,
    EcommerceDeliveryProfile,
    EcommerceGraphicRoleBinding,
    EcommerceJobNextAction,
    EcommerceLayoutPlan,
    EcommerceLayoutScene,
    EcommerceLayoutShot,
    EcommerceProductionCompileProfile,
    EcommerceProductionJobProjection,
    EcommerceProductionJobRequest,
    EcommerceRequirementResolution,
    EcommerceTypographyToken,
    EcommerceVisualSystemProfile,
)
from ai_video.production.ad_creative_types import AdBeatRole
from ai_video.production.commercial_graphics import (
    GraphicRole,
    GraphicSafeAreaInsets,
)
from ai_video.production.models import VisualStrategy


PACKAGE_ID = "1" * 64


def _profiles():
    delivery = EcommerceDeliveryProfile.create(
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        fps=24,
        codec_profile="h264",
        audio_sample_rate_hz=48_000,
        platform="short-video",
        placement="vertical-feed",
        constraints=("Keep commercial copy inside the declared safe area.",),
    )
    visual = EcommerceVisualSystemProfile.create(
        brand_token_ids=("brand-primary", "brand-end-card"),
        safe_area=GraphicSafeAreaInsets(
            top_milli=50,
            right_milli=50,
            bottom_milli=80,
            left_milli=50,
        ),
        typography_tokens=(
            EcommerceTypographyToken(
                token_id="type-primary",
                font_family="sans-serif",
                font_size_px=64,
                font_weight=700,
                letter_spacing_px=0,
                text_color="#FFFFFFFF",
                background_color="#00000099",
            ),
        ),
        role_bindings=(
            EcommerceGraphicRoleBinding(
                role=GraphicRole.CTA,
                typography_token_id="type-primary",
            ),
            EcommerceGraphicRoleBinding(
                role=GraphicRole.BRAND_END_CARD,
                typography_token_id="type-primary",
            ),
        ),
    )
    layout = EcommerceLayoutPlan.create(
        source_package_id=PACKAGE_ID,
        delivery_profile_id=delivery.profile_id,
        visual_system_profile_id=visual.profile_id,
        scenes=(
            EcommerceLayoutScene(
                scene_id="scene-product",
                source_set_id="set-product",
                location="Product stage",
                time="day",
                mood="clean commercial",
                participant_ids=("talent-presenter",),
                continuity_constraints=("Product remains frame center.",),
            ),
        ),
        shots=(
            EcommerceLayoutShot(
                shot_id="shot-hook",
                scene_id="scene-product",
                character_ids=("talent-presenter",),
                visual_strategy=VisualStrategy.GENERATED_VIDEO,
                continuity_constraints=("Preserve product identity.",),
            ),
        ),
        beat_roles=(
            EcommerceBeatRoleBinding(
                beat_id="beat-hook",
                role=AdBeatRole.PROBLEM,
            ),
        ),
        graphic_treatments=(),
        product_presentations=(),
        protagonist_ids=("talent-presenter",),
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


def test_visual_contracts_are_independently_content_addressed_and_frozen() -> None:
    delivery, visual, layout, compile_profile = _profiles()

    assert len({
        delivery.profile_id,
        visual.profile_id,
        layout.layout_plan_id,
        compile_profile.profile_id,
    }) == 4
    with pytest.raises(ValidationError):
        delivery.width = 720  # type: ignore[misc]
    with pytest.raises(ValidationError):
        layout.shots = ()  # type: ignore[misc]


def test_delivery_profile_rejects_geometry_that_does_not_match_aspect_ratio() -> None:
    with pytest.raises(ValidationError, match="9:16"):
        EcommerceDeliveryProfile.create(
            aspect_ratio="9:16",
            width=1920,
            height=1080,
            fps=24,
            codec_profile="h264",
            audio_sample_rate_hz=48_000,
            platform="short-video",
            placement="vertical-feed",
            constraints=(),
        )


def test_visual_system_rejects_unknown_typography_binding() -> None:
    with pytest.raises(ValidationError, match="typography"):
        EcommerceVisualSystemProfile.create(
            brand_token_ids=("brand-primary",),
            safe_area=GraphicSafeAreaInsets(),
            typography_tokens=(),
            role_bindings=(
                EcommerceGraphicRoleBinding(
                    role=GraphicRole.CTA,
                    typography_token_id="missing-token",
                ),
            ),
        )


def test_typography_rejects_font_family_not_expressible_by_current_renderer() -> None:
    with pytest.raises(ValidationError, match="sans-serif"):
        EcommerceTypographyToken(
            token_id="type-brand",
            font_family="Inter",
            font_size_px=64,
            font_weight=700,
            letter_spacing_px=0,
            text_color="#FFFFFFFF",
        )


def test_layout_plan_rejects_unknown_scene() -> None:
    delivery, visual, _layout, _compile_profile = _profiles()
    shot = EcommerceLayoutShot(
        shot_id="shot-hook",
        scene_id="missing-scene",
        character_ids=(),
        visual_strategy=VisualStrategy.MOTION_GRAPHICS,
        continuity_constraints=(),
    )
    with pytest.raises(ValidationError, match="scene"):
        EcommerceLayoutPlan.create(
            source_package_id=PACKAGE_ID,
            delivery_profile_id=delivery.profile_id,
            visual_system_profile_id=visual.profile_id,
            scenes=(
                EcommerceLayoutScene(
                    scene_id="scene-product",
                    source_set_id=None,
                    location="Product stage",
                    time="day",
                    mood="clean commercial",
                    participant_ids=(),
                    continuity_constraints=(),
                ),
            ),
            shots=(shot,),
            beat_roles=(),
            graphic_treatments=(),
            product_presentations=(),
            protagonist_ids=(),
        )


def test_layout_plan_rejects_duplicate_shot() -> None:
    delivery, visual, layout, _compile_profile = _profiles()
    with pytest.raises(ValidationError, match="Shot IDs must be unique"):
        EcommerceLayoutPlan.create(
            source_package_id=PACKAGE_ID,
            delivery_profile_id=delivery.profile_id,
            visual_system_profile_id=visual.profile_id,
            scenes=layout.scenes,
            shots=(layout.shots[0], layout.shots[0]),
            beat_roles=(),
            graphic_treatments=(),
            product_presentations=(),
            protagonist_ids=(),
        )


def test_job_request_and_projection_are_intent_and_read_only_projection_only(
    tmp_path: Path,
) -> None:
    delivery, _visual, _layout, compile_profile = _profiles()
    request = EcommerceProductionJobRequest(
        schema_version="ecommerce-production-job-request/1",
        job_id="job-001",
        project_root=tmp_path.resolve(),
        handoff_id="2" * 64,
        expected_project_id="project-001",
        execution_policy_id=compile_profile.profile_id,
        delivery_profile_id=delivery.profile_id,
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )
    projection = EcommerceProductionJobProjection(
        schema_version="ecommerce-production-job-projection/1",
        job_id=request.job_id,
        handoff_id=request.handoff_id,
        expected_project_id=request.expected_project_id,
        next_action=EcommerceJobNextAction.BOOTSTRAP_PROJECT,
        manifest_revision=None,
        next_shot_id=None,
        blocker=None,
    )

    assert "status" not in type(request).model_fields
    assert "status" not in type(projection).model_fields
    with pytest.raises(ValidationError):
        projection.next_action = EcommerceJobNextAction.BLOCKED  # type: ignore[misc]


def test_job_request_requires_absolute_project_root(tmp_path: Path) -> None:
    delivery, _visual, _layout, compile_profile = _profiles()
    with pytest.raises(ValidationError, match="absolute"):
        EcommerceProductionJobRequest(
            schema_version="ecommerce-production-job-request/1",
            job_id="job-001",
            project_root=Path("relative-project"),
            handoff_id="2" * 64,
            expected_project_id="project-001",
            execution_policy_id=compile_profile.profile_id,
            delivery_profile_id=delivery.profile_id,
            max_new_generation_attempts=2,
            max_repairs_per_shot=1,
        )
