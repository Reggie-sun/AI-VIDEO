"""Offline provider mappings for the sealed neutral generation requirement."""

from __future__ import annotations

from pathlib import Path

import ai_video.production.minimax_h3 as h3_module
import ai_video.production.minimax_hailuo as hailuo_module
import pytest

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
    ProviderVideoRequestCompiler,
)
from ai_video.production.video import ProviderProfilePointer, VideoGenerationMode
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    AssetEvidence,
    AudioNeed,
    ContinuityMode as RequirementContinuityMode,
    GenerationMode as RequirementGenerationMode,
    OutputGeometryPolicy,
    OutputNeed,
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
from test_production_comfy_video import _profile_and_comfy_root


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
    projection = _replace_requirement(
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
                compiler_version="1",
            ),
        )

        assert routing.decision.outcome is RoutingOutcome.SELECTED
        assert routing.provider_bound_request is not None
        compiled = family.compile_request(
            routing.provider_bound_request,
            projection.requirement,
        )
        assert isinstance(compiled, CompiledProviderVideoRequest)
        assert compiled.request.image_bindings == ()
        assert compiled.request.media_bindings == ()
        resolved = family.resolve(compiled.request)
        assert resolved.provider_name == "comfy-local-h3-t8"
        assert resolved.capability_id == capability_id
        assert resolved.effective_output.native_audio is True


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
