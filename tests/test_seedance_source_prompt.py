"""Verbatim approved source uses the existing compiler and recipe checks."""

import hashlib

import pytest

from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
from ai_video.production.seedance import SeedanceVideoProvider
from ai_video.production.seedance_native_prompt import SeedanceNativePromptBinding
from ai_video.production.shot_router import AdapterCompilerContract, ProviderBoundVideoRequest, VideoGenerationResolver
from ai_video.production.video_compiler import CompiledProviderVideoRequest
from ai_video.production.video_requirement import AudioNeed, GenerationIntent, OutputNeed, Pacing, SubjectAction
from test_production_generation_decision import acceptance_policy
from test_production_provider_neutral_adapters import _replace_requirement
from test_production_seedance import _profile, _profile_pointer, _request
from test_production_shot_router import _asset, _context, _first_frame_projection, _lifecycle, _policy, _verified_requirement


def _case(*, added_camera=None, first_frame=False):
    profile = _profile()
    model_id = "doubao-seedance-2-0-fast-260128" if first_frame else _request(profile).model_id
    output = _request(profile).output_requirement
    context = _context(important=False, keyframe=_asset("first_frame", "original-opening", "a" * 64)
        if first_frame else None)
    base = _first_frame_projection(context) if first_frame else _verified_requirement(context)
    source = base.requirement.target_shot.intent
    intent = GenerationIntent(subject_action=SubjectAction(progression=source),
        pacing=Pacing(shot_duration_seconds=output.duration_seconds))
    if added_camera is not None:
        intent = intent.model_copy(update={"camera_intent": intent.camera_intent.model_copy(
            update={"movement": added_camera})})
    projection = _replace_requirement(base, generation_intent=intent,
        output_need=OutputNeed(duration_seconds=output.duration_seconds, width=output.width,
            height=output.height, aspect_ratio=output.ratio, fps=output.fps, container_mime=output.mime_type),
        audio_need=AudioNeed.REQUIRED)
    provider = SeedanceVideoProvider(profile=profile, transport=object(),
        credential=lambda: pytest.fail("offline compile must not read credentials"), input_reference=object())
    selected = next(v for v in provider.capabilities().variants if v.model_id == model_id
        and v.mode.value == projection.requirement.generation_mode.value and v.output_capability.supports(output))
    compiler = AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="2")
    expression = RequirementExpression(requirement_id="source", level="acceptance", stage="raw_generation",
        dimension="source_fidelity", observable=source, tolerance="verbatim", measurement="human review",
        proof="human", intent_paths=("generation_intent.subject_action.progression",), native_text=(source,),
        production_owner="shot_authoring")
    acceptance = acceptance_policy((expression,))
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"), profile_sha256=profile.profile_sha256,
        compiler_hash=compiler.compiler_hash, requirement_hash=projection.requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash, acceptance_policy=acceptance, expressions=(expression,))
    lifecycle = _lifecycle(context)
    if first_frame:
        lifecycle = lifecycle.model_copy(update={"input_artifact_ids": (*lifecycle.input_artifact_ids, context.shot_keyframe.asset_id)})
    routed = VideoGenerationResolver()._bind_requirement(projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True), provider_profile=_profile_pointer(profile),
        capabilities=provider.capabilities(), selected_capability_id=selected.capability_id,
        output_requirement=output, lifecycle=lifecycle, compiler_contract=compiler)
    assert routed.provider_bound_request is not None
    bound = ProviderBoundVideoRequest.create(**{
        **{k: getattr(routed.provider_bound_request, k) for k in ProviderBoundVideoRequest.model_fields
            if k != "provider_bound_request_hash"}, "generation_recipe": recipe})
    return profile, bound, projection.requirement, source


def _compile(profile, bound, requirement, source, *, preserved=True, evidence=None):
    digest = hashlib.sha256(source.encode()).hexdigest()
    binding = SeedanceNativePromptBinding(provider_bound_request_hash=bound.provider_bound_request_hash,
        prompt_text=source, prompt_sha256=digest, source_evidence_sha256=evidence or digest,
        source_preservation=preserved)
    provider = SeedanceVideoProvider(profile=profile, transport=object(),
        credential=lambda: pytest.fail("offline compile must not read credentials"),
        input_reference=object(), native_prompt_binding=binding)
    return provider.compile_request(bound, requirement)


