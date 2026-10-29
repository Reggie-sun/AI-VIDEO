"""Jimeng references must survive the canonical causal-state recompile."""

import hashlib

import pytest

from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng import JimengVideoProvider
from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.video import VideoProviderCapabilities
from ai_video.production.video_requirement import AudioNeed, OutputNeed, TypedStateReference
from ai_video.production.video_transition import CausalDimension
from test_production_jimeng import FakeBrowser, FakeCommitter, NOW, setup
from test_production_shot_router import (
    AdapterCompilerContract, ContinuityMode, VideoGenerationResolver,
    _asset, _context, _identity_reference_projection, _lifecycle, _policy, _reseal_projection,
)
from tests.reference_authoring_fixture import with_fixture_reference_planning
from test_production_video_intent_validation import _complete_intent


def _causal_reference(monkeypatch, *, long_text=False, oversized=False, video=False):
    original = setup()[0]._profile
    profile = JimengProfile.model_validate({**original.model_dump(),
        "duration_seconds": 6, "benefit_amount": 10 if video else 6})
    provider = JimengVideoProvider(profile=profile, transport=FakeBrowser(),
        reference_resolver=lambda _: pytest.fail("pure compile cannot read media"),
        committer=FakeCommitter(), now=lambda: NOW)
    motion = _asset("reference_video", "whitebox", "d" * 64,
        mime_type="video/mp4", duration_millis=4000, fps=24)
    context = _context(continuity=ContinuityMode.NONE,
        reference_videos=(motion,) if video else ())
    if oversized:
        context = context.model_copy(update={"canonical_character_references": tuple(
            asset.model_copy(update={"width": 9000}) for asset in context.canonical_character_references)})
    facts = {dimension: f"authored closing fact for {dimension.value}" for dimension in CausalDimension}
    intent = _complete_intent()
    intent = intent.model_copy(update={
        "close_state": TypedStateReference(kind="typed_hash",
            state_hash=canonical_sha256({dimension.value: fact for dimension, fact in facts.items()})),
        "close_causal_facts": facts,
        "pacing": intent.pacing.model_copy(update={"shot_duration_seconds": 6}),
        **({"subject_action": intent.subject_action.model_copy(update={
            "progression": "沿指定路径平稳移动。" * 600}),
            # The camera purpose names the overridden progression, so re-derive it.
            "reference_planning": None} if long_text else {}),
    })
    intent = with_fixture_reference_planning(intent)
    projection = _reseal_projection(_identity_reference_projection(context),
        contract_version="provider-neutral-video-requirement/4", continuity_mode="none",
        generation_intent=intent, audio_need=AudioNeed.REQUIRED,
        output_need=OutputNeed(timing_mode="content_driven", duration_seconds=6,
            geometry_policy="adaptive", aspect_ratio="16:9", container_mime="video/mp4"))
    if video:
        from ai_video.production.video_requirement import AssetEvidence, SemanticReferenceRole
        projection = _reseal_projection(projection,
            asset_evidence=(*projection.requirement.asset_evidence,
                AssetEvidence(role=SemanticReferenceRole.VIDEO_REFERENCE, asset_id=motion.asset_id,
                    asset_sha256=motion.asset_sha256, mime_type=motion.mime_type,
                    size_bytes=motion.size_bytes, width=motion.width, height=motion.height,
                    duration_millis=motion.duration_millis, fps=motion.fps)),
            semantic_reference_roles=(*projection.requirement.semantic_reference_roles,
                                      SemanticReferenceRole.VIDEO_REFERENCE))
    declared = provider.capabilities()
    monkeypatch.setattr(provider, "capabilities", lambda: VideoProviderCapabilities.create(
        provider_name=declared.provider_name,
        variants=tuple(v.model_copy(update={"production_qualification": "QUALIFIED"}) for v in declared.variants)))
    result = VideoGenerationResolver()._bind_requirement(projection=projection,
        context=context, policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=profile.pointer(), capabilities=provider.capabilities(),
        selected_capability_id=profile.capability_id, output_requirement=profile.output(),
        lifecycle=_lifecycle(context).model_copy(update={"input_artifact_ids":
            (context.target_shot_id, *(a.asset_id for a in context.canonical_character_references),
             *(a.asset_id for a in context.reference_videos))}),
        compiler_contract=AdapterCompilerContract.create(compiler_id=profile.compiler_id, compiler_version="1"))
    assert result.provider_bound_request is not None, result.decision
    return provider, result.provider_bound_request, projection.requirement


