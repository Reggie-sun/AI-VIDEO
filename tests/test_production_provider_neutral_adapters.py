"""Offline provider mappings for the sealed neutral generation requirement."""

from __future__ import annotations

from pathlib import Path

import ai_video.production.minimax_h3 as h3_module
import ai_video.production.minimax_hailuo as hailuo_module
import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production._video_requirement_routing import requirement_output_matches
from ai_video.production.comfy_video import ComfyUIVideoProvider
from ai_video.production.comfy_t8_video import (
    ComfyUIT8VideoProvider,
    load_t8_video_execution_profile,
)
from ai_video.production.comfy_t8_turbo_video import (
    ComfyUIT8TurboVideoProvider,
    load_t8_turbo_video_execution_profile,
)
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.minimax_h3 import MiniMaxH3VideoProvider
from ai_video.production.minimax_hailuo import MiniMaxHailuoVideoProvider
from ai_video.production.seedance import SeedanceVideoProvider
from ai_video.production.seedance_capabilities import (
    validate_seedance_capability_matrix,
)
from ai_video.production.shot_router import (
    AdapterCompilerContract,
    ContinuityMode,
    MotionRequirement,
    RoutingOutcome,
    VideoGenerationResolver,
)
from ai_video.production.video_compiler import (
    CompiledProviderVideoRequest,
    ProviderRequirementUnsupported,
    ProviderRequirementUnsupportedReason,
    ProviderVideoRequestCompiler,
    compile_provider_video_request,
    require_compiled_provider_request,
)
from ai_video.production.video import (
    ProviderProfilePointer,
    VideoGenerationMode,
    VideoOutputRecoveryStrategy,
    VideoProviderCapabilities,
)
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    AssetEvidence,
    AudioNeed,
    CapabilityNeed,
    ContinuityMode as RequirementContinuityMode,
    GenerationMode as RequirementGenerationMode,
    OutputGeometryPolicy,
    OutputNeed,
    Pacing,
    ProviderNeutralVideoRequirement,
    QualityNeed,
    SemanticReferenceRole,
    VerifiedGenerationRequirementProjection,
)
from test_production_minimax_h3 import _output as _h3_output
from test_production_minimax_h3 import _profile as _h3_profile
from test_production_minimax_hailuo import _i2v_output as _hailuo_i2v_output
from test_production_minimax_hailuo import _profile as _hailuo_profile
from test_production_seedance import (
    _profile as _seedance_profile,
    _profile_pointer as _seedance_profile_pointer,
    _request as _seedance_request,
)
from test_production_shot_router import (
    _asset,
    _context,
    _lifecycle,
    _policy,
    _verified_requirement,
)
from test_production_comfy_video import QUALITY_PROFILE_PATH, _profile_and_comfy_root
from tests.test_production_video_intent_validation import (
    _compatible_fl2va,
    _complete_intent,
)


def _replace_requirement(
    projection: VerifiedGenerationRequirementProjection,
    **updates: object,
) -> VerifiedGenerationRequirementProjection:
    requirement = ProviderNeutralVideoRequirement.create(
        **{
            **projection.requirement.model_dump(
                mode="python",
                exclude={"requirement_id", "requirement_hash"},
            ),
            **updates,
        }
    )
    return VerifiedGenerationRequirementProjection.create(
        requirement=requirement,
        plan_hash=projection.plan_hash,
        verified_source_request_content_hash=(
            requirement.source_request_content_hash
        ),
        target_shot_id=requirement.target_shot.shot_id,
        target_shot_revision=requirement.target_shot.revision,
        target_shot_content_hash=requirement.target_shot.content_hash,
    )