def test_verbatim_approved_shot_compiles_without_invented_rich_intent():
    profile, bound, requirement, source = _case()
    result = _compile(profile, bound, requirement, source)
    assert isinstance(result, CompiledProviderVideoRequest)
    assert result.provider_native_prompt.encode() == source.encode()
    assert result.request.prompt_text == source
    assert result.request.provider_bound_request_hash == bound.provider_bound_request_hash
    assert requirement.generation_intent.primary_camera_motion is None
    assert requirement.generation_intent.lighting_intent is None


def test_verbatim_single_first_frame_preserves_i2v_role_and_original_bytes_identity():
    profile, bound, requirement, source = _case(first_frame=True)
    result = _compile(profile, bound, requirement, source)
    assert isinstance(result, CompiledProviderVideoRequest)
    assert result.request.mode.value == "image_to_video"
    assert result.request.prompt_text.encode() == source.encode()
    assert len(result.request.image_bindings) == 1
    image = result.request.image_bindings[0]
    assert image.role == "first_frame"
    assert image.asset_id == "asset-original-opening"
    assert image.asset_sha256 == "a" * 64


@pytest.mark.parametrize("damage", ["extra_role", "conditioned"])
def test_verbatim_first_frame_does_not_replace_other_conditioning_shapes(damage):
    from ai_video.production.video_requirement import SemanticReferenceRole

    profile, bound, requirement, source = _case(first_frame=True)
    changes = ({"semantic_reference_roles": (SemanticReferenceRole.FIRST_FRAME, SemanticReferenceRole.LAST_FRAME)}
        if damage == "extra_role" else {"conditioning_compatibility": object()})
    altered = requirement.model_copy(update=changes)
    with pytest.raises(ValueError, match="conditioned|single first frame"):
        _compile(profile, bound, altered, source)


def test_incomplete_new_creation_still_refused():
    profile, bound, requirement, source = _case()
    result = _compile(profile, bound, requirement, source, preserved=False)
    assert result.outcome == "unsupported"


@pytest.mark.parametrize("edit", [lambda s: s + " Extra camera design.", lambda s: s[:-1]])
def test_source_edit_cannot_claim_verbatim_preservation(edit):
    profile, bound, requirement, source = _case()
    with pytest.raises(ValueError, match="approved Shot"):
        _compile(profile, bound, requirement, edit(source))


def test_source_evidence_hash_must_match_original_text():
    profile, bound, requirement, source = _case()
    with pytest.raises(ValueError, match="source evidence"):
        _compile(profile, bound, requirement, source, evidence="a" * 64)


def test_verbatim_flag_does_not_hide_unexpressed_authored_camera():
    profile, bound, requirement, source = _case(added_camera="A newly invented rear-follow camera.")
    result = _compile(profile, bound, requirement, source)
    assert result.outcome == "unsupported"
    assert "generation_intent.camera_intent.movement" in result.unsupported_field_paths


def test_source_duration_control_must_match_bound_output():
    profile, bound, requirement, source = _case()
    altered = requirement.model_copy(update={"generation_intent": requirement.generation_intent.model_copy(
        update={"pacing": Pacing(shot_duration_seconds=99)})})
    with pytest.raises(ValueError, match="duration"):
        _compile(profile, bound, altered, source)


def test_source_cannot_replace_v4_camera_complete_contract():
    profile, bound, requirement, source = _case()
    altered = requirement.model_copy(update={"contract_version": "provider-neutral-video-requirement/4"})
    with pytest.raises(ValueError, match="rich or conditioned"):
        _compile(profile, bound, altered, source)


def test_source_cannot_replace_typed_hash_continuity():
    profile, bound, requirement, source = _case()
    from ai_video.production.video_requirement import TypedStateReference

    altered = requirement.model_copy(update={"generation_intent": requirement.generation_intent.model_copy(
        update={"open_state": TypedStateReference(kind="typed_hash", state_hash="b" * 64)})})
    with pytest.raises(ValueError, match="continuity evidence"):
        _compile(profile, bound, altered, source)