@pytest.mark.parametrize("long_text", [False, True])
def test_exact_causal_reference_recompiles_the_complete_jimeng_grammar(monkeypatch, long_text):
    provider, bound, requirement = _causal_reference(monkeypatch, long_text=long_text)
    compiled = provider.compile_request(bound, requirement)
    assert compiled.outcome == "compiled", compiled
    resolved = provider.resolve(compiled.request)
    assert "{{image:0}}" in resolved.prompt_text
    assert "authored closing fact for" in resolved.prompt_text
    if long_text:
        assert len(resolved.prompt_text) > 5000


@pytest.mark.parametrize("tamper", ["prompt", "grammar", "compiler"])
def test_causal_recompile_rejects_resealed_native_prompt_tampering(monkeypatch, tamper):
    from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt
    from ai_video.production.video_compiler import compile_provider_video_request

    provider, bound, requirement = _causal_reference(monkeypatch)
    native = compile_jimeng_native_prompt(compiler_id=provider._profile.compiler_id,
        compiler_version="1", requirement=requirement, provider_bound=bound)
    compiler_id = provider._profile.compiler_id
    if tamper == "prompt":
        text = native.prompt_text + "\n额外未批准动作"
        native = native.model_copy(update={"prompt_text": text,
            "prompt_sha256": hashlib.sha256(text.encode()).hexdigest()})
    elif tamper == "grammar":
        native = native.model_copy(update={"grammar_contract": "jimeng-made-up-v1"})
    else:
        compiler_id = "another-provider-video-compiler"
    result = compile_provider_video_request(provider_bound=bound, requirement=requirement,
        compiler_id=compiler_id, compiler_version="1", capabilities=provider.capabilities(),
        native_prompt=native)
    assert result.outcome == "unsupported"


def test_selected_reference_cannot_claim_compiled_when_exact_provider_limits_reject_it(monkeypatch):
    provider, bound, requirement = _causal_reference(monkeypatch, oversized=True)
    compiled = provider.compile_request(bound, requirement)
    assert compiled.outcome == "unsupported"
    assert compiled.unsupported_field_paths == ("selected_jimeng_input_limits",)
    assert provider._transport.uploads == []


def _with_reference_duty(bound, requirement, *, purpose="identity", wrong_sha=False, asset_index=0):
    from ai_video.production.generation_recipe import GenerationRecipe, SeedPolicy
    from ai_video.production.generation_input_control import GenerationInputControl, ReferenceDuty
    from test_generation_input_control import _rule, _sealed_acceptance

    asset = requirement.asset_evidence[asset_index]
    scope = (f"白模素材{asset.asset_id}只引导抓握动作和运镜，不继承外观与材质。"
             if asset.mime_type.startswith("video/") else
             f"仅使用素材{asset.asset_id}保持人物身份，不继承姿态、运镜或动作。")
    duty = ReferenceDuty(asset_id=asset.asset_id,
        asset_sha256="f" * 64 if wrong_sha else asset.asset_sha256,
        role=asset.role.value, purpose=purpose, scope_text=scope,
        canonical_owner_id=asset.canonical_owner_id)
    rule = _rule("identity-reference-duty", control=GenerationInputControl(
        mechanism="reference_guidance", references=(duty,)),
        native_text=(scope,), intent_paths=("generation_intent.subject_action.progression",))
    acceptance = _sealed_acceptance((rule,))
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=bound.provider_profile.profile_sha256,
        compiler_hash=bound.compiler_contract.compiler_hash,
        requirement_hash=requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance, expressions=(rule,))
    return type(bound).create(**{name: getattr(bound, name) for name in type(bound).model_fields
        if name not in {"provider_bound_request_hash", "generation_recipe"}},
        generation_recipe=recipe), scope


@pytest.mark.parametrize("purpose", ["identity", "layout", "whitebox"])
def test_reference_duty_is_expressed_beside_its_exact_native_material(monkeypatch, purpose):
    provider, bound, requirement = _causal_reference(monkeypatch)
    bound, scope = _with_reference_duty(bound, requirement, purpose=purpose)
    compiled = provider.compile_request(bound, requirement)
    assert compiled.outcome == "compiled", compiled
    assert scope in compiled.request.prompt_text
    assert "{{image:0}}" in compiled.request.prompt_text
    assert compiled.request.image_bindings[0].asset_sha256 == requirement.asset_evidence[0].asset_sha256


def test_unbound_reference_duty_stays_unsupported(monkeypatch):
    provider, bound, requirement = _causal_reference(monkeypatch)
    bound, _ = _with_reference_duty(bound, requirement, wrong_sha=True)
    assert provider.compile_request(bound, requirement).outcome == "unsupported"


def test_dropping_authored_reference_scope_cannot_pass_common_compiler(monkeypatch):
    from ai_video.production import jimeng_prompt

    provider, bound, requirement = _causal_reference(monkeypatch)
    bound, _ = _with_reference_duty(bound, requirement)
    monkeypatch.setattr(jimeng_prompt, "_authored_reference_text", lambda *_: "")
    assert provider.compile_request(bound, requirement).outcome == "unsupported"