@pytest.mark.parametrize(
    "strategy",
    (None, VideoOutputRecoveryStrategy.NON_RECOVERABLE_EPHEMERAL_URL),
)
def test_remote_output_recovery_is_rejected_purely_before_compilation(
    strategy: VideoOutputRecoveryStrategy | None,
) -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    output = _h3_output()
    projection = _replace_requirement(
        _verified_requirement(context),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.OPTIONAL,
    )
    variant = h3_module._VARIANT.model_copy(
        update={"output_recovery_strategy": strategy}
    )
    capabilities = VideoProviderCapabilities.create(
        provider_name=h3_module._PROVIDER_NAME,
        variants=(variant,),
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_h3_profile(),
        capabilities=capabilities,
        selected_capability_id=h3_module._CAPABILITY_ID,
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="minimax-h3-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None

    result = compile_provider_video_request(
        provider_bound=routing.provider_bound_request,
        requirement=projection.requirement,
        compiler_id="minimax-h3-video-compiler",
        compiler_version="1",
        capabilities=capabilities,
    )

    assert isinstance(result, ProviderRequirementUnsupported)
    assert result.reason is ProviderRequirementUnsupportedReason.OUTPUT_LOCATOR_NOT_RECOVERABLE
    assert result.unsupported_field_paths == (
        "selection.output_recovery_strategy",
    )
    assert result.prompt_text is None
    assert result.payload is None
    assert variant.lookup_supported is True
    with pytest.raises(AiVideoError) as exc_info:
        require_compiled_provider_request(result)
    assert exc_info.value.code is ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED
    assert exc_info.value.retryable is False
    assert "OUTPUT_LOCATOR_NOT_RECOVERABLE" in (exc_info.value.technical_detail or "")


def test_current_remote_adapters_declare_exact_output_recovery_strategy() -> None:
    seedance_profile = _seedance_profile()

    assert {
        entry.variant.output_recovery_strategy
        for entry in seedance_profile.capabilities
    } == {VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID}
    assert (
        h3_module._VARIANT.output_recovery_strategy
        is VideoOutputRecoveryStrategy.REQUERY_BY_EFFECT_ID
    )
    assert {
        variant.output_recovery_strategy
        for variant in hailuo_module._CAPABILITIES.variants
    } == {VideoOutputRecoveryStrategy.DURABLE_FILE_ID}


def test_seedance_official_matrix_rejects_output_recovery_strategy_drift() -> None:
    profile = _seedance_profile()
    first = profile.capabilities[0]
    mutated = first.model_copy(
        update={
            "variant": first.variant.model_copy(
                update={
                    "output_recovery_strategy": (
                        VideoOutputRecoveryStrategy.NON_RECOVERABLE_EPHEMERAL_URL
                    )
                }
            )
        }
    )

    with pytest.raises(ValueError, match="frozen official variant"):
        validate_seedance_capability_matrix((mutated, *profile.capabilities[1:]))


def test_requirement_output_rejects_unproven_duration_and_ratio() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    base = _verified_requirement(context)
    provider_selected = VideoFlexibleOutputRequirement(
        timing_mode="provider_selected",
        duration_seconds=None,
        frame_count=None,
        dimension_mode="adaptive",
        width=None,
        height=None,
        resolution_label="720p",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=False,
    )
    duration_requirement = _replace_requirement(
        base,
        output_need=OutputNeed(
            timing_mode="content_driven",
            duration_seconds=4,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio="adaptive",
            fps=24,
            container_mime="video/mp4",
        ),
    ).requirement
    exact_output = _h3_output().model_copy(
        update={"width": 1024, "height": 576}
    )
    ratio_requirement = _replace_requirement(
        base,
        output_need=OutputNeed(
            duration_seconds=exact_output.duration_seconds,
            geometry_policy=OutputGeometryPolicy.EXACT,
            aspect_ratio="1:1",
            fps=exact_output.fps,
            container_mime=exact_output.mime_type,
        ),
    ).requirement

    assert not requirement_output_matches(
        duration_requirement,
        provider_selected,
    )
    assert not requirement_output_matches(ratio_requirement, exact_output)


def test_minimax_h3_compiles_neutral_t2v_to_exact_offline_capability() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    output = _h3_output()
    projection = _replace_requirement(
        _verified_requirement(context),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.OPTIONAL,
    )
    compiler = AdapterCompilerContract.create(
        compiler_id="minimax-h3-video-compiler",
        compiler_version="1",
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_h3_profile(),
        capabilities=h3_module._CAPABILITIES,
        selected_capability_id=h3_module._CAPABILITY_ID,
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=compiler,
    )
    assert routing.decision.outcome is RoutingOutcome.SELECTED
    assert routing.provider_bound_request is not None
    provider = MiniMaxH3VideoProvider(transport=object(), credential=lambda: "unused")
    assert isinstance(provider, ProviderVideoRequestCompiler)

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    resolved = provider.resolve(compiled.request)
    assert resolved.requirement_hash == projection.requirement.requirement_hash
    assert resolved.capability_id == h3_module._CAPABILITY_ID


def test_adapter_returns_typed_unsupported_for_unexpressible_quality_floor() -> None:
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    output = _h3_output()
    projection = _replace_requirement(
        _verified_requirement(context),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.OPTIONAL,
        quality_need=QualityNeed(
            objective_tier="production",
            minimum_codec="h265",
            native_enforcement_required=True,
        ),
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_h3_profile(),
        capabilities=h3_module._CAPABILITIES,
        selected_capability_id=h3_module._CAPABILITY_ID,
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="minimax-h3-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None
    provider = MiniMaxH3VideoProvider(transport=object(), credential=lambda: "unused")

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, ProviderRequirementUnsupported)
    assert compiled.prompt_text is None
    assert compiled.payload is None
    assert compiled.unsupported_field_paths == (
        "quality_need.native_enforcement_required",
        "quality_need.minimum_codec",
    )


def test_local_h3_compiles_neutral_first_frame_without_runtime_execution(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path)
    image_root = tmp_path / "images"
    image_root.mkdir()
    terminal = _asset("continuity_terminal", "local-h3-terminal", "9" * 64)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
        important=False,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=124,
        dimension_mode="exact",
        width=608,
        height=352,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=RequirementGenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.EXACT_TERMINAL,
        semantic_reference_roles=(SemanticReferenceRole.CONTINUITY_TERMINAL,),
        asset_evidence=(
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
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=608,
            height=352,
            aspect_ratio="adaptive",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.OPTIONAL,
    )
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=image_root,
        image_resolver=lambda *_: image_root / "unused.png",
        transport=object(),
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-fl2va",
            profile_version="v1",
            profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
            profile_sha256=profile.profile_content_hash,
        ),
        capabilities=provider.capabilities(),
        selected_capability_id="minimax-h3-fl2va-local-v1",
        output_requirement=output,
        lifecycle=_lifecycle(context).model_copy(
            update={
                "input_artifact_ids": (
                    context.target_shot_id,
                    terminal.asset_id,
                )
            }
        ),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.request.seed is None
    resolved = provider.resolve(compiled.request)
    assert resolved.requirement_hash == projection.requirement.requirement_hash
    assert resolved.provider_name == "comfy-local-h3"
    assert resolved.effective_seed == (
        int(compiled.request.request_input_hash[:16], 16) & ((1 << 63) - 1)
    )
    assert provider.resolve(compiled.request) == resolved


