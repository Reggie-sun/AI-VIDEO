from __future__ import annotations

from types import SimpleNamespace

from pydantic import ValidationError
import pytest

from ai_video.production.hashing import canonical_sha256, seal_artifact
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
    ContinuityProviderRouteBinding,
    ContinuityMode,
    MotionRequirement,
    ProviderRouteIdentity,
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
from ai_video.production._video_requirement_routing import requirement_bindings
from ai_video.production.video_requirement import (
    AssetEvidence,
    AudioNeed,
    AxisContinuity,
    CapabilityNeed,
    ContinuityMode as RequirementContinuityMode,
    ExpressionStrength,
    GenerationIntent,
    GenerationMode as RequirementGenerationMode,
    MotionRequirement as RequirementMotionRequirement,
    OutputNeed,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    SemanticReferenceRole,
    SpaceContinuity,
    VerifiedGenerationRequirementProjection,
)
from tests.fixtures.planning_factory import make_character, make_scene
from ai_video.production.video_compiler import compile_provider_video_request
from ai_video.production.video import (
    BillingKind,
    ContinuityArtifactIdentity,
    ContinuityConstraintSet,
    ContinuityReferenceBinding,
    ProviderProfilePointer,
    TerminalFrameEvidence,
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
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    RuntimeSeal,
    StackComponentIdentity,
)
from ai_video.production.video_transition import (
    BoundaryKind,
    ContinuityAnchorBinding,
    ContinuityAnchorRole,
    ContinuityObligation,
    ContinuityTransitionPolicy,
    CreativeArtifactIdentity,
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


def test_c4_requirement_bindings_use_exact_native_multi_anchor_order():
    terminal = _asset("continuity_terminal", "terminal", HASH_A)
    endpoint = _asset("last_frame", "endpoint", HASH_B)
    identity = _asset("character_reference", "identity", HASH_C)
    motion_tail = _asset(
        "reference_video",
        "motion-tail",
        HASH_D,
        mime_type="video/mp4",
        duration_millis=500,
        fps=24,
    )
    requirement = SimpleNamespace(
        c4_multi_anchor_binding=object(),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.APPROVED_ENDPOINT,
                asset_id=endpoint.asset_id,
                asset_sha256=endpoint.asset_sha256,
                mime_type=endpoint.mime_type,
                width=endpoint.width,
                height=endpoint.height,
                size_bytes=endpoint.size_bytes,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.CONTINUITY_MOTION_TAIL,
                asset_id=motion_tail.asset_id,
                asset_sha256=motion_tail.asset_sha256,
                mime_type=motion_tail.mime_type,
                width=motion_tail.width,
                height=motion_tail.height,
                size_bytes=motion_tail.size_bytes,
                duration_millis=motion_tail.duration_millis,
                fps=motion_tail.fps,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.CONTINUITY_TERMINAL,
                asset_id=terminal.asset_id,
                asset_sha256=terminal.asset_sha256,
                mime_type=terminal.mime_type,
                width=terminal.width,
                height=terminal.height,
                size_bytes=terminal.size_bytes,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.IDENTITY,
                asset_id=identity.asset_id,
                asset_sha256=identity.asset_sha256,
                mime_type=identity.mime_type,
                width=identity.width,
                height=identity.height,
                size_bytes=identity.size_bytes,
            ),
        ),
    )
    context = SimpleNamespace(
        canonical_character_references=(identity,),
        canonical_scene_reference=None,
        shot_keyframe=None,
        upstream_terminal=terminal,
        last_frame=endpoint,
        reference_videos=(motion_tail,),
        reference_audios=(),
    )

    roles, assets = requirement_bindings(requirement, context) or ((), ())

    assert roles == ("first_frame", "last_frame", "reference", "reference_video")
    assert tuple(asset.asset_id for asset in assets) == (
        terminal.asset_id,
        endpoint.asset_id,
        identity.asset_id,
        motion_tail.asset_id,
    )


def test_multi_anchor_context_fails_closed_without_sealed_c4_requirement():
    context = _context(continuity=ContinuityMode.MULTI_ANCHOR)

    visual = ShotVisualResolver().resolve(context, _policy())
    with pytest.raises(
        ValueError,
        match="must use resolve_requirement with sequence evidence",
    ):
        VideoGenerationResolver().inspect_capability(
            context=context,
            policy=_policy(),
            provider_profile=_profile(),
            capabilities=_capabilities(
                _variant(VideoGenerationMode.IMAGE_TO_VIDEO)
            ),
            selected_capability_id="capability-image_to_video",
            output_requirement=_output(),
        )

    assert visual.outcome is RoutingOutcome.BLOCKED_MISSING_INPUT
    assert visual.reason_codes == (
        RouterReasonCode.MULTI_ANCHOR_REQUIREMENT_REQUIRED,
    )


