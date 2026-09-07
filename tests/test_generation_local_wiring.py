"""Offline common-caller wiring for registered Local video adapters.

These tests compile and resolve only.  Their transports/runtime inspectors fail
if touched, so they cannot submit, start ComfyUI, or generate media.
"""

from pathlib import Path

import pytest

from ai_video.production.comfy_t8_native_turbo_video import ComfyUIT8NativeTurboVideoProvider
from ai_video.production.comfy_video import ComfyUIVideoProvider
from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget,
)
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.local_h3_provider_family import LocalH3VideoProviderFamily
from ai_video.production.hashing import canonical_sha256
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video import ProviderProfilePointer
from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
from ai_video.production.video_requirement import (
    AssetEvidence, AudioNeed, CapabilityNeed, ConditioningLane, GenerationMode,
    OutputNeed, SemanticReferenceRole,
)
from ai_video.production.video_compiler import CompiledProviderVideoRequest

from test_production_comfy_t8_turbo_video import _provider as turbo_provider
from test_production_comfy_t8_video import _provider as quality_provider
from test_production_comfy_t8_native_turbo_video import (
    PROFILE_PATHS as NATIVE_PROFILE_PATHS,
    _load as native_profile,
)
from test_production_comfy_video import QUALITY_PROFILE_PATH, _profile_and_comfy_root
from test_production_generation_decision import acceptance_policy, setup_decision
from test_production_h3_prompt import _requirement as h3_prompt_requirement
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_shot_router import _asset, _context, _lifecycle, _verified_requirement
from tests.test_production_video_intent_validation import _compatible_fl2va


REPO_ROOT = Path(__file__).parents[1]


def forbidden(*args, **kwargs):
    raise AssertionError("offline local wiring must not touch transport, credentials, or runtime")


def _output(profile, *, label="h3_t8_native"):
    return VideoFlexibleOutputRequirement(
        timing_mode="frame_count", frame_count=getattr(profile, "frame_count", 124),
        dimension_mode="exact", width=getattr(profile, "width", 608), height=getattr(profile, "height", 352),
        resolution_label=label, ratio="16:9" if label == "h3_t8_native" else "adaptive",
        fps=profile.fps, container="mp4", mime_type="video/mp4", native_audio=True,
    )


def _acceptance():
    return acceptance_policy((RequirementExpression(
        requirement_id="hand", level="acceptance", stage="raw_generation",
        dimension="action", observable="hand action remains visible",
        tolerance="exact", measurement="frozen viewing", proof="analyzer",
        intent_paths=("generation_intent.performance_intent.hand_behavior",),
        native_text=(), production_owner="shot_authoring",
    ),))


def _projection(setup, output, *, image_to_video=False):
    intent = h3_prompt_requirement().generation_intent
    if image_to_video:
        duration = output.frame_count / output.fps
        intent = intent.model_copy(update={
            "pacing": intent.pacing.model_copy(
                update={"shot_duration_seconds": duration}
            )
        })
    updates = {
        "contract_version": "provider-neutral-video-requirement/4",
        "generation_intent": intent,
        "generation_intent_hash": canonical_sha256({
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }),
        "output_need": OutputNeed(
            timing_mode="frame_count", frame_count=output.frame_count,
            width=output.width, height=output.height, fps=output.fps,
            container_mime=output.mime_type),
        "audio_need": AudioNeed.REQUIRED,
    }
    if image_to_video:
        first = setup["context"].shot_keyframe
        assert first is not None
        updates.update({
            "generation_mode": GenerationMode.IMAGE_TO_VIDEO,
            "conditioning_compatibility": _compatible_fl2va().model_copy(update={
                "lane": ConditioningLane.I2VA, "first_anchor_id": first.asset_id,
                "last_anchor_id": None, "available_duration_seconds": duration,
            }),
            "capability_need": CapabilityNeed(needs_first_frame=True, accepts_local_execution=True,
                                                accepts_remote_execution=False),
        })
    return _replace_requirement(setup["projection"], **updates)


def _prepare(*, provider, profile, compiler, output, setup, projection):
    lifecycle = setup["lifecycle"]
    if projection.requirement.generation_mode is GenerationMode.IMAGE_TO_VIDEO:
        first = setup["context"].shot_keyframe
        lifecycle = lifecycle.model_copy(update={"input_artifact_ids": (
            *dict.fromkeys((*lifecycle.input_artifact_ids,
                            setup["context"].target_shot_id, first.asset_id)),)})
    current = {**{key: value for key, value in setup.items() if key != "inputs"},
               "projection": projection, "lifecycle": lifecycle,
               "acceptance": _acceptance()}
    limits = setup["inputs"].limits.model_copy(update={
        "allowed_remote_candidates": (),
    })
    orchestrator = GenerationFeedbackOrchestrator(
        targets=(RegisteredGenerationTarget(provider, profile, compiler, output),),
        context_loader=lambda: current, history_loader=GenerationHistory,
        policy=DecisionPolicy(allow_bounded_exploration=True),
    )
    return orchestrator.prepare(limits=limits)


