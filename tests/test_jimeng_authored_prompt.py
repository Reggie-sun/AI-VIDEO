"""Exact QA-owned Chinese prose reaches Jimeng without a template fallback."""

import hashlib
import re

import pytest

from ai_video.production.generation_recipe import GenerationRecipe, RequirementExpression, SeedPolicy
from ai_video.production.hashing import canonical_sha256
from ai_video.production.jimeng import JimengVideoProvider
from ai_video.production.jimeng_contracts import JimengProfile
from ai_video.production.video import VideoProviderCapabilities
from ai_video.production.video_requirement import AudioNeed, OutputNeed
from test_generation_input_control import _sealed_acceptance
from test_production_jimeng import FakeBrowser, FakeCommitter, NOW, setup
from test_production_shot_router import (
    AdapterCompilerContract, ContinuityMode, VideoGenerationResolver,
    _context, _identity_reference_projection, _lifecycle, _policy, _reseal_projection,
)
from test_production_video_intent_validation import _complete_intent


TEXT = "真人雨夜便利店，人物目光和持物保持连续。林序低声求证，骑手普通回应。先看饭团再抬左手短指，完整收回身侧。参考{{image:0}}只保人物身份。"


def _leaf_paths(value, prefix="generation_intent"):
    if isinstance(value, dict):
        return [path for key, child in value.items()
                for path in _leaf_paths(child, prefix + "." + key)]
    if isinstance(value, list):
        return [path for index, child in enumerate(value)
                for path in _leaf_paths(child, prefix + "." + str(index))]
    return [prefix] if value is not None and value != "unspecified" else []


def _fixture(monkeypatch, *, missing_path=None, stale_hash=False, fragment=None, text=TEXT,
             compiler_version="1"):
    original = setup()[0]._profile
    profile = JimengProfile.model_validate({**original.model_dump(), "duration_seconds": 6, "benefit_amount": 6})
    provider = JimengVideoProvider(profile=profile, transport=FakeBrowser(),
        reference_resolver=lambda _: pytest.fail("offline compile must not upload or read media"),
        committer=FakeCommitter(), now=lambda: NOW)
    context = _context(continuity=ContinuityMode.NONE, shot_intent=text)
    intent = _complete_intent()
    intent = intent.model_copy(update={"pacing": intent.pacing.model_copy(update={"shot_duration_seconds": 6})})
    projection = _reseal_projection(_identity_reference_projection(context),
        contract_version="provider-neutral-video-requirement/4", continuity_mode="none",
        generation_intent=intent, audio_need=AudioNeed.REQUIRED,
        output_need=OutputNeed(timing_mode="content_driven", duration_seconds=6,
            geometry_policy="adaptive", aspect_ratio="16:9", container_mime="video/mp4"))
    declared = provider.capabilities()
    monkeypatch.setattr(provider, "capabilities", lambda: VideoProviderCapabilities.create(
        provider_name=declared.provider_name,
        variants=tuple(variant.model_copy(update={"production_qualification": "QUALIFIED"})
                       for variant in declared.variants)))
    routed = VideoGenerationResolver()._bind_requirement(
        projection=projection, context=context,
        policy=_policy(remote_authorized=True, budget_authorized=True),
        provider_profile=profile.pointer(), capabilities=provider.capabilities(),
        selected_capability_id=profile.capability_id, output_requirement=profile.output(),
        lifecycle=_lifecycle(context).model_copy(update={"input_artifact_ids": (context.target_shot_id, *(a.asset_id for a in context.canonical_character_references))}), compiler_contract=AdapterCompilerContract.create(
            compiler_id=profile.compiler_id, compiler_version=compiler_version))
    assert routed.provider_bound_request is not None, routed.decision.model_dump_json()
    bound = routed.provider_bound_request
    paths = tuple(_leaf_paths(intent.model_dump(mode="json")))
    rule = RequirementExpression(requirement_id="authored-expression", level="acceptance",
        stage="raw_generation", dimension="input_expression", observable="核对精简正文的封存表达",
        tolerance="按批准内容", measurement="核对实际输入与映射", proof="technical",
        production_owner="qa_acceptance", intent_paths=paths, native_text=(fragment or text,),
        native_text_mapping={"intent_sha256": "f" * 64 if stale_hash else canonical_sha256(intent.model_dump(mode="json")),
            "bindings": [{"intent_path": path, "fragment_indices": [0]}
                         for path in paths if path != missing_path]})
    acceptance = _sealed_acceptance((rule,))
    recipe = GenerationRecipe(seed=SeedPolicy(kind="uncontrolled"),
        profile_sha256=profile.pointer().profile_sha256, compiler_hash=bound.compiler_contract.compiler_hash,
        requirement_hash=projection.requirement.requirement_hash,
        rubric_hash=acceptance.profile_content_hash, acceptance_policy=acceptance, expressions=(rule,))
    bound = type(bound).create(**{name: getattr(bound, name) for name in type(bound).model_fields
        if name not in {"provider_bound_request_hash", "generation_recipe"}}, generation_recipe=recipe)
    return provider, bound, projection.requirement


