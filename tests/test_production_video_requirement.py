from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_requirement import (
    ActionEndpoint,
    AssetEvidence,
    AudioNeed,
    AxisContinuity,
    CameraAmplitudeClass,
    CameraEndpoint,
    CameraIntent,
    CameraMotionContract,
    CameraMovementKind,
    CameraMotionEndState,
    CameraMotionStartState,
    CameraSpeedClass,
    CameraSubjectRelation,
    CameraSubjectRelationKind,
    CapabilityNeed,
    ConditioningLane,
    ContinuityMode,
    ContinuityStateKind,
    DialogueIntent,
    ExpressionStrength,
    GenerationIntent,
    GenerationMode,
    GenerationOperation,
    IdentityContinuity,
    IdentityPreservation,
    MotionEnvelope,
    MotionRequirement,
    OutputGeometryPolicy,
    OutputNeed,
    Pacing,
    ProviderNeutralGenerationIntentProjection,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    ReviewEvidenceLink,
    SceneContinuity,
    SemanticReferenceRole,
    SpaceContinuity,
    SubjectAction,
    TypedStateReference,
    UNSPECIFIED,
)
from ai_video.production.models import Character, Scene, Shot


_SAFE_ID = r"^[A-Za-z0-9._:/-]{1,256}$"
_SHA256 = r"^[0-9a-f]{64}$"


def _character() -> Character:
    return Character(
        artifact_id="character-hero",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-character-hero",
        source_provenance=(
            {
                "kind": "user_input",
                "reference": "fixture",
            },
        ),
        character_id="hero",
        name="Hero",
        identity="lead",
        appearance_bible="blue jacket",
        reference_asset_ids=("reference-hero",),
    )


def _scene() -> Scene:
    return Scene(
        artifact_id="scene-room",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-scene-room",
        source_provenance=(
            {
                "kind": "user_input",
                "reference": "fixture",
            },
        ),
        scene_id="room",
        location="lab",
        time="night",
        mood="tense",
        participant_ids=("hero",),
        continuity_constraints=("preserve screen direction",),
        visual_reference_asset_ids=("reference-room",),
    )


def _shot() -> Shot:
    return Shot(
        artifact_id="artifact-shot-1",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-shot-1",
        source_provenance=(
            {
                "kind": "user_input",
                "reference": "fixture",
            },
        ),
        shot_id="shot-1",
        scene_id="room",
        storyboard_beat_id="beat-1",
        intent="Hero enters the lab.",
        duration_policy={"mode": "fixed", "seconds": 3},
        character_ids=("hero",),
        continuity_constraints=(),
        visual_strategy="static_image",
        required_asset_roles=(),
        motion_directives=(),
    )


def _intent_evidence(shot: Shot | None = None) -> dict[str, str]:
    target = shot or _shot()
    return {
        "target_shot_id": target.shot_id,
        "target_shot_content_hash": target.content_hash,
    }


def _asset(role: str = "first_frame", asset_id: str = "frame-shot-1") -> AssetEvidence:
    return AssetEvidence(
        role=SemanticReferenceRole(role),
        asset_id=asset_id,
        asset_sha256="1" * 64,
        canonical_owner_id="shot-1",
        mime_type="image/png",
        width=1920,
        height=1080,
        size_bytes=1024,
    )