def test_c4_static_requirement_routes_and_compiles_exact_request():
    from ai_video.production._video_continuity import C4SemanticBoundaryState
    from test_production_video import (
        _c4_binding,
        _c4_cardinality,
    )

    context = _context(
        continuity=ContinuityMode.MULTI_ANCHOR,
        terminal=_asset("continuity_terminal", "terminal", "7" * 64),
        last_frame=_asset("last_frame", "endpoint", "f" * 64),
        character_references=(
            _asset("character_reference", "c4-identity", "e" * 64),
        ),
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="test-c4-compiler",
        compiler_version="1",
    )
    source_context = _context(
        shot_id="shot-1",
        continuity=ContinuityMode.NONE,
        keyframe=_asset("first_frame", "c4-source-opening", HASH_A),
        important=False,
    )
    source_lifecycle = _lifecycle(source_context).model_copy(
        update={
            "input_artifact_ids": (
                source_context.target_shot_id,
                source_context.shot_keyframe.asset_id,
            ),
            "seal_terminal_frame": True,
        }
    )
    previous_bound = _route_first_frame(
        source_context,
        provider_name="exact-provider",
        provider_kind="local_test",
        model_id="model-test",
        profile_id="exact-profile",
        profile_sha256=HASH_D,
        lifecycle=source_lifecycle,
        compiler_contract=compiler,
    )
    continuity_lifecycle = _terminal_lifecycle(
        context,
        source_context=source_context,
        source_bound_request=previous_bound,
    )
    assert continuity_lifecycle.continuity_binding is not None
    binding = _c4_binding(
        terminal=continuity_lifecycle.continuity_binding.terminal_frame,
        selected_registry_revision_id=HASH_F,
        identity_changes={"registry_revision_id": HASH_F},
        endpoint_changes={
            "target_shot_id": context.target_shot_id,
            "target_shot_revision": context.target_shot_revision,
            "target_shot_content_hash": context.target_shot_content_hash,
            "registry_revision_id": HASH_F,
            "duration_milliseconds": 4_000,
        },
        semantic_boundary=C4SemanticBoundaryState.create(
            target_shot_id=context.target_shot_id,
            target_shot_revision=context.target_shot_revision,
            target_shot_content_hash=context.target_shot_content_hash,
            open_state=("exact terminal",),
            must_hold=("canonical identity and axis",),
            changes_here=("decelerate into approved endpoint",),
            close_state=("approved endpoint",),
        ),
    )
    terminal_asset = context.upstream_terminal.model_copy(
        update={
            "asset_id": binding.terminal.extracted_asset_id,
            "asset_sha256": binding.terminal.extracted_sha256,
            "mime_type": binding.terminal.extracted_mime_type,
            "size_bytes": binding.terminal.extracted_size_bytes,
            "width": binding.terminal.extracted_width,
            "height": binding.terminal.extracted_height,
        }
    )
    endpoint_asset = context.last_frame.model_copy(
        update={
            "asset_id": binding.approved_endpoint.asset_id,
            "asset_sha256": binding.approved_endpoint.asset_sha256,
            "mime_type": binding.approved_endpoint.asset_mime_type,
            "size_bytes": binding.approved_endpoint.asset_size_bytes,
            "width": binding.approved_endpoint.asset_width,
            "height": binding.approved_endpoint.asset_height,
        }
    )
    identity_asset = context.canonical_character_references[0].model_copy(
        update={
            "asset_id": binding.identity_anchor.asset_id,
            "asset_sha256": binding.identity_anchor.asset_sha256,
            "mime_type": binding.identity_anchor.asset_mime_type,
            "size_bytes": binding.identity_anchor.asset_size_bytes,
            "width": binding.identity_anchor.asset_width,
            "height": binding.identity_anchor.asset_height,
        }
    )
    context = context.model_copy(
        update={
            "upstream_terminal": terminal_asset,
            "last_frame": endpoint_asset,
            "canonical_character_references": (identity_asset,),
        }
    )
    evidence = (
        AssetEvidence(
            role=SemanticReferenceRole.CONTINUITY_TERMINAL,
            asset_id=terminal_asset.asset_id,
            asset_sha256=terminal_asset.asset_sha256,
            mime_type=terminal_asset.mime_type,
            width=terminal_asset.width,
            height=terminal_asset.height,
            size_bytes=terminal_asset.size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.APPROVED_ENDPOINT,
            asset_id=endpoint_asset.asset_id,
            asset_sha256=endpoint_asset.asset_sha256,
            mime_type=endpoint_asset.mime_type,
            width=endpoint_asset.width,
            height=endpoint_asset.height,
            size_bytes=endpoint_asset.size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.IDENTITY,
            asset_id=identity_asset.asset_id,
            asset_sha256=identity_asset.asset_sha256,
            mime_type=identity_asset.mime_type,
            width=identity_asset.width,
            height=identity_asset.height,
            size_bytes=identity_asset.size_bytes,
        ),
    )
    intent = GenerationIntent(
        space_continuity=SpaceContinuity(
            subject_position="preserve exact screen-space position",
            screen_direction="left_to_right",
        ),
        axis_continuity=AxisContinuity(
            camera_axis="same_side",
            framing_continuity="preserve subject scale",
        ),
    )
    character = make_character().model_copy(
        update={
            "artifact_id": "character-001",
            "revision": 3,
            "content_hash": HASH_C,
        }
    )
    requirement = ProviderNeutralVideoRequirement.create(
        source_request_content_hash=HASH_A,
        intent_evidence_hash=HASH_B,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        target_shot=context.activated_shot,
        scene=make_scene(scene_id=context.activated_shot.scene_id),
        characters=(character,),
        asset_evidence=evidence,
        c4_multi_anchor_binding=binding,
        generation_mode=RequirementGenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.MULTI_ANCHOR,
        motion_requirement=RequirementMotionRequirement.CHARACTER_ACTION,
        generation_intent=intent,
        semantic_reference_roles=tuple(item.role for item in evidence),
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
    projection = VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=HASH_D,
        verified_source_request_content_hash=HASH_A,
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )
    variant = _variant(VideoGenerationMode.IMAGE_TO_VIDEO).model_copy(
        update={
            "allowed_image_roles": ("first_frame", "last_frame", "reference"),
            "max_reference_count": 1,
            "binding_cardinality_constraints": _c4_cardinality(motion=False),
        }
    )
    lifecycle = _lifecycle(context).model_copy(
        update={
            "input_artifact_ids": (
                context.target_shot_id,
                binding.terminal.source_shot_id,
                binding.terminal.source_video_asset_id,
                terminal_asset.asset_id,
                binding.terminal.source_provenance_receipt_id,
                binding.terminal.extraction_receipt_id,
                binding.terminal_materialization_receipt_id,
                identity_asset.asset_id,
                binding.identity_anchor.source_provenance_receipt_id,
                binding.identity_anchor.materialization_receipt_id,
                endpoint_asset.asset_id,
                binding.approved_endpoint.source_provenance_receipt_id,
                binding.approved_endpoint.materialization_receipt_id,
                binding.approved_endpoint.feasibility_receipt.receipt_id,
                (
                    binding.approved_endpoint.feasibility_receipt.human_approval_receipt_id
                ),
            )
        }
    )
    profile = _profile()
    capabilities = _capabilities(variant)
    source_route = _bound_route_identity(previous_bound)
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=capabilities.variants[0],
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=context,
        lifecycle=lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=source_route,
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )
    incomplete_variant = variant.model_copy(
        update={"binding_cardinality_constraints": ()}
    )
    incomplete_capabilities = _capabilities(incomplete_variant)
    incomplete_destination_route = _selected_route_identity(
        provider_name=incomplete_capabilities.provider_name,
        variant=incomplete_capabilities.variants[0],
        provider_profile=profile,
        compiler_contract=compiler,
    )
    incomplete_transition = _transition_policy(
        source_context=source_context,
        target_context=context,
        lifecycle=lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=source_route,
        destination_route=incomplete_destination_route,
    )
    incomplete_routing = _continuity_routing(
        transition=incomplete_transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=incomplete_destination_route,
    )
    incomplete = VideoGenerationResolver()._bind_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=incomplete_capabilities,
        selected_capability_id=incomplete_variant.capability_id,
        output_requirement=_output(),
        lifecycle=lifecycle,
        compiler_contract=compiler,
        continuity_routing=incomplete_routing,
    )
    stale_binding = _c4_binding(
        endpoint_changes={
            "target_shot_id": context.target_shot_id,
            "target_shot_revision": context.target_shot_revision,
            "target_shot_content_hash": context.target_shot_content_hash,
            "duration_milliseconds": 4_000,
        },
        semantic_boundary=binding.semantic_boundary,
    )
    stale_evidence = (
        AssetEvidence(
            role=SemanticReferenceRole.CONTINUITY_TERMINAL,
            asset_id=stale_binding.terminal.extracted_asset_id,
            asset_sha256=stale_binding.terminal.extracted_sha256,
            mime_type=stale_binding.terminal.extracted_mime_type,
            width=stale_binding.terminal.extracted_width,
            height=stale_binding.terminal.extracted_height,
            size_bytes=stale_binding.terminal.extracted_size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.APPROVED_ENDPOINT,
            asset_id=stale_binding.approved_endpoint.asset_id,
            asset_sha256=stale_binding.approved_endpoint.asset_sha256,
            mime_type=stale_binding.approved_endpoint.asset_mime_type,
            width=stale_binding.approved_endpoint.asset_width,
            height=stale_binding.approved_endpoint.asset_height,
            size_bytes=stale_binding.approved_endpoint.asset_size_bytes,
        ),
        AssetEvidence(
            role=SemanticReferenceRole.IDENTITY,
            asset_id=stale_binding.identity_anchor.asset_id,
            asset_sha256=stale_binding.identity_anchor.asset_sha256,
            mime_type=stale_binding.identity_anchor.asset_mime_type,
            width=stale_binding.identity_anchor.asset_width,
            height=stale_binding.identity_anchor.asset_height,
            size_bytes=stale_binding.identity_anchor.asset_size_bytes,
        ),
    )
    stale_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **requirement.model_dump(
                mode="python",
                exclude={
                    "requirement_id",
                    "requirement_hash",
                    "c4_multi_anchor_binding",
                },
            ),
            "c4_multi_anchor_binding": stale_binding,
            "asset_evidence": stale_evidence,
        }
    )
    stale_projection = VerifiedGenerationRequirementProjection.create(
        requirement=stale_requirement,
        plan_hash=HASH_D,
        verified_source_request_content_hash=HASH_A,
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )

    with pytest.raises(
        ValueError,
        match="full continuity terminal does not match",
    ):
        VideoGenerationResolver()._bind_requirement(
            projection=stale_projection,
            context=context,
            policy=_policy(),
            provider_profile=profile,
            capabilities=capabilities,
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=lifecycle,
            compiler_contract=compiler,
            continuity_routing=continuity_routing,
        )

    routed = VideoGenerationResolver()._bind_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id=variant.capability_id,
        output_requirement=_output(),
        lifecycle=lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert incomplete.decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert incomplete.provider_bound_request is None
    assert routed.decision.outcome is RoutingOutcome.SELECTED, (
        routed.decision.reason_codes,
        routed.decision.rationale,
    )
    assert routed.provider_bound_request is not None
    compiled = compile_provider_video_request(
        provider_bound=routed.provider_bound_request,
        requirement=requirement,
        compiler_id=compiler.compiler_id,
        compiler_version=compiler.compiler_version,
        capabilities=_capabilities(variant),
    )
    assert compiled.request.c4_multi_anchor_binding == binding
    assert tuple(item.role for item in compiled.request.image_bindings) == (
        "first_frame",
        "last_frame",
        "reference",
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
    provider_kind: str = "local_test",
    model_id: str = "model-test",
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
        provider_kind=provider_kind,
        model_id=model_id,
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


def _capabilities(
    *variants: VideoCapabilityVariant,
    provider_name: str = "exact-provider",
) -> VideoProviderCapabilities:
    return VideoProviderCapabilities.create(
        provider_name=provider_name,
        variants=variants,
    )


def _profile(
    *,
    profile_id: str = "exact-profile",
    profile_sha256: str = HASH_D,
) -> ProviderProfilePointer:
    from pathlib import Path

    return ProviderProfilePointer(
        profile_id=profile_id,
        profile_version="1",
        profile_path=Path(f"provider-profiles/{profile_sha256}.json"),
        profile_sha256=profile_sha256,
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
        characters=tuple(
            make_character(character_id=character_id)
            for character_id in context.activated_shot.character_ids
        ),
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


def _exact_terminal_projection(
    context: ShotRoutingContext,
) -> VerifiedGenerationRequirementProjection:
    terminal = context.upstream_terminal
    assert terminal is not None
    original = _verified_requirement(context)
    intent = original.requirement.generation_intent.model_copy(
        update={
            "space_continuity": SpaceContinuity(
                subject_position="preserve exact screen-space position",
                screen_direction="left_to_right",
            ),
            "axis_continuity": AxisContinuity(
                camera_axis="same_side",
                framing_continuity="preserve subject scale",
            ),
        }
    )
    requirement = ProviderNeutralVideoRequirement.create(
        **{
            **original.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "generation_mode": RequirementGenerationMode.IMAGE_TO_VIDEO,
            "continuity_mode": RequirementContinuityMode.EXACT_TERMINAL,
            "semantic_reference_roles": (
                SemanticReferenceRole.CONTINUITY_TERMINAL,
            ),
            "asset_evidence": (
                AssetEvidence(
                    role=SemanticReferenceRole.CONTINUITY_TERMINAL,
                    asset_id=terminal.asset_id,
                    asset_sha256=terminal.asset_sha256,
                    mime_type=terminal.mime_type,
                    width=terminal.width,
                    height=terminal.height,
                    size_bytes=terminal.size_bytes,
                ),
            ),
            "capability_need": CapabilityNeed(
                needs_first_frame=True,
                needs_terminal_reference=True,
            ),
            "generation_intent": intent,
        }
    )
    return VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=original.plan_hash,
        verified_source_request_content_hash=(
            original.verified_source_request_content_hash
        ),
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )


def _first_frame_projection(
    context: ShotRoutingContext,
) -> VerifiedGenerationRequirementProjection:
    first_frame = context.shot_keyframe
    assert first_frame is not None
    original = _verified_requirement(context)
    requirement = ProviderNeutralVideoRequirement.create(
        **{
            **original.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "generation_mode": RequirementGenerationMode.IMAGE_TO_VIDEO,
            "semantic_reference_roles": (SemanticReferenceRole.FIRST_FRAME,),
            "asset_evidence": (
                AssetEvidence(
                    role=SemanticReferenceRole.FIRST_FRAME,
                    asset_id=first_frame.asset_id,
                    asset_sha256=first_frame.asset_sha256,
                    mime_type=first_frame.mime_type,
                    width=first_frame.width,
                    height=first_frame.height,
                    size_bytes=first_frame.size_bytes,
                ),
            ),
            "capability_need": CapabilityNeed(needs_first_frame=True),
        }
    )
    return VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=original.plan_hash,
        verified_source_request_content_hash=(
            original.verified_source_request_content_hash
        ),
        target_shot_id=context.target_shot_id,
        target_shot_revision=context.target_shot_revision,
        target_shot_content_hash=context.target_shot_content_hash,
    )


