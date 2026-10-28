"""Chinese rendering of the H3 native three-field grammar.

Only the H3 grammar markers stay in their native form: the three field headers,
``[Shot 1]``, the ``<d>[Language]…</d>`` dialogue tag and the ``S1`` speaker
marker. Every connective, label and enum value is rendered in Chinese, and
``unspecified`` sentinels are omitted rather than written into the prompt.
Validation stays with ``_h3_prompt``; this module only renders validated intent.
"""

from __future__ import annotations

import re

from ai_video.production.performance_direction import render_performance_direction

H3_ZH_GRAMMAR_CONTRACT = "h3-three-field-zh-v1"
H3_GRAMMAR_CONTRACTS = frozenset({"h3-three-field-v1", H3_ZH_GRAMMAR_CONTRACT})


def h3_prompt_language(native_prompt) -> str:
    """Recompile language sealed by a native prompt's grammar contract."""

    grammar = getattr(native_prompt, "grammar_contract", None)
    return "zh" if grammar == H3_ZH_GRAMMAR_CONTRACT else "en"

_UNSPECIFIED = "unspecified"

_MOVEMENT = {
    "locked": "固定机位",
    "pan_left": "向左摇镜",
    "pan_right": "向右摇镜",
    "tilt_up": "向上摇镜",
    "tilt_down": "向下摇镜",
    "dolly_in": "推镜",
    "dolly_out": "拉镜",
    "truck_left": "向左横移",
    "truck_right": "向右横移",
    "pedestal_up": "垂直升高",
    "pedestal_down": "垂直降低",
    "orbit_left": "向左环绕",
    "orbit_right": "向右环绕",
    "crane_up": "摇臂上升",
    "crane_down": "摇臂下降",
}
_DIRECTION = {
    "left": "向左",
    "right": "向右",
    "up": "向上",
    "down": "向下",
    "forward": "向前",
    "backward": "向后",
}
_AMPLITUDE = {"subtle": "小幅", "moderate": "中等幅度", "pronounced": "大幅"}
_SPEED = {"very_slow": "极慢", "slow": "慢速", "moderate": "中速", "fast": "快速"}
_START_MOTION = {"stationary": "静止", "in_motion": "运动中"}
_END_MOTION = {"settled": "停稳", "continuing": "持续运动"}
_RELATION = {
    "fixed_frame": "固定构图",
    "maintain_offset": "保持相对距离",
    "follow": "跟随",
    "lead": "前导",
    "reveal": "揭示",
}

# Chinese counterparts of the English reserved-structure checks. Authored
# fields may not smuggle edit/transition instructions or, for no-dialogue
# shots, speech cues into the compiled prompt.
ZH_RESERVED_TRANSITION_INSTRUCTION = re.compile(
    r"切到|切至|切换到|切入|切出|转场|叠化|闪切|闪白|淡入|淡出|变速|补帧"
)
ZH_NO_DIALOGUE_SPEECH_CUE = re.compile(r"旁白|对白|台词|解说|人声|说话|念出|配音")


def _yes_no(value: bool) -> str:
    return "是" if value else "否"


def _clauses(*items: tuple[str, object]) -> list[str]:
    """Render ``label：value`` clauses, omitting unspecified sentinels."""

    rendered = []
    for label, value in items:
        if value is None:
            continue
        text = str(value)
        if not text.strip() or text.strip().casefold() == _UNSPECIFIED:
            continue
        rendered.append(f"{label}：{text}" if label else text)
    return rendered


def _action_chain(*states: str) -> str | None:
    present = [state for state in states if state.strip().casefold() != _UNSPECIFIED]
    return " → ".join(present) if present else None


def _join(parts: list[str]) -> str:
    return "；".join(parts)