def test_final_chinese_shot_text_is_the_exact_native_request(monkeypatch):
    provider, bound, requirement = _fixture(monkeypatch)
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "compiled", result.model_dump_json()
    assert result.request.prompt_text == TEXT
    assert not re.search(r"[A-Za-z]", result.request.prompt_text.replace("{{image:0}}", ""))
    assert result.request.prompt_text.count("{{image:0}}") == 1
    assert result.request.image_bindings[0].asset_sha256 == requirement.asset_evidence[0].asset_sha256
    assert provider.resolve(result.request).prompt_text == TEXT
    assert provider._transport.uploads == []


def test_legacy_compiler_keeps_historical_terminal_newline_bytes(monkeypatch):
    text = TEXT + "\n"
    provider, bound, requirement = _fixture(monkeypatch, text=text)
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "compiled"
    assert result.request.adapter_compiler_version == "1"
    assert result.request.prompt_text == text


@pytest.mark.parametrize("outer", ["\n", "\r\n", " \t", "\ufeff", "\u3000",
    "\u0085", "\u200b", "\u180e", "\u001c"])
def test_v2_seals_ecmascript_trimmed_bytes_before_preview(monkeypatch, outer):
    import json
    import subprocess

    text = outer + TEXT + outer
    expected = json.loads(subprocess.check_output(["node", "-e",
        "let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(JSON.parse(s).trim())))"],
        input=json.dumps(text).encode()))
    # QA still owns literal fragments. Boundary whitespace is not a required
    # fragment in the real S05 recipe; the compiler must not rewrite QA.
    provider, bound, requirement = _fixture(monkeypatch, text=text, fragment=TEXT,
        compiler_version="2")
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "compiled", result.model_dump_json()
    assert result.request.adapter_compiler_version == "2"
    assert result.request.prompt_text == expected
    assert provider.resolve(result.request).prompt_text == expected
    assert requirement.target_shot.intent == text
    assert result.request.image_bindings[0].asset_sha256 == requirement.asset_evidence[0].asset_sha256
    assert result.request.prompt_text.count("{{image:0}}") == 1
    assert provider._transport.uploads == []


def test_v2_does_not_weaken_a_qa_fragment_requiring_terminal_whitespace(monkeypatch):
    provider, bound, requirement = _fixture(monkeypatch, text=TEXT + "\n",
        compiler_version="2")
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "unsupported"
    assert "authored-expression" in result.unsupported_field_paths
    assert provider._transport.uploads == []


@pytest.mark.parametrize("change", ["stale", "fragment", "performance"])
def test_incomplete_final_text_evidence_never_falls_back_to_long_template(monkeypatch, change):
    provider, bound, requirement = _fixture(monkeypatch,
        stale_hash=change == "stale", fragment="未出现在最终正文里的必需片段" if change == "fragment" else None,
        missing_path="generation_intent.performance_intent.visible_response" if change == "performance" else None)
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "unsupported", result
    assert result.input_expression_report is not None
    assert result.input_expression_report.prompt_text == TEXT
    assert result.input_expression_report.actual_quality == "NOT_EVALUATED"
    assert provider._transport.uploads == []