def _identity_reference_projection(
    context: ShotRoutingContext,
) -> VerifiedGenerationRequirementProjection:
    identity = context.canonical_character_references[0]
    character = make_character(character_id=context.important_character_ids[0])
    requirement = ProviderNeutralVideoRequirement.create(
        source_request_content_hash=HASH_A,
        intent_evidence_hash=HASH_B,
        generation_intent_hash=HASH_C,
        target_shot=context.activated_shot,
        scene=make_scene(scene_id=context.activated_shot.scene_id),
        characters=(character,),
        generation_mode=RequirementGenerationMode.REFERENCE_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.REFERENCE,
        motion_requirement=RequirementMotionRequirement.FREE_COMPLEX,
        generation_intent=GenerationIntent(),
        semantic_reference_roles=(SemanticReferenceRole.IDENTITY,),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.IDENTITY,
                asset_id=identity.asset_id,
                asset_sha256=identity.asset_sha256,
                canonical_owner_id=identity.canonical_owner_id,
                canonical_owner_content_hash=(
                    identity.canonical_owner_content_hash
                ),
                mime_type=identity.mime_type,
                width=identity.width,
                height=identity.height,
                size_bytes=identity.size_bytes,
            ),
        ),
        capability_need=CapabilityNeed(
            needs_identity_reference=True,
            max_reference_count=1,
        ),
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