def render_h3_v4_zh(
    requirement,
    *,
    state_texts: dict[str, str],
    endpoint_text: str,
    dialogue_language: str | None,
) -> str:
    intent = requirement.generation_intent
    performance = intent.performance_intent
    treatment = intent.visual_treatment
    lighting = intent.lighting_intent
    ambience = intent.ambience_intent
    dialogue = intent.dialogue_intent
    music = intent.music_intent
    motion = intent.primary_camera_motion
    relation = intent.camera_subject_relation

    parts: list[str] = []
    if dialogue.mode == "dialogue":
        parts.append(
            f"对白：说话人S1即{dialogue.speaker_id}，"
            f"{'在画内' if dialogue.on_screen else '在画外'}。"
            f"以下为表演与反应指导，不得念出：{dialogue.response_obligation}。"
            f"只在{dialogue.start_seconds:.3f}秒至{dialogue.end_seconds:.3f}秒之间说话。"
            f"{'需要' if dialogue.lip_sync_required else '不需要'}口型同步。"
            "只有下列标记内的文字被说出，且只说一次。说话人S1准确且只说："
            f"<d>[{dialogue_language}] {dialogue.verbatim_text}</d>"
            "标记外不得出现旁白或其他人声"
        )
    camera_motion = (
        "固定机位"
        if motion.movement_kind.value == "locked"
        else (
            f"{_MOVEMENT[motion.movement_kind.value]}，"
            f"{_AMPLITUDE[motion.amplitude_class.value]}，"
            f"{_SPEED[motion.speed_class.value]}，方向{_DIRECTION[motion.direction]}"
        )
    )
    parts += _clauses(
        ("场景", requirement.scene.scene_id),
        ("起始状态", state_texts["open_state"]),
        (
            "动作",
            _action_chain(
                intent.subject_action.start_state,
                intent.subject_action.progression,
                endpoint_text,
            ),
        ),
        ("结束状态", state_texts["close_state"]),
        ("表演触发", performance.trigger),
        ("可见反应", performance.visible_response),
        ("视线", performance.gaze_target),
        ("身体", performance.body_behavior),
        ("双手", performance.hand_behavior),
        ("表演终态", performance.terminal_performance_state),
        ("画面质感", treatment.medium_look),
        ("色调", treatment.palette),
        ("材质", treatment.material_treatment),
        ("禁止", "、".join(treatment.prohibited_visual_drift)),
        ("光源", lighting.motivated_source),
        ("光线方向", lighting.direction),
        ("曝光优先", lighting.exposure_priority),
        ("光线连续", lighting.continuity_state),
        ("画面方向", intent.space_continuity.screen_direction),
        ("摄影轴线", intent.axis_continuity.camera_axis),
        ("构图连续", intent.axis_continuity.framing_continuity),
        ("起始构图", intent.camera_endpoint.start_framing),
        ("运镜", camera_motion),
        (
            "镜头与主体关系",
            f"对主体{relation.subject_id}{_RELATION[relation.relation_kind.value]}，"
            f"从{relation.start_relation}到{relation.end_relation}",
        ),
        ("结束构图", intent.camera_endpoint.end_framing),
        ("运镜起始状态", _START_MOTION[motion.start_motion_state.value]),
        ("运镜结束状态", _END_MOTION[motion.end_motion_state.value]),
        ("时长", f"{intent.pacing.shot_duration_seconds:g}秒"),
    )
    visual = "[Shot 1] " + _join(parts)
    direction = render_performance_direction(performance, language="zh")
    if direction:
        visual += "；" + direction

    foley = "、".join(ambience.foley_cues) if ambience.foley_cues else "无"
    sound_parts = _clauses(
        ("环境声", ambience.environment_bed),
        ("拟音", foley),
        ("明确静音", _yes_no(ambience.explicitly_silent)),
    )
    if dialogue.mode == "none":
        sound_parts.append("无对白")
    music_text = (
        _join(_clauses(("", music.instrumentation), ("", music.tempo_rhythm),
                       ("", music.dynamics)))
        if music.mode == "music"
        else "无"
    )
    return "\n".join(
        (
            f"integrated_multimodal_description: {visual}",
            f"overall_soundscape: {_join(sound_parts)}",
            f"non_diegetic_music: {music_text or '无'}",
        )
    )


