from __future__ import annotations

from ai_video.production._video_intent_validation import (
    ConditioningCompatibilityEvidence,
    ConditioningLane,
    validate_conditioning_compatibility,
    validate_generation_intent_for_continuity,
)
from ai_video.production.video_requirement import (
    ActionEndpoint,
    AmbienceIntent,
    AxisContinuity,
    CameraAmplitudeClass,
    CameraEndpoint,
    CameraMotionContract,
    CameraMovementKind,
    CameraMotionEndState,
    CameraMotionStartState,
    CameraSubjectRelation,
    CameraSubjectRelationKind,
    CameraSpeedClass,
    ContinuityStateKind,
    DialogueIntent,
    GenerationIntent,
    LightingIntent,
    MusicIntent,
    Pacing,
    PerformanceIntent,
    SpaceContinuity,
    SubjectAction,
    TypedStateReference,
    VisualTreatment,
)


def _complete_intent() -> GenerationIntent:
    return GenerationIntent(
        open_state=TypedStateReference(
            kind=ContinuityStateKind.TYPED_TEXT,
            state_text="hero standing at screen left holding the prop",
        ),
        close_state=TypedStateReference(
            kind=ContinuityStateKind.TYPED_TEXT,
            state_text="hero settled at screen right still holding the prop",
        ),
        space_continuity=SpaceContinuity(screen_direction="left_to_right"),
        axis_continuity=AxisContinuity(
            camera_axis="same_side",
            framing_continuity="medium_to_medium_close",
        ),
        subject_action=SubjectAction(
            start_state="standing",
            progression="walks to the marked endpoint",
            endpoint=ActionEndpoint(state_text="settled at endpoint"),
        ),
        pacing=Pacing(shot_duration_seconds=124 / 24),
        performance_intent=PerformanceIntent(
            trigger="receives the product offer",
            visible_response="acknowledges with a small nod",
            gaze_target="elder and product",
            body_behavior="upright and attentive",
            hand_behavior="reaches once and secures the product",
            terminal_performance_state="settled holding the product",
        ),
        visual_treatment=VisualTreatment(
            medium_look="natural commercial live action",
            palette="warm neutral interior",
            material_treatment="realistic skin and product surfaces",
            prohibited_visual_drift=("no illustration",),
        ),
        lighting_intent=LightingIntent(
            motivated_source="soft window light",
            direction="camera left",
            exposure_priority="faces and product label",
            continuity_state="constant through the shot",
        ),
        ambience_intent=AmbienceIntent(
            environment_bed="quiet interior room tone",
            foley_cues=("soft product handoff",),
        ),
        dialogue_intent=DialogueIntent(mode="none"),
        music_intent=MusicIntent(mode="none"),
        primary_camera_motion=CameraMotionContract(
            movement_kind=CameraMovementKind.DOLLY_IN,
            direction="forward",
            amplitude_class=CameraAmplitudeClass.SUBTLE,
            speed_class=CameraSpeedClass.SLOW,
            start_motion_state=CameraMotionStartState.STATIONARY,
            end_motion_state=CameraMotionEndState.SETTLED,
        ),
        camera_subject_relation=CameraSubjectRelation(
            subject_id="hero",
            relation_kind=CameraSubjectRelationKind.MAINTAIN_OFFSET,
            start_relation="medium two-shot centered on the handoff",
            end_relation="same axis and offset on the new holder",
        ),
        camera_endpoint=CameraEndpoint(
            start_framing="medium shot",
            end_framing="medium close-up",
        ),
    )


def _compatible_fl2va() -> ConditioningCompatibilityEvidence:
    return ConditioningCompatibilityEvidence(
        lane=ConditioningLane.FL2VA,
        first_anchor_id="anchor-first",
        last_anchor_id="anchor-last",
        same_subject_scale=True,
        composition_compatible=True,
        screen_order_compatible=True,
        axis_compatible=True,
        camera_path_reachable=True,
        character_prop_state_reachable=True,
        action_endpoint_reachable=True,
        available_duration_seconds=124 / 24,
    )


def test_complete_continuity_intent_has_no_diagnostics() -> None:
    assert validate_generation_intent_for_continuity(_complete_intent()) == ()


def test_incomplete_continuity_intent_returns_stable_field_paths() -> None:
    result = validate_generation_intent_for_continuity(GenerationIntent())

    assert result == (
        "generation_intent.open_state",
        "generation_intent.close_state",
        "generation_intent.subject_action.start_state",
        "generation_intent.subject_action.progression",
        "generation_intent.subject_action.endpoint",
        "generation_intent.space_continuity.screen_direction",
        "generation_intent.axis_continuity.camera_axis",
        "generation_intent.axis_continuity.framing_continuity",
        "generation_intent.performance_intent",
        "generation_intent.visual_treatment",
        "generation_intent.lighting_intent",
        "generation_intent.ambience_intent",
        "generation_intent.dialogue_intent",
        "generation_intent.music_intent",
        "generation_intent.primary_camera_motion",
        "generation_intent.camera_subject_relation",
        "generation_intent.camera_endpoint.start_framing",
        "generation_intent.camera_endpoint.end_framing",
        "generation_intent.pacing.shot_duration_seconds",
    )


def test_incompatible_fl2va_anchor_reports_exact_failed_dimensions() -> None:
    evidence = _compatible_fl2va().model_copy(
        update={"same_subject_scale": False, "action_endpoint_reachable": False}
    )

    assert validate_conditioning_compatibility(evidence) == (
        "conditioning_compatibility.same_subject_scale",
        "conditioning_compatibility.action_endpoint_reachable",
    )