def _terminal_lifecycle(
    context: ShotRoutingContext,
    *,
    source_context: ShotRoutingContext | None = None,
    source_bound_request=None,
) -> VideoGenerationLifecycleEnvelope:
    terminal = context.upstream_terminal
    assert terminal is not None
    base = _lifecycle(context)
    continuity_binding = None
    input_ids = [context.target_shot_id, terminal.asset_id]
    if source_context is not None:
        assert source_bound_request is not None
        source_registry = source_bound_request.lifecycle.base_registry
        evidence = TerminalFrameEvidence.create(
            source_shot_id=source_context.target_shot_id,
            source_shot_revision=source_context.target_shot_revision,
            source_shot_content_hash=source_context.target_shot_content_hash,
            source_video_asset_id=source_bound_request.lifecycle.output_asset_id,
            source_video_sha256=HASH_B,
            source_generation_id=source_bound_request.lifecycle.generation_id,
            source_request_input_hash=(
                source_bound_request.provider_bound_request_hash
            ),
            source_resolved_generation_hash=(
                source_bound_request.provider_bound_request_hash
            ),
            source_provenance_receipt_id="source-video-provenance",
            extraction_receipt_id=HASH_E,
            source_registry=source_registry,
            source_container_name="mp4",
            source_codec_name="h264",
            source_width=terminal.width,
            source_height=terminal.height,
            source_fps_numerator=24,
            source_fps_denominator=1,
            source_duration_milliseconds=4000,
            source_frame_count=96,
            frame_index=95,
            timestamp_numerator=95,
            timestamp_denominator=24,
            selection_rule="generated_candidate_terminal",
            extraction_contract_version="terminal-frame-v1",
            extractor_name="ffmpeg",
            extractor_version="7.1",
            extracted_asset_id=terminal.asset_id,
            extracted_sha256=terminal.asset_sha256,
            extracted_mime_type="image/png",
            extracted_size_bytes=terminal.size_bytes,
            extracted_width=terminal.width,
            extracted_height=terminal.height,
            extracted_color_space="bt709",
        )
        constraints = ContinuityConstraintSet.create(
            scene_identity=ContinuityArtifactIdentity(
                artifact_id=context.activated_shot.scene_id,
                revision=1,
                content_hash=context.scene_content_hash,
            ),
            character_identities=(
                ContinuityArtifactIdentity(
                    artifact_id="continuity-subject",
                    revision=1,
                    content_hash=HASH_A,
                ),
            ),
            camera_axis="preserve screen axis",
            framing="preserve subject scale",
            lighting="preserve motivated lighting",
            color="preserve palette",
            motion_direction="preserve motion vector",
            exit_state="source terminal",
            entrance_state="target opening",
        )
        continuity_binding = ContinuityReferenceBinding.create(
            role="first_frame",
            terminal_frame=evidence,
            target_shot_id=context.target_shot_id,
            target_shot_revision=context.target_shot_revision,
            target_shot_content_hash=context.target_shot_content_hash,
            constraints=constraints,
        )
        input_ids.extend(
            (
                source_context.target_shot_id,
                source_bound_request.lifecycle.output_asset_id,
            )
        )
    return base.model_copy(
        update={
            "input_artifact_ids": tuple(dict.fromkeys(input_ids)),
            "continuity_binding": continuity_binding,
            "seal_terminal_frame": True,
        }
    )


def _route_first_frame(
    context: ShotRoutingContext,
    *,
    provider_name: str,
    provider_kind: str,
    model_id: str,
    profile_id: str,
    profile_sha256: str,
    lifecycle: VideoGenerationLifecycleEnvelope,
    compiler_contract: AdapterCompilerContract | None = None,
):
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind=provider_kind,
        model_id=model_id,
    )
    result = VideoGenerationResolver()._bind_requirement(
        projection=_first_frame_projection(context),
        context=context,
        policy=_policy(),
        provider_profile=_profile(
            profile_id=profile_id,
            profile_sha256=profile_sha256,
        ),
        capabilities=_capabilities(variant, provider_name=provider_name),
        selected_capability_id=variant.capability_id,
        output_requirement=_output(),
        lifecycle=lifecycle,
        compiler_contract=(
            compiler_contract
            or AdapterCompilerContract.create(
                compiler_id="continuity-test-compiler",
                compiler_version="1",
            )
        ),
    )
    assert result.provider_bound_request is not None
    return result.provider_bound_request


def _bound_route_identity(bound_request) -> ProviderRouteIdentity:
    return ProviderRouteIdentity.create(
        provider_name=bound_request.provider_name,
        provider_kind=bound_request.provider_kind,
        model_id=bound_request.model_id,
        provider_profile=bound_request.provider_profile,
        capability_id=bound_request.capability_id,
        capability_fingerprint=bound_request.capability_fingerprint,
        execution_kind=bound_request.execution_kind,
        billing_kind=bound_request.billing_kind,
        compiler_contract=bound_request.compiler_contract,
    )


def _selected_route_identity(
    *,
    provider_name: str,
    variant: VideoCapabilityVariant,
    provider_profile: ProviderProfilePointer,
    compiler_contract: AdapterCompilerContract,
) -> ProviderRouteIdentity:
    from ai_video.production._video_capability_fingerprint import (
        capability_variant_fingerprint,
    )

    return ProviderRouteIdentity.create(
        provider_name=provider_name,
        provider_kind=variant.provider_kind,
        model_id=variant.model_id,
        provider_profile=provider_profile,
        capability_id=variant.capability_id,
        capability_fingerprint=capability_variant_fingerprint(variant),
        execution_kind=variant.execution_kind,
        billing_kind=variant.billing_kind,
        compiler_contract=compiler_contract,
    )


def _execution_stack_identity(
    route: ProviderRouteIdentity,
    *,
    workflow_hash: str = "none",
    runtime_content_hash: str | None = None,
    output_contract_hash: str = HASH_0,
) -> GenerationExecutionStackIdentity:
    return GenerationExecutionStackIdentity.create(
        materialization_status="materialized",
        candidate_id=route.provider_name,
        contract_version=route.compiler_contract.compiler_version,
        provider_kind=route.provider_kind,
        deployment_identity=route.provider_name,
        model_id=route.model_id,
        capability_id=route.capability_id,
        profile_hash=route.provider_profile.profile_sha256,
        compiler_hash=route.compiler_contract.compiler_hash,
        workflow_hash=workflow_hash,
        components=(
            StackComponentIdentity(
                ordinal=0,
                kind="artifact",
                component_id=route.model_id,
                content_hash=route.capability_fingerprint,
            ),
        ),
        sampler_identity="provider_managed",
        scheduler_identity="provider_managed",
        runtime_seals=(
            RuntimeSeal(
                name=route.provider_kind,
                version=route.model_id,
                content_hash=(
                    runtime_content_hash or route.capability_fingerprint
                ),
            ),
        ),
        output_contract_hash=output_contract_hash,
    )


