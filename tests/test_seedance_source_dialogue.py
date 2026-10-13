"""Source dialogue attests controls only from an exact declaration."""
from types import SimpleNamespace

import pytest

from ai_video.production.generation_recipe import _unexpressed_authored_text
from ai_video.production.seedance_source_expression import _source_native_prompt
from ai_video.production.video_requirement import DialogueIntent, GenerationIntent


def facts(**changes):
    return DialogueIntent.model_validate(dict(mode="dialogue", language="zh", speaker_id="speaker",
        verbatim_text="原句。", start_seconds=0.1, end_seconds=2.7, on_screen=False,
        response_obligation="原句。", lip_sync_required=False) | changes)


def native(dialogue, text, *, native_audio=True):
    intent = GenerationIntent(dialogue_intent=dialogue)
    result = _source_native_prompt(
        SimpleNamespace(output_requirement=SimpleNamespace(native_audio=native_audio, duration_seconds=4)),
        SimpleNamespace(generation_intent=intent), text, ())
    return result, _unexpressed_authored_text(SimpleNamespace(generation_intent=intent), text,
                                           result.expressed_control_paths)


@pytest.mark.parametrize("on_screen,lip", [(False, False), (True, True)])
def test_exact_chinese_source_dialogue_preserves_bytes_and_expresses_controls(on_screen, lip):
    text = ("原生对白约束：普通话；[0.1–2.7s]“请在终点站下车。”；"
            + ("画内" if on_screen else "画外") + "；"
            + ("口型与对白同步" if lip else "不要求口型同步") + "。")
    dialogue = facts(verbatim_text="请在终点站下车。", response_obligation="请在终点站下车。",
                     on_screen=on_screen, lip_sync_required=lip)
    result, errors = native(dialogue, text)
    assert result.prompt_text.encode() == text.encode()
    assert not errors


@pytest.mark.parametrize("change", [
    {"start_seconds": 0.2}, {"end_seconds": 2.8}, {"on_screen": True},
    {"lip_sync_required": True}, {"language": "en"}, {"verbatim_text": "另一句。"}])
def test_mismatched_source_declaration_cannot_attest_typed_controls(change):
    dialogue = facts().model_copy(update=change)
    _, errors = native(dialogue, "原生对白约束：普通话；[0.1–2.7s]“原句。”；画外；不要求口型同步。")
    assert errors


def test_verbatim_substring_without_declaration_cannot_attest_window_or_screen():
    dialogue = facts()
    _, errors = native(dialogue, "[0.1–2.7s] 原句。")
    assert "generation_intent.dialogue_intent.start_seconds" in errors
    assert "generation_intent.dialogue_intent.on_screen" in errors


def test_dialogue_source_cannot_allow_missing_native_audio():
    with pytest.raises(ValueError, match="native audio"):
        native(facts(),
               "原句。", native_audio=False)


def test_dialogue_window_outside_bound_output_rejected():
    with pytest.raises(ValueError, match="duration"):
        native(facts(end_seconds=5),
            "原生对白约束：普通话；[0.1–5s]“原句。”；不要求口型同步。")


@pytest.mark.parametrize("first_frame", [False, True])
def test_source_dialogue_survives_public_common_compiler_with_exact_source_bytes(first_frame):
    from ai_video.production.seedance import SeedanceVideoProvider
    from ai_video.production.seedance_source_expression import SourceReferenceMaterial, SourceTextPart
    from ai_video.production.shot_router import AdapterCompilerContract, ProviderBoundVideoRequest
    from ai_video.production.video_compiler import CompiledProviderVideoRequest
    from test_seedance_source_expression import _expression, _rebind_source_expression
    from test_seedance_source_prompt import _case

    profile, bound, requirement, source = _case(first_frame=first_frame)
    prompt = source + "\n原生对白约束：普通话；[0.1–2.7s]“原句。”；画外；不要求口型同步。"
    requirement = requirement.model_copy(update={"generation_intent":
        requirement.generation_intent.model_copy(update={"dialogue_intent": facts(),
            "subject_action": requirement.generation_intent.subject_action.model_copy(
                update={"progression": prompt})})})
    frames = (() if not first_frame else (SourceReferenceMaterial(
        asset_id=requirement.asset_evidence[0].asset_id,
        asset_sha256=requirement.asset_evidence[0].asset_sha256, role="first_frame"),))
    bound, requirement = _rebind_source_expression(bound, requirement,
        _expression((SourceTextPart(text=prompt),), implicit_references=frames), prompt)
    compiler = AdapterCompilerContract.create(compiler_id="seedance-video-compiler", compiler_version="3")
    bound = ProviderBoundVideoRequest.create(**{
        **{name: getattr(bound, name) for name in ProviderBoundVideoRequest.model_fields
           if name != "provider_bound_request_hash"},
        "compiler_contract": compiler,
        "generation_recipe": bound.generation_recipe.model_copy(update={"compiler_hash": compiler.compiler_hash})})
    def forbidden(*args, **kwargs):
        pytest.fail("offline compilation cannot use Provider effects or credentials")
    provider = SeedanceVideoProvider(profile=profile, transport=forbidden,
        credential=forbidden, input_reference=forbidden)
    compiled = provider.compile_request(bound, requirement)
    assert isinstance(compiled, CompiledProviderVideoRequest)
    assert compiled.request.prompt_text.encode() == prompt.encode()
    assert compiled.request.output_requirement.native_audio
