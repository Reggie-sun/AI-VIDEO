from __future__ import annotations

from pydantic import ValidationError
import pytest

from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    DurationPolicy,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    Shot,
    SourceReference,
    VisualStrategy,
)
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    ContinuityMode,
    MotionRequirement,
    RouterAssetIdentity,
    RouterContinuityState,
    RouterPolicyIdentity,
    RouterReasonCode,
    RoutingOutcome,
    ShotRoutingContext,
    ShotVisualResolver,
    VideoGenerationLifecycleEnvelope,
    VideoGenerationResolver,
    VideoRoutingPolicy,
)
from ai_video.production.video_requirement import (
    AudioNeed,
    CapabilityNeed,
    ContinuityMode as RequirementContinuityMode,
    ExpressionStrength,
    GenerationIntent,
    GenerationMode as RequirementGenerationMode,
    MotionRequirement as RequirementMotionRequirement,
    OutputNeed,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    VerifiedGenerationRequirementProjection,
)
from tests.fixtures.planning_factory import make_scene
from ai_video.production.video import (
    BillingKind,
    ProviderProfilePointer,
    VideoCapabilityVariant,
    VideoExecutionKind,
    VideoGenerationMode,
    VideoGenerationRequest,
    VideoImageReferenceBinding,
    VideoOutputRequirement,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64
HASH_D = "d" * 64
HASH_E = "e" * 64
HASH_F = "f" * 64
HASH_0 = "0" * 64


def _asset(
    role: str,
    suffix: str,
    sha256: str,
    *,
    mime_type: str | None = None,
    size_bytes: int = 1_000_000,
    width: int | None = 1024,
    height: int | None = 576,
    duration_millis: int | None = None,
    fps: int | None = None,
    registry_revision_id: str = HASH_F,
    canonical_owner_id: str | None = None,
    canonical_owner_content_hash: str | None = None,
) -> RouterAssetIdentity:
    canonical_owner_kind = None
    if role == "character_reference":
        canonical_owner_kind = "character"
        canonical_owner_id = canonical_owner_id or "hero"
        canonical_owner_content_hash = canonical_owner_content_hash or HASH_A
    elif role == "scene_reference":
        canonical_owner_kind = "scene"
        canonical_owner_id = canonical_owner_id or "scene-room"
        canonical_owner_content_hash = canonical_owner_content_hash or HASH_B
    return RouterAssetIdentity(
        role=role,
        asset_id=f"asset-{suffix}",
        asset_sha256=sha256,
        source_registry_revision_id=registry_revision_id,
        canonical_owner_kind=canonical_owner_kind,
        canonical_owner_id=canonical_owner_id,
        canonical_owner_content_hash=canonical_owner_content_hash,
        mime_type=(
            mime_type
            or ("video/mp4" if role == "existing_video" else "image/png")
        ),
        size_bytes=size_bytes,
        width=width,
        height=height,
        duration_millis=duration_millis,
        fps=fps,
    )


def _context(
    *,
    motion: MotionRequirement = MotionRequirement.CHARACTER_ACTION,
    continuity: ContinuityMode = ContinuityMode.NONE,
    important: bool = True,
    existing_video: RouterAssetIdentity | None = None,
    terminal: RouterAssetIdentity | None = None,
    keyframe: RouterAssetIdentity | None = None,
    character_references: tuple[RouterAssetIdentity, ...] | None = None,
    scene_reference: RouterAssetIdentity | None = None,
    continuity_state: RouterContinuityState | None = None,
    last_frame: RouterAssetIdentity | None = None,
    reference_videos: tuple[RouterAssetIdentity, ...] = (),
    reference_audios: tuple[RouterAssetIdentity, ...] = (),
    visual_strategy: VisualStrategy = VisualStrategy.GENERATED_VIDEO,
    shot_id: str = "shot-2",
    scene_id: str = "scene-room",
    shot_intent: str = "Continue the exact authored action.",
    important_character_ids: tuple[str, ...] | None = None,
    character_bible_hashes: tuple[str, ...] | None = None,
    scene_content_hash: str = HASH_B,
) -> ShotRoutingContext:
    if important_character_ids is None:
        important_character_ids = ("hero",) if important else ()
    if character_bible_hashes is None:
        character_bible_hashes = (HASH_A,) if important else ()
    if character_references is None:
        character_references = (
            (_asset("character_reference", "character", HASH_A),)
            if important
            else ()
        )
    if scene_reference is None and important:
        scene_reference = _asset("scene_reference", "scene", HASH_B)
    continuity_constraints = (
        (continuity_state.shot_constraint_token,)
        if continuity_state is not None
        and continuity in {ContinuityMode.REFERENCE, ContinuityMode.SEMANTIC}
        else ()
    )
    activated_shot = seal_artifact(
        Shot(
            artifact_id=f"{shot_id}-artifact",
            revision=3,
            content_hash="0" * 64,
            creation_receipt_id="router-test-authoring",
            source_provenance=(
                SourceReference(kind="user_input", reference="router-test"),
            ),
            shot_id=shot_id,
            scene_id=scene_id,
            storyboard_beat_id="beat-2",
            intent=shot_intent,
            duration_policy=DurationPolicy(mode="fixed", seconds=4),
            character_ids=important_character_ids,
            continuity_constraints=continuity_constraints,
            visual_strategy=visual_strategy,
        )
    )
    return ShotRoutingContext(
        activated_shot=activated_shot,
        target_shot_id=activated_shot.shot_id,
        target_shot_revision=activated_shot.revision,
        target_shot_content_hash=activated_shot.content_hash,
        storyboard_revision=2,
        storyboard_content_hash=HASH_D,
        selected_registry_revision_id=HASH_F,
        character_bible_content_hashes=character_bible_hashes,
        scene_content_hash=scene_content_hash,
        important_character_ids=important_character_ids,
        canonical_character_references=character_references,
        canonical_scene_reference=scene_reference,
        approved_existing_video=existing_video,
        shot_keyframe=keyframe,
        upstream_terminal=terminal,
        last_frame=last_frame,
        reference_videos=reference_videos,
        reference_audios=reference_audios,
        motion_requirement=motion,
        continuity_mode=continuity,
        semantic_continuity_state=continuity_state,
        allowed_visual_strategies=tuple(VisualStrategy),
        allowed_generation_modes=tuple(VideoGenerationMode),
    )


def _continuity_state(
    *,
    state_id: str = "alice-continuity",
    character_identity_hashes: tuple[str, ...] = (HASH_A,),
    story_state_hash: str = HASH_A,
    wardrobe_state_hashes: tuple[str, ...] = (HASH_B,),
    injury_state_hashes: tuple[str, ...] = (HASH_C,),
    prop_state_hashes: tuple[str, ...] = (HASH_D,),
    scene_state_hash: str | None = HASH_B,
) -> RouterContinuityState:
    return RouterContinuityState.create(
        state_id=state_id,
        state_revision=2,
        character_identity_hashes=character_identity_hashes,
        story_state_hash=story_state_hash,
        wardrobe_state_hashes=wardrobe_state_hashes,
        injury_state_hashes=injury_state_hashes,
        prop_state_hashes=prop_state_hashes,
        scene_state_hash=scene_state_hash,
    )


def _policy(
    *,
    policy_hash: str = HASH_A,
    local_resources: bool = True,
    remote_authorized: bool = False,
    budget_authorized: bool = False,
) -> VideoRoutingPolicy:
    return VideoRoutingPolicy(
        identity=RouterPolicyIdentity(
            policy_id="router-local-draft",
            policy_version="1",
            policy_sha256=policy_hash,
        ),
        local_resources_available=local_resources,
        remote_authorized=remote_authorized,
        budget_authorized=budget_authorized,
    )


def _output() -> VideoOutputRequirement:
    return VideoOutputRequirement(
        duration_seconds=4,
        width=1024,
        height=576,
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )


def test_output_capability_omits_absent_exact_geometry_from_identity() -> None:
    capability = VideoOutputCapability(
        min_duration_seconds=1,
        max_duration_seconds=10,
        provider_selected_duration=True,
        dimension_modes=("adaptive",),
        resolution_labels=("adaptive",),
        ratios=("adaptive",),
        fps_values=(24,),
        containers=("mp4",),
        native_audio_options=(False,),
    )

    payload = capability.model_dump(mode="json")

    assert not {
        "min_width",
        "max_width",
        "min_height",
        "max_height",
        "dimension_multiple",
    }.intersection(payload)


def _variant(
    mode: VideoGenerationMode,
    *,
    capability_id: str | None = None,
    execution_kind: VideoExecutionKind = VideoExecutionKind.LOCAL,
) -> VideoCapabilityVariant:
    roles: tuple[str, ...]
    max_references: int
    required_first_frame = False
    if mode is VideoGenerationMode.TEXT_TO_VIDEO:
        roles = ()
        max_references = 0
    elif mode is VideoGenerationMode.IMAGE_TO_VIDEO:
        roles = ("first_frame",)
        max_references = 1
        required_first_frame = True
    else:
        roles = ("reference",)
        max_references = 4
    return VideoCapabilityVariant(
        capability_id=capability_id or f"capability-{mode.value}",
        provider_kind="local_test",
        model_id="model-test",
        profile_version="1",
        execution_kind=execution_kind,
        billing_kind=(
            BillingKind.LOCAL_UNMETERED
            if execution_kind is VideoExecutionKind.LOCAL
            else BillingKind.METERED
        ),
        mode=mode,
        output=_output(),
        allowed_image_roles=roles,
        required_first_frame=required_first_frame,
        max_reference_count=max_references,
        allowed_image_mime_types=("image/png",),
        max_image_bytes=20_000_000,
        min_image_width=1,
        min_image_height=1,
        negative_prompt_supported=True,
        seed_supported=True,
        fps_supported=True,
        idempotent_submit=True,
        lookup_supported=True,
    )


def _capabilities(*variants: VideoCapabilityVariant) -> VideoProviderCapabilities:
    return VideoProviderCapabilities.create(
        provider_name="exact-provider",
        variants=variants,
    )


def _profile() -> ProviderProfilePointer:
    from pathlib import Path

    return ProviderProfilePointer(
        profile_id="exact-profile",
        profile_version="1",
        profile_path=Path(f"provider-profiles/{HASH_D}.json"),
        profile_sha256=HASH_D,
    )


def _verified_requirement(
    context: ShotRoutingContext,
) -> VerifiedGenerationRequirementProjection:
    requirement = ProviderNeutralVideoRequirement.create(
        source_request_content_hash=HASH_A,
        intent_evidence_hash=HASH_B,
        generation_intent_hash=HASH_C,
        target_shot=context.activated_shot,
        scene=make_scene(scene_id=context.activated_shot.scene_id),
        generation_mode=RequirementGenerationMode.TEXT_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.NONE,
        motion_requirement=RequirementMotionRequirement.FREE_COMPLEX,
        generation_intent=GenerationIntent(),
        output_need=OutputNeed(
            duration_seconds=4,
            width=1024,
            height=576,
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.FORBIDDEN,
        quality_need=QualityNeed(objective_tier="production"),
    )
    return VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=HASH_D,
        verified_source_request_content_hash=HASH_A,
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )


def _lifecycle(context: ShotRoutingContext) -> VideoGenerationLifecycleEnvelope:
    from pathlib import Path

    return VideoGenerationLifecycleEnvelope(
        generation_id="generation-shot-2",
        target_asset_role="primary_visual",
        base_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash=HASH_A,
            file_sha256=HASH_B,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{HASH_F}.json"),
            revision_id=HASH_F,
            content_hash=HASH_F,
            file_sha256=HASH_C,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            path=Path(f"state/dependency_graph.{HASH_C}.json"),
            revision_id=HASH_C,
            content_hash=HASH_C,
            file_sha256=HASH_D,
        ),
        input_artifact_ids=(context.target_shot_id,),
        output_asset_id="video-output",
    )


