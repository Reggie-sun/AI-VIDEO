"""Real remote native compilers behind the common caller, without transport."""

import pytest

from ai_video.production.generation_feedback import (
    GenerationFeedbackOrchestrator, GenerationHistory, RegisteredGenerationTarget,
)
from ai_video.production.generation_decision import DecisionPolicy
from ai_video.production.generation_recipe import RequirementExpression
from ai_video.production.shot_router import AdapterCompilerContract
from ai_video.production.video_requirement import AmbienceIntent, AudioNeed, OutputNeed, Pacing
from test_production_generation_decision import setup_decision, acceptance_policy
from test_production_provider_neutral_adapters import _replace_requirement
from tests.test_production_video_intent_validation import _complete_intent


def forbidden(*args, **kwargs):
    raise AssertionError("compiler-only wiring must not use transport or credentials")


def prepare(provider, profile, output, compiler_id, compiler_version="2", authorized_model=None, setup=None):
    setup = setup or setup_decision()
    intent = _complete_intent().model_copy(update={
        "pacing": Pacing(shot_duration_seconds=output.duration_seconds or 4),
        **({"ambience_intent": AmbienceIntent(environment_bed="none", explicitly_silent=True)}
           if not output.native_audio else {}),
    })
    conditioning = setup["projection"].requirement.conditioning_compatibility
    if conditioning is not None:
        conditioning = conditioning.model_copy(update={"available_duration_seconds": output.duration_seconds})
    projection = _replace_requirement(setup["projection"],
        contract_version="provider-neutral-video-requirement/4", generation_intent=intent,
        conditioning_compatibility=conditioning,
        output_need=OutputNeed(timing_mode="provider_selected" if getattr(output, "timing_mode", None)
            == "provider_selected" else "fixed", duration_seconds=output.duration_seconds, width=output.width,
            height=output.height, geometry_policy=getattr(output, "dimension_mode", "exact"),
            aspect_ratio=getattr(output, "ratio", None), fps=output.fps, container_mime=output.mime_type),
        audio_need=AudioNeed.REQUIRED if output.native_audio else AudioNeed.FORBIDDEN)
    acceptance = acceptance_policy((RequirementExpression(
        requirement_id="hand", level="acceptance", stage="raw_generation", dimension="action",
        observable="hand secures product", tolerance="exact", measurement="viewing", proof="human",
        intent_paths=("generation_intent.performance_intent.hand_behavior",), production_owner="shot_authoring"),))
    current = {**{k: v for k, v in setup.items() if k != "inputs"}, "projection": projection,
               "acceptance": acceptance}
    target = RegisteredGenerationTarget(provider, profile, AdapterCompilerContract.create(
        compiler_id=compiler_id, compiler_version=compiler_version), output)
    capabilities = provider.capabilities()
    limits = setup["inputs"].limits.model_copy(update={"allowed_remote_candidates": tuple(
        f"{capabilities.provider_name}/{v.capability_id}" for v in capabilities.variants
        if authorized_model is None or v.model_id == authorized_model)})
    return GenerationFeedbackOrchestrator(targets=(target,), context_loader=lambda: current,
        history_loader=GenerationHistory, policy=DecisionPolicy(allow_bounded_exploration=True)).prepare(limits=limits)


@pytest.mark.parametrize("model", [
    "doubao-seedance-2-5-260628", "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128", "doubao-seedance-2-0-mini-260615",
    "doubao-seedance-1-5-pro-251215", "doubao-seedance-1-0-pro-250528",
    "doubao-seedance-1-0-pro-fast-251015",
])
def test_seedance_registered_models_through_common_caller(model):
    from ai_video.production.seedance import SeedanceVideoProvider
    from test_production_seedance import _active_profile, _profile_pointer, _request

    profile = _active_profile(model)
    output = _request(profile, model_id=model).output_requirement
    entry = next(c for c in profile.capabilities if c.variant.mode.value == "text_to_video")
    raster = next(r for r in entry.output_rasters if r.resolution_label == "720p" and r.ratio == "16:9")
    output = output.model_copy(update={"native_audio": True in entry.variant.output_capability.native_audio_options,
        "width": raster.width, "height": raster.height, "resolution_label": raster.resolution_label,
        "ratio": raster.ratio})
    if "-2-0-mini-" in model:
        output = output.model_copy(update={"timing_mode": "provider_selected", "duration_seconds": None})
    provider = SeedanceVideoProvider(profile=profile, transport=forbidden, credential=forbidden,
                                    input_reference=forbidden)
    result = prepare(provider, _profile_pointer(profile), output, "seedance-video-compiler")
    assert result.decision.disposition == "GENERATE_ONCE"
    assert result.compilation.outcome == "compiled"
    assert result.execution_binding is not None
    assert result.resolved_request.model_id == model
    assert "reaches once and secures the product" in result.resolved_request.prompt_text


