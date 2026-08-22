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
    CameraEndpoint,
    CameraIntent,
    CapabilityNeed,
    ContinuityMode,
    ContinuityStateKind,
    ExpressionStrength,
    GenerationIntent,
    GenerationMode,
    IdentityContinuity,
    IdentityPreservation,
    MotionEnvelope,
    MotionRequirement,
    OutputGeometryPolicy,
    OutputNeed,
    Pacing,
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
    assert "c4_multi_anchor_binding" not in requirement._hash_payload()


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