def _request_from_decision(
    decision,
    *,
    prompt_text: str = "Preserve the exact activated semantic continuity state.",
) -> VideoGenerationRequest:
    from pathlib import Path

    bindings = tuple(
        VideoImageReferenceBinding(
            role=role,
            asset_id=asset.asset_id,
            asset_sha256=asset.asset_sha256,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            size_bytes=asset.size_bytes,
        )
        for asset, role in zip(
            decision.input_assets,
            decision.required_binding_roles,
            strict=True,
        )
    )
    return VideoGenerationRequest.create(
        generation_id=f"generation-{decision.target_shot_content_hash[:12]}",
        provider_name=decision.provider_name,
        provider_kind="local_test",
        model_id="model-test",
        provider_profile=decision.provider_profile,
        target_shot_id=decision.target_shot_id,
        target_shot_revision=decision.target_shot_revision,
        target_shot_content_hash=decision.target_shot_content_hash,
        target_asset_role="primary_visual",
        target_visual_strategy="generated_video",
        mode=decision.selected_mode,
        prompt_text=prompt_text,
        negative_prompt_text="",
        image_bindings=bindings,
        output_requirement=decision.output_requirement,
        seed=17,
        base_project=ProjectSnapshotPointer(
            path=Path("project.yaml"),
            revision=1,
            content_hash=HASH_A,
            file_sha256=HASH_B,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{HASH_B}.json"),
            revision_id=HASH_B,
            content_hash=HASH_B,
            file_sha256=HASH_C,
        ),
        base_dependency_graph=DependencyGraphSnapshotPointer(
            path=Path(f"state/dependency_graph.{HASH_C}.json"),
            revision_id=HASH_C,
            content_hash=HASH_C,
            file_sha256=HASH_D,
        ),
        input_artifact_ids=(
            decision.target_shot_id,
            *(asset.asset_id for asset in decision.input_assets),
        ),
        output_asset_id="video-output",
    )