def render_h3_t2va_zh(requirement, *, endpoint_text: str, dialogue_language: str | None) -> str:
    intent = requirement.generation_intent
    performance = intent.performance_intent
    treatment = intent.visual_treatment
    lighting = intent.lighting_intent
    ambience = intent.ambience_intent
    dialogue = intent.dialogue_intent
    music = intent.music_intent
    endpoint = intent.camera_endpoint
    camera = intent.camera_intent
    space = intent.space_continuity
    axis = intent.axis_continuity
    envelope = intent.motion_envelope

    parts = _clauses(
        ("", treatment.medium_look),
        (
            "动作",
            _action_chain(
                intent.subject_action.start_state,
                intent.subject_action.progression,
                endpoint_text,
            ),
        ),
        ("动作终点必须发生变化", _yes_no(intent.subject_action.endpoint.required_change)),
        ("表演触发", performance.trigger),
        ("可见反应", performance.visible_response),
        ("视线", performance.gaze_target),
        ("身体", performance.body_behavior),
        ("双手", performance.hand_behavior),
        ("表演终态", performance.terminal_performance_state),
        ("色调", treatment.palette),
        ("材质", treatment.material_treatment),
        ("光源", lighting.motivated_source),
        ("光线方向", lighting.direction),
        ("曝光优先", lighting.exposure_priority),
        ("光线连续", lighting.continuity_state),
        ("人物位置", space.subject_position),
        ("画面方向", space.screen_direction),
        ("入画", space.entrance_state or "无"),
        ("出画", space.exit_state or "无"),
        ("空间越轴规则", space.crossing_policy),
        ("摄影轴线", axis.camera_axis),
        ("构图连续", axis.framing_continuity),
        ("轴线越轴规则", axis.crossing_policy),
        ("构图意图", camera.framing_intent),
        ("起始构图", endpoint.start_framing),
        ("运镜", "固定机位" if camera.movement in {"locked", "locked-off"} else None),
        ("镜头稳定", camera.stability),
        ("机位锁定", _yes_no(endpoint.position_lock)),
        ("朝向锁定", _yes_no(endpoint.orientation_lock)),
        ("结束构图", endpoint.end_framing),
        ("运动", _action_chain(envelope.onset, envelope.peak, envelope.settle)),
        ("运动方向", envelope.direction),
        ("运动幅度", envelope.amplitude_class),
        ("节奏", intent.pacing.cadence),
        ("速度感", intent.pacing.tempo_class),
        ("时长", f"{intent.pacing.shot_duration_seconds:.3f}秒"),
        ("禁止", "、".join(treatment.prohibited_visual_drift) or "无"),
    )
    parts.append("画面中不出现任何可见文字、字幕或说明文字")
    visual = "[Shot 1] " + _join(parts)
    direction = render_performance_direction(performance, language="zh")
    if direction:
        visual += "；" + direction

    foley = "、".join(ambience.foley_cues) if ambience.foley_cues else "无"
    sound_parts = _clauses(
        ("环境声", ambience.environment_bed),
        ("明确静音", _yes_no(ambience.explicitly_silent)),
        ("拟音", foley),
    )
    if dialogue.mode == "dialogue":
        sound_parts.append(
            f"说话人{dialogue.speaker_id}只说一次"
            f"<d>[{dialogue_language}]{dialogue.verbatim_text}</d>"
            f"，时间为{dialogue.start_seconds:.3f}秒至{dialogue.end_seconds:.3f}秒"
        )
        sound_parts.append("在画内" if dialogue.on_screen else "在画外")
        sound_parts += _clauses(("反应要求", dialogue.response_obligation))
        sound_parts.append(f"{'需要' if dialogue.lip_sync_required else '不需要'}口型同步")
        sound_parts.append("无旁白，无其他人声")
    else:
        sound_parts.append("声音只包含上述环境声与物理拟音")
    music_text = (
        _join(_clauses(("", music.instrumentation), ("", music.tempo_rhythm),
                       ("", music.dynamics)))
        if music.mode == "music"
        else "无"
    )
    return "\n".join(
        (
            f"integrated_multimodal_description: {visual}",
            f"overall_soundscape: {_join(sound_parts)}",
            f"non_diegetic_music: {music_text or '无'}",
        )
    )


__all__ = [
    "H3_GRAMMAR_CONTRACTS",
    "H3_ZH_GRAMMAR_CONTRACT",
    "ZH_NO_DIALOGUE_SPEECH_CUE",
    "ZH_RESERVED_TRANSITION_INSTRUCTION",
    "render_h3_t2va_zh",
    "h3_prompt_language",
    "render_h3_v4_zh",
]
