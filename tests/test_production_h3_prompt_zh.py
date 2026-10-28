from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from ai_video.production._causal_state_expression import render_causal_facts
from ai_video.production._h3_prompt import (
    H3PromptCompilation,
    H3PromptUnsupported,
    compile_h3_prompt,
)
from ai_video.production.comfy_t8_native_turbo_profile import (
    load_t8_native_turbo_execution_profile,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.performance_direction import (
    CharacterPerformanceDirection,
    PerformanceBeat,
    PerformanceIntent,
    render_performance_direction,
)
from ai_video.production.video_requirement import (
    CapabilityNeed,
    ContinuityMode,
    DialogueIntent,
    GenerationMode,
    ProviderNeutralVideoRequirement,
)
from ai_video.production.video_transition import CausalDimension
from tests.test_production_h3_prompt import _requirement

REPO_ROOT = Path(__file__).resolve().parents[1]
_GRAMMAR_TOKENS = {
    "integrated_multimodal_description",
    "overall_soundscape",
    "non_diegetic_music",
    "Shot",
    "S1",
    "d",
    "Chinese",
    "English",
}


def _legacy_t2va_requirement() -> ProviderNeutralVideoRequirement:
    current = _requirement()
    intent = current.generation_intent.model_copy(
        update={
            "camera_intent": current.generation_intent.camera_intent.model_copy(
                update={"movement": "locked"}
            ),
            "primary_camera_motion": None,
            "camera_subject_relation": None,
        }
    )
    payload = current.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"})
    payload.update(
        contract_version="provider-neutral-video-requirement/1",
        generation_mode=GenerationMode.TEXT_TO_VIDEO,
        continuity_mode=ContinuityMode.NONE,
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        conditioning_compatibility=None,
        asset_evidence=(),
        semantic_reference_roles=(),
        capability_need=CapabilityNeed(),
    )
    return ProviderNeutralVideoRequirement.create(**payload)


def _authored_tokens(requirement: ProviderNeutralVideoRequirement) -> set[str]:
    # The camera motion contract is validator-owned enums, never authored text.
    intent = requirement.generation_intent.model_dump(
        mode="json", exclude={"primary_camera_motion"}
    )
    relation = requirement.generation_intent.camera_subject_relation
    if relation is not None:
        intent["camera_subject_relation"] = {
            "subject_id": relation.subject_id,
            "start_relation": relation.start_relation,
            "end_relation": relation.end_relation,
        }
    authored = json.dumps(
        {
            "intent": intent,
            "scene_id": requirement.scene.scene_id,
        },
        ensure_ascii=False,
    )
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", authored))


def _with_trigger(requirement, trigger: str):
    performance = requirement.generation_intent.performance_intent
    intent = requirement.generation_intent.model_copy(
        update={"performance_intent": performance.model_copy(update={"trigger": trigger})}
    )
    return requirement.model_copy(update={"generation_intent": intent})


@pytest.mark.parametrize("build", [_requirement, _legacy_t2va_requirement])
def test_zh_prompt_keeps_only_h3_grammar_and_authored_text_in_latin(build) -> None:
    requirement = build()

    result = compile_h3_prompt(requirement, language="zh")

    assert isinstance(result, H3PromptCompilation)
    prompt = result.prompt_text
    assert [line.split(":", 1)[0] for line in prompt.splitlines()] == [
        "integrated_multimodal_description",
        "overall_soundscape",
        "non_diegetic_music",
    ]
    assert prompt.count("[Shot 1]") == 1
    compiler_latin = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", prompt)) - _authored_tokens(
        requirement
    )
    assert compiler_latin <= _GRAMMAR_TOKENS
    assert "unspecified" not in prompt


def test_zh_v4_prompt_renders_camera_contract_in_chinese() -> None:
    prompt = compile_h3_prompt(_requirement(), language="zh").prompt_text

    assert "运镜：推镜，小幅，慢速，方向向前" in prompt
    assert "forward" not in prompt
    assert "运镜结束状态：停稳" in prompt
    assert prompt.endswith("non_diegetic_music: 无")