def test_unbound_marker_still_fails_selected_material_admission(monkeypatch):
    provider, bound, requirement = _fixture(monkeypatch, text=TEXT.replace("{{image:0}}", "{{image:9}}"))
    assert provider.compile_request(bound, requirement).outcome == "unsupported"
    assert provider._transport.uploads == []


def test_causal_legacy_recipe_keeps_its_exact_automatic_grammar(monkeypatch):
    from ai_video.production.jimeng_prompt import compile_jimeng_native_prompt
    from test_jimeng_causal_compilation import _causal_reference

    provider, bound, requirement = _causal_reference(monkeypatch)
    native = compile_jimeng_native_prompt(compiler_id=provider._profile.compiler_id,
        compiler_version="1", provider_bound=bound, requirement=requirement)
    result = provider.compile_request(bound, requirement)
    assert result.outcome == "compiled", result.model_dump_json()
    assert result.request.prompt_text == native.prompt_text
    assert result.request.prompt_text.startswith("Opening state:")
    assert result.request.prompt_text.count("{{image:0}}") == 1
    assert hashlib.sha256(native.prompt_text.encode()).hexdigest() == native.prompt_sha256


@pytest.mark.parametrize("case", ["valid", "stale", "wrong_path", "missing_intent", "removed"])
def test_explicit_raw_revision_requires_current_scalar_mapping(monkeypatch, case):
    from ai_video.production.generation_authored_retarget import _acceptance_revision_ids
    provider, bound, requirement = _fixture(monkeypatch)
    new = bound.generation_recipe.acceptance_policy
    rule = bound.generation_recipe.expressions[0]
    old_rule = rule.model_copy(update={"native_text_mapping": None, "native_text": ()})
    old = _sealed_acceptance((old_rule,))
    if case in {"stale", "wrong_path"}:
        data = rule.model_dump(mode="json")
        if case == "stale":
            data["native_text_mapping"]["intent_sha256"] = "f" * 64
        else:
            data["native_text_mapping"]["bindings"][0]["intent_path"] = "generation_intent.subject_action"
            data["intent_paths"].append("generation_intent.subject_action")
        new = _sealed_acceptance((RequirementExpression.model_validate(data),))
    if case == "removed":
        old, new = new, old
    result = _acceptance_revision_ids(old, new,
        intent=None if case == "missing_intent" else requirement.generation_intent)
    assert result == (("authored-expression",) if case == "valid" else None)


def test_canonical_qualification_admits_current_mapping_and_rejects_stale_intent(tmp_path):
    from test_generation_authored_retarget import (
        _same_model_reference_repair, _retarget_target, _retarget_binding, _changed_acceptance,
    )
    from ai_video.production._qualification_authoring_revision import allows_authored_generation_retarget
    baseline, retained, target, _, _ = _same_model_reference_repair(tmp_path)
    path = "generation_intent.pacing.cadence"
    acceptance = _changed_acceptance(retained.candidate.recipe.acceptance_policy, changes={
        "performance": {"intent_paths": ["generation_intent.performance_intent", path],
            "native_text": ["压低声音焦急求证"], "native_text_mapping": {
                "intent_sha256": canonical_sha256(target.intent.model_dump(mode="json")),
                "bindings": [{"intent_path": path, "fragment_indices": [0]}]}}})
    target = _retarget_target(baseline, retained, acceptance=acceptance,
                             revised_requirement_ids=("performance",))
    binding, selected = _retarget_binding(baseline, retained, target, request_changes={
        "prompt_text": baseline.compiled_request.activation_scope.request.prompt_text + " 压低声音焦急求证"})
    selected.capabilities = retained.candidate.capabilities
    assert allows_authored_generation_retarget(binding, selected)
    intent = target.intent.model_copy(update={"pacing": target.intent.pacing.model_copy(
        update={"cadence": "未经封存的新节奏"})})
    binding.projection.requirement.generation_intent = intent
    assert not allows_authored_generation_retarget(binding, selected)