def test_stock20_v4_compiles_exact_h3_prompt_without_neutral_fallback(
    tmp_path: Path,
) -> None:
    artifact_root, comfy_root, profile = _profile_and_comfy_root(
        tmp_path, QUALITY_PROFILE_PATH
    )
    image_root = tmp_path / "images-v4"
    image_root.mkdir()
    first = _asset("continuity_terminal", "v4-first", "8" * 64)
    last = _asset("last_frame", "v4-last", "9" * 64)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=first,
        last_frame=last,
        important=False,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count",
        frame_count=124,
        dimension_mode="exact",
        width=608,
        height=352,
        resolution_label="h3_native",
        ratio="adaptive",
        fps=24,
        container="mp4",
        mime_type="video/mp4",
        native_audio=True,
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_mode=RequirementGenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.EXACT_TERMINAL,
        generation_intent=_complete_intent(),
        conditioning_compatibility=_compatible_fl2va().model_copy(
            update={
                "first_anchor_id": first.asset_id,
                "last_anchor_id": last.asset_id,
            }
        ),
        capability_need=CapabilityNeed(
            needs_first_frame=True,
            needs_last_frame=True,
            needs_continuity_state=True,
            accepts_local_execution=True,
            accepts_remote_execution=False,
        ),
        semantic_reference_roles=(
            SemanticReferenceRole.CONTINUITY_TERMINAL,
            SemanticReferenceRole.LAST_FRAME,
        ),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.CONTINUITY_TERMINAL,
                asset_id=first.asset_id,
                asset_sha256=first.asset_sha256,
                mime_type=first.mime_type,
                width=first.width,
                height=first.height,
                size_bytes=first.size_bytes,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.LAST_FRAME,
                asset_id=last.asset_id,
                asset_sha256=last.asset_sha256,
                mime_type=last.mime_type,
                width=last.width,
                height=last.height,
                size_bytes=last.size_bytes,
            ),
        ),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=608,
            height=352,
            aspect_ratio="adaptive",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.OPTIONAL,
    )
    provider = ComfyUIVideoProvider(
        profile,
        artifact_root=artifact_root,
        comfy_root=comfy_root,
        image_root=image_root,
        image_resolver=lambda *_: image_root / "unused.png",
        transport=object(),
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-fl2va",
            profile_version="v1",
            profile_path=Path(
                f"provider-profiles/{profile.profile_content_hash}.json"
            ),
            profile_sha256=profile.profile_content_hash,
        ),
        capabilities=provider.capabilities(),
        selected_capability_id="minimax-h3-fl2va-local-v1",
        output_requirement=output,
        lifecycle=_lifecycle(context).model_copy(
            update={
                "input_artifact_ids": (
                    context.target_shot_id,
                    first.asset_id,
                    last.asset_id,
                )
            }
        ),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-video-compiler",
            compiler_version="2",
        ),
    )
    assert routing.provider_bound_request is not None, routing.decision.model_dump_json(
        indent=2
    )

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.adapter_compiler_version == "2"
    assert compiled.provider_native_prompt.count("[Shot 1]") == 1
    assert "integrated_multimodal_description:" in compiled.provider_native_prompt
    assert "generation_mode=" not in compiled.provider_native_prompt

    performance = projection.requirement.generation_intent.performance_intent
    assert performance is not None
    stale_intent = projection.requirement.generation_intent.model_copy(
        update={
            "performance_intent": performance.model_copy(
                update={"trigger": "mutated after sealing"}
            )
        }
    )
    stale_requirement = projection.requirement.model_copy(
        update={"generation_intent": stale_intent}
    )
    stale = provider.compile_request(
        routing.provider_bound_request,
        stale_requirement,
    )
    assert isinstance(stale, ProviderRequirementUnsupported)
    assert stale.reason is ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH
    assert stale.unsupported_field_paths == ("requirement_hash",)

    generic = compile_provider_video_request(
        provider_bound=routing.provider_bound_request,
        requirement=projection.requirement,
        compiler_id="comfy-local-h3-video-compiler",
        compiler_version="2",
        capabilities=provider.capabilities(),
    )
    assert isinstance(generic, ProviderRequirementUnsupported)
    assert generic.reason is ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
    assert generic.unsupported_field_paths == ("generation_intent",)

    legacy_artifact_root, legacy_comfy_root, legacy_profile = _profile_and_comfy_root(
        tmp_path / "legacy"
    )
    legacy_provider = ComfyUIVideoProvider(
        legacy_profile,
        artifact_root=legacy_artifact_root,
        comfy_root=legacy_comfy_root,
        image_root=image_root,
        image_resolver=lambda *_: image_root / "unused.png",
        transport=object(),
    )
    unsupported = legacy_provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )
    assert isinstance(unsupported, ProviderRequirementUnsupported)
    assert unsupported.reason is ProviderRequirementUnsupportedReason.COMPILER_VERSION_UNSUPPORTED
    assert unsupported.unsupported_field_paths == ("provider_profile",)