@pytest.mark.parametrize("provider_name", ["h3", "hailuo"])
def test_minimax_remote_models_through_common_caller(provider_name):
    if provider_name == "h3":
        from ai_video.production.minimax_h3 import MiniMaxH3VideoProvider as Provider
        from test_production_minimax_h3 import _profile, _output
        compiler = "minimax-h3-video-compiler"
    else:
        from ai_video.production.minimax_hailuo import MiniMaxHailuoVideoProvider as Provider
        from test_production_minimax_hailuo import _profile, _output
        compiler = "minimax-hailuo-video-compiler"
    provider = Provider(transport=forbidden, credential=forbidden)
    result = prepare(provider, _profile(), _output(), compiler)
    assert result.decision.disposition == "GENERATE_ONCE"
    assert result.compilation.outcome == "compiled"
    assert result.execution_binding is not None


@pytest.mark.parametrize("model", ["viduq3-pro", "viduq3-turbo"])
def test_vidu_registered_t2v_models_through_common_caller(model):
    from ai_video.production.vidu import ViduVideoProvider
    from test_production_vidu import _profile, _request

    profile = _profile()
    output = _request(profile=profile).output_requirement
    provider = ViduVideoProvider(profile=profile, transport=forbidden, credential=forbidden,
                                 image_resolver=forbidden)
    result = prepare(provider, profile.pointer(), output, "vidu-video-compiler", compiler_version="3", authorized_model=model)
    assert result.decision.disposition == "GENERATE_ONCE"
    assert result.compilation.outcome == "compiled"
    assert result.resolved_request.model_id == model
    assert result.execution_binding is not None
    # All registered variants were created; task scope limits execution, not
    # inventory discovery or assessment of other models/modes.
    assert len(result.inputs.candidates) == len(provider.capabilities().variants)


def conditioned_setup(mode, *, image_references=False):
    from ai_video.production.video_requirement import (
        AssetEvidence, CapabilityNeed, ConditioningCompatibilityEvidence, GenerationMode, SemanticReferenceRole,
    )
    from test_production_shot_router import _asset, _context, _lifecycle, _verified_requirement

    bindings = []
    kwargs = {"important": False}
    if mode in {"image_to_video", "first_last_frame_video"}:
        first = _asset("first_frame", "first", "1" * 64)
        kwargs["keyframe"] = first
        bindings.append((SemanticReferenceRole.FIRST_FRAME, first))
        if mode == "first_last_frame_video":
            last = _asset("last_frame", "last", "2" * 64)
            kwargs["last_frame"] = last
            bindings.append((SemanticReferenceRole.LAST_FRAME, last))
    elif image_references:
        scene = _asset("scene_reference", "scene", "3" * 64)
        kwargs["scene_reference"] = scene
        bindings.append((SemanticReferenceRole.SCENE, scene))
    else:
        video = _asset("reference_video", "source", "4" * 64, mime_type="video/mp4",
                       width=1280, height=720, duration_millis=5000, fps=24)
        kwargs["reference_videos"] = (video,)
        bindings.append((SemanticReferenceRole.VIDEO_REFERENCE, video))
    context = _context(**kwargs)
    projection = _replace_requirement(_verified_requirement(context),
        generation_mode=GenerationMode(mode),
        semantic_reference_roles=tuple(role for role, _ in bindings),
        asset_evidence=tuple(AssetEvidence(
            role=role, asset_id=a.asset_id, asset_sha256=a.asset_sha256, mime_type=a.mime_type,
            width=a.width, height=a.height, size_bytes=a.size_bytes,
            duration_millis=a.duration_millis, fps=a.fps) for role, a in bindings))
    if mode in {"image_to_video", "first_last_frame_video"}:
        # V4 validation occurs in prepare, together with complete rich intent.
        projection = projection.model_copy(update={"requirement": projection.requirement.model_copy(update={
            "capability_need": CapabilityNeed(needs_first_frame=True, needs_last_frame=mode == "first_last_frame_video"),
            "conditioning_compatibility": ConditioningCompatibilityEvidence(
                lane="fl2va" if mode == "first_last_frame_video" else "i2va",
                first_anchor_id=bindings[0][1].asset_id,
                last_anchor_id=bindings[1][1].asset_id if mode == "first_last_frame_video" else None,
                same_subject_scale=True, composition_compatible=True, screen_order_compatible=True,
                axis_compatible=True, camera_path_reachable=True, character_prop_state_reachable=True,
                action_endpoint_reachable=True, available_duration_seconds=4),
        })})
    setup = setup_decision()
    setup.update(context=context, projection=projection, lifecycle=_lifecycle(context).model_copy(
        update={"input_artifact_ids": (context.target_shot_id, *(a.asset_id for _, a in bindings))}))
    return setup