def _continuity_routing(
    *,
    transition: ContinuityTransitionPolicy,
    previous_bound,
    previous_shot: Shot,
    destination_route: ProviderRouteIdentity,
    source_execution_stack: GenerationExecutionStackIdentity | None = None,
    destination_execution_stack: GenerationExecutionStackIdentity | None = None,
) -> ContinuityProviderRouteBinding:
    source_route = _bound_route_identity(previous_bound)
    return ContinuityProviderRouteBinding.create(
        transition_policy=transition,
        previous_shot=previous_shot,
        previous_provider_bound_request=previous_bound,
        source_route=source_route,
        destination_route=destination_route,
        source_execution_stack=(
            source_execution_stack or _execution_stack_identity(source_route)
        ),
        destination_execution_stack=(
            destination_execution_stack
            or _execution_stack_identity(destination_route)
        ),
    )


def _transition_policy(
    *,
    source_context: ShotRoutingContext,
    target_context: ShotRoutingContext,
    lifecycle: VideoGenerationLifecycleEnvelope,
    boundary: BoundaryKind,
    obligation: ContinuityObligation,
    source_route: ProviderRouteIdentity,
    destination_route: ProviderRouteIdentity,
    source_execution_stack: GenerationExecutionStackIdentity | None = None,
    destination_execution_stack: GenerationExecutionStackIdentity | None = None,
) -> ContinuityTransitionPolicy:
    source_stack = source_execution_stack or _execution_stack_identity(source_route)
    destination_stack = (
        destination_execution_stack
        or _execution_stack_identity(destination_route)
    )
    if obligation is ContinuityObligation.FULL_CONTINUITY:
        anchors = tuple(
            ContinuityAnchorBinding(
                role=role,
                source_kind="planned_derivation",
                source_identity=f"{source_context.target_shot_id}-{role.value}",
                content_hash={
                    ContinuityAnchorRole.FIRST_FRAME: HASH_A,
                    ContinuityAnchorRole.LAST_FRAME: HASH_B,
                    ContinuityAnchorRole.REFERENCE: HASH_C,
                    ContinuityAnchorRole.REFERENCE_VIDEO: HASH_D,
                }[role],
                evidence_fingerprint={
                    ContinuityAnchorRole.FIRST_FRAME: HASH_B,
                    ContinuityAnchorRole.LAST_FRAME: HASH_C,
                    ContinuityAnchorRole.REFERENCE: HASH_D,
                    ContinuityAnchorRole.REFERENCE_VIDEO: HASH_E,
                }[role],
            )
            for role in ContinuityAnchorRole
        )
        dimensions = (
            "camera_velocity",
            "identity",
            "screen_axis",
            "subject_position",
        )
    elif obligation is ContinuityObligation.IDENTITY_STYLE_CARRYOVER:
        anchors = (
            ContinuityAnchorBinding(
                role=ContinuityAnchorRole.REFERENCE,
                source_kind="planned_derivation",
                source_identity=f"{source_context.target_shot_id}-identity",
                content_hash=HASH_C,
                evidence_fingerprint=HASH_D,
            ),
        )
        dimensions = ("identity",)
    else:
        anchors = ()
        dimensions = ()
    return ContinuityTransitionPolicy.create(
        policy_id=f"{source_context.target_shot_id}-{target_context.target_shot_id}",
        project=lifecycle.base_project,
        registry=lifecycle.base_registry,
        source_shot=CreativeArtifactIdentity(
            artifact_id=source_context.activated_shot.artifact_id,
            revision=source_context.target_shot_revision,
            content_hash=source_context.target_shot_content_hash,
        ),
        target_shot=CreativeArtifactIdentity(
            artifact_id=target_context.activated_shot.artifact_id,
            revision=target_context.target_shot_revision,
            content_hash=target_context.target_shot_content_hash,
        ),
        boundary_kind=boundary,
        continuity_obligation=obligation,
        take_id=(
            "take-continuity-test"
            if boundary is BoundaryKind.WITHIN_CONTINUOUS_TAKE
            else None
        ),
        source_execution_stack_hash=source_stack.execution_stack_hash,
        destination_execution_stack_hash=destination_stack.execution_stack_hash,
        continuity_grade="c4_native_boundary_motion",
        required_carryover_dimensions=dimensions,
        anchors=anchors,
        qa_policy_hash=HASH_E,
        authoring_evidence_hash=HASH_F,
    )


def _sequence_fixture():
    source_context = _context(
        shot_id="shot-1",
        continuity=ContinuityMode.NONE,
        keyframe=_asset("first_frame", "shot-1-opening", HASH_A),
        important=False,
    )
    source_lifecycle = _lifecycle(source_context).model_copy(
        update={
            "input_artifact_ids": (
                source_context.target_shot_id,
                source_context.shot_keyframe.asset_id,
            ),
            "seal_terminal_frame": True,
        }
    )
    previous_bound = _route_first_frame(
        source_context,
        provider_name="continuity-provider",
        provider_kind="provider-a",
        model_id="model-a",
        profile_id="provider-a-profile",
        profile_sha256=HASH_A,
        lifecycle=source_lifecycle,
    )
    terminal = _asset("continuity_terminal", "shot-1-terminal", HASH_E)
    target_context = _context(
        shot_id="shot-2",
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
        important=False,
    )
    target_lifecycle = _terminal_lifecycle(
        target_context,
        source_context=source_context,
        source_bound_request=previous_bound,
    )
    return source_context, previous_bound, target_context, target_lifecycle, terminal


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

    result = VideoGenerationResolver()._resolve_capability(
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


def test_continuity_bearing_direct_resolve_requires_sequence_api() -> None:
    terminal = _asset("continuity_terminal", "terminal", HASH_C)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
    )
    capabilities = _capabilities(_variant(VideoGenerationMode.IMAGE_TO_VIDEO))

    with pytest.raises(
        ValueError,
        match="must use resolve_requirement with sequence evidence",
    ):
        VideoGenerationResolver().inspect_capability(
            context=context,
            policy=_policy(),
            provider_profile=_profile(),
            capabilities=capabilities,
            selected_capability_id="capability-image_to_video",
            output_requirement=_output(),
        )