def test_local_t8_family_compiles_both_exact_lanes_without_runtime_execution() -> None:
    root = Path(__file__).resolve().parents[1]
    profile = load_t8_video_execution_profile(
        root / "workflows/profiles/minimax_h3_t8_t2va_quality.json",
        artifact_root=root,
    )
    quality_provider = ComfyUIT8VideoProvider(
        profile,
        artifact_root=root,
        comfy_root=root,
        runtime_inspector=lambda: (_ for _ in ()).throw(
            AssertionError("offline compiler mapping must not inspect runtime")
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
            AssertionError("offline compiler mapping must not inspect runtime")
        ),
        transport=object(),
    )
    family = LocalH3VideoProviderFamily((quality_provider, turbo_provider))
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
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
    legacy_projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=RequirementGenerationMode.TEXT_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.NONE,
        semantic_reference_roles=(),
        asset_evidence=(),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=1344,
            height=768,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    intent = _complete_intent().model_copy(
        update={"pacing": Pacing(shot_duration_seconds=124 / 24)}
    )
    projection = _replace_requirement(
        legacy_projection,
        contract_version="provider-neutral-video-requirement/4",
        generation_mode=RequirementGenerationMode.TEXT_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(
            {
                "schema": "provider-neutral-generation-intent/2",
                "generation_intent": intent.model_dump(mode="json"),
            }
        ),
        conditioning_compatibility=None,
        semantic_reference_roles=(),
        asset_evidence=(),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=1344,
            height=768,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    lanes = (
        (
            profile,
            "minimax-h3-t8-t2va-quality",
            "minimax-h3-t8-t2va-quality-v1",
            "comfy-local-h3-t8-video-compiler",
        ),
        (
            turbo_profile,
            "minimax-h3-t8-t2va-turbo",
            "minimax-h3-t8-t2va-turbo-v1",
            "comfy-local-h3-t8-turbo-video-compiler",
        ),
    )
    for selected_profile, profile_id, capability_id, compiler_id in lanes:
        routing = VideoGenerationResolver().resolve_requirement(
            projection=projection,
            context=context,
            policy=_policy(),
            provider_profile=ProviderProfilePointer(
                profile_id=profile_id,
                profile_version="v1",
                profile_path=Path(
                    f"provider-profiles/{selected_profile.profile_content_hash}.json"
                ),
                profile_sha256=selected_profile.profile_content_hash,
            ),
            capabilities=family.capabilities(),
            selected_capability_id=capability_id,
            output_requirement=output,
            lifecycle=_lifecycle(context),
            compiler_contract=AdapterCompilerContract.create(
                compiler_id=compiler_id,
                compiler_version="3",
            ),
        )

        assert routing.decision.outcome is RoutingOutcome.SELECTED
        assert routing.provider_bound_request is not None
        compiled = family.compile_request(
            routing.provider_bound_request,
            projection.requirement,
        )
        assert isinstance(compiled, CompiledProviderVideoRequest)
        assert compiled.adapter_compiler_version == "3"
        assert "integrated_multimodal_description:" in compiled.provider_native_prompt
        assert "overall_soundscape:" in compiled.provider_native_prompt
        assert "non_diegetic_music:" in compiled.provider_native_prompt
        assert "generation_mode=" not in compiled.provider_native_prompt
        assert "scene_mood={" not in compiled.provider_native_prompt
        assert compiled.request.image_bindings == ()
        assert compiled.request.media_bindings == ()
        resolved = family.resolve(compiled.request)
        assert resolved.provider_name == "comfy-local-h3-t8"
        assert resolved.capability_id == capability_id
        assert resolved.effective_output.native_audio is True

        legacy_routing = VideoGenerationResolver().resolve_requirement(
            projection=legacy_projection,
            context=context,
            policy=_policy(),
            provider_profile=ProviderProfilePointer(
                profile_id=profile_id,
                profile_version="v1",
                profile_path=Path(
                    f"provider-profiles/{selected_profile.profile_content_hash}.json"
                ),
                profile_sha256=selected_profile.profile_content_hash,
            ),
            capabilities=family.capabilities(),
            selected_capability_id=capability_id,
            output_requirement=output,
            lifecycle=_lifecycle(context),
            compiler_contract=AdapterCompilerContract.create(
                compiler_id=compiler_id,
                compiler_version="3",
            ),
        )
        assert legacy_routing.provider_bound_request is not None
        unsupported = family.compile_request(
            legacy_routing.provider_bound_request,
            legacy_projection.requirement,
        )
        assert isinstance(unsupported, ProviderRequirementUnsupported)
        assert unsupported.reason is (
            ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED
        )
        assert "generation_intent.open_state" in unsupported.unsupported_field_paths


def test_t8_quality_native_compiler_uses_h3_three_field_prompt_without_neutral_field_leakage() -> None:
    root = Path(__file__).resolve().parents[1]
    profile = load_t8_video_execution_profile(
        root / "workflows/profiles/minimax_h3_t8_t2va_quality.json",
        artifact_root=root,
    )
    provider = ComfyUIT8VideoProvider(
        profile,
        artifact_root=root,
        comfy_root=root,
        runtime_inspector=lambda: (_ for _ in ()).throw(
            AssertionError("offline compiler mapping must not inspect runtime")
        ),
        transport=object(),
    )
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
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
    native_intent = _complete_intent().model_copy(
        update={
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=RequirementGenerationMode.TEXT_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.NONE,
        generation_intent=native_intent,
        capability_need=CapabilityNeed(
            needs_native_audio=True,
            accepts_local_execution=True,
            accepts_remote_execution=False,
        ),
        semantic_reference_roles=(),
        asset_evidence=(),
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=124,
            geometry_policy=OutputGeometryPolicy.EXACT,
            width=1344,
            height=768,
            aspect_ratio="16:9",
            fps=24,
            container_mime="video/mp4",
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-t8-t2va-quality",
            profile_version="v1",
            profile_path=Path(
                f"provider-profiles/{profile.profile_content_hash}.json"
            ),
            profile_sha256=profile.profile_content_hash,
        ),
        capabilities=provider.capabilities(),
        selected_capability_id="minimax-h3-t8-t2va-quality-v1",
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-video-compiler",
            compiler_version="3",
        ),
    )
    assert routing.provider_bound_request is not None

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.adapter_compiler_version == "3"
    assert compiled.provider_native_prompt.count("[Shot 1]") == 1
    assert "integrated_multimodal_description:" in compiled.provider_native_prompt
    assert "overall_soundscape:" in compiled.provider_native_prompt
    assert "non_diegetic_music:" in compiled.provider_native_prompt
    assert "generation_mode=" not in compiled.provider_native_prompt
    assert "scene_mood=" not in compiled.provider_native_prompt
    assert "scene_constraints=" not in compiled.provider_native_prompt

    malformed_requirement = projection.requirement.model_copy(
        update={"generation_intent": "oops"}
    )
    malformed = provider.compile_request(
        routing.provider_bound_request,
        malformed_requirement,
    )
    assert isinstance(malformed, ProviderRequirementUnsupported)
    assert malformed.reason is ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH

    stale_projection = _replace_requirement(
        projection,
        source_request_content_hash="e" * 64,
    )
    stale = provider.compile_request(
        routing.provider_bound_request,
        stale_projection.requirement,
    )
    assert isinstance(stale, ProviderRequirementUnsupported)
    assert stale.reason is ProviderRequirementUnsupportedReason.LINEAGE_MISMATCH

    legacy_compiler_routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(),
        provider_profile=ProviderProfilePointer(
            profile_id="minimax-h3-t8-t2va-quality",
            profile_version="v1",
            profile_path=Path(
                f"provider-profiles/{profile.profile_content_hash}.json"
            ),
            profile_sha256=profile.profile_content_hash,
        ),
        capabilities=provider.capabilities(),
        selected_capability_id="minimax-h3-t8-t2va-quality-v1",
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-video-compiler",
            compiler_version="2",
        ),
    )
    assert legacy_compiler_routing.provider_bound_request is not None
    legacy_compiler = provider.compile_request(
        legacy_compiler_routing.provider_bound_request,
        projection.requirement,
    )
    assert isinstance(legacy_compiler, ProviderRequirementUnsupported)
    assert legacy_compiler.reason is (
        ProviderRequirementUnsupportedReason.COMPILER_VERSION_UNSUPPORTED
    )