@pytest.mark.parametrize("purpose", ["whitebox", "motion", "camera"])
def test_whitebox_video_duty_reaches_native_prompt_and_exact_media_binding(monkeypatch, purpose):
    provider, bound, requirement = _causal_reference(monkeypatch, video=True)
    bound, scope = _with_reference_duty(bound, requirement, purpose=purpose, asset_index=1)
    compiled = provider.compile_request(bound, requirement)
    assert compiled.outcome == "compiled", compiled
    assert "参考素材2 {{video:1}}" in compiled.request.prompt_text
    assert scope in compiled.request.prompt_text
    assert compiled.request.media_bindings[0].asset_id == requirement.asset_evidence[1].asset_id
    assert provider.resolve(compiled.request).media_bindings == compiled.request.media_bindings


def test_standard_causal_recipe_expresses_facts_without_reinserting_the_state_seal(monkeypatch):
    from ai_video.production.generation_feedback import _expressions
    from ai_video.production.generation_recipe import GenerationRecipe, SeedPolicy
    from test_requirement_semantics import marked_policy, semantic_rule

    provider, bound, requirement = _causal_reference(monkeypatch)
    state_hash = requirement.generation_intent.close_state.state_hash
    rule = semantic_rule("causal-close")
    rule.update(dimension="causal_state", observable=state_hash, tolerance="exact",
        measurement="Inspect every dimension at the raw Shot close",
        intent_paths=["generation_intent.close_state.state_hash"])
    acceptance = marked_policy([rule])
    expressions = _expressions(acceptance, requirement)
    assert state_hash in expressions[0].native_text
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=bound.provider_profile.profile_sha256,
        compiler_hash=bound.compiler_contract.compiler_hash,
        requirement_hash=requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash,
        acceptance_policy=acceptance, expressions=expressions)
    bound = type(bound).create(**{name: getattr(bound, name) for name in type(bound).model_fields
        if name not in {"provider_bound_request_hash", "generation_recipe"}}, generation_recipe=recipe)
    original = recipe.model_dump_json()
    compiled = provider.compile_request(bound, requirement)
    assert compiled.outcome == "compiled", compiled
    assert state_hash not in compiled.request.prompt_text
    assert "authored closing fact for" in compiled.request.prompt_text
    assert recipe.model_dump_json() == original


@pytest.mark.parametrize("model_id", ["seedance_2.5", "seedance_2.0_mini",
                                    "seedance_2.0_vip", "seedance_2.0_fast_vip"])
def test_text_only_shot_survives_real_requirement_routing_compilation_and_resolve(monkeypatch, model_id):
    from test_jimeng_shot_modes import _profile
    from test_production_shot_router import _verified_requirement, MotionRequirement

    profile = _profile(model_id, "text_to_video")
    provider = JimengVideoProvider(profile=profile, transport=FakeBrowser(),
        reference_resolver=lambda _: pytest.fail("text-only Shot has no uploads"),
        committer=FakeCommitter(), now=lambda: NOW)
    context = _context(important=False, motion=MotionRequirement.FREE_COMPLEX)
    intent = _complete_intent().model_copy(update={
        "pacing": _complete_intent().pacing.model_copy(update={"shot_duration_seconds": profile.duration_seconds})})
    projection = _reseal_projection(_verified_requirement(context),
        contract_version="provider-neutral-video-requirement/4", generation_intent=intent,
        audio_need=AudioNeed.REQUIRED, output_need=OutputNeed(timing_mode="content_driven",
            duration_seconds=profile.duration_seconds, geometry_policy="adaptive",
            aspect_ratio=profile.aspect_ratio, container_mime="video/mp4"))
    declared = provider.capabilities()
    monkeypatch.setattr(provider, "capabilities", lambda: VideoProviderCapabilities.create(
        provider_name=declared.provider_name,
        variants=tuple(v.model_copy(update={"production_qualification": "QUALIFIED"}) for v in declared.variants)))
    result = VideoGenerationResolver()._bind_requirement(projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=profile.pointer(), capabilities=provider.capabilities(),
        selected_capability_id=profile.capability_id, output_requirement=profile.output(),
        lifecycle=_lifecycle(context), compiler_contract=AdapterCompilerContract.create(
            compiler_id=profile.compiler_id, compiler_version="1"))
    assert result.provider_bound_request is not None, result.decision
    compiled = provider.compile_request(result.provider_bound_request, projection.requirement)
    assert compiled.outcome == "compiled", compiled
    resolved = provider.resolve(compiled.request)
    assert resolved.mode.value == "text_to_video"
    assert not resolved.image_bindings and not resolved.media_bindings