@pytest.mark.parametrize(
    ("context", "expected_strategy", "expected_reason"),
    [
        (
            _context(existing_video=_asset("existing_video", "approved", HASH_D)),
            VisualStrategy.EXISTING_VIDEO,
            RouterReasonCode.APPROVED_EXISTING_VIDEO,
        ),
        (
            _context(motion=MotionRequirement.NONE, important=False),
            VisualStrategy.STATIC_IMAGE,
            RouterReasonCode.NO_MOTION_REQUIRED,
        ),
        (
            _context(motion=MotionRequirement.LIGHT_TRANSFORM, important=False),
            VisualStrategy.IMAGE_MOTION,
            RouterReasonCode.LIGHT_MOTION_FROM_KEYFRAME,
        ),
        (
            _context(motion=MotionRequirement.GRAPHIC, important=False),
            VisualStrategy.MOTION_GRAPHICS,
            RouterReasonCode.GRAPHIC_MOTION_REQUIRED,
        ),
        (
            _context(motion=MotionRequirement.FREE_COMPLEX, important=False),
            VisualStrategy.GENERATED_VIDEO,
            RouterReasonCode.FREE_ENVIRONMENT_MOTION_ENABLES_T2V,
        ),
    ],
)
def test_visual_resolver_uses_deterministic_priority_matrix(
    context: ShotRoutingContext,
    expected_strategy: VisualStrategy,
    expected_reason: RouterReasonCode,
) -> None:
    result = ShotVisualResolver().resolve(context, _policy())

    assert result.outcome is RoutingOutcome.PROPOSED
    assert result.proposed_visual_strategy is expected_strategy
    assert expected_reason in result.reason_codes


def test_visual_resolver_blocks_important_character_without_anchor() -> None:
    context = _context(
        character_references=(),
        scene_reference=None,
        keyframe=None,
    )

    result = ShotVisualResolver().resolve(context, _policy())

    assert result.outcome is RoutingOutcome.BLOCKED_MISSING_INPUT
    assert result.proposed_visual_strategy is None
    assert RouterReasonCode.MISSING_CHARACTER_REFERENCE in result.reason_codes
    assert result.required_generation_mode is not VideoGenerationMode.TEXT_TO_VIDEO


def test_reference_continuity_proposes_r2v_without_copying_terminal_as_first_frame() -> None:
    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.REFERENCE,
        terminal=terminal,
        continuity_state=_continuity_state(),
    )

    visual = ShotVisualResolver().resolve(context, _policy())

    assert visual.outcome is RoutingOutcome.PROPOSED
    assert visual.proposed_visual_strategy is VisualStrategy.GENERATED_VIDEO
    assert visual.required_generation_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    assert visual.required_binding_roles == ("reference",)
    assert visual.reason_codes == (
        RouterReasonCode.REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE,
    )


def test_exact_terminal_continuity_precedes_unproven_existing_video() -> None:
    existing = _asset("existing_video", "approved", HASH_D)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        existing_video=existing,
        terminal=_asset("continuity_terminal", "terminal", HASH_C),
    )

    proposal = ShotVisualResolver().resolve(context, _policy())

    assert proposal.outcome is RoutingOutcome.PROPOSED
    assert proposal.proposed_visual_strategy is VisualStrategy.GENERATED_VIDEO
    assert proposal.required_generation_mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert proposal.reason_codes == (
        RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
    )


def test_approved_existing_video_requires_mp4_mime() -> None:
    with pytest.raises(ValidationError):
        _context(
            existing_video=_asset(
                "existing_video",
                "not-video",
                HASH_D,
                mime_type="image/png",
            )
        )


def test_context_binds_canonical_references_to_registry_and_subjects() -> None:
    payload = _context().model_dump(mode="json")
    payload["selected_registry_revision_id"] = HASH_F
    payload["canonical_character_references"][0].update(
        {
            "source_registry_revision_id": HASH_F,
            "canonical_owner_kind": "character",
            "canonical_owner_id": "hero",
            "canonical_owner_content_hash": HASH_A,
        }
    )
    payload["canonical_scene_reference"].update(
        {
            "source_registry_revision_id": HASH_F,
            "canonical_owner_kind": "scene",
            "canonical_owner_id": "scene-room",
            "canonical_owner_content_hash": HASH_B,
        }
    )

    context = ShotRoutingContext.model_validate(payload)

    assert context.selected_registry_revision_id == HASH_F
    invalid_owner = context.model_dump(mode="json")
    invalid_owner["canonical_character_references"][0][
        "canonical_owner_id"
    ] = "intruder"
    with pytest.raises(ValidationError):
        ShotRoutingContext.model_validate(invalid_owner)

    invalid_scene_owner = context.model_dump(mode="json")
    invalid_scene_owner["canonical_scene_reference"][
        "canonical_owner_id"
    ] = "scene-elsewhere"
    with pytest.raises(ValidationError):
        ShotRoutingContext.model_validate(invalid_scene_owner)

    invalid_registry = context.model_dump(mode="json")
    invalid_registry["canonical_scene_reference"][
        "source_registry_revision_id"
    ] = HASH_E
    with pytest.raises(ValidationError):
        ShotRoutingContext.model_validate(invalid_registry)


def test_context_rejects_duplicate_asset_id_across_projected_roles() -> None:
    character = _asset("character_reference", "shared", HASH_A)
    scene = _asset("scene_reference", "scene", HASH_B).model_copy(
        update={"asset_id": character.asset_id}
    )

    with pytest.raises(ValidationError):
        _context(
            character_references=(character,),
            scene_reference=scene,
        )

    terminal = _asset("continuity_terminal", "terminal", HASH_C).model_copy(
        update={"asset_id": character.asset_id}
    )
    with pytest.raises(ValidationError):
        _context(
            continuity=ContinuityMode.REFERENCE,
            continuity_state=_continuity_state(),
            character_references=(character,),
            terminal=terminal,
        )


def test_reference_continuity_requires_semantic_state() -> None:
    context = _context(
        continuity=ContinuityMode.REFERENCE,
        terminal=_asset("continuity_terminal", "terminal", HASH_C),
    )

    result = ShotVisualResolver().resolve(context, _policy())

    assert result.outcome is RoutingOutcome.BLOCKED_MISSING_INPUT
    assert result.reason_codes == (
        RouterReasonCode.MISSING_SEMANTIC_CONTINUITY_STATE,
    )


def test_reference_continuity_requires_exact_r2v_capability_without_fallback() -> None:
    context = _context(
        continuity=ContinuityMode.REFERENCE,
        terminal=_asset("continuity_terminal", "terminal", HASH_C),
        continuity_state=_continuity_state(),
    )

    result = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert result.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert result.required_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    assert context.upstream_terminal in result.input_assets
    assert tuple(asset.asset_id for asset in result.input_assets) == tuple(
        sorted(asset.asset_id for asset in result.input_assets)
    )
    assert "first_frame" not in result.required_binding_roles
    assert result.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_exact_terminal_without_important_character_still_requires_terminal_i2v() -> None:
    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        important=False,
        terminal=terminal,
    )

    result = ShotVisualResolver().resolve(context, _policy())

    assert result.outcome is RoutingOutcome.PROPOSED
    assert result.proposed_visual_strategy is VisualStrategy.GENERATED_VIDEO
    assert result.required_generation_mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert result.required_binding_roles == ("first_frame",)


def test_exact_terminal_uses_exact_terminal_as_first_frame() -> None:
    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
    )
    capabilities = _capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO))

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id="capability-image_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.required_mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert decision.selected_mode is VideoGenerationMode.IMAGE_TO_VIDEO
    assert decision.required_binding_roles == ("first_frame",)
    assert decision.input_assets == (terminal,)
    assert decision.reason_codes == (
        RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
    )


def test_free_motion_can_use_text_to_video_without_identity_or_continuity() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.required_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert decision.selected_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert decision.required_binding_roles == ()
    assert decision.input_assets == ()