def test_zh_t2va_prompt_forbids_visible_text_in_chinese() -> None:
    prompt = compile_h3_prompt(_legacy_t2va_requirement(), language="zh").prompt_text

    assert "运镜：固定机位" in prompt
    assert "画面中不出现任何可见文字、字幕或说明文字" in prompt
    assert "声音只包含上述环境声与物理拟音" in prompt


@pytest.mark.parametrize(
    ("build", "sha256"),
    [
        (_requirement, "8a41728d3712657746311696b46b1d5aa15886b4a52330d1e111fe2eeb954099"),
        (
            _legacy_t2va_requirement,
            "e0cc8051fc125db95971c7273cb3a004de50de6a187036ab7439737972e544c3",
        ),
    ],
)
def test_default_language_keeps_exact_english_bytes(build, sha256: str) -> None:
    # Golden hashes come from the pre-change compiler; English replay must not drift.
    requirement = build()

    assert compile_h3_prompt(requirement).prompt_sha256 == sha256
    assert compile_h3_prompt(requirement) == compile_h3_prompt(requirement, language="en")


def test_zh_t2va_dialogue_keeps_native_tag_and_speaker_window() -> None:
    current = _legacy_t2va_requirement()
    intent = current.generation_intent.model_copy(
        update={
            "dialogue_intent": DialogueIntent(
                mode="dialogue",
                language="zh-CN",
                speaker_id="hero",
                verbatim_text="我留下。",
                start_seconds=0.5,
                end_seconds=1.5,
                on_screen=True,
                response_obligation="轻声而坚定",
                lip_sync_required=True,
            )
        }
    )
    payload = current.model_dump(mode="python", exclude={"requirement_id", "requirement_hash"})
    payload.update(
        generation_intent=intent,
        generation_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
    )

    result = compile_h3_prompt(ProviderNeutralVideoRequirement.create(**payload), language="zh")

    assert isinstance(result, H3PromptCompilation)
    assert "说话人hero只说一次<d>[Chinese]我留下。</d>，时间为0.500秒至1.500秒" in result.prompt_text
    assert "需要口型同步" in result.prompt_text and "无旁白，无其他人声" in result.prompt_text


def test_unknown_language_fails_closed() -> None:
    with pytest.raises(ValueError):
        compile_h3_prompt(_requirement(), language="fr")


@pytest.mark.parametrize("build", [_requirement, _legacy_t2va_requirement])
def test_zh_prompt_rejects_chinese_transition_instruction(build) -> None:
    result = compile_h3_prompt(_with_trigger(build(), "镜头切到窗外"), language="zh")

    assert isinstance(result, H3PromptUnsupported)
    assert "generation_intent.performance_intent.trigger" in result.unsupported_field_paths


def test_zh_t2va_rejects_speech_cue_when_dialogue_is_absent() -> None:
    requirement = _with_trigger(_legacy_t2va_requirement(), "听见旁白后抬头")
    assert requirement.generation_intent.dialogue_intent.mode == "none"

    result = compile_h3_prompt(requirement, language="zh")

    assert isinstance(result, H3PromptUnsupported)
    assert "generation_intent.performance_intent.trigger" in result.unsupported_field_paths


