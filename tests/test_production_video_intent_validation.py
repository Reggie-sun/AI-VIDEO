from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256
from ai_video.production._conditioning_scale_transition import (
    ScaleTransitionEvidence,
    scale_transition_camera_intent_hash,
)
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


def _scale_transition(intent=None, **updates) -> ScaleTransitionEvidence:
    intent = intent or _complete_intent()
    data = dict(
        first_anchor_id="anchor-first", first_anchor_sha256="1" * 64,
        last_anchor_id="anchor-last", last_anchor_sha256="2" * 64,
        camera_intent_hash=scale_transition_camera_intent_hash(intent),
        available_duration_seconds=intent.pacing.shot_duration_seconds,
        sources=(
            dict(source_id="geometry", kind="anchor_geometry_review",
                 evidence_ref="evidence/anchor-review.json", sha256="a" * 64),
            dict(source_id="trajectory", kind="trajectory",
                 evidence_ref="evidence/path.json", sha256="b" * 64),
        ),
        findings=tuple(dict(
            finding_id=name, verdict="PASS", rationale="Exact sources reviewed prospectively",
            source_ids=("geometry",) if name == "anchor_correspondence" else ("trajectory",),
        ) for name in ("anchor_correspondence", "scale_fov_continuity",
                       "duration_reachable", "continuous_camera_path")),
    )
    data.update(updates)
    return ScaleTransitionEvidence.create(**data)


def test_same_scale_legacy_bytes_and_hash_are_unchanged() -> None:
    evidence = _compatible_fl2va()
    assert "scale_transition" not in evidence.model_dump(mode="json")
    assert canonical_sha256(evidence) == "3ac5b6e0fd4e1c48470838bca1bc494c978be5923dd92ed48097d35fbf7dec79"


def test_scale_transition_requires_complete_bound_prospective_evidence() -> None:
    intent = _complete_intent()
    evidence = _compatible_fl2va().model_copy(update={
        "same_subject_scale": False, "scale_transition": _scale_transition(intent),
    })
    assert validate_conditioning_compatibility(
        evidence, generation_intent=intent, output_duration_seconds=124 / 24,
    ) == ()
    assert validate_conditioning_compatibility(evidence)
    changed = intent.model_copy(update={"camera_endpoint": CameraEndpoint(
        start_framing="wide", end_framing="close",
    )})
    assert "conditioning_compatibility.scale_transition.camera_intent_hash" in validate_conditioning_compatibility(
        evidence, generation_intent=changed, output_duration_seconds=124 / 24,
    )


@pytest.mark.parametrize("verdict", ["FAIL", "NOT_EVALUATED"])
def test_scale_transition_nonpassing_review_is_recordable_but_not_admissible(verdict) -> None:
    extension = _scale_transition()
    findings = [f.model_dump(mode="json") for f in extension.findings]
    findings[0]["verdict"] = verdict
    extension = _scale_transition(findings=findings)
    evidence = _compatible_fl2va().model_copy(update={
        "same_subject_scale": False, "scale_transition": extension,
    })
    assert "conditioning_compatibility.scale_transition.findings" in validate_conditioning_compatibility(
        evidence, generation_intent=_complete_intent(), output_duration_seconds=124 / 24,
    )


def test_scale_transition_rejects_hash_tampering_and_incomplete_sources() -> None:
    extension = _scale_transition()
    bad = extension.model_dump(mode="json")
    bad["last_anchor_sha256"] = "3" * 64
    with pytest.raises(ValidationError, match="content_hash"):
        ScaleTransitionEvidence.model_validate(bad)
    with pytest.raises(ValidationError, match="four"):
        _scale_transition(findings=extension.findings[:-1])
    with pytest.raises(ValidationError, match="source"):
        _scale_transition(sources=[dict(source_id="trajectory", kind="proxy",
                                      evidence_ref="proxy.blend", sha256="c" * 64)])
    findings = [f.model_dump(mode="json") for f in extension.findings]
    findings[0]["source_ids"] = ["trajectory"]
    with pytest.raises(ValidationError, match="source"):
        _scale_transition(findings=findings)


def test_scale_transition_missing_unknown_and_unusable_evidence_fails_closed() -> None:
    intent = _complete_intent()
    for value in (False, None):
        evidence = _compatible_fl2va().model_copy(update={"same_subject_scale": value})
        assert "conditioning_compatibility.same_subject_scale" in validate_conditioning_compatibility(
            evidence, generation_intent=intent, output_duration_seconds=124 / 24,
        )
    extension = _scale_transition()
    findings = [item.model_dump(mode="json") for item in extension.findings]
    findings[0]["source_ids"] = ["unknown"]
    with pytest.raises(ValidationError, match="unknown source"):
        _scale_transition(findings=findings)
    findings[0]["source_ids"] = ["geometry"]
    findings[0]["rationale"] = "  "
    with pytest.raises(ValidationError, match="blank"):
        _scale_transition(findings=findings)
    with pytest.raises(ValidationError):
        _scale_transition(available_duration_seconds=float("inf"))
    extension = extension.model_copy(update={"content_hash": "d" * 64})
    evidence = _compatible_fl2va().model_copy(update={
        "same_subject_scale": False, "scale_transition": extension,
    })
    assert validate_conditioning_compatibility(
        evidence, generation_intent=intent, output_duration_seconds=124 / 24,
    ) == ("conditioning_compatibility.scale_transition.content_hash",)


@pytest.mark.parametrize("locked", [False, True])
def test_scale_transition_cannot_attest_missing_or_locked_camera_motion(locked) -> None:
    motion = CameraMotionContract(
        movement_kind=CameraMovementKind.LOCKED, direction="none",
        amplitude_class=CameraAmplitudeClass.SUBTLE, speed_class=CameraSpeedClass.VERY_SLOW,
        start_motion_state=CameraMotionStartState.STATIONARY,
        end_motion_state=CameraMotionEndState.SETTLED,
    ) if locked else None
    intent = _complete_intent().model_copy(update={"primary_camera_motion": motion})
    evidence = _compatible_fl2va().model_copy(update={
        "same_subject_scale": False, "scale_transition": _scale_transition(intent),
    })
    assert "conditioning_compatibility.scale_transition.primary_camera_motion" in validate_conditioning_compatibility(
        evidence, generation_intent=intent, output_duration_seconds=124 / 24,
    )


@pytest.mark.parametrize("field", ["composition_compatible", "screen_order_compatible", "axis_compatible",
                                   "camera_path_reachable", "character_prop_state_reachable", "action_endpoint_reachable"])
def test_scale_transition_does_not_relax_other_compatibility_dimensions(field) -> None:
    evidence = _compatible_fl2va().model_copy(update={
        "same_subject_scale": False, "scale_transition": _scale_transition(), field: False,
    })
    assert f"conditioning_compatibility.{field}" in validate_conditioning_compatibility(
        evidence, generation_intent=_complete_intent(), output_duration_seconds=124 / 24,
    )


@pytest.mark.parametrize("same_scale,lane", [(True, "fl2va"), (None, "fl2va"), (False, "i2va")])
def test_scale_transition_rejects_contradictory_or_single_anchor_lanes(same_scale, lane) -> None:
    data = _compatible_fl2va().model_dump(mode="json")
    data.update(same_subject_scale=same_scale, lane=lane, scale_transition=_scale_transition())
    if lane == "i2va":
        data["last_anchor_id"] = None
    with pytest.raises(ValidationError, match="scale_transition"):
        ConditioningCompatibilityEvidence.model_validate(data)
