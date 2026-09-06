"""Native prose projection for new Vidu requests."""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production.models import StrictModel
from ai_video.production.video_requirement import (
    ContinuityStateKind,
    ProviderNeutralVideoRequirement,
)


class _ViduPromptModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ViduPromptUnsupported(_ViduPromptModel):
    outcome: Literal["unsupported"] = "unsupported"
    unsupported_field_paths: tuple[str, ...] = Field(min_length=1)
    prompt_text: None = None


class ViduPromptCompilation(_ViduPromptModel):
    outcome: Literal["compiled"] = "compiled"
    prompt_text: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_hash(self) -> "ViduPromptCompilation":
        if self.prompt_sha256 != hashlib.sha256(
            self.prompt_text.encode("utf-8")
        ).hexdigest():
            raise ValueError("prompt_sha256 does not match prompt_text")
        return self


ViduPromptResult = ViduPromptCompilation | ViduPromptUnsupported


_REFERENCE_SENTENCES = {
    "identity": "保持提供的人物身份参考中的外观连续一致。",
    "scene": "保持提供的场景参考中的空间和环境连续一致。",
    "first_frame": "以提供的首帧图像作为精确的视觉起点。",
    "last_frame": "以提供的末帧图像作为动作结束时应达到的视觉状态。",
    "continuity_terminal": "从提供的连续性末帧状态开始。",
    "approved_endpoint": "以提供的已批准终点图像作为动作结束时应达到的视觉状态。",
    "continuity_motion_tail": "延续提供的动作尾段参考中的运动状态。",
    "video_reference": "保持提供的视频参考中的可见连续性。",
    "audio_reference": "遵循提供的声音参考。",
}


def _state_text(state: object, path: str) -> tuple[str | None, tuple[str, ...]]:
    kind = getattr(state, "kind", None)
    if kind is ContinuityStateKind.UNSPECIFIED:
        return (None, (path,)) if getattr(state, "required_change", False) else (None, ())
    if kind is not ContinuityStateKind.TYPED_TEXT:
        return None, (path,)
    text = getattr(state, "state_text", None)
    return (text, ()) if isinstance(text, str) and text else (None, (path,))


def _endpoint_text(endpoint: object) -> tuple[str | None, tuple[str, ...]]:
    text = getattr(endpoint, "state_text", None)
    if isinstance(text, str) and text:
        return text, ()
    if getattr(endpoint, "state_ref", None) or getattr(endpoint, "state_hash", None):
        return None, ("generation_intent.subject_action.endpoint",)
    return None, ()


def _optional(label: str, value: str | None) -> str | None:
    if value is None or value == "unspecified":
        return None
    return f"{label}：{value}。"