def test_exact_capability_denial_does_not_try_another_variant() -> None:
    context = _context()
    selected_t2v = _variant(
        VideoGenerationMode.TEXT_TO_VIDEO,
        capability_id="selected-t2v",
    )
    unused_r2v = _variant(
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        capability_id="unused-r2v",
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(unused_r2v, selected_t2v),
        selected_capability_id="selected-t2v",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.required_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    assert decision.selected_mode is None
    assert decision.selected_capability_id == "selected-t2v"
    assert decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_terminal_mime_and_measurements_must_satisfy_exact_capability() -> None:
    terminal = _asset(
        "continuity_terminal",
        "terminal-jpeg",
        HASH_C,
        mime_type="image/jpeg",
    )
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO)),
        selected_capability_id="capability-image_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_selected_profile_version_must_match_capability() -> None:
    profile = _profile().model_copy(update={"profile_version": "different"})
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_routing_context_rejects_asset_in_the_wrong_semantic_role() -> None:
    with pytest.raises(ValidationError):
        _context(
            continuity=ContinuityMode.EXACT_TERMINAL,
            terminal=_asset("first_frame", "wrong-terminal-role", HASH_C),
        )


def test_hero_or_repair_remains_blocked_in_first_phase() -> None:
    context = _context(
        motion=MotionRequirement.HERO_OR_REPAIR,
        important=False,
    )
    policy = _policy()

    visual = ShotVisualResolver().resolve(context, policy)
    generation = VideoGenerationResolver().resolve(
        context=context,
        policy=policy,
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert visual.outcome is RoutingOutcome.BLOCKED_POLICY
    assert generation.outcome is RoutingOutcome.BLOCKED_POLICY
    assert generation.selected_mode is None
    assert generation.reason_codes == (
        RouterReasonCode.HERO_SHOT_REQUIRES_HYBRID_OR_V2V,
    )


def test_remote_capability_requires_authorization_before_selection() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(
                VideoGenerationMode.TEXT_TO_VIDEO,
                execution_kind=VideoExecutionKind.REMOTE,
            )
        ),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_AUTHORIZATION
    assert decision.required_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert decision.reason_codes == (
        RouterReasonCode.REMOTE_AUTHORIZATION_REQUIRED,
    )


def test_local_capability_requires_available_local_resources() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(local_resources=False),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert decision.reason_codes == (
        RouterReasonCode.LOCAL_RESOURCE_POLICY_DENIED,
    )


def test_remote_capability_requires_budget_after_authorization() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(remote_authorized=True),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(
                VideoGenerationMode.TEXT_TO_VIDEO,
                execution_kind=VideoExecutionKind.REMOTE,
            )
        ),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert decision.reason_codes == (
        RouterReasonCode.BUDGET_POLICY_DENIED,
    )


def test_output_requirement_must_match_exact_capability() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    output = _output().model_copy(update={"duration_seconds": 5})

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=output,
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_generation_mode_must_be_allowed_by_context() -> None:
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
    ).model_copy(
        update={
            "allowed_generation_modes": (VideoGenerationMode.IMAGE_TO_VIDEO,),
        }
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )


def test_visual_strategy_must_be_allowed_by_context() -> None:
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
    ).model_copy(
        update={"allowed_visual_strategies": (VisualStrategy.STATIC_IMAGE,)}
    )

    proposal = ShotVisualResolver().resolve(context, _policy())

    assert proposal.outcome is RoutingOutcome.BLOCKED_POLICY
    assert proposal.reason_codes == (
        RouterReasonCode.VISUAL_STRATEGY_POLICY_DENIED,
    )


def test_video_resolver_rejects_non_generated_activated_strategy() -> None:
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
        visual_strategy=VisualStrategy.STATIC_IMAGE,
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert decision.reason_codes == (
        RouterReasonCode.ROUTER_REQUIRES_GENERATED_VIDEO_SHOT,
    )


def test_hybrid_generated_layer_uses_the_same_exact_generation_contract() -> None:
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
        visual_strategy=VisualStrategy.HYBRID,
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.selected_mode is VideoGenerationMode.TEXT_TO_VIDEO


def test_reference_input_order_is_canonicalized_before_semantic_hashing() -> None:
    first_reference = _asset("character_reference", "first", HASH_A)
    second_reference = _asset("character_reference", "second", HASH_B)
    scene_reference = _asset("scene_reference", "scene", HASH_C)
    common = {
        "policy": _policy(),
        "provider_profile": _profile(),
        "capabilities": _capabilities(
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
        ),
        "selected_capability_id": "capability-reference_to_video",
        "output_requirement": _output(),
    }

    first = VideoGenerationResolver().resolve(
        context=_context(
            character_references=(first_reference, second_reference),
            scene_reference=scene_reference,
        ),
        **common,
    )
    second = VideoGenerationResolver().resolve(
        context=_context(
            character_references=(second_reference, first_reference),
            scene_reference=scene_reference,
        ),
        **common,
    )

    assert first.outcome is RoutingOutcome.SELECTED
    assert second.outcome is RoutingOutcome.SELECTED
    assert tuple(asset.asset_id for asset in first.input_assets) == tuple(
        sorted(asset.asset_id for asset in first.input_assets)
    )
    assert first.input_assets == second.input_assets
    assert first.semantic_routing_hash == second.semantic_routing_hash


def test_remote_authorization_changes_audit_not_semantic_routing() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    kwargs = {
        "context": context,
        "provider_profile": _profile(),
        "capabilities": _capabilities(
            _variant(
                VideoGenerationMode.TEXT_TO_VIDEO,
                execution_kind=VideoExecutionKind.REMOTE,
            )
        ),
        "selected_capability_id": "capability-text_to_video",
        "output_requirement": _output(),
    }

    blocked = VideoGenerationResolver().resolve(
        policy=_policy(),
        **kwargs,
    )
    selected = VideoGenerationResolver().resolve(
        policy=_policy(remote_authorized=True, budget_authorized=True),
        **kwargs,
    )

    assert blocked.outcome is RoutingOutcome.BLOCKED_AUTHORIZATION
    assert selected.outcome is RoutingOutcome.SELECTED
    assert blocked.semantic_routing_hash == selected.semantic_routing_hash
    assert blocked.audit_decision_hash != selected.audit_decision_hash


def test_exact_reference_capability_selects_r2v_with_all_anchors() -> None:
    terminal = _asset("continuity_terminal", "z-terminal", HASH_C)
    character = _asset("character_reference", "a-character", HASH_A)
    scene = _asset("scene_reference", "m-scene", HASH_B)
    context = _context(
        continuity=ContinuityMode.REFERENCE,
        terminal=terminal,
        continuity_state=_continuity_state(),
        character_references=(character,),
        scene_reference=scene,
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
        ),
        selected_capability_id="capability-reference_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.selected_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    assert decision.continuity_mode is ContinuityMode.REFERENCE
    assert decision.required_binding_roles == (
        "reference",
        "reference",
        "reference",
    )
    assert decision.input_assets == (character, scene, terminal)
    assert all(role != "first_frame" for role in decision.required_binding_roles)
    assert decision.reason_codes == (
        RouterReasonCode.REFERENCE_CONTINUITY_USES_TERMINAL_REFERENCE,
    )
    request = _request_from_decision(decision)
    assert tuple(binding.asset_id for binding in request.image_bindings) == (
        "asset-a-character",
        "asset-m-scene",
        "asset-z-terminal",
    )