def test_continuous_take_rejects_lower_cost_provider_preselection() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    lower_cost_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="lower-cost-model",
    )
    locked_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-a",
        model_id="model-a",
    )
    locked_profile = _profile(
        profile_id="provider-a-profile",
        profile_sha256=HASH_A,
    )
    locked_capabilities = _capabilities(
        locked_variant,
        provider_name="continuity-provider",
    )
    source_route = _bound_route_identity(previous_bound)
    locked_route = _selected_route_identity(
        provider_name=locked_capabilities.provider_name,
        variant=locked_variant,
        provider_profile=locked_profile,
        compiler_contract=compiler,
    )
    assert locked_route == source_route
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=source_route,
        destination_route=locked_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=locked_route,
    )

    rejected = VideoGenerationResolver()._bind_requirement(
        projection=_exact_terminal_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=_profile(
            profile_id="lower-cost-profile",
            profile_sha256=HASH_C,
        ),
        capabilities=_capabilities(
            lower_cost_variant,
            provider_name="lower-cost-provider",
        ),
        selected_capability_id=lower_cost_variant.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )
    selected = VideoGenerationResolver()._bind_requirement(
        projection=_exact_terminal_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=locked_profile,
        capabilities=locked_capabilities,
        selected_capability_id=locked_variant.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert rejected.decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert rejected.decision.reason_codes == (
        RouterReasonCode.CONTINUITY_PROVIDER_LOCKED,
    )
    assert rejected.provider_bound_request is None
    assert selected.decision.outcome is RoutingOutcome.SELECTED
    assert selected.provider_bound_request is not None
    assert selected.provider_bound_request.provider_name == "continuity-provider"


def test_hard_cut_identity_carryover_allows_new_provider_route() -> None:
    (
        source_context,
        previous_bound,
        _,
        _,
        terminal,
    ) = _sequence_fixture()
    character = make_character()
    identity_reference = _asset(
        "character_reference",
        "hard-cut-identity",
        HASH_A,
        canonical_owner_id=character.character_id,
        canonical_owner_content_hash=character.content_hash,
    )
    target_context = _context(
        shot_id="shot-2",
        continuity=ContinuityMode.REFERENCE,
        terminal=terminal,
        continuity_state=_continuity_state(),
        motion=MotionRequirement.FREE_COMPLEX,
        important_character_ids=(character.character_id,),
        character_bible_hashes=(character.content_hash,),
        character_references=(identity_reference,),
    )
    identity = target_context.canonical_character_references[0]
    target_lifecycle = _lifecycle(target_context).model_copy(
        update={
            "input_artifact_ids": (
                target_context.target_shot_id,
                identity.asset_id,
            )
        }
    )
    variant = _variant(
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )
    profile = _profile(
        profile_id="provider-b-profile",
        profile_sha256=HASH_C,
    )
    capabilities = _capabilities(variant, provider_name="provider-b")
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=variant,
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
        source_route=_bound_route_identity(previous_bound),
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )

    result = VideoGenerationResolver()._bind_requirement(
        projection=_identity_reference_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id=variant.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert result.decision.outcome is RoutingOutcome.SELECTED, (
        result.decision.reason_codes,
        result.decision.rationale,
    )
    assert result.decision.required_binding_roles == ("reference",)
    assert result.decision.input_assets == (identity,)
    assert result.provider_bound_request is not None
    assert result.provider_bound_request.provider_name == "provider-b"


def test_identity_carryover_cannot_seal_none_t2v_route() -> None:
    source_context, previous_bound, _, _, _ = _sequence_fixture()
    target_context = _context(
        shot_id="shot-2",
        continuity=ContinuityMode.NONE,
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
    )
    lifecycle = _lifecycle(target_context)
    variant = _variant(
        VideoGenerationMode.TEXT_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )
    profile = _profile(
        profile_id="provider-b-profile",
        profile_sha256=HASH_C,
    )
    capabilities = _capabilities(variant, provider_name="provider-b")
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=variant,
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
        source_route=_bound_route_identity(previous_bound),
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )

    with pytest.raises(
        ValueError,
        match=(
            "identity/style carryover requires reference or semantic "
            "continuity mode"
        ),
    ):
        VideoGenerationResolver()._bind_requirement(
            projection=_verified_requirement(target_context),
            context=target_context,
            policy=_policy(),
            provider_profile=profile,
            capabilities=capabilities,
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=lifecycle,
            compiler_contract=compiler,
            continuity_routing=continuity_routing,
        )


def test_explicit_cross_provider_full_continuity_binds_previous_terminal_first() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        terminal,
    ) = _sequence_fixture()
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )
    profile = _profile(
        profile_id="provider-b-profile",
        profile_sha256=HASH_C,
    )
    capabilities = _capabilities(variant, provider_name="provider-b")
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=variant,
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=_bound_route_identity(previous_bound),
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )

    result = VideoGenerationResolver()._bind_requirement(
        projection=_exact_terminal_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id=variant.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert result.decision.outcome is RoutingOutcome.SELECTED
    assert result.decision.required_binding_roles[0] == "first_frame"
    assert result.decision.input_assets[0] == terminal
    assert result.decision.continuity_transition_policy_hash == transition.policy_hash
    assert result.decision.previous_provider_bound_request_hash == (
        previous_bound.provider_bound_request_hash
    )
    assert result.provider_bound_request is not None
    assert result.provider_bound_request.input_assets[0] == terminal


def test_cross_stack_gate_applies_when_provider_route_is_unchanged() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    route = _bound_route_identity(previous_bound)
    source_stack = _execution_stack_identity(route)
    destination_stack = _execution_stack_identity(
        route,
        workflow_hash=HASH_B,
    )
    assert source_stack.output_contract_hash != route.capability_fingerprint
    assert source_stack.execution_stack_hash != destination_stack.execution_stack_hash
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=route,
        destination_route=route,
        source_execution_stack=source_stack,
        destination_execution_stack=destination_stack,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=route,
        source_execution_stack=source_stack,
        destination_execution_stack=destination_stack,
    )
    projection = _exact_terminal_projection(target_context)
    incomplete_intent = GenerationIntent()
    incomplete_requirement = ProviderNeutralVideoRequirement.create(
        **{
            **projection.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            "generation_intent": incomplete_intent,
            "generation_intent_hash": canonical_sha256(
                incomplete_intent.model_dump(mode="json")
            ),
        }
    )
    incomplete_projection = VerifiedGenerationRequirementProjection.create(
        requirement=incomplete_requirement,
        plan_hash=projection.plan_hash,
        verified_source_request_content_hash=(
            projection.verified_source_request_content_hash
        ),
        target_shot_id=target_context.target_shot_id,
        target_shot_revision=target_context.target_shot_revision,
        target_shot_content_hash=target_context.target_shot_content_hash,
    )
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind=route.provider_kind,
        model_id=route.model_id,
    )

    with pytest.raises(
        ValueError,
        match="cross-stack full continuity requires explicit spatial and camera intent",
    ):
        VideoGenerationResolver()._bind_requirement(
            projection=incomplete_projection,
            context=target_context,
            policy=_policy(),
            provider_profile=route.provider_profile,
            capabilities=_capabilities(
                variant,
                provider_name=route.provider_name,
            ),
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=target_lifecycle,
            compiler_contract=route.compiler_contract,
            continuity_routing=continuity_routing,
        )