def _requirement_kwargs(
    *,
    shot: Shot | None = None,
    review_hash: str | None = None,
) -> dict[str, object]:
    target = shot or _shot()
    intent = GenerationIntent(
        open_state=TypedStateReference(
            kind=ContinuityStateKind.UNSPECIFIED,
            state_ref=None,
            state_text=None,
            state_hash=None,
        ),
        close_state=TypedStateReference(
            kind=ContinuityStateKind.UNSPECIFIED,
            state_ref=None,
            state_text=None,
            state_hash=None,
        ),
        identity_continuity=IdentityContinuity(
            character_ids=("hero",),
            preservation=IdentityPreservation.EXACT,
        ),
        scene_continuity=SceneContinuity(scene_id="room"),
        space_continuity=SpaceContinuity(
            subject_position="center",
            screen_direction="screen_left",
            crossing_policy=UNSPECIFIED,
        ),
        axis_continuity=AxisContinuity(
            camera_axis="neutral",
            crossing_policy=UNSPECIFIED,
        ),
        subject_action=SubjectAction(
            start_state="hero-stands",
            progression="hero-walks",
            endpoint=ActionEndpoint(
                state_ref="hero-sits",
                required_change=True,
            ),
        ),
        motion_envelope=MotionEnvelope(
            onset="ease_in",
            peak="midpoint",
            settle="ease_out",
            direction="forward",
            amplitude_class="medium",
        ),
        pacing=Pacing(cadence="medium", tempo_class="normal"),
        camera_intent=CameraIntent(
            movement="locked",
            stability="locked",
            framing_intent="medium_shot",
            expression_strength=ExpressionStrength.NATIVE_CONTROL_REQUIRED,
        ),
        camera_endpoint=CameraEndpoint(
            start_framing="medium_shot",
            end_framing="medium_shot",
            position_lock=True,
            orientation_lock=True,
        ),
    )
    review_link = (
        ReviewEvidenceLink(
            evidence_ref="review-evidence-1",
            target_shot_id=target.shot_id,
            target_shot_content_hash=target.content_hash,
            review_decision_hash=review_hash or ("a" * 64),
        )
        if review_hash is not None or True
        else None
    )
    return {
        "contract_version": "provider-neutral-video-requirement/1",
        "source_request_content_hash": "f" * 64,
        "target_shot": target,
        "scene": _scene(),
        "characters": (_character(),),
        "intent_evidence_hash": canonical_sha256(_intent_evidence(target)),
        "generation_intent": intent,
        "generation_intent_hash": canonical_sha256(intent.model_dump(mode="json")),
        "review_evidence": review_link,
        "asset_evidence": (_asset(),),
        "generation_mode": GenerationMode.REFERENCE_TO_VIDEO,
        "continuity_mode": ContinuityMode.REFERENCE,
        "motion_requirement": MotionRequirement.CHARACTER_ACTION,
        "semantic_reference_roles": (
            SemanticReferenceRole("first_frame"),
        ),
        "capability_need": CapabilityNeed(
            needs_first_frame=True,
            needs_continuity_state=True,
        ),
        "output_need": OutputNeed(
            timing_mode="fixed",
            duration_seconds=3.0,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        "audio_need": AudioNeed.OPTIONAL,
        "quality_need": QualityNeed(
            objective_tier="production",
            minimum_raster="720p",
            minimum_codec="h264",
            native_enforcement_required=True,
        ),
    }


def test_t1_requirement_models_are_strict_and_extra_forbidden():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    payload = requirement.model_dump(mode="python")
    payload["unexpected_field"] = "no"

    with pytest.raises(ValidationError, match="extra"):
        ProviderNeutralVideoRequirement.model_validate(payload)


def test_t1_requirement_models_are_frozen_and_hash_typed():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    with pytest.raises(ValidationError, match="frozen"):
        requirement.source_request_content_hash = "0" * 64

    tampered = requirement.model_dump(mode="python")
    tampered["source_request_content_hash"] = "0" * 64
    with pytest.raises(ValidationError, match="requirement_hash"):
        ProviderNeutralVideoRequirement.model_validate(tampered)

    unsealed = requirement.model_dump(mode="python")
    unsealed["requirement_hash"] = "0" * 64
    with pytest.raises(ValidationError, match="requirement_hash"):
        ProviderNeutralVideoRequirement.model_validate(unsealed)


def test_c4_absence_preserves_v1_requirement_contract_and_hash_payload():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    assert requirement.contract_version == "provider-neutral-video-requirement/1"
    assert requirement.requirement_hash == (
        "e4e5efaaf1cc0a493b7484d06233bed3bf499fd1fddca9290f9671aa90b8f272"
    )
    assert "c4_multi_anchor_binding" not in requirement._hash_payload()


def test_historical_generation_intent_projection_hash_stays_bit_for_bit() -> None:
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())
    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=requirement.generation_intent,
        output_need=requirement.output_need,
        audio_need=requirement.audio_need,
        quality_need=requirement.quality_need,
        semantic_reference_roles=requirement.semantic_reference_roles,
    )

    assert projection.projection_hash == (
        "178edc3e5fe695df9060b4b4bb06b199eed5e5f6253e2f7bdd2917380d54751e"
    )
    assert "camera_motion" not in projection.model_dump(mode="json")[
        "generation_intent"
    ]


@pytest.mark.parametrize(
    ("semantic_roles", "media_asset_ids"),
    [
        ((SemanticReferenceRole.IDENTITY,), ()),
        ((), ("reference-video-1",)),
    ],
)
def test_explicit_text_to_video_projection_rejects_media_references(
    semantic_roles: tuple[SemanticReferenceRole, ...],
    media_asset_ids: tuple[str, ...],
) -> None:
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    with pytest.raises(ValidationError, match="cannot carry media reference"):
        ProviderNeutralGenerationIntentProjection.create(
            generation_intent=requirement.generation_intent,
            generation_operation=GenerationOperation.TEXT_TO_VIDEO,
            output_need=requirement.output_need,
            audio_need=requirement.audio_need,
            quality_need=requirement.quality_need,
            semantic_reference_roles=semantic_roles,
            media_reference_asset_ids=media_asset_ids,
        )


def test_explicit_rich_text_to_video_projection_requires_no_conditioning() -> None:
    payload = _v4_requirement_kwargs()

    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=payload["generation_intent"],
        generation_operation=GenerationOperation.TEXT_TO_VIDEO,
        conditioning_compatibility=None,
        output_need=payload["output_need"],
        audio_need=payload["audio_need"],
        quality_need=payload["quality_need"],
        semantic_reference_roles=(),
        media_reference_asset_ids=(),
    )

    assert projection.generation_intent.primary_camera_motion is not None
    assert projection.conditioning_compatibility is None
    assert "conditioning_compatibility" not in projection.model_dump(mode="json")