@pytest.mark.parametrize("model,mode", [
    (model, mode) for model, modes in [
        ("viduq3-pro", ("image_to_video",)),
        ("viduq3-turbo", ("image_to_video",)),
        ("viduq3", ("reference_to_video",)),
        ("viduq2-pro", ("video_extend",)),
        ("viduq2-turbo", ("video_extend",)),
    ] for mode in modes
])
def test_vidu_conditioned_modes_through_common_caller(model, mode):
    from ai_video.production.vidu import ViduVideoProvider
    from test_production_vidu import _profile, _request

    profile = _profile()
    output = _request().output_requirement
    if mode != "reference_to_video":
        output = output.model_copy(update={"dimension_mode": "adaptive", "width": None,
            "height": None, "ratio": "adaptive"})
    if mode == "video_extend":
        output = output.model_copy(update={"duration_seconds": 9, "native_audio": False})
    provider = ViduVideoProvider(profile=profile, transport=forbidden, credential=forbidden,
                                 image_resolver=forbidden, extension_source=forbidden)
    result = prepare(provider, profile.pointer(), output, "vidu-video-compiler", "3", model,
                     conditioned_setup(mode, image_references=mode == "reference_to_video"))
    assert result.execution_binding is not None, result
    assert result.resolved_request.mode.value == mode


@pytest.mark.parametrize("mode", ["image_to_video", "first_last_frame_video", "reference_to_video",
                                   "video_edit", "video_extend"])
def test_seedance25_conditioned_modes_through_common_caller(mode):
    from ai_video.production.seedance import SeedanceVideoProvider
    from test_production_seedance import _active_profile, _profile_pointer, _request

    profile = _active_profile("doubao-seedance-2-5-260628")
    output = _request(profile).output_requirement.model_copy(update={
        "dimension_mode": "adaptive", "width": None, "height": None, "ratio": "adaptive"})
    if mode == "video_edit":
        output = output.model_copy(update={"timing_mode": "provider_selected", "duration_seconds": None})
    provider = SeedanceVideoProvider(profile=profile, transport=forbidden, credential=forbidden,
                                    input_reference=forbidden)
    result = prepare(provider, _profile_pointer(profile), output, "seedance-video-compiler",
                     setup=conditioned_setup(mode))
    assert result.execution_binding is not None, result
    assert result.resolved_request.image_bindings or result.resolved_request.media_bindings


@pytest.mark.parametrize("mode", ["reference_to_video", "video_edit", "video_extend"])
def test_conditioned_mode_cannot_use_empty_references_or_first_frame_attestation(mode):
    from ai_video.production._video_intent_validation import validate_requirement_conditioning_compatibility
    requirement = conditioned_setup(mode)["projection"].requirement
    empty = requirement.model_copy(update={"asset_evidence": ()})
    assert "asset_evidence.references" in validate_requirement_conditioning_compatibility(empty)
    first_frame_proof = conditioned_setup("image_to_video")["projection"].requirement.conditioning_compatibility
    misplaced = requirement.model_copy(update={"conditioning_compatibility": first_frame_proof})
    assert "conditioning_compatibility" in validate_requirement_conditioning_compatibility(misplaced)


@pytest.mark.parametrize("mode", ["video_edit", "video_extend"])
@pytest.mark.parametrize("field", ["width", "height", "duration_millis", "fps", "size_bytes"])
def test_edit_extend_requires_measured_source_video_identity(mode, field):
    from ai_video.production._video_intent_validation import validate_requirement_conditioning_compatibility
    requirement = conditioned_setup(mode)["projection"].requirement
    source = requirement.asset_evidence[0].model_copy(update={field: None})
    missing = requirement.model_copy(update={"asset_evidence": (source,)})
    assert "asset_evidence.source_video" in validate_requirement_conditioning_compatibility(missing)