def test_reference_only_provider_cannot_claim_cross_stack_spatial_continuity() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    reference_only = _variant(
        VideoGenerationMode.REFERENCE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="identity-reference-only",
    )
    profile = _profile(
        profile_id="provider-b-reference-profile",
        profile_sha256=HASH_C,
    )
    capabilities = _capabilities(
        reference_only,
        provider_name="reference-only-provider",
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=reference_only,
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=_bound_route_identity(previous_bound),
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )

    result = VideoGenerationResolver()._bind_requirement(
        projection=_exact_terminal_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id=reference_only.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert result.decision.outcome is RoutingOutcome.BLOCKED_CAPABILITY
    assert result.decision.reason_codes == (
        RouterReasonCode.CONTINUITY_FRAME_CONDITIONING_REQUIRED,
    )
    assert result.provider_bound_request is None


def test_continuity_requirement_cannot_omit_sequence_route_binding() -> None:
    (
        _,
        _,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )

    with pytest.raises(
        ValueError,
        match="requires exact sequence routing evidence",
    ):
        VideoGenerationResolver()._bind_requirement(
            projection=_exact_terminal_projection(target_context),
            context=target_context,
            policy=_policy(),
            provider_profile=_profile(
                profile_id="provider-b-profile",
                profile_sha256=HASH_C,
            ),
            capabilities=_capabilities(variant, provider_name="provider-b"),
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=target_lifecycle,
            compiler_contract=AdapterCompilerContract.create(
                compiler_id="continuity-test-compiler",
                compiler_version="1",
            ),
        )


def test_full_continuity_rejects_binding_for_another_target_shot() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    lifecycle_binding = target_lifecycle.continuity_binding
    assert lifecycle_binding is not None
    stale_binding = ContinuityReferenceBinding.create(
        **{
            **lifecycle_binding.model_dump(
                mode="python",
                exclude={"binding_hash"},
            ),
            "target_shot_id": "shot-other",
            "target_shot_revision": 1,
            "target_shot_content_hash": HASH_D,
        }
    )
    stale_lifecycle = target_lifecycle.model_copy(
        update={"continuity_binding": stale_binding}
    )
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )
    profile = _profile(
        profile_id="provider-b-profile",
        profile_sha256=HASH_C,
    )
    capabilities = _capabilities(variant, provider_name="provider-b")
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    destination_route = _selected_route_identity(
        provider_name=capabilities.provider_name,
        variant=variant,
        provider_profile=profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=_bound_route_identity(previous_bound),
        destination_route=destination_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=destination_route,
    )

    with pytest.raises(
        ValueError,
        match="does not match the exact current target",
    ):
        VideoGenerationResolver()._bind_requirement(
            projection=_exact_terminal_projection(target_context),
            context=target_context,
            policy=_policy(),
            provider_profile=profile,
            capabilities=capabilities,
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=stale_lifecycle,
            compiler_contract=compiler,
            continuity_routing=continuity_routing,
        )


def test_stale_transition_hash_cannot_release_provider_lock() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    source_route = _bound_route_identity(previous_bound)
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=source_route,
        destination_route=source_route,
    )
    routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=source_route,
    )
    stale_policy = transition.model_copy(
        update={"destination_execution_stack_hash": HASH_B}
    )
    stale_routing = routing.model_copy(
        update={"transition_policy": stale_policy}
    )
    variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-a",
        model_id="model-a",
    )

    with pytest.raises(ValidationError):
        VideoGenerationResolver()._bind_requirement(
            projection=_exact_terminal_projection(target_context),
            context=target_context,
            policy=_policy(),
            provider_profile=_profile(
                profile_id="provider-a-profile",
                profile_sha256=HASH_A,
            ),
            capabilities=_capabilities(
                variant,
                provider_name="continuity-provider",
            ),
            selected_capability_id=variant.capability_id,
            output_requirement=_output(),
            lifecycle=target_lifecycle,
            compiler_contract=AdapterCompilerContract.create(
                compiler_id="continuity-test-compiler",
                compiler_version="1",
            ),
            continuity_routing=stale_routing,
        )


def test_cross_stack_binding_rejects_unsealed_destination_provider() -> None:
    (
        source_context,
        previous_bound,
        target_context,
        target_lifecycle,
        _,
    ) = _sequence_fixture()
    compiler = AdapterCompilerContract.create(
        compiler_id="continuity-test-compiler",
        compiler_version="1",
    )
    sealed_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-b",
        model_id="model-b",
    )
    sealed_profile = _profile(
        profile_id="provider-b-profile",
        profile_sha256=HASH_C,
    )
    sealed_route = _selected_route_identity(
        provider_name="provider-b",
        variant=sealed_variant,
        provider_profile=sealed_profile,
        compiler_contract=compiler,
    )
    transition = _transition_policy(
        source_context=source_context,
        target_context=target_context,
        lifecycle=target_lifecycle,
        boundary=BoundaryKind.HARD_CUT,
        obligation=ContinuityObligation.FULL_CONTINUITY,
        source_route=_bound_route_identity(previous_bound),
        destination_route=sealed_route,
    )
    continuity_routing = _continuity_routing(
        transition=transition,
        previous_bound=previous_bound,
        previous_shot=source_context.activated_shot,
        destination_route=sealed_route,
    )
    unsealed_variant = _variant(
        VideoGenerationMode.IMAGE_TO_VIDEO,
        provider_kind="provider-c",
        model_id="model-c",
    )
    unsealed_profile = _profile(
        profile_id="provider-c-profile",
        profile_sha256=HASH_D,
    )
    unsealed_capabilities = _capabilities(
        unsealed_variant,
        provider_name="provider-c",
    )
    unsealed_route = _selected_route_identity(
        provider_name=unsealed_capabilities.provider_name,
        variant=unsealed_variant,
        provider_profile=unsealed_profile,
        compiler_contract=compiler,
    )

    with pytest.raises(
        ValueError,
        match="policy must bind exact source and destination execution stacks",
    ):
        _continuity_routing(
            transition=transition,
            previous_bound=previous_bound,
            previous_shot=source_context.activated_shot,
            destination_route=unsealed_route,
        )

    result = VideoGenerationResolver()._bind_requirement(
        projection=_exact_terminal_projection(target_context),
        context=target_context,
        policy=_policy(),
        provider_profile=unsealed_profile,
        capabilities=unsealed_capabilities,
        selected_capability_id=unsealed_variant.capability_id,
        output_requirement=_output(),
        lifecycle=target_lifecycle,
        compiler_contract=compiler,
        continuity_routing=continuity_routing,
    )

    assert result.decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert result.decision.reason_codes == (
        RouterReasonCode.CONTINUITY_DESTINATION_ROUTE_MISMATCH,
    )
    assert result.provider_bound_request is None