def compile_vidu_prompt(
    requirement: ProviderNeutralVideoRequirement,
) -> ViduPromptResult:
    """Render legacy /1 intent as readable Vidu prose without metadata leakage."""

    intent = requirement.generation_intent
    unsupported: list[str] = []
    if requirement.contract_version != "provider-neutral-video-requirement/1":
        unsupported.append("contract_version")
    if any(
        value is not None
        for value in (
            requirement.commercial_execution_class,
            requirement.product_fidelity_requirement,
            requirement.approved_commercial_source,
            requirement.source_strategy,
            intent.performance_intent,
            intent.visual_treatment,
            intent.lighting_intent,
            intent.ambience_intent,
            intent.dialogue_intent,
            intent.music_intent,
            intent.primary_camera_motion,
            intent.camera_subject_relation,
        )
    ):
        unsupported.append("generation_intent")
    opening, opening_paths = _state_text(intent.open_state, "generation_intent.open_state")
    closing, closing_paths = _state_text(intent.close_state, "generation_intent.close_state")
    endpoint, endpoint_paths = _endpoint_text(intent.subject_action.endpoint)
    unsupported.extend((*opening_paths, *closing_paths, *endpoint_paths))
    if unsupported:
        return ViduPromptUnsupported(
            unsupported_field_paths=tuple(dict.fromkeys(unsupported))
        )

    identity = intent.identity_continuity
    scene = intent.scene_continuity
    camera = intent.camera_intent
    endpoint_intent = intent.camera_endpoint
    action = intent.subject_action
    motion = intent.motion_envelope
    pacing = intent.pacing
    space = intent.space_continuity
    axis = intent.axis_continuity
    sentences = []
    reference_roles = {role.value for role in requirement.semantic_reference_roles}
    unsupported_roles = reference_roles.difference(_REFERENCE_SENTENCES)
    if unsupported_roles:
        return ViduPromptUnsupported(
            unsupported_field_paths=("semantic_reference_roles",)
        )
    sentences.extend(
        _REFERENCE_SENTENCES[role]
        for role in sorted(reference_roles)
    )
    if opening is not None:
        sentences.append(f"开场：{opening}。")
    if intent.open_state.required_change:
        sentences.append("开场状态必须产生真实的可见变化，不能用静止画面代替。")
    if identity.preservation.value != "unspecified":
        sentences.append("保持画面中人物的外观、服装和身份连续一致。")
    if identity.allowed_variation:
        sentences.append(
            "允许的变化仅限于" + "、".join(identity.allowed_variation) + "。"
        )
    if scene is not None:
        sentences.extend(
            item
            for item in (
                _optional("时间", scene.time_of_day),
                _optional("氛围", scene.mood),
            )
            if item is not None
        )
        sentences.extend(f"场景约束：{item}。" for item in scene.state_constraints)
    sentences.extend(
        item
        for item in (
            _optional("人物位置", space.subject_position),
            _optional("屏幕方向", space.screen_direction),
            _optional("进场状态", space.entrance_state),
            _optional("离场状态", space.exit_state),
            _optional("空间越轴规则", space.crossing_policy),
            _optional("摄影机轴线", axis.camera_axis),
            _optional("构图连续性", axis.framing_continuity),
            _optional("轴线越界规则", axis.crossing_policy),
        )
        if item is not None
    )
    action_parts = []
    if action.start_state != "unspecified":
        action_parts.append(f"从{action.start_state}开始")
    if action.progression != "unspecified":
        action_parts.append(action.progression)
    if endpoint is not None:
        action_parts.append(f"以{endpoint}结束")
    if action_parts:
        sentences.append("动作：" + "，".join(action_parts) + "。")
    if action.endpoint.required_change:
        sentences.append("该动作必须产生真实的可见状态变化，不能用静止画面代替。")
    sentences.extend(
        item
        for item in (
            _optional("动作起始", motion.onset),
            _optional("动作峰值", motion.peak),
            _optional("动作停稳", motion.settle),
            _optional("动作方向", motion.direction),
            _optional("动作幅度", motion.amplitude_class),
            _optional("节奏", pacing.cadence),
            _optional("速度", pacing.tempo_class),
        )
        if item is not None
    )
    if pacing.shot_duration_seconds is not None:
        sentences.append(f"镜头时长为{pacing.shot_duration_seconds:g}秒。")
    if closing is not None:
        sentences.append(f"收束状态：{closing}。")
    if intent.close_state.required_change:
        sentences.append("收束状态必须产生真实的可见变化，不能用静止画面代替。")
    sentences.extend(
        item
        for item in (
            _optional("摄影机运动", camera.movement),
            _optional("摄影机稳定性", camera.stability),
            _optional("构图意图", camera.framing_intent),
            _optional("起始构图", endpoint_intent.start_framing),
            _optional("结束构图", endpoint_intent.end_framing),
        )
        if item is not None
    )
    if endpoint_intent.position_lock and endpoint_intent.orientation_lock:
        sentences.append("摄影机位置和朝向全程锁定。")
    elif endpoint_intent.position_lock:
        sentences.append("摄影机位置全程锁定。")
    elif endpoint_intent.orientation_lock:
        sentences.append("摄影机朝向全程锁定。")
    prompt = unicodedata.normalize("NFC", " ".join(sentences))
    if not prompt or len(prompt) > 5000:
        return ViduPromptUnsupported(unsupported_field_paths=("generation_intent",))
    return ViduPromptCompilation(
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    )


__all__ = [
    "ViduPromptCompilation",
    "ViduPromptResult",
    "ViduPromptUnsupported",
    "compile_vidu_prompt",
]