def test_reference_routing_generalizes_across_distinct_references_and_prompts() -> None:
    cases = (
        {
            "shot_id": "shot-alice-doorway",
            "scene_id": "scene-warehouse-door",
            "shot_intent": (
                "Low-angle side close-up: Alice pivots at the warehouse door, "
                "black coat torn at the left shoulder, pistol held in her right hand."
            ),
            "character_id": "alice",
            "character_hash": HASH_A,
            "scene_hash": HASH_B,
            "terminal_hash": HASH_C,
            "state": _continuity_state(
                state_id="alice-doorway-continuity",
                story_state_hash=HASH_D,
            ),
        },
        {
            "shot_id": "shot-kai-train",
            "scene_id": "scene-sunlit-train",
            "shot_intent": (
                "Wide tracking shot: Kai in a yellow raincoat runs left along a "
                "sunlit train platform while carrying a blue violin case."
            ),
            "character_id": "kai",
            "character_hash": HASH_E,
            "scene_hash": HASH_F,
            "terminal_hash": HASH_0,
            "state": _continuity_state(
                state_id="kai-train-continuity",
                character_identity_hashes=(HASH_E,),
                story_state_hash=HASH_E,
                wardrobe_state_hashes=(HASH_F,),
                injury_state_hashes=(),
                prop_state_hashes=(HASH_0,),
                scene_state_hash=HASH_F,
            ),
        },
    )
    decisions = []
    requests = []

    for case in cases:
        character_reference = _asset(
            "character_reference",
            f"{case['character_id']}-reference",
            case["character_hash"],
            canonical_owner_id=case["character_id"],
            canonical_owner_content_hash=case["character_hash"],
        )
        scene_reference = _asset(
            "scene_reference",
            f"{case['scene_id']}-reference",
            case["scene_hash"],
            canonical_owner_id=case["scene_id"],
            canonical_owner_content_hash=case["scene_hash"],
        )
        terminal = _asset(
            "continuity_terminal",
            f"{case['shot_id']}-terminal",
            case["terminal_hash"],
        )
        context = _context(
            continuity=ContinuityMode.REFERENCE,
            terminal=terminal,
            continuity_state=case["state"],
            character_references=(character_reference,),
            scene_reference=scene_reference,
            shot_id=case["shot_id"],
            scene_id=case["scene_id"],
            shot_intent=case["shot_intent"],
            important_character_ids=(case["character_id"],),
            character_bible_hashes=(case["character_hash"],),
            scene_content_hash=case["scene_hash"],
        )
        decision = VideoGenerationResolver().resolve(
            context=context,
            policy=_policy(),
            provider_profile=_profile(),
            capabilities=_capabilities(
                _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
            ),
            selected_capability_id="capability-reference_to_video",
            output_requirement=_output(),
        )
        request = _request_from_decision(
            decision,
            prompt_text=case["shot_intent"],
        )
        expected_bindings = tuple(
            (
                "reference",
                asset.asset_id,
                asset.asset_sha256,
            )
            for asset in sorted(
                (character_reference, scene_reference, terminal),
                key=lambda item: item.asset_id,
            )
        )

        assert decision.outcome is RoutingOutcome.SELECTED
        assert decision.selected_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
        assert decision.semantic_continuity_state == case["state"]
        assert (
            case["state"].shot_constraint_token
            in context.activated_shot.continuity_constraints
        )
        assert tuple(
            (binding.role, binding.asset_id, binding.asset_sha256)
            for binding in request.image_bindings
        ) == expected_bindings
        decisions.append(decision)
        requests.append(request)

    assert all(decision.outcome is RoutingOutcome.SELECTED for decision in decisions)
    assert all(
        decision.selected_mode is VideoGenerationMode.REFERENCE_TO_VIDEO
        for decision in decisions
    )
    assert all(decision.required_binding_roles == ("reference",) * 3 for decision in decisions)
    assert requests[0].prompt_text == cases[0]["shot_intent"]
    assert requests[1].prompt_text == cases[1]["shot_intent"]
    assert requests[0].request_input_hash != requests[1].request_input_hash
    assert decisions[0].semantic_routing_hash != decisions[1].semantic_routing_hash
    assert {
        binding.asset_sha256 for binding in requests[0].image_bindings
    }.isdisjoint(binding.asset_sha256 for binding in requests[1].image_bindings)


def test_semantic_continuity_carries_state_but_never_terminal_pixels() -> None:
    terminal = _asset("continuity_terminal", "available-but-unused", HASH_C)
    state = _continuity_state()
    context = _context(
        continuity=ContinuityMode.SEMANTIC,
        terminal=terminal,
        continuity_state=state,
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
        ),
        selected_capability_id="capability-reference_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.continuity_mode is ContinuityMode.SEMANTIC
    assert decision.semantic_continuity_state == state
    assert terminal not in decision.input_assets
    assert all(asset.role != "continuity_terminal" for asset in decision.input_assets)
    assert decision.reason_codes == (
        RouterReasonCode.SEMANTIC_CONTINUITY_USES_STATE_ONLY,
    )


def test_semantic_continuity_requires_sealed_state() -> None:
    context = _context(continuity=ContinuityMode.SEMANTIC)

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
        ),
        selected_capability_id="capability-reference_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.BLOCKED_MISSING_INPUT
    assert decision.reason_codes == (
        RouterReasonCode.MISSING_SEMANTIC_CONTINUITY_STATE,
    )


def test_semantic_continuity_does_not_reuse_unproven_existing_video() -> None:
    context = _context(
        continuity=ContinuityMode.SEMANTIC,
        continuity_state=_continuity_state(),
        existing_video=_asset("existing_video", "unproven", HASH_D),
    )

    proposal = ShotVisualResolver().resolve(context, _policy())

    assert proposal.outcome is RoutingOutcome.PROPOSED
    assert proposal.proposed_visual_strategy is VisualStrategy.GENERATED_VIDEO
    assert proposal.proposed_visual_strategy is not VisualStrategy.EXISTING_VIDEO


def test_continuity_state_must_be_materialized_in_activated_shot() -> None:
    state = _continuity_state()
    context = _context(
        continuity=ContinuityMode.SEMANTIC,
        continuity_state=state,
    )

    unprojected_shot = seal_artifact(
        context.activated_shot.model_copy(
            update={"content_hash": "0" * 64, "continuity_constraints": ()}
        )
    )
    with pytest.raises(ValidationError):
        ShotRoutingContext.model_validate(
            {
                **context.model_dump(mode="json"),
                "activated_shot": unprojected_shot.model_dump(mode="json"),
                "target_shot_content_hash": unprojected_shot.content_hash,
            }
        )


def test_none_continuity_ignores_available_terminal_and_semantic_state() -> None:
    terminal = _asset("continuity_terminal", "available-but-unused", HASH_C)
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        continuity=ContinuityMode.NONE,
        important=False,
        terminal=terminal,
        continuity_state=_continuity_state(),
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.continuity_mode is ContinuityMode.NONE
    assert decision.semantic_continuity_state is None
    assert decision.input_assets == ()
    assert decision.reason_codes == (RouterReasonCode.NO_CONTINUITY,)


def test_exact_terminal_ignores_extra_semantic_state() -> None:
    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
        continuity_state=_continuity_state(),
    )

    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO)),
        selected_capability_id="capability-image_to_video",
        output_requirement=_output(),
    )

    assert decision.outcome is RoutingOutcome.SELECTED
    assert decision.semantic_continuity_state is None