def test_free_motion_can_use_text_to_video_without_identity_or_continuity() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver()._resolve_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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
    generation = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    first = VideoGenerationResolver().inspect_capability(
        context=_context(
            character_references=(first_reference, second_reference),
            scene_reference=scene_reference,
        ),
        **common,
    )
    second = VideoGenerationResolver().inspect_capability(
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

    blocked = VideoGenerationResolver().inspect_capability(
        policy=_policy(),
        **kwargs,
    )
    selected = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver()._resolve_capability(
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
        decision = VideoGenerationResolver()._resolve_capability(
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

    decision = VideoGenerationResolver()._resolve_capability(
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

    decision = VideoGenerationResolver()._resolve_capability(
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

    decision = VideoGenerationResolver().inspect_capability(
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

    decision = VideoGenerationResolver()._resolve_capability(
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
    first = VideoGenerationResolver()._resolve_capability(
        context=_context(
            continuity=ContinuityMode.SEMANTIC,
            continuity_state=first_state,
        ),
        **common,
    )
    second = VideoGenerationResolver()._resolve_capability(
        context=_context(
            continuity=ContinuityMode.SEMANTIC,
            continuity_state=second_state,
        ),
        **common,
    )
    none = VideoGenerationResolver().inspect_capability(
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

    first = VideoGenerationResolver().inspect_capability(
        policy=_policy(policy_hash=HASH_A),
        **kwargs,
    )
    second = VideoGenerationResolver().inspect_capability(
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

    first = VideoGenerationResolver().inspect_capability(
        capabilities=_capabilities(selected, unused),
        **common,
    )
    second = VideoGenerationResolver().inspect_capability(
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


@pytest.mark.parametrize("entrypoint", ["resolve", "resolve_requirement", "planner"])
@pytest.mark.parametrize("references_available", [False, True])
def test_explicit_t2v_cannot_downgrade_important_character(
    entrypoint: str, references_available: bool,
) -> None:
    context = _context()
    if not references_available:
        context = context.model_copy(update={
            "canonical_character_references": (),
            "canonical_scene_reference": None,
        })
    context = context.model_copy(update={
        "allowed_generation_modes": (VideoGenerationMode.TEXT_TO_VIDEO,),
    })
    kwargs = {
        "context": context,
        "policy": _policy(),
        "provider_profile": _profile(),
        "capabilities": _capabilities(
            _variant(VideoGenerationMode.TEXT_TO_VIDEO),
            _variant(VideoGenerationMode.IMAGE_TO_VIDEO),
            _variant(VideoGenerationMode.REFERENCE_TO_VIDEO),
        ),
        "selected_capability_id": "capability-text_to_video",
        "output_requirement": _output(),
    }
    if entrypoint == "resolve":
        decision = VideoGenerationResolver().inspect_capability(
            **kwargs, requirement_mode=VideoGenerationMode.TEXT_TO_VIDEO,
            requirement_binding_roles=(), requirement_input_assets=(),
        )
    else:
        projection = _verified_requirement(context)
        if entrypoint == "planner":
            from ai_video.planning import VideoPlanner, require_current_video_plan
            from ai_video.production.video_requirement import (
                GenerationOperation,
                MotionEnvelope,
                ProviderNeutralGenerationIntentProjection,
                SubjectAction,
            )
            from tests.fixtures.planning_factory import make_request

            requirement = projection.requirement
            request = make_request(
                target_shot=context.activated_shot,
                scene_context=requirement.scene,
                character_context=requirement.characters,
                available_assets=(),
                review_decision=None,
                planning_contract_version="video-planner/3",
                generation_intent=ProviderNeutralGenerationIntentProjection.create(
                    generation_intent=GenerationIntent(
                        subject_action=SubjectAction(
                            start_state="seated beside the window",
                            progression="raises the left hand toward the glass",
                        ),
                        motion_envelope=MotionEnvelope(
                            onset="immediate", peak="raises hand", settle="holds",
                        ),
                    ),
                    generation_operation=GenerationOperation.TEXT_TO_VIDEO,
                    output_need=requirement.output_need,
                    audio_need=requirement.audio_need,
                    quality_need=requirement.quality_need,
                ),
            )
            projection = require_current_video_plan(
                current_request=request, plan=VideoPlanner().plan(request),
            )
        result = VideoGenerationResolver()._bind_requirement(
            **kwargs, projection=projection,
            lifecycle=_lifecycle(context),
            compiler_contract=AdapterCompilerContract.create(
                compiler_id="fake-video-compiler", compiler_version="1",
            ),
        )
        assert result.provider_bound_request is None
        decision = result.decision

    assert decision.outcome is RoutingOutcome.BLOCKED_POLICY
    assert decision.reason_codes == (
        RouterReasonCode.IMPORTANT_CHARACTER_REQUIRES_VISUAL_ANCHOR,
    )
    assert decision.required_mode is VideoGenerationMode.TEXT_TO_VIDEO
    assert decision.selected_mode is None


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

    first = VideoGenerationResolver()._bind_requirement(**kwargs)
    second = VideoGenerationResolver()._bind_requirement(**kwargs)

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

    result = VideoGenerationResolver()._bind_requirement(
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

    result = VideoGenerationResolver()._bind_requirement(
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

    selected = VideoGenerationResolver().inspect_capability(
        context=context,
        policy=_policy(),
        provider_profile=profile,
        capabilities=capabilities,
        selected_capability_id="minimax-h3-t8-t2va-quality-v1",
        output_requirement=output,
    )
    turbo_selected = VideoGenerationResolver().inspect_capability(
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
    missing = VideoGenerationResolver().inspect_capability(
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

    h3_decision = VideoGenerationResolver()._resolve_capability(
        context=context,
        policy=_policy(),
        provider_profile=h3_profile,
        capabilities=h3_capabilities,
        selected_capability_id=h3_variant.capability_id,
        output_requirement=h3_output,
    )
    unsupported_h3_decision = VideoGenerationResolver()._resolve_capability(
        context=context,
        policy=_policy(),
        provider_profile=h3_profile,
        capabilities=h3_capabilities,
        selected_capability_id=h3_variant.capability_id,
        output_requirement=h3_output.model_copy(
            update={"width": 16384, "height": 16384}
        ),
    )
    hailuo_decision = VideoGenerationResolver()._resolve_capability(
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
    decision = VideoGenerationResolver().inspect_capability(
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

    i2va_decision = VideoGenerationResolver().inspect_capability(
        context=i2va_context,
        policy=_policy(),
        provider_profile=_profile(),
        capabilities=capabilities,
        selected_capability_id=i2va_variant.capability_id,
        output_requirement=_output(),
    )
    fl2va_decision = VideoGenerationResolver().inspect_capability(
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
    cross_decision = VideoGenerationResolver().inspect_capability(
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
    no_ref_decision = VideoGenerationResolver().inspect_capability(
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
    overflow_decision = VideoGenerationResolver().inspect_capability(
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
    decision = VideoGenerationResolver().inspect_capability(
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
    decision = VideoGenerationResolver().inspect_capability(
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