def test_hailuo_compiles_first_frame_to_adaptive_i2v_without_fixed_pixels() -> None:
    terminal = _asset("continuity_terminal", "hailuo-terminal", "c" * 64)
    context = _context(
        continuity=ContinuityMode.EXACT_TERMINAL,
        terminal=terminal,
        important=False,
    )
    output = _hailuo_i2v_output()
    projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=RequirementGenerationMode.IMAGE_TO_VIDEO,
        continuity_mode=RequirementContinuityMode.EXACT_TERMINAL,
        semantic_reference_roles=(SemanticReferenceRole.CONTINUITY_TERMINAL,),
        asset_evidence=(
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
        output_need=OutputNeed(
            timing_mode="frame_count",
            frame_count=output.frame_count,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio="adaptive",
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.FORBIDDEN,
    )
    lifecycle = _lifecycle(context).model_copy(
        update={"input_artifact_ids": (context.target_shot_id, terminal.asset_id)}
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_hailuo_profile(),
        capabilities=hailuo_module._CAPABILITIES,
        selected_capability_id=hailuo_module._I2V_CAPABILITY_ID,
        output_requirement=output,
        lifecycle=lifecycle,
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="minimax-hailuo-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None
    provider = MiniMaxHailuoVideoProvider(
        transport=object(),
        credential=lambda: "unused",
    )

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.request.output_requirement.width is None
    assert compiled.request.output_requirement.height is None
    resolved = provider.resolve(compiled.request)
    assert resolved.capability_id == hailuo_module._I2V_CAPABILITY_ID


def test_seedance_compiles_exact_profile_t2v_without_materialization_or_network() -> None:
    profile = _seedance_profile()
    request_fixture = _seedance_request(profile)
    output = request_fixture.output_requirement
    context = _context(motion=MotionRequirement.FREE_COMPLEX, important=False)
    projection = _replace_requirement(
        _verified_requirement(context),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            aspect_ratio=output.ratio,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: "unused",
        input_reference=object(),
    )
    selected = tuple(
        variant
        for variant in provider.capabilities().variants
        if variant.model_id == request_fixture.model_id
        and variant.mode is request_fixture.mode
        and variant.output_capability is not None
        and variant.output_capability.supports(output)
    )
    assert len(selected) == 1
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_seedance_profile_pointer(profile),
        capabilities=provider.capabilities(),
        selected_capability_id=selected[0].capability_id,
        output_requirement=output,
        lifecycle=_lifecycle(context),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="seedance-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    resolved = provider.resolve(compiled.request)
    assert resolved.capability_id == selected[0].capability_id
    assert resolved.effective_output == output


def test_seedance_r2v_preserves_multiple_typed_video_and_audio_references() -> None:
    profile = _seedance_profile()
    output = _seedance_request(profile).output_requirement
    video = _asset(
        "reference_video",
        "seedance-video",
        "d" * 64,
        mime_type="video/mp4",
        width=1280,
        height=720,
        duration_millis=5_000,
        fps=24,
    )
    video_two = _asset(
        "reference_video",
        "seedance-video-two",
        "f" * 64,
        mime_type="video/mp4",
        width=1280,
        height=720,
        duration_millis=5_000,
        fps=24,
    )
    audio = _asset(
        "reference_audio",
        "seedance-audio",
        "e" * 64,
        mime_type="audio/mpeg",
        width=None,
        height=None,
        duration_millis=5_000,
        fps=None,
    )
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
        reference_videos=(video, video_two),
        reference_audios=(audio,),
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=RequirementGenerationMode.REFERENCE_TO_VIDEO,
        semantic_reference_roles=(
            SemanticReferenceRole.VIDEO_REFERENCE,
            SemanticReferenceRole.AUDIO_REFERENCE,
        ),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.VIDEO_REFERENCE,
                asset_id=video.asset_id,
                asset_sha256=video.asset_sha256,
                mime_type=video.mime_type,
                width=video.width,
                height=video.height,
                size_bytes=video.size_bytes,
                duration_millis=video.duration_millis,
                fps=video.fps,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.AUDIO_REFERENCE,
                asset_id=audio.asset_id,
                asset_sha256=audio.asset_sha256,
                mime_type=audio.mime_type,
                size_bytes=audio.size_bytes,
                duration_millis=audio.duration_millis,
            ),
            AssetEvidence(
                role=SemanticReferenceRole.VIDEO_REFERENCE,
                asset_id=video_two.asset_id,
                asset_sha256=video_two.asset_sha256,
                mime_type=video_two.mime_type,
                width=video_two.width,
                height=video_two.height,
                size_bytes=video_two.size_bytes,
                duration_millis=video_two.duration_millis,
                fps=video_two.fps,
            ),
        ),
        output_need=OutputNeed(
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            aspect_ratio=output.ratio,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: "unused",
        input_reference=object(),
    )
    selected = next(
        variant
        for variant in provider.capabilities().variants
        if variant.model_id == "doubao-seedance-2-5-260628"
        and variant.mode is VideoGenerationMode.REFERENCE_TO_VIDEO
    )
    lifecycle = _lifecycle(context).model_copy(
        update={
            "input_artifact_ids": (
                context.target_shot_id,
                audio.asset_id,
                video.asset_id,
                video_two.asset_id,
            )
        }
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_seedance_profile_pointer(profile),
        capabilities=provider.capabilities(),
        selected_capability_id=selected.capability_id,
        output_requirement=output,
        lifecycle=lifecycle,
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="seedance-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert tuple(binding.role for binding in compiled.request.media_bindings) == (
        "reference_video",
        "reference_video",
        "reference_audio",
    )
    resolved = provider.resolve(compiled.request)
    assert resolved.capability_id == selected.capability_id


