"""Offline native-prompt contracts for new Vidu request compilation."""

from __future__ import annotations

import pytest

from ai_video.production._vidu_prompt import (
    ViduPromptCompilation,
    ViduPromptUnsupported,
    compile_vidu_prompt,
)
from ai_video.production.video_requirement import (
    ActionEndpoint,
    AxisContinuity,
    CameraEndpoint,
    CameraIntent,
    GenerationIntent,
    IdentityContinuity,
    IdentityPreservation,
    MotionEnvelope,
    Pacing,
    SceneContinuity,
    SpaceContinuity,
    SubjectAction,
    TypedStateReference,
    ContinuityStateKind,
)
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
from test_production_video_requirement import _requirement_kwargs


def _requirement():
    payload = _requirement_kwargs()
    intent = GenerationIntent(
        open_state=TypedStateReference(
            kind=ContinuityStateKind.TYPED_TEXT,
            state_text="The seated man has no reflection while seven passengers do.",
        ),
        close_state=TypedStateReference(
            kind=ContinuityStateKind.TYPED_TEXT,
            state_text="His left hand stops before the glass and still has no reflection.",
        ),
        identity_continuity=IdentityContinuity(
            character_ids=("hero",),
            preservation=IdentityPreservation.EXACT,
            allowed_variation=("eye movement, breathing, and the left-hand action",),
        ),
        scene_continuity=SceneContinuity(
            scene_id="room",
            time_of_day="late night",
            mood="cold urban suspense",
            state_constraints=(
                "Keep the camera and framing from the supplied first frame. "
                "The phone hand stays on the lap. No visible captions, text, or digits. "
                "The off-screen announcement says Lin Yan, please get off at the terminal station.",
            ),
        ),
        space_continuity=SpaceContinuity(
            subject_position="seated by the window",
            screen_direction="toward the glass",
            crossing_policy="do not cross the screen axis",
        ),
        axis_continuity=AxisContinuity(
            camera_axis="same side of the carriage",
            framing_continuity="preserve the original composition",
            crossing_policy="no axis crossing",
        ),
        subject_action=SubjectAction(
            start_state="looks at the empty reflected seat",
            progression="raises only the anatomical left hand toward the glass with the palm facing it",
            endpoint=ActionEndpoint(
                state_text="left hand stops two centimetres before the glass with no reflected hand",
                required_change=True,
            ),
        ),
        motion_envelope=MotionEnvelope(
            onset="immediate", peak="left hand rising", settle="left hand hovering",
            direction="toward the window", amplitude_class="small natural movement",
        ),
        pacing=Pacing(
            cadence="the missing reflection is recognized in the first three seconds",
            tempo_class="restrained", shot_duration_seconds=4.0,
        ),
        camera_intent=CameraIntent(
            movement="locked", stability="locked-off static camera, no movement",
            framing_intent="wide close shot at seated eye level",
        ),
        camera_endpoint=CameraEndpoint(
            start_framing="man below and black window above",
            end_framing="the same composition with the hovering left hand",
            position_lock=True,
            orientation_lock=True,
        ),
    )
    payload.update(generation_intent=intent)
    return ProviderNeutralVideoRequirement.create(**payload)


def test_vidu_prompt_preserves_authored_s01_semantics_without_bookkeeping() -> None:
    result = compile_vidu_prompt(_requirement())

    assert isinstance(result, ViduPromptCompilation)
    assert "seven passengers" in result.prompt_text
    assert "left hand" in result.prompt_text
    assert "announcement says Lin Yan" in result.prompt_text
    assert "His left hand stops before the glass and still has no reflection" in result.prompt_text
    assert "必须产生真实的可见状态变化" in result.prompt_text
    assert "摄影机位置和朝向全程锁定" in result.prompt_text
    assert "允许的变化仅限于eye movement" in result.prompt_text
    assert "generation_mode=" not in result.prompt_text
    assert "camera_position_lock=" not in result.prompt_text
    assert "scene_id=" not in result.prompt_text
    assert "hero" not in result.prompt_text
    assert "unspecified" not in result.prompt_text


def test_vidu_prompt_rejects_opaque_state_instead_of_dropping_it() -> None:
    requirement = _requirement()
    intent = requirement.generation_intent.model_copy(
        update={
            "open_state": TypedStateReference(
                kind=ContinuityStateKind.TYPED_HASH,
                state_hash="a" * 64,
            )
        }
    )
    payload = requirement.model_dump(
        mode="python", exclude={"requirement_id", "requirement_hash"}
    )
    payload["generation_intent"] = intent
    result = compile_vidu_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, ViduPromptUnsupported)
    assert result.unsupported_field_paths == ("generation_intent.open_state",)


def test_vidu_prompt_expresses_independent_opening_and_closing_required_changes() -> None:
    requirement = _requirement()
    intent = requirement.generation_intent.model_copy(
        update={
            "open_state": TypedStateReference(
                kind=ContinuityStateKind.TYPED_TEXT,
                state_text="opening-only state change",
                required_change=True,
            ),
            "close_state": TypedStateReference(
                kind=ContinuityStateKind.TYPED_TEXT,
                state_text="closing-only state change",
                required_change=True,
            ),
        }
    )
    payload = requirement.model_dump(
        mode="python", exclude={"requirement_id", "requirement_hash"}
    )
    payload["generation_intent"] = intent
    result = compile_vidu_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, ViduPromptCompilation)
    assert "opening-only state change" in result.prompt_text
    assert "开场状态必须产生真实的可见变化" in result.prompt_text
    assert "closing-only state change" in result.prompt_text
    assert "收束状态必须产生真实的可见变化" in result.prompt_text


@pytest.mark.parametrize("field", ["open_state", "close_state"])
def test_vidu_prompt_rejects_unspecified_state_that_requires_change(field: str) -> None:
    requirement = _requirement()
    intent = requirement.generation_intent.model_copy(
        update={field: TypedStateReference(required_change=True)}
    )
    payload = requirement.model_dump(
        mode="python", exclude={"requirement_id", "requirement_hash"}
    )
    payload["generation_intent"] = intent
    result = compile_vidu_prompt(ProviderNeutralVideoRequirement.create(**payload))

    assert isinstance(result, ViduPromptUnsupported)
    assert result.unsupported_field_paths == (f"generation_intent.{field}",)


def test_vidu_prompt_rejects_camera_complete_contract() -> None:
    requirement = _requirement().model_copy(
        update={"contract_version": "provider-neutral-video-requirement/4"}
    )
    result = compile_vidu_prompt(requirement)

    assert isinstance(result, ViduPromptUnsupported)
    assert "contract_version" in result.unsupported_field_paths