def test_continuity_mode_and_state_change_semantic_routing_hash() -> None:
    common = {
        "policy": _policy(),
        "provider_profile": _profile(),
        "capabilities": _capabilities(
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO)
        ),
        "selected_capability_id": "capability-reference_to_video",
        "output_requirement": _output(),
    }
    first_state = _continuity_state(story_state_hash=HASH_A)
    second_state = _continuity_state(story_state_hash=HASH_D)
    first = VideoGenerationResolver().resolve(
        context=_context(
            continuity=ContinuityMode.SEMANTIC,
            continuity_state=first_state,
        ),
        **common,
    )
    second = VideoGenerationResolver().resolve(
        context=_context(
            continuity=ContinuityMode.SEMANTIC,
            continuity_state=second_state,
        ),
        **common,
    )
    none = VideoGenerationResolver().resolve(
        context=_context(continuity=ContinuityMode.NONE),
        **common,
    )

    assert first.semantic_routing_hash != second.semantic_routing_hash
    assert first.semantic_routing_hash != none.semantic_routing_hash
    assert first.target_shot_content_hash != second.target_shot_content_hash
    first_request = _request_from_decision(first)
    second_request = _request_from_decision(second)
    assert first_request.request_input_hash != second_request.request_input_hash


def test_policy_identity_changes_audit_hash_but_not_semantic_hash() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    kwargs = {
        "context": context,
        "provider_profile": _profile(),
        "capabilities": _capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        "selected_capability_id": "capability-text_to_video",
        "output_requirement": _output(),
    }

    first = VideoGenerationResolver().resolve(
        policy=_policy(policy_hash=HASH_A),
        **kwargs,
    )
    second = VideoGenerationResolver().resolve(
        policy=_policy(policy_hash=HASH_B),
        **kwargs,
    )

    assert first.semantic_routing_hash == second.semantic_routing_hash
    assert first.audit_decision_hash != second.audit_decision_hash


def test_unselected_capability_order_does_not_change_semantic_routing() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    selected = _variant(
        VideoGenerationMode.TEXT_TO_VIDEO,
        capability_id="selected-t2v",
    )
    unused = _variant(
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        capability_id="unused-r2v",
    )
    common = {
        "context": context,
        "policy": _policy(),
        "provider_profile": _profile(),
        "selected_capability_id": "selected-t2v",
        "output_requirement": _output(),
    }

    first = VideoGenerationResolver().resolve(
        capabilities=_capabilities(selected, unused),
        **common,
    )
    second = VideoGenerationResolver().resolve(
        capabilities=_capabilities(unused, selected),
        **common,
    )

    assert first.semantic_routing_hash == second.semantic_routing_hash
    assert first.audit_decision_hash != second.audit_decision_hash


def test_router_models_are_strict_and_immutable() -> None:
    context = _context()

    with pytest.raises(ValidationError):
        ShotRoutingContext.model_validate(
            {**context.model_dump(mode="json"), "unexpected": True}
        )

    with pytest.raises(ValidationError):
        context.target_shot_revision = 4


def test_router_context_accepts_explicit_optional_last_frame() -> None:
    last_frame = _asset("last_frame", "planned-endpoint", HASH_E)

    context = _context(
        motion=MotionRequirement.CHARACTER_ACTION,
        important=False,
        keyframe=_asset("first_frame", "opening", HASH_D),
        last_frame=last_frame,
    )

    assert context.last_frame == last_frame


def test_router_exposes_prompt_free_provider_bound_projection_contract() -> None:
    from ai_video.production import shot_router

    assert hasattr(shot_router, "ProviderBoundVideoRequest")
    assert hasattr(VideoGenerationResolver, "resolve_requirement")


def test_router_projects_verified_requirement_to_deterministic_prompt_free_bound_request() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    projection = _verified_requirement(context)
    compiler = AdapterCompilerContract.create(
        compiler_id="fake-video-compiler",
        compiler_version="1",
    )
    kwargs = {
        "projection": projection,
        "context": context,
        "policy": _policy(),
        "provider_profile": _profile(),
        "capabilities": _capabilities(
            _variant(VideoGenerationMode.TEXT_TO_VIDEO)
        ),
        "selected_capability_id": "capability-text_to_video",
        "output_requirement": _output(),
        "lifecycle": _lifecycle(context),
        "compiler_contract": compiler,
    }

    first = VideoGenerationResolver().resolve_requirement(**kwargs)
    second = VideoGenerationResolver().resolve_requirement(**kwargs)

    assert first.decision.outcome is RoutingOutcome.SELECTED
    assert first.provider_bound_request == second.provider_bound_request
    assert first.provider_bound_request is not None
    assert first.provider_bound_request.requirement_hash == (
        projection.requirement.requirement_hash
    )
    serialized = first.provider_bound_request.model_dump(mode="json")
    assert "prompt_text" not in serialized
    assert "payload" not in serialized


def test_router_native_control_requirement_blocks_without_bound_request() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    projection = _verified_requirement(context)
    intent = projection.requirement.generation_intent.model_copy(
        update={
            "camera_intent": projection.requirement.generation_intent.camera_intent.model_copy(
                update={
                    "expression_strength": ExpressionStrength.NATIVE_CONTROL_REQUIRED
                }
            )
        }
    )
    requirement = ProviderNeutralVideoRequirement.create(
        **{
            **projection.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "generation_intent": intent,
        }
    )
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=HASH_D,
        verified_source_request_content_hash=HASH_A,
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )

    result = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=_capabilities(_variant(VideoGenerationMode.TEXT_TO_VIDEO)),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="fake-video-compiler",
            compiler_version="1",
        ),
    )

    assert result.decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert result.provider_bound_request is None


def test_router_intersects_provider_execution_with_requirement_policy() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    projection = _verified_requirement(context)
    requirement = ProviderNeutralVideoRequirement.create(
        **{
            **projection.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "capability_need": CapabilityNeed(
                accepts_local_execution=True,
                accepts_remote_execution=False,
            ),
        }
    )
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=projection.plan_hash,
        verified_source_request_content_hash=(
            projection.verified_source_request_content_hash
        ),
        target_shot_id=projection.target_shot_id,
        target_shot_revision=projection.target_shot_revision,
        target_shot_content_hash=projection.target_shot_content_hash,
    )

    result = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_profile(),
        capabilities=_capabilities(
            _variant(
                VideoGenerationMode.TEXT_TO_VIDEO,
                execution_kind=VideoExecutionKind.REMOTE,
            )
        ),
        selected_capability_id="capability-text_to_video",
        output_requirement=_output(),
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="fake-video-compiler",
            compiler_version="1",
        ),
    )

    assert result.decision.outcome is RoutingOutcome.BLOCKED_AUTHORIZATION
    assert result.provider_bound_request is None

def test_router_surface_is_available_from_production_package() -> None:
    from ai_video.production import (
        ContinuityMode as PublicContinuityMode,
        RouterContinuityState as PublicRouterContinuityState,
        ShotVisualResolver as PublicShotVisualResolver,
        VideoGenerationResolver as PublicVideoGenerationResolver,
    )

    assert PublicContinuityMode is ContinuityMode
    assert PublicRouterContinuityState is RouterContinuityState
    assert PublicShotVisualResolver is ShotVisualResolver
    assert PublicVideoGenerationResolver is VideoGenerationResolver