@pytest.mark.parametrize(
    ("requirement_mode", "provider_mode"),
    [
        (RequirementGenerationMode.VIDEO_EDIT, VideoGenerationMode.VIDEO_EDIT),
        (RequirementGenerationMode.VIDEO_EXTEND, VideoGenerationMode.VIDEO_EXTEND),
    ],
)
def test_seedance_edit_and_extend_neutral_modes_reach_exact_offline_capability(
    requirement_mode: RequirementGenerationMode,
    provider_mode: VideoGenerationMode,
) -> None:
    profile = _seedance_profile()
    base_output = _seedance_request(profile).output_requirement
    output = VideoFlexibleOutputRequirement(
        timing_mode=(
            "provider_selected"
            if provider_mode is VideoGenerationMode.VIDEO_EDIT
            else "exact_seconds"
        ),
        duration_seconds=(
            None
            if provider_mode is VideoGenerationMode.VIDEO_EDIT
            else base_output.duration_seconds
        ),
        dimension_mode="adaptive",
        width=None,
        height=None,
        resolution_label=base_output.resolution_label,
        ratio="adaptive",
        fps=base_output.fps,
        container=base_output.container,
        mime_type=base_output.mime_type,
        native_audio=base_output.native_audio,
    )
    video = _asset(
        "reference_video",
        "seedance-source-video",
        "7" * 64,
        mime_type="video/mp4",
        width=1280,
        height=720,
        duration_millis=5_000,
        fps=24,
    )
    context = _context(
        motion=MotionRequirement.FREE_COMPLEX,
        important=False,
        reference_videos=(video,),
    )
    projection = _replace_requirement(
        _verified_requirement(context),
        generation_mode=requirement_mode,
        semantic_reference_roles=(SemanticReferenceRole.VIDEO_REFERENCE,),
        asset_evidence=(
            AssetEvidence(
                role=SemanticReferenceRole.VIDEO_REFERENCE,
                asset_id=video.asset_id,
                asset_sha256=video.asset_sha256,
                mime_type=video.mime_type,
                width=video.width,
                height=video.height,
                size_bytes=video.size_bytes,
                duration_millis=video.duration_millis,
                fps=video.fps,
            ),
        ),
        output_need=OutputNeed(
            timing_mode=(
                "provider_selected"
                if output.timing_mode == "provider_selected"
                else "fixed"
            ),
            duration_seconds=output.duration_seconds,
            width=output.width,
            height=output.height,
            geometry_policy=OutputGeometryPolicy.ADAPTIVE,
            aspect_ratio=output.ratio,
            fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.OPTIONAL,
    )
    provider = SeedanceVideoProvider(
        profile=profile,
        transport=object(),
        credential=lambda: "unused",
        input_reference=object(),
    )
    selected = next(
        variant
        for variant in provider.capabilities().variants
        if variant.model_id == "doubao-seedance-2-5-260628"
        and variant.mode is provider_mode
    )
    routing = VideoGenerationResolver().resolve_requirement(
        projection=projection,
        context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=_seedance_profile_pointer(profile),
        capabilities=provider.capabilities(),
        selected_capability_id=selected.capability_id,
        output_requirement=output,
        lifecycle=_lifecycle(context).model_copy(
            update={
                "input_artifact_ids": (
                    context.target_shot_id,
                    video.asset_id,
                )
            }
        ),
        compiler_contract=AdapterCompilerContract.create(
            compiler_id="seedance-video-compiler",
            compiler_version="1",
        ),
    )
    assert routing.provider_bound_request is not None

    compiled = provider.compile_request(
        routing.provider_bound_request,
        projection.requirement,
    )

    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.request.mode is provider_mode
    assert tuple(item.role for item in compiled.request.media_bindings) == (
        "reference_video",
    )
    assert provider.resolve(compiled.request).capability_id == selected.capability_id