def _v4_requirement_kwargs() -> dict[str, object]:
    from tests.test_production_video_intent_validation import (
        _compatible_fl2va,
        _complete_intent,
    )

    payload = _requirement_kwargs()
    payload.pop("contract_version")
    intent = _complete_intent().model_copy(
        update={"pacing": Pacing(shot_duration_seconds=3.0)}
    )
    payload["generation_intent"] = intent
    payload["conditioning_compatibility"] = _compatible_fl2va().model_copy(
        update={
            "lane": ConditioningLane.I2VA,
            "first_anchor_id": "frame-shot-1",
            "last_anchor_id": None,
            "available_duration_seconds": 3.0,
        }
    )
    payload["generation_mode"] = GenerationMode.IMAGE_TO_VIDEO
    payload["generation_intent_hash"] = canonical_sha256(
        {
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }
    )
    return payload


def test_camera_motion_contract_is_singular_and_versioned_under_v4() -> None:
    payload = _v4_requirement_kwargs()
    intent = payload["generation_intent"]

    requirement = ProviderNeutralVideoRequirement.create(**payload)

    assert requirement.contract_version == "provider-neutral-video-requirement/4"
    assert requirement.generation_intent.primary_camera_motion == (
        intent.primary_camera_motion
    )
    assert requirement.requirement_hash == canonical_sha256(requirement._hash_payload())