def test_t8_family_requires_explicit_quality_or_turbo_selection_without_fallback() -> None:
    from pathlib import Path

    from ai_video.production.comfy_t8_video import (
        ComfyUIT8VideoProvider,
        load_t8_video_execution_profile,
    )
    from ai_video.production.comfy_t8_turbo_video import (
        ComfyUIT8TurboVideoProvider,
        load_t8_turbo_video_execution_profile,
    )
    from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily

    root = Path(__file__).resolve().parents[1]
    execution_profile = load_t8_video_execution_profile(
        root / "workflows/profiles/minimax_h3_t8_t2va_quality.json",
        artifact_root=root,
    )
    quality_provider = ComfyUIT8VideoProvider(
        execution_profile,
        artifact_root=root,
        comfy_root=root,
        runtime_inspector=lambda: (_ for _ in ()).throw(
            AssertionError("Router selection must not inspect the local runtime")
        ),
        transport=object(),
    )
    turbo_profile = load_t8_turbo_video_execution_profile(
        root / "workflows/profiles/minimax_h3_t8_t2va_turbo.json",
        artifact_root=root,
    )
    turbo_provider = ComfyUIT8TurboVideoProvider(
        turbo_profile,
        artifact_root=root,
        comfy_root=root,
        runtime_inspector=lambda: (_ for _ in ()).throw(
            AssertionError("Router selection must not inspect the local runtime")
        ),
        transport=object(),
    )
    capabilities = LocalH3VideoProviderFamily(
        (quality_provider, turbo_provider)
    ).capabilities()
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=124,
        dimension_mode="exact",
        width=1344,
        height=768,
        resolution_label="h3_t8_native",
        ratio="16:9",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    profile = ProviderProfilePointer(
        profile_id="minimax-h3-t8-t2va-quality",
        profile_version="v1",
        profile_path=Path(
            f"provider-profiles/{execution_profile.profile_content_hash}.json"
        ),
        profile_sha256=execution_profile.profile_content_hash,
    )
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    selected = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id="minimax-h3-t8-t2va-quality-v1",
        output_requirement=output,
    )
    turbo_selected = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-t8-t2va-turbo",
            profile_version="v1",
            profile_path=Path(
                f"provider-profiles/{turbo_profile.profile_content_hash}.json"
            ),
            profile_sha256=turbo_profile.profile_content_hash,
        ),
        capabilities=capabilities,
        selected_capability_id="minimax-h3-t8-t2va-turbo-v1",
        output_requirement=output,
    )
    missing = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id="minimax-h3-fl2va-local-v1",
        output_requirement=output,
    )

    assert selected.outcome is RoutingOutcome.SELECTED
    assert selected.provider_name == "comfy-local-h3-t8"
    assert selected.required_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert selected.required_binding_roles == ()
    assert turbo_selected.outcome is RoutingOutcome.SELECTED
    assert turbo_selected.provider_name == "comfy-local-h3-t8"
    assert turbo_selected.selected_capability_id == "minimax-h3-t8-t2va-turbo-v1"
    assert turbo_selected.required_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert turbo_selected.required_binding_roles == ()
    assert missing.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert missing.provider_name == "comfy-local-h3-t8"
    assert missing.selected_capability_id == "minimax-h3-fl2va-local-v1"
    assert missing.selected_capability_fingerprint is None
    assert missing.reason_codes == (RouterReasonCode.PROVIDER_CAPABILITY_DENIED,)


def test_exact_terminal_accepts_real_h3_and_hailuo_i2v_capabilities() -> None:
    from pathlib import Path

    from ai_video.production.comfy_video import (
        ComfyUIVideoProvider,
        load_local_video_execution_profile,
    )
    from ai_video.production.minimax_hailuo import MiniMaxHailuoVideoProvider

    root = Path(__file__).resolve().parents[1]
    h3_execution_profile = load_local_video_execution_profile(
        root / "workflows/profiles/minimax_h3_fl2va_quality.json",
        artifact_root=root,
    )
    h3_provider = ComfyUIVideoProvider(
        h3_execution_profile,
        artifact_root=root,
        comfy_root=root,
        image_root=root,
        image_resolver=lambda *_: root / "unused.png",
        transport=object(),
        commit_resolver=lambda: h3_execution_profile.comfyui_commit,
    )
    h3_capabilities = h3_provider.capabilities()
    h3_variant = next(
        variant
        for variant in h3_capabilities.variants
        if variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    hailuo_capabilities = MiniMaxHailuoVideoProvider(
        transport=object(),
        credential=lambda _: (_ for _ in ()).throw(
            AssertionError("offline capability inspection must not read credentials")
        ),
    ).capabilities()
    hailuo_i2v_variant = next(
        variant
        for variant in hailuo_capabilities.variants
        if variant.mode is VideoGenerationMode.IMAGE_TO_VIDEO
    )
    assert h3_variant.required_first_frame is True
    assert h3_variant.max_reference_count == 0
    assert hailuo_i2v_variant.required_first_frame is True
    assert hailuo_i2v_variant.max_reference_count == 0
    h3_output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=124,
        dimension_mode="exact",
        width=1344,
        height=672,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    hailuo_i2v_output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=141,
        dimension_mode="adaptive",
        width=None,
        height=None,
        resolution_label="768P",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )

    h3_profile = ProviderProfilePointer(
        profile_id="minimax-h3-fl2va-quality",
        profile_version="v1",
        profile_path=Path(
            f"provider-profiles/{h3_execution_profile.profile_content_hash}.json"
        ),
        profile_sha256=h3_execution_profile.profile_content_hash,
    )
    hailuo_profile = ProviderProfilePointer(
        profile_id="minimax-hailuo-default",
        profile_version="hailuo-2.3-v1",
        profile_path=Path(f"provider-profiles/{HASH_A}.json"),
        profile_sha256=HASH_A,
    )

    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
    )

    h3_decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=h3_profile,
        capabilities=h3_capabilities,
        selected_capability_id=h3_variant.capability_id,
        output_requirement=h3_output,
    )
    unsupported_h3_decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=h3_profile,
        capabilities=h3_capabilities,
        selected_capability_id=h3_variant.capability_id,
        output_requirement=h3_output.model_copy(
            update={"width": 16384, "height": 16384}
        ),
    )
    hailuo_decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=hailuo_profile,
        capabilities=hailuo_capabilities,
        selected_capability_id=hailuo_i2v_variant.capability_id,
        output_requirement=hailuo_i2v_output,
    )

    assert h3_decision.outcome is RoutingOutcome.SELECTED
    assert h3_decision.selected_capability_id == h3_variant.capability_id
    assert h3_decision.required_binding_roles == ("first_frame",)
    assert h3_decision.input_assets == (terminal,)
    assert h3_decision.reason_codes == (
        RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
    )
    assert unsupported_h3_decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert unsupported_h3_decision.reason_codes == (
        RouterReasonCode.PROVIDER_CAPABILITY_DENIED,
    )
    assert hailuo_decision.outcome is RoutingOutcome.SELECTED
    assert (
        hailuo_decision.selected_capability_id == hailuo_i2v_variant.capability_id
    )
    assert hailuo_decision.required_binding_roles == ("first_frame",)
    assert hailuo_decision.input_assets == (terminal,)
    assert hailuo_decision.reason_codes == (
        RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
    )