def _pointer(profile, *, version):
    return ProviderProfilePointer(
        profile_id=profile.capability_id if hasattr(profile, "capability_id") else profile.lane_id,
        profile_version=version,
        profile_path=Path(f"provider-profiles/{profile.profile_content_hash}.json"),
        profile_sha256=profile.profile_content_hash,
    )


def _native_fl2va_setup():
    first = _asset("first_frame", "native-fl2-first", "8" * 64)
    last = _asset("last_frame", "native-fl2-last", "9" * 64)
    context = _context(important=False, keyframe=first, last_frame=last)
    base = setup_decision()
    profile = native_profile("FL2VA")
    output = _output(profile)
    duration = output.frame_count / output.fps
    intent = h3_prompt_requirement().generation_intent.model_copy(update={
        "pacing": h3_prompt_requirement().generation_intent.pacing.model_copy(
            update={"shot_duration_seconds": duration}
        )
    })
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_intent=intent,
        generation_intent_hash=canonical_sha256({
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }),
        generation_mode=GenerationMode.IMAGE_TO_VIDEO,
        semantic_reference_roles=(
            SemanticReferenceRole.FIRST_FRAME,
            SemanticReferenceRole.LAST_FRAME,
        ),
        asset_evidence=tuple(
            AssetEvidence(
                role=role, asset_id=asset.asset_id, asset_sha256=asset.asset_sha256,
                mime_type=asset.mime_type, width=asset.width, height=asset.height,
                size_bytes=asset.size_bytes,
            )
            for role, asset in (
                (SemanticReferenceRole.FIRST_FRAME, first),
                (SemanticReferenceRole.LAST_FRAME, last),
            )
        ),
        conditioning_compatibility=_compatible_fl2va().model_copy(update={
            "lane": ConditioningLane.FL2VA,
            "first_anchor_id": first.asset_id,
            "last_anchor_id": last.asset_id,
            "available_duration_seconds": duration,
        }),
        capability_need=CapabilityNeed(
            needs_first_frame=True, needs_last_frame=True,
            accepts_local_execution=True, accepts_remote_execution=False,
        ),
        output_need=OutputNeed(
            timing_mode="frame_count", frame_count=output.frame_count,
            width=output.width, height=output.height, fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    return {
        **base,
        "context": context,
        "projection": projection,
        "lifecycle": _lifecycle(context).model_copy(update={
            "input_artifact_ids": (
                context.target_shot_id, first.asset_id, last.asset_id,
            )
        }),
    }, profile, output


def _native_ref2va_setup():
    context = _context(important=True)
    base = setup_decision()
    profile = native_profile("Ref2VA")
    output = _output(profile)
    identity = context.canonical_character_references[0]
    scene = context.canonical_scene_reference
    assert scene is not None
    intent = h3_prompt_requirement().generation_intent
    projection = _replace_requirement(
        _verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4",
        generation_intent=intent,
        generation_intent_hash=canonical_sha256({
            "schema": "provider-neutral-generation-intent/2",
            "generation_intent": intent.model_dump(mode="json"),
        }),
        generation_mode=GenerationMode.REFERENCE_TO_VIDEO,
        semantic_reference_roles=(
            SemanticReferenceRole.IDENTITY,
            SemanticReferenceRole.SCENE,
        ),
        asset_evidence=tuple(
            AssetEvidence(
                role=role, asset_id=asset.asset_id,
                asset_sha256=asset.asset_sha256, mime_type=asset.mime_type,
                width=asset.width, height=asset.height, size_bytes=asset.size_bytes,
                canonical_owner_id=asset.canonical_owner_id,
                canonical_owner_content_hash=asset.canonical_owner_content_hash,
            )
            for role, asset in (
                (SemanticReferenceRole.IDENTITY, identity),
                (SemanticReferenceRole.SCENE, scene),
            )
        ),
        capability_need=CapabilityNeed(
            needs_identity_reference=True, needs_scene_reference=True,
            max_reference_count=2,
            accepts_local_execution=True, accepts_remote_execution=False,
        ),
        output_need=OutputNeed(
            timing_mode="frame_count", frame_count=output.frame_count,
            width=output.width, height=output.height, fps=output.fps,
            container_mime=output.mime_type,
        ),
        audio_need=AudioNeed.REQUIRED,
    )
    return {
        **base,
        "context": context,
        "projection": projection,
        "lifecycle": _lifecycle(context).model_copy(update={
            "input_artifact_ids": (
                context.target_shot_id, identity.asset_id, scene.asset_id,
            ),
        }),
    }, profile, output


def _native_family(tmp_path):
    children = []
    for task in NATIVE_PROFILE_PATHS:
        profile = native_profile(task)
        input_root = tmp_path / profile.task_type
        input_root.mkdir()
        children.append(ComfyUIT8NativeTurboVideoProvider(
            profile, artifact_root=REPO_ROOT, comfy_root=REPO_ROOT, input_root=input_root,
            asset_resolver=forbidden, runtime_inspector=forbidden, transport=forbidden,
        ))
    return LocalH3VideoProviderFamily(children)


@pytest.mark.parametrize("factory,compiler_id", [
    (quality_provider, "comfy-local-h3-t8-video-compiler"),
    (turbo_provider, "comfy-local-h3-t8-turbo-video-compiler"),
], ids=["t8-quality", "t8-turbo"])
def test_t8_quality_and_turbo_reach_actual_compiler_through_common_caller(tmp_path, factory, compiler_id):
    provider, transport, profile = factory(tmp_path)
    output = _output(profile)
    setup = setup_decision()
    prepared = _prepare(
        provider=provider, profile=_pointer(profile, version="v1"), output=output,
        compiler=AdapterCompilerContract.create(compiler_id=compiler_id, compiler_version="3"),
        setup=setup, projection=_projection(setup, output),
    )
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.resolved_request is not None
    assert prepared.execution_binding is not None
    assert transport.workflows == []


def test_current_h3_quality_profile_reaches_i2va_compiler_without_transport(tmp_path):
    artifact_root, comfy_root, profile = _profile_and_comfy_root(tmp_path, QUALITY_PROFILE_PATH)
    image_root = tmp_path / "images"
    image_root.mkdir()
    provider = ComfyUIVideoProvider(
        profile, artifact_root=artifact_root, comfy_root=comfy_root, image_root=image_root,
        image_resolver=forbidden, transport=forbidden, commit_resolver=forbidden,
    )
    output = VideoFlexibleOutputRequirement(
        timing_mode="frame_count", frame_count=124, dimension_mode="exact", width=608, height=352,
        resolution_label="h3_native", ratio="adaptive", fps=24, container="mp4",
        mime_type="video/mp4", native_audio=True,
    )
    setup = setup_decision(reference_hash="a" * 64)
    prepared = _prepare(
        provider=provider, profile=_pointer(profile, version="v1"), output=output,
        compiler=AdapterCompilerContract.create(compiler_id="comfy-local-h3-video-compiler", compiler_version="2"),
        setup=setup, projection=_projection(setup, output, image_to_video=True),
    )
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.compilation.adapter_compiler_id == "comfy-local-h3-video-compiler"
    assert "framing continuity medium_to_medium_close" in prepared.compilation.provider_native_prompt
    assert "initial motion state stationary" in prepared.compilation.provider_native_prompt
    assert "duration 5.16667 seconds" in prepared.compilation.provider_native_prompt
    assert "explicitly silent false" in prepared.compilation.provider_native_prompt
    assert prepared.resolved_request is not None
    assert prepared.execution_binding is not None


def test_native_t2va_family_delegates_common_caller_to_actual_compiler(tmp_path):
    family = _native_family(tmp_path)
    profile = native_profile("T2VA")
    output = _output(profile)
    setup = setup_decision()
    prepared = _prepare(
        provider=family, profile=_pointer(profile, version="v2"), output=output,
        compiler=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-native-turbo-video-compiler", compiler_version="2"),
        setup=setup, projection=_projection(setup, output),
    )
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.resolved_request is not None
    assert prepared.execution_binding is not None
    assert {variant.mode.value for variant in family.capabilities().variants} == {
        "text_to_video", "image_to_video", "reference_to_video",
    }
    assert len(family.capabilities().variants) == 4


@pytest.mark.parametrize("task", ["I2VA", "FL2VA", "Ref2VA"])
def test_native_v2_family_selects_and_resolves_each_registered_mode(task, tmp_path):
    family = _native_family(tmp_path)
    if task == "I2VA":
        setup = setup_decision(reference_hash="a" * 64)
        profile = native_profile(task)
        output = _output(profile)
        projection = _projection(setup, output, image_to_video=True)
    elif task == "FL2VA":
        setup, profile, output = _native_fl2va_setup()
        projection = setup["projection"]
    else:
        setup, profile, output = _native_ref2va_setup()
        projection = setup["projection"]
    prepared = _prepare(
        provider=family, profile=_pointer(profile, version="v2"), output=output,
        compiler=AdapterCompilerContract.create(
            compiler_id="comfy-local-h3-t8-native-turbo-video-compiler", compiler_version="2"),
        setup=setup, projection=projection,
    )
    assert prepared.decision.disposition == "GENERATE_ONCE"
    assert prepared.decision.selected_candidate_id.endswith(profile.capability_id)
    assert isinstance(prepared.compilation, CompiledProviderVideoRequest)
    assert prepared.resolved_request is not None
    assert prepared.execution_binding is not None
    assert task in NATIVE_PROFILE_PATHS
