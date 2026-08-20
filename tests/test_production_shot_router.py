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
    ContinuityMode,
    MotionRequirement,
    RouterAssetIdentity,
    RouterContinuityState,
    RouterPolicyIdentity,
    RouterReasonCode,
    RoutingOutcome,
    ShotRoutingContext,
    ShotVisualResolver,
    VideoGenerationResolver,
    VideoRoutingPolicy,
)
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
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement


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
    width: int = 1024,
    height: int = 576,
) -> RouterAssetIdentity:
    return RouterAssetIdentity(
        role=role,
        asset_id=f"asset-{suffix}",
        asset_sha256=sha256,
        mime_type=(
            mime_type
            or ("video/mp4" if role == "existing_video" else "image/png")
        ),
        size_bytes=size_bytes,
        width=width,
        height=height,
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
        character_bible_content_hashes=character_bible_hashes,
        scene_content_hash=scene_content_hash,
        important_character_ids=important_character_ids,
        canonical_character_references=character_references,
        canonical_scene_reference=scene_reference,
        approved_existing_video=existing_video,
        shot_keyframe=keyframe,
        upstream_terminal=terminal,
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
        )
        scene_reference = _asset(
            "scene_reference",
            f"{case['scene_id']}-reference",
            case["scene_hash"],
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
        dimension_mode="exact",
        width=1366,
        height=768,
        resolution_label="768P",
        ratio="16:9",
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
    assert hailuo_decision.outcome is RoutingOutcome.SELECTED
    assert (
        hailuo_decision.selected_capability_id == hailuo_i2v_variant.capability_id
    )
    assert hailuo_decision.required_binding_roles == ("first_frame",)
    assert hailuo_decision.input_assets == (terminal,)
    assert hailuo_decision.reason_codes == (
        RouterReasonCode.EXACT_TERMINAL_USES_FIRST_FRAME,
    )