def _cardinality_constraint(**changes: object):
    from ai_video.production.video_contracts import VideoBindingCardinalityConstraint

    values: dict[str, object] = {
        "roles": ("first_frame",),
        "min_count": 1,
        "max_count": 1,
    }
    values.update(changes)
    return VideoBindingCardinalityConstraint(**values)


def test_router_rejects_capability_cardinality_violation_before_provider_bound_construction() -> None:
    from ai_video.production.video_contracts import VideoBindingCardinalityConstraint

    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        capability_id="cardinality-i2v",
    )
    variant_with_constraints = variant.model_copy(
        update={
            "binding_cardinality_constraints": (
                VideoBindingCardinalityConstraint(
                    roles=("first_frame",), min_count=1, max_count=1
                ),
                VideoBindingCardinalityConstraint(
                    roles=("last_frame",), min_count=1, max_count=1
                ),
            )
        }
    )
    capabilities = _capabilities(variant_with_constraints)
    keyframe = _asset("first_frame", "i2v-keyframe", HASH_A)
    context = _context(
        important=True,
        keyframe=keyframe,
    )
    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=variant_with_constraints.capability_id,
        output_requirement=_output(),
    )
    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (RouterReasonCode.PROVIDER_CAPABILITY_DENIED,)


def test_router_distinguishes_i2va_from_fl2va_when_both_are_image_to_video_mode() -> None:
    from ai_video.production.video_contracts import VideoBindingCardinalityConstraint

    i2va_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO, capability_id="i2va-only"
    ).model_copy(
        update={
            "binding_cardinality_constraints": (
                VideoBindingCardinalityConstraint(
                    roles=("first_frame",), min_count=1, max_count=1
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference",), min_count=0, max_count=0
                ),
            )
        }
    )
    fl2va_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO, capability_id="fl2va-only"
    ).model_copy(
        update={
            "allowed_image_roles": ("first_frame", "last_frame"),
            "binding_cardinality_constraints": (
                VideoBindingCardinalityConstraint(
                    roles=("first_frame",), min_count=1, max_count=1
                ),
                VideoBindingCardinalityConstraint(
                    roles=("last_frame",), min_count=1, max_count=1
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference",), min_count=0, max_count=0
                ),
            ),
        }
    )
    capabilities = _capabilities(i2va_variant, fl2va_variant)
    keyframe = _asset("first_frame", "i2v-keyframe", HASH_A)
    last_frame = _asset("last_frame", "i2v-last", HASH_B)
    i2va_context = _context(important=True, keyframe=keyframe)
    fl2va_context = _context(
        important=True, keyframe=keyframe, last_frame=last_frame
    )

    i2va_decision = VideoGenerationResolver().resolve(
        context=i2va_context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=i2va_variant.capability_id,
        output_requirement=_output(),
    )
    fl2va_decision = VideoGenerationResolver().resolve(
        context=fl2va_context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=fl2va_variant.capability_id,
        output_requirement=_output(),
        requirement_mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        requirement_binding_roles=("first_frame", "last_frame"),
        requirement_input_assets=(keyframe, last_frame),
    )
    cross_decision = VideoGenerationResolver().resolve(
        context=i2va_context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=fl2va_variant.capability_id,
        output_requirement=_output(),
        requirement_mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        requirement_binding_roles=("first_frame",),
        requirement_input_assets=(keyframe,),
    )

    assert i2va_decision.outcome is RoutingOutcome.SELECTED
    assert fl2va_decision.outcome is RoutingOutcome.SELECTED
    assert cross_decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY


def test_router_ref2va_capability_rejects_missing_or_overflowing_references() -> None:
    from ai_video.production.video_contracts import VideoBindingCardinalityConstraint

    ref2va_variant = _variant(
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        capability_id="ref2va-only",
    ).model_copy(
        update={
            "allowed_image_roles": ("reference",),
            "max_reference_count": 9,
            "binding_cardinality_constraints": (
                VideoBindingCardinalityConstraint(
                    roles=("first_frame",), min_count=0, max_count=0
                ),
                VideoBindingCardinalityConstraint(
                    roles=("last_frame",), min_count=0, max_count=0
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference",), min_count=0, max_count=9
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference_video",), min_count=0, max_count=3
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference_audio",), min_count=0, max_count=3
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference", "reference_video", "reference_audio"),
                    min_count=1,
                    max_count=15,
                ),
            ),
        }
    )
    capabilities = _capabilities(ref2va_variant)
    context_no_ref = _context(important=False)
    overflow_refs: tuple[RouterAssetIdentity, ...] = tuple(
        _asset(
            "character_reference",
            f"ref-{i}",
            HASH_A,
            canonical_owner_id=f"character-{i}",
        )
        for i in range(10)
    )
    overflow_context = _context(important=False)
    no_ref_decision = VideoGenerationResolver().resolve(
        context=context_no_ref,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=ref2va_variant.capability_id,
        output_requirement=_output(),
        requirement_mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        requirement_binding_roles=(),
        requirement_input_assets=(),
    )
    overflow_decision = VideoGenerationResolver().resolve(
        context=overflow_context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=ref2va_variant.capability_id,
        output_requirement=_output(),
        requirement_mode=VideoGenerationMode.REFERENCE_TO_VIDEO,
        requirement_binding_roles=("reference",) * len(overflow_refs),
        requirement_input_assets=overflow_refs,
    )
    assert no_ref_decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert overflow_decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY


def test_router_does_not_fallback_when_v2_capability_id_is_unknown() -> None:
    i2va_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO, capability_id="i2va-real"
    )
    fl2va_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO, capability_id="fl2va-real"
    ).model_copy(update={"allowed_image_roles": ("first_frame", "last_frame")})
    capabilities = _capabilities(i2va_variant, fl2va_variant)
    context = _context(
        important=True,
        keyframe=_asset("first_frame", "keyframe", HASH_A),
    )
    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id="minimax-h3-t8-i2va-turbo-native-v2",
        output_requirement=_output(),
    )
    assert decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert decision.reason_codes == (RouterReasonCode.PROVIDER_CAPABILITY_DENIED,)


def test_router_selected_capability_fingerprint_includes_canonical_constraints() -> None:
    from ai_video.production.video_contracts import VideoBindingCardinalityConstraint
    from ai_video.production.hashing import canonical_sha256

    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO, capability_id="card-i2v"
    ).model_copy(
        update={
            "binding_cardinality_constraints": (
                VideoBindingCardinalityConstraint(
                    roles=("first_frame",), min_count=1, max_count=1
                ),
                VideoBindingCardinalityConstraint(
                    roles=("reference",), min_count=0, max_count=0
                ),
            )
        }
    )
    capabilities = _capabilities(variant)
    context = _context(
        important=True,
        keyframe=_asset("first_frame", "keyframe", HASH_A),
    )
    decision = VideoGenerationResolver().resolve(
        context=context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=variant.capability_id,
        output_requirement=_output(),
    )
    assert decision.outcome is RoutingOutcome.SELECTED
    legacy_dump = variant.model_dump(mode="json", exclude={"binding_cardinality_constraints"})
    assert decision.selected_capability_fingerprint != canonical_sha256(legacy_dump)