def test_zh_causal_facts_and_performance_direction_are_chinese() -> None:
    facts = ((CausalDimension.HAND_CONTACT, "左手离开玻璃"),)

    assert render_causal_facts(facts, language="zh") == "手部接触：左手离开玻璃"
    assert render_causal_facts(facts) == "hand contact: 左手离开玻璃"
    assert render_performance_direction(_requirement().generation_intent, language="zh") == ""
    performance = PerformanceIntent(
        **_requirement().generation_intent.performance_intent.model_dump(),
        character_directions=(
            CharacterPerformanceDirection(
                character_id="hero", screen_identity="林砚", role="principal",
                visibility="visible", beats=(PerformanceBeat(
                    phase="response", trigger="听见广播", emotion="警觉", intensity="subtle",
                    facial_expression="眉头收紧", gaze_target="车窗", breathing="屏住呼吸",
                    body_behavior="身体不动"),),
            ),
            CharacterPerformanceDirection(
                character_id="pa", screen_identity="列车广播", role="supporting",
                visibility="offscreen", offscreen_reason="声音来自车顶扬声器", beats=(),
            ),
        ),
    )
    assert render_performance_direction(performance, language="zh") == (
        "人物表演指导：林砚（主要角色，在画内）：反应阶段，在听见广播之后，表现警觉，强度轻微；"
        "面部表情：眉头收紧；视线目标：车窗；呼吸：屏住呼吸；身体动作：身体不动。"
        "列车广播（配角，在画外）：保持在画外，原因是声音来自车顶扬声器。"
    )
    with pytest.raises(ValueError):
        render_causal_facts(facts, language="fr")


def test_prompt_language_keeps_legacy_profile_hashes_and_seals_zh() -> None:
    profiles = REPO_ROOT / "workflows/profiles"
    legacy_path = profiles / "minimax_h3_t8_i2va_turbo_native_v2.json"
    legacy = load_t8_native_turbo_execution_profile(legacy_path, artifact_root=REPO_ROOT)
    zh = load_t8_native_turbo_execution_profile(
        profiles / "minimax_h3_t8_i2va_turbo_native_v2_zh.json", artifact_root=REPO_ROOT
    )

    assert legacy.prompt_language == "en"
    assert "prompt_language" not in legacy.model_dump(mode="json")
    assert legacy.profile_content_hash == json.loads(legacy_path.read_text())[
        "profile_content_hash"
    ]
    assert zh.prompt_language == "zh"
    assert zh.capability_id == legacy.capability_id
    assert zh.profile_content_hash != legacy.profile_content_hash


@pytest.mark.parametrize(
    "name",
    [
        "minimax_h3_fl2va_quality",
        "minimax_h3_t8_t2va_quality",
        "minimax_h3_t8_t2va_turbo",
        "minimax_h3_t8_t2va_turbo_native_v2",
        "minimax_h3_t8_i2va_turbo_native_v2",
        "minimax_h3_t8_fl2va_turbo_native_v2",
        "minimax_h3_t8_ref2va_turbo_native_v2",
        "minimax_h3_t8_ref2va_turbo_native_17s_v3",
    ],
)
def test_every_zh_profile_differs_from_its_lane_only_by_prompt_language(name: str) -> None:
    from ai_video.production.comfy_t8_turbo_video import load_t8_turbo_video_execution_profile
    from ai_video.production.comfy_t8_video import load_t8_video_execution_profile
    from ai_video.production.comfy_video import load_local_video_execution_profile

    load = (
        load_local_video_execution_profile
        if name.startswith("minimax_h3_fl2va")
        else load_t8_turbo_video_execution_profile
        if name == "minimax_h3_t8_t2va_turbo"
        else load_t8_video_execution_profile
        if name == "minimax_h3_t8_t2va_quality"
        else load_t8_native_turbo_execution_profile
    )
    profiles = REPO_ROOT / "workflows/profiles"
    en = load(profiles / f"{name}.json", artifact_root=REPO_ROOT)
    zh = load(profiles / f"{name}_zh.json", artifact_root=REPO_ROOT)

    assert (en.prompt_language, en.h3_grammar_contract) == ("en", "h3-three-field-v1")
    assert (zh.prompt_language, zh.h3_grammar_contract) == ("zh", "h3-three-field-zh-v1")
    assert type(zh) is type(en)
    assert zh.model_dump(mode="json", exclude={"prompt_language", "profile_content_hash"}) == (
        en.model_dump(mode="json", exclude={"profile_content_hash"})
    )
    assert zh.profile_content_hash != en.profile_content_hash