def test_v4_generation_modes_enforce_conditioning_and_reference_boundaries() -> None:
    payload = _v4_requirement_kwargs()
    payload["conditioning_compatibility"] = None

    with pytest.raises(ValidationError, match="conditioning_compatibility"):
        ProviderNeutralVideoRequirement.create(**payload)

    payload = _v4_requirement_kwargs()
    payload.update(
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        conditioning_compatibility=None,
    )
    with pytest.raises(ValidationError, match="asset_evidence"):
        ProviderNeutralVideoRequirement.create(**payload)

    payload.update(
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
        continuity_mode=ContinuityMode.EXACT_TERMINAL,
    )
    with pytest.raises(ValidationError, match="continuity_mode"):
        ProviderNeutralVideoRequirement.create(**payload)

    payload.update(
        continuity_mode=ContinuityMode.SEMANTIC,
        capability_need=CapabilityNeed(needs_first_frame=True),
    )
    with pytest.raises(ValidationError, match="capability_need.needs_first_frame"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_v4_text_to_video_requires_no_conditioning_evidence() -> None:
    payload = _v4_requirement_kwargs()
    payload.update(
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )

    requirement = ProviderNeutralVideoRequirement.create(**payload)

    assert requirement.contract_version == "provider-neutral-video-requirement/4"
    assert requirement.generation_mode is GenerationMode.TEXT_TO_VIDEO
    assert requirement.conditioning_compatibility is None

    payload["conditioning_compatibility"] = _v4_requirement_kwargs()[
        "conditioning_compatibility"
    ]
    with pytest.raises(ValidationError, match="conditioning_compatibility"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_v4_conditioning_rejects_anchor_identity_or_duration_drift() -> None:
    payload = _v4_requirement_kwargs()
    evidence = payload["conditioning_compatibility"]
    payload["conditioning_compatibility"] = evidence.model_copy(
        update={"first_anchor_id": "different-anchor"}
    )
    with pytest.raises(ValidationError, match="first_anchor_id"):
        ProviderNeutralVideoRequirement.create(**payload)

    payload = _v4_requirement_kwargs()
    evidence = payload["conditioning_compatibility"]
    payload["conditioning_compatibility"] = evidence.model_copy(
        update={"available_duration_seconds": 4.0}
    )
    with pytest.raises(ValidationError, match="duration"):
        ProviderNeutralVideoRequirement.create(**payload)


def _scale_transition_requirement_kwargs() -> dict[str, object]:
    from tests.test_production_video_intent_validation import _compatible_fl2va, _scale_transition

    payload = _v4_requirement_kwargs()
    intent = payload["generation_intent"]
    payload.update(
        generation_mode=GenerationMode.FIRST_LAST_FRAME_VIDEO,
        asset_evidence=(_asset(asset_id="anchor-first"),
                        _asset("last_frame", "anchor-last").model_copy(update={"asset_sha256": "2" * 64})),
        semantic_reference_roles=(SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.LAST_FRAME),
        capability_need=CapabilityNeed(needs_first_frame=True, needs_last_frame=True),
        conditioning_compatibility=_compatible_fl2va().model_copy(update={
            "same_subject_scale": False, "available_duration_seconds": 3.0,
            "scale_transition": _scale_transition(intent),
        }),
    )
    return payload


def test_scale_transition_roundtrips_through_projection_and_exact_requirement() -> None:
    requirement = ProviderNeutralVideoRequirement.create(**_scale_transition_requirement_kwargs())
    projection = ProviderNeutralGenerationIntentProjection.create(
        generation_intent=requirement.generation_intent,
        conditioning_compatibility=requirement.conditioning_compatibility,
        output_need=requirement.output_need,
        audio_need=requirement.audio_need,
        quality_need=requirement.quality_need,
    )
    assert ProviderNeutralVideoRequirement.model_validate_json(requirement.model_dump_json()) == requirement
    assert ProviderNeutralGenerationIntentProjection.model_validate_json(projection.model_dump_json()) == projection
    assert projection.conditioning_compatibility.same_subject_scale is False
    assert requirement.conditioning_compatibility.scale_transition.content_hash


@pytest.mark.parametrize("position,field,value", [
    (0, "asset_sha256", "3" * 64), (1, "asset_sha256", "3" * 64),
    (0, "asset_id", "wrong-first"), (1, "asset_id", "wrong-last"),
    (1, "width", 1280),
])
def test_scale_transition_checks_actual_anchor_evidence(position, field, value) -> None:
    payload = _scale_transition_requirement_kwargs()
    assets = list(payload["asset_evidence"])
    assets[position] = assets[position].model_copy(update={field: value})
    payload["asset_evidence"] = tuple(assets)
    with pytest.raises(ValidationError, match="anchor"):
        ProviderNeutralVideoRequirement.create(**payload)


@pytest.mark.parametrize("drift", ["camera", "duration", "anchor_ids", "copied_hash", "none_scale"])
def test_scale_transition_projection_and_requirement_reject_stale_binding(drift) -> None:
    from ai_video.production._conditioning_scale_transition import ScaleTransitionEvidence

    payload = _scale_transition_requirement_kwargs()
    evidence = payload["conditioning_compatibility"]
    extension = evidence.scale_transition
    if drift == "camera":
        payload["generation_intent"] = payload["generation_intent"].model_copy(update={
            "camera_endpoint": CameraEndpoint(start_framing="different", end_framing="different"),
        })
    elif drift == "duration":
        payload["output_need"] = payload["output_need"].model_copy(update={"duration_seconds": 4.0})
    elif drift == "anchor_ids":
        data = extension.model_dump(exclude={"content_hash"})
        data["first_anchor_id"] = "different-first"
        extension = ScaleTransitionEvidence.create(**data)
    elif drift == "copied_hash":
        extension = extension.model_copy(update={"last_anchor_sha256": "4" * 64})
    else:
        evidence = evidence.model_copy(update={"same_subject_scale": None})
    payload["conditioning_compatibility"] = evidence.model_copy(update={"scale_transition": extension})
    with pytest.raises(ValidationError, match="conditioning|scale_transition"):
        ProviderNeutralGenerationIntentProjection.create(
            generation_intent=payload["generation_intent"],
            conditioning_compatibility=payload["conditioning_compatibility"],
            output_need=payload["output_need"], audio_need=payload["audio_need"],
            quality_need=payload["quality_need"],
        )
    with pytest.raises(ValidationError):
        ProviderNeutralVideoRequirement.create(**payload)


def test_legacy_v4_requirement_hash_is_unchanged() -> None:
    # A legacy v4 requirement predates reference planning; it must reopen unchanged.
    payload = _v4_requirement_kwargs()
    intent = payload["generation_intent"].model_copy(update={"reference_planning": None})
    payload["generation_intent"] = intent
    payload["generation_intent_hash"] = canonical_sha256({
        "schema": "provider-neutral-generation-intent/2",
        "generation_intent": intent.model_dump(mode="json"),
    })
    requirement = ProviderNeutralVideoRequirement.create(**payload)
    assert requirement.requirement_hash == "e410378982624bb058447a4d8cf5d969b7d73bdb1335a06494d6b023da1fe243"


def test_scale_transition_locked_camera_rejects_even_resealed_all_pass_review() -> None:
    from tests.test_production_video_intent_validation import _scale_transition

    payload = _scale_transition_requirement_kwargs()
    intent = payload["generation_intent"].model_copy(update={
        "primary_camera_motion": CameraMotionContract(
            movement_kind=CameraMovementKind.LOCKED, direction="none",
            amplitude_class=CameraAmplitudeClass.SUBTLE, speed_class=CameraSpeedClass.VERY_SLOW,
            start_motion_state=CameraMotionStartState.STATIONARY,
            end_motion_state=CameraMotionEndState.SETTLED,
        ),
    })
    evidence = payload["conditioning_compatibility"].model_copy(update={
        "scale_transition": _scale_transition(intent),
    })
    with pytest.raises(ValidationError, match="scale_transition.primary_camera_motion"):
        ProviderNeutralGenerationIntentProjection.create(
            generation_intent=intent, conditioning_compatibility=evidence,
            output_need=payload["output_need"], audio_need=payload["audio_need"],
            quality_need=payload["quality_need"],
        )
    payload.update(generation_intent=intent, conditioning_compatibility=evidence,
                   generation_intent_hash=canonical_sha256({
                       "schema": "provider-neutral-generation-intent/2",
                       "generation_intent": intent.model_dump(mode="json"),
                   }))
    with pytest.raises(ValidationError, match="scale_transition.primary_camera_motion"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_locked_camera_requires_stationary_to_settled() -> None:
    with pytest.raises(ValidationError, match="locked camera"):
        CameraMotionContract(
            movement_kind=CameraMovementKind.LOCKED,
            direction="none",
            amplitude_class=CameraAmplitudeClass.SUBTLE,
            speed_class=CameraSpeedClass.VERY_SLOW,
            start_motion_state=CameraMotionStartState.IN_MOTION,
            end_motion_state=CameraMotionEndState.SETTLED,
        )


def test_camera_movement_rejects_contradictory_direction() -> None:
    with pytest.raises(ValidationError, match="pan_left camera requires left"):
        CameraMotionContract(
            movement_kind=CameraMovementKind.PAN_LEFT,
            direction="right",
            amplitude_class=CameraAmplitudeClass.SUBTLE,
            speed_class=CameraSpeedClass.SLOW,
            start_motion_state=CameraMotionStartState.STATIONARY,
            end_motion_state=CameraMotionEndState.SETTLED,
        )


def test_locked_camera_rejects_noncanonical_motion_strength() -> None:
    with pytest.raises(ValidationError, match="canonical subtle/very_slow"):
        CameraMotionContract(
            movement_kind=CameraMovementKind.LOCKED,
            direction="none",
            amplitude_class=CameraAmplitudeClass.PRONOUNCED,
            speed_class=CameraSpeedClass.FAST,
            start_motion_state=CameraMotionStartState.STATIONARY,
            end_motion_state=CameraMotionEndState.SETTLED,
        )


def test_v4_rejects_camera_only_intent_without_rich_upstream_owners() -> None:
    payload = _requirement_kwargs()
    payload.pop("contract_version")
    payload["generation_intent"] = payload["generation_intent"].model_copy(
        update={
            "primary_camera_motion": CameraMotionContract(
                movement_kind=CameraMovementKind.LOCKED,
                direction="none",
                amplitude_class=CameraAmplitudeClass.SUBTLE,
                speed_class=CameraSpeedClass.VERY_SLOW,
                start_motion_state=CameraMotionStartState.STATIONARY,
                end_motion_state=CameraMotionEndState.SETTLED,
            )
        }
    )

    with pytest.raises(ValidationError, match="complete rich generation intent"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_locked_camera_rejects_reveal_relation_as_second_motion() -> None:
    with pytest.raises(ValidationError, match="locked camera relation"):
        GenerationIntent(
            primary_camera_motion=CameraMotionContract(
                movement_kind=CameraMovementKind.LOCKED,
                direction="none",
                amplitude_class=CameraAmplitudeClass.SUBTLE,
                speed_class=CameraSpeedClass.VERY_SLOW,
                start_motion_state=CameraMotionStartState.STATIONARY,
                end_motion_state=CameraMotionEndState.SETTLED,
            ),
            camera_subject_relation=CameraSubjectRelation(
                subject_id="hero",
                relation_kind=CameraSubjectRelationKind.REVEAL,
                start_relation="subject obscured",
                end_relation="subject revealed",
            ),
        )


@pytest.mark.parametrize(
    "relation_text",
    (
        "orbit left around subject",
        "pan right while following",
        "crane upward independently",
    ),
)
def test_camera_subject_relation_rejects_secondary_camera_motion(
    relation_text: str,
) -> None:
    with pytest.raises(ValidationError, match="secondary camera motion"):
        CameraSubjectRelation(
            subject_id="hero",
            relation_kind=CameraSubjectRelationKind.FOLLOW,
            start_relation="stable medium offset",
            end_relation=relation_text,
        )


def test_multi_anchor_requirement_fails_closed_without_c4_binding():
    payload = _requirement_kwargs()
    payload["continuity_mode"] = ContinuityMode.MULTI_ANCHOR

    with pytest.raises(ValidationError, match="multi-anchor continuity"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_c4_requirement_seals_exact_motion_anchors_under_v2_contract():
    from test_production_video import _c4_binding

    binding = _c4_binding(tier="motion_boundary")
    target = _shot().model_copy(
        update={
            "shot_id": "shot-001",
            "artifact_id": "shot-001-artifact",
            "revision": 3,
            "content_hash": "a" * 64,
        }
    )
    character = _character().model_copy(
        update={
            "artifact_id": "character-001",
            "revision": 3,
            "content_hash": "c" * 64,
        }
    )
    tail = binding.motion_tail
    assert tail is not None
    evidence = (
        AssetEvidence(
            role=SemanticReferenceRole.CONTINUITY_TERMINAL,
            asset_id=binding.terminal.extracted_asset_id,
            asset_sha256=binding.terminal.extracted_sha256,
            mime_type=binding.terminal.extracted_mime_type,
            width=binding.terminal.extracted_width,
            height=binding.terminal.extracted_height,
            size_bytes=binding.terminal.extracted_size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.IDENTITY,
            asset_id=binding.identity_anchor.asset_id,
            asset_sha256=binding.identity_anchor.asset_sha256,
            mime_type=binding.identity_anchor.asset_mime_type,
            width=binding.identity_anchor.asset_width,
            height=binding.identity_anchor.asset_height,
            size_bytes=binding.identity_anchor.asset_size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.APPROVED_ENDPOINT,
            asset_id=binding.approved_endpoint.asset_id,
            asset_sha256=binding.approved_endpoint.asset_sha256,
            mime_type=binding.approved_endpoint.asset_mime_type,
            width=binding.approved_endpoint.asset_width,
            height=binding.approved_endpoint.asset_height,
            size_bytes=binding.approved_endpoint.asset_size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.CONTINUITY_MOTION_TAIL,
            asset_id=tail.extracted_asset_id,
            asset_sha256=tail.extracted_sha256,
            mime_type=tail.extracted_mime_type,
            width=tail.extracted_width,
            height=tail.extracted_height,
            size_bytes=tail.extracted_size_bytes,
            duration_millis=tail.extracted_duration_milliseconds,
            fps=tail.extracted_fps_numerator // tail.extracted_fps_denominator,
        ),
    )

    requirement = ProviderNeutralVideoRequirement.create(
        source_request_content_hash="f" * 64,
        intent_evidence_hash="e" * 64,
        generation_intent_hash=canonical_sha256(
            GenerationIntent().model_dump(mode="json")
        ),
        target_shot=target,
        scene=_scene(),
        characters=(character,),
        asset_evidence=evidence,
        c4_multi_anchor_binding=binding,
        generation_mode=GenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=ContinuityMode.MULTI_ANCHOR,
        motion_requirement=MotionRequirement.CHARACTER_ACTION,
        generation_intent=GenerationIntent(),
        semantic_reference_roles=tuple(item.role for item in evidence),
    )

    assert requirement.contract_version == "provider-neutral-video-requirement/2"
    assert requirement.c4_multi_anchor_binding == binding
    assert requirement.requirement_hash == canonical_sha256(requirement._hash_payload())

    payload = requirement.model_dump(
        mode="python", exclude={"requirement_id", "requirement_hash"}
    )
    payload["characters"] = (
        character.model_copy(update={"artifact_id": "different-character-artifact"}),
    )
    with pytest.raises(ValidationError, match="identity anchor"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_t1_requirement_hash_is_deterministic_for_same_input():
    first = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())
    second = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    assert first.requirement_hash == second.requirement_hash
    assert first.requirement_id == second.requirement_id
    assert first == second


def test_dialogue_language_is_sealed_without_rehashing_historical_missing_field() -> None:
    historical = DialogueIntent(
        mode="dialogue",
        speaker_id="hero",
        verbatim_text="Hello.",
        start_seconds=0.5,
        end_seconds=1.5,
        on_screen=True,
        response_obligation="listener attends",
    )
    historical_intent = GenerationIntent(dialogue_intent=historical)

    historical_dump = historical_intent.model_dump(mode="json")
    assert "language" not in historical_dump["dialogue_intent"]
    assert canonical_sha256(historical_dump) == (
        "077e9b41fd5109d96e12bf014ba3c511b01be0ea3e9d20dde4bb0ababf614053"
    )

    payload = _requirement_kwargs()
    payload["generation_intent"] = historical_intent
    payload["generation_intent_hash"] = canonical_sha256(
        historical_intent.model_dump(mode="json")
    )
    historical_requirement = ProviderNeutralVideoRequirement.create(**payload)
    assert (
        ProviderNeutralVideoRequirement.model_validate_json(
            historical_requirement.model_dump_json()
        )
        == historical_requirement
    )

    sealed = historical.model_copy(update={"language": "en-US"})
    sealed_dump = GenerationIntent(dialogue_intent=sealed).model_dump(mode="json")
    assert sealed_dump["dialogue_intent"]["language"] == "en-US"

    with pytest.raises(ValidationError, match="none dialogue boundary"):
        DialogueIntent(mode="none", language="en-US")


def test_conversation_preserves_ordered_speakers_without_dialogue_timestamps():
    dialogue = DialogueIntent.model_validate({
        "mode": "conversation", "language": "zh",
        "turns": [
            {"speaker_id": "clerk", "verbatim_text": "慢点，里面烫。",
             "on_screen": True, "lip_sync_required": True,
             "response_obligation": "顾客听见后收手。"},
            {"speaker_id": "linxu", "verbatim_text": "谢了。袋子不用。",
             "on_screen": True, "lip_sync_required": True,
             "response_obligation": "店员听完才抽纸。"},
        ],
    })
    payload = GenerationIntent(dialogue_intent=dialogue).model_dump(mode="json")
    assert payload["dialogue_intent"] == {
        "mode": "conversation", "language": "zh",
        "turns": [
            {"speaker_id": "clerk", "verbatim_text": "慢点，里面烫。",
             "on_screen": True, "lip_sync_required": True,
             "response_obligation": "顾客听见后收手。"},
            {"speaker_id": "linxu", "verbatim_text": "谢了。袋子不用。",
             "on_screen": True, "lip_sync_required": True,
             "response_obligation": "店员听完才抽纸。"},
        ],
    }
    assert GenerationIntent.model_validate(payload).dialogue_intent == dialogue


@pytest.mark.parametrize("fault", ("timing", "scalar", "empty", "missing-language", "turn-time", "blank-text"))
def test_conversation_rejects_ambiguous_or_timed_turns(fault):
    data = {"mode": "conversation", "language": "zh", "turns": [
        {"speaker_id": "hero", "verbatim_text": "谢了。", "on_screen": True,
         "lip_sync_required": True, "response_obligation": "对方倾听。"}]}
    if fault == "timing":
        data.update(start_seconds=0, end_seconds=8)
    elif fault == "scalar":
        data["speaker_id"] = "hero"
    elif fault == "empty":
        data["turns"] = []
    elif fault == "missing-language":
        data.pop("language")
    elif fault == "turn-time":
        data["turns"][0]["start_seconds"] = 1
    else:
        data["turns"][0]["verbatim_text"] = "  "
    with pytest.raises(ValidationError):
        DialogueIntent.model_validate(data)


@pytest.mark.parametrize("fault", ("unknown-speaker", "no-audio", "offscreen-lips"))
def test_conversation_keeps_speaker_and_audio_boundaries(fault):
    turn = {"speaker_id": "hero", "verbatim_text": "谢了。", "on_screen": True,
            "lip_sync_required": True, "response_obligation": "对方倾听。"}
    if fault == "unknown-speaker":
        turn["speaker_id"] = "unregistered"
    elif fault == "offscreen-lips":
        turn["on_screen"] = False
    payload = _requirement_kwargs()
    if fault == "no-audio":
        payload["audio_need"] = AudioNeed.FORBIDDEN
    with pytest.raises(ValidationError):
        intent = GenerationIntent(dialogue_intent=DialogueIntent.model_validate({
            "mode": "conversation", "language": "zh", "turns": [turn]}))
        payload["generation_intent"] = intent
        payload["generation_intent_hash"] = canonical_sha256(intent.model_dump(mode="json"))
        ProviderNeutralVideoRequirement.create(**payload)


@pytest.mark.parametrize("language", ("zh-Hans-CN", "es-419"))
def test_dialogue_language_accepts_canonical_core_tags(language: str) -> None:
    assert DialogueIntent(
        mode="dialogue",
        language=language,
        speaker_id="hero",
        verbatim_text="Exact speech.",
        start_seconds=0.5,
        end_seconds=1.5,
        on_screen=True,
        response_obligation="listener attends",
    ).language == language


@pytest.mark.parametrize(
    "language",
    (
        "EN-US",
        "en-US-u-ca-gregory",
        "en-12",
        "en-ABCDE",
        "en-abcde-abcde",
    ),
)
def test_dialogue_language_rejects_noncanonical_or_extended_tags(language: str) -> None:
    with pytest.raises(ValidationError, match="language"):
        DialogueIntent(
            mode="dialogue",
            language=language,
            speaker_id="hero",
            verbatim_text="Exact speech.",
            start_seconds=0.5,
            end_seconds=1.5,
            on_screen=True,
            response_obligation="listener attends",
        )


def test_t1_requirement_rejects_non_nfc_nested_text() -> None:
    payload = _requirement_kwargs()
    intent = payload["generation_intent"]
    assert isinstance(intent, GenerationIntent)
    payload["generation_intent"] = intent.model_copy(
        update={
            "subject_action": intent.subject_action.model_copy(
                update={"progression": "cafe\N{COMBINING ACUTE ACCENT}"}
            )
        }
    )

    with pytest.raises(ValidationError, match="Unicode NFC"):
        ProviderNeutralVideoRequirement.create(**payload)


def test_t1_requirement_id_derives_from_hash_and_excludes_itself():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    assert requirement.requirement_id == (
        f"video-requirement-{requirement.requirement_hash[:24]}"
    )

    payload = requirement.model_dump(mode="python")
    payload["requirement_id"] = "video-requirement-arbitrary"
    with pytest.raises(ValidationError, match="requirement_id"):
        ProviderNeutralVideoRequirement.model_validate(payload)


def test_t1_requirement_recursively_rejects_provider_workflow_prompt_fields():
    payload = _requirement_kwargs()
    requirement = ProviderNeutralVideoRequirement.create(**payload)
    dumped = requirement.model_dump(mode="python")

    forbidden_paths = (
        ("provider_name",),
        ("model_id",),
        ("endpoint_id",),
        ("profile_id",),
        ("workflow_hash",),
        ("prompt_text",),
        ("payload",),
        ("skill_name",),
        ("asset_uri",),
        ("permit_id",),
        ("fallback_order",),
    )

    def _contains(d: object, path: tuple[str, ...]) -> bool:
        if not path:
            return True
        head, *rest = path
        if not isinstance(d, dict):
            return False
        if head not in d:
            return False
        return _contains(d[head], tuple(rest))

    for path in forbidden_paths:
        assert not _contains(dumped, path), (
            f"forbidden path {path!r} leaked into requirement payload"
        )


def test_t1_requirement_create_rejects_provider_field_blobs():
    payload = _requirement_kwargs()
    payload["generation_mode"] = GenerationMode.REFERENCE_TO_VIDEO

    requirement = ProviderNeutralVideoRequirement.create(**payload)

    assert getattr(requirement, "provider_name", None) is None
    assert getattr(requirement, "prompt_text", None) is None


def test_t1_requirement_contract_version_is_exactly_one():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    assert requirement.contract_version == "provider-neutral-video-requirement/1"


def test_t1_requirement_assets_bind_to_typed_reference_roles():
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())

    asset_ids = {asset.asset_id for asset in requirement.asset_evidence}
    assert "frame-shot-1" in asset_ids


def test_t1_requirement_does_not_import_planning_or_router_or_lifecycle():
    import ai_video.production.video_requirement as module

    source = getattr(module, "__file__", "")
    assert source.endswith("video_requirement.py")

    forbidden_prefixes = (
        "ai_video.planning",
        "ai_video.production.shot_router",
        "ai_video.production.video",
        "ai_video.production.video_generation",
        "ai_video.production.state_commit",
        "ai_video.production.composition",
        "ai_video.production.hyperframes",
        "ai_video.cli",
    )

    for name in dir(module):
        value = getattr(module, name, None)
        if not hasattr(value, "__module__"):
            continue
        origin = getattr(value, "__module__", "")
        assert not any(
            origin == prefix or origin.startswith(f"{prefix}.")
            for prefix in forbidden_prefixes
        ), (
            f"{name} imported from forbidden origin {origin}"
        )


def test_t1_requirement_exposes_no_io_or_provider_helpers():
    import ai_video.production.video_requirement as module

    forbidden_tokens = (
        "subprocess",
        "httpx",
        "requests",
        "keyring",
        "higgsfield",
        "hell_grind",
        "video_shotcraft",
        "seedance",
        "hailuo",
        "comfy",
    )

    for token in forbidden_tokens:
        assert token not in module.__dict__


def test_t1_requirement_unspecified_kind_is_not_silently_inferred():
    payload = _requirement_kwargs()
    requirement = ProviderNeutralVideoRequirement.create(**payload)

    assert requirement.generation_intent.open_state.kind is ContinuityStateKind.UNSPECIFIED
    assert requirement.generation_intent.close_state.kind is ContinuityStateKind.UNSPECIFIED


def test_t1_typed_state_and_action_endpoint_reject_ambiguous_payloads():
    with pytest.raises(ValidationError, match="exactly one"):
        TypedStateReference(
            kind=ContinuityStateKind.TYPED_REF,
            state_ref="state-1",
            state_text="duplicate state",
        )
    with pytest.raises(ValidationError, match="at most one"):
        ActionEndpoint(
            state_ref="state-1",
            state_hash="a" * 64,
        )


def test_t1_requirement_evidence_hash_changes_when_evidence_identity_changes():
    base = _requirement_kwargs()
    first = ProviderNeutralVideoRequirement.create(**base)

    payload = dict(base)
    payload["source_request_content_hash"] = "e" * 64
    second = ProviderNeutralVideoRequirement.create(**payload)

    assert first.requirement_hash != second.requirement_hash
    assert first.source_request_content_hash != second.source_request_content_hash


def test_t1_requirement_cycle_neutral_module_can_be_imported_by_planning():
    import ai_video.production.video_requirement as requirement_module

    assert hasattr(requirement_module, "ProviderNeutralVideoRequirement")
    assert not hasattr(requirement_module, "VideoPlanningRequest")


def test_t1_verified_projection_seals_requirement_and_verified_lineage():
    import ai_video.production.video_requirement as requirement_module

    projection_type = getattr(
        requirement_module,
        "VerifiedGenerationRequirementProjection",
        None,
    )
    assert projection_type is not None
    requirement = ProviderNeutralVideoRequirement.create(**_requirement_kwargs())
    projection = projection_type.create(
        requirement=requirement,
        plan_hash="a" * 64,
        verified_source_request_content_hash=requirement.source_request_content_hash,
        target_shot_id=requirement.target_shot.shot_id,
        target_shot_revision=requirement.target_shot.revision,
        target_shot_content_hash=requirement.target_shot.content_hash,
    )

    assert projection.requirement == requirement
    assert len(projection.projection_hash) == 64
    tampered = projection.model_dump(mode="python")
    tampered["target_shot_content_hash"] = "b" * 64
    with pytest.raises(ValidationError, match="lineage"):
        projection_type.model_validate(tampered)


def test_t2_generation_intent_projection_seals_typed_neutral_inputs():
    import ai_video.production.video_requirement as requirement_module

    projection_type = getattr(
        requirement_module,
        "ProviderNeutralGenerationIntentProjection",
        None,
    )
    assert projection_type is not None
    values = _requirement_kwargs()
    projection = projection_type.create(
        generation_intent=values["generation_intent"],
        semantic_reference_roles=(SemanticReferenceRole.VIDEO_REFERENCE,),
        media_reference_asset_ids=("video-b", "video-a"),
        output_need=values["output_need"],
        audio_need=values["audio_need"],
        quality_need=values["quality_need"],
    )

    assert len(projection.projection_hash) == 64
    assert projection.media_reference_asset_ids == ("video-a", "video-b")
    tampered = projection.model_dump(mode="python")
    tampered["audio_need"] = AudioNeed.REQUIRED
    with pytest.raises(ValidationError, match="projection_hash"):
        projection_type.model_validate(tampered)


def test_new_attempt_request_construction_has_one_compiler_owner():
    production_root = Path(__file__).parents[1] / "src/ai_video/production"
    owners = {
        path.name
        for path in production_root.glob("*.py")
        if re.search(
            r"(?<!Resolved)VideoGenerationRequest\.create\(",
            path.read_text(encoding="utf-8"),
        )
    }

    assert owners == {"video_compiler.py"}


def test_retired_plan_hint_bypass_is_absent_from_runtime_source():
    source_root = Path(__file__).parents[1] / "src"

    assert all(
        "plan_hint" not in path.read_text(encoding="utf-8")
        for path in source_root.rglob("*.py")
    )
