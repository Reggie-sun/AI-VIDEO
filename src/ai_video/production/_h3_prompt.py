from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production._video_intent_validation import (
    validate_camera_subject_relation,
    validate_generation_intent_for_continuity,
)
from ai_video.production.models import StrictModel
from ai_video.production.video_requirement import ProviderNeutralVideoRequirement


class _H3PromptModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class H3PromptUnsupported(_H3PromptModel):
    outcome: Literal["unsupported"] = "unsupported"
    unsupported_field_paths: tuple[str, ...] = Field(min_length=1)
    prompt_text: None = None


class H3PromptCompilation(_H3PromptModel):
    outcome: Literal["compiled"] = "compiled"
    prompt_text: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_hash(self) -> "H3PromptCompilation":
        if self.prompt_sha256 != hashlib.sha256(self.prompt_text.encode("utf-8")).hexdigest():
            raise ValueError("prompt_sha256 does not match prompt_text")
        return self


H3PromptResult = H3PromptCompilation | H3PromptUnsupported


_RESERVED_PROMPT_STRUCTURE = re.compile(
    r"\[Shot\s+\d+\]|"
    r"(?:integrated_multimodal_description|overall_soundscape|non_diegetic_music):",
    flags=re.IGNORECASE,
)
_RESERVED_TRANSITION_INSTRUCTION = re.compile(
    r"\b(?:cut|dissolve|flash|transition)\s+"
    r"(?:to|into|from|between|at)\b|"
    r"\b(?:xfade|retime|interpolat(?:e|ion))\b|"
    r"\b\d{1,2}:\d{2}(?:\.\d+)?\s*,?\s*"
    r"(?:cut|dissolve|flash|transition)\b",
    flags=re.IGNORECASE,
)


def _reserved_field_paths(value: object, *, path: str) -> tuple[str, ...]:
    if isinstance(value, str):
        has_line_boundary = value.splitlines() != [value]
        is_dialogue_text = path.endswith("dialogue_intent.verbatim_text")
        return (
            (path,)
            if (
                has_line_boundary
                or _RESERVED_PROMPT_STRUCTURE.search(value)
                or (
                    not is_dialogue_text
                    and _RESERVED_TRANSITION_INSTRUCTION.search(value)
                )
            )
            else ()
        )
    if isinstance(value, dict):
        return tuple(
            field_path
            for key, item in value.items()
            for field_path in _reserved_field_paths(item, path=f"{path}.{key}")
        )
    if isinstance(value, (list, tuple)):
        return tuple(
            field_path
            for index, item in enumerate(value)
            for field_path in _reserved_field_paths(item, path=f"{path}.{index}")
        )
    return ()


def _state_text(state: object) -> str:
    for field in ("state_ref", "state_text", "state_hash"):
        value = getattr(state, field, None)
        if value:
            return str(value)
    return "unspecified"


def compile_h3_prompt(requirement: ProviderNeutralVideoRequirement) -> H3PromptResult:
    intent = requirement.generation_intent
    diagnostics = list(
        validate_generation_intent_for_continuity(intent, audio_need=requirement.audio_need)
    )
    if intent.camera_subject_relation is not None:
        diagnostics.extend(
            validate_camera_subject_relation(intent.camera_subject_relation)
        )
    if requirement.contract_version != "provider-neutral-video-requirement/4":
        diagnostics.append("contract_version")
    if intent.camera_intent.movement != "unspecified":
        diagnostics.append("generation_intent.camera_intent.movement")
    diagnostics.extend(
        _reserved_field_paths(
            intent.model_dump(mode="python"),
            path="generation_intent",
        )
    )
    if (
        _RESERVED_PROMPT_STRUCTURE.search(requirement.target_shot.intent)
        or _RESERVED_TRANSITION_INSTRUCTION.search(requirement.target_shot.intent)
    ):
        diagnostics.append("target_shot.intent")
    if diagnostics:
        return H3PromptUnsupported(
            unsupported_field_paths=tuple(dict.fromkeys(diagnostics))
        )

    performance = intent.performance_intent
    treatment = intent.visual_treatment
    lighting = intent.lighting_intent
    ambience = intent.ambience_intent
    dialogue = intent.dialogue_intent
    music = intent.music_intent
    motion = intent.primary_camera_motion
    relation = intent.camera_subject_relation
    assert all(
        item is not None
        for item in (
            performance,
            treatment,
            lighting,
            ambience,
            dialogue,
            music,
            motion,
            relation,
        )
    )
    assert performance is not None
    assert treatment is not None
    assert lighting is not None
    assert ambience is not None
    assert dialogue is not None
    assert music is not None
    assert motion is not None
    assert relation is not None

    dialogue_text = "none"
    if dialogue.mode == "dialogue":
        assert dialogue.verbatim_text is not None
        dialogue_text = (
            f"speaker {dialogue.speaker_id} says verbatim "
            f"utf8_bytes={len(dialogue.verbatim_text.encode('utf-8'))} "
            f"text={dialogue.verbatim_text} "
            f"from {dialogue.start_seconds:.3f}s to {dialogue.end_seconds:.3f}s; "
            f"on_screen={str(dialogue.on_screen).lower()}; "
            f"response obligation {dialogue.response_obligation}; "
            f"lip_sync_required={str(dialogue.lip_sync_required).lower()}"
        )
    foley = ", ".join(ambience.foley_cues) if ambience.foley_cues else "none"
    music_text = "none"
    if music.mode == "music":
        music_text = (
            f"{music.instrumentation}; {music.tempo_rhythm}; {music.dynamics}"
        )
    camera_motion_text = (
        "locked-off camera"
        if motion.movement_kind.value == "locked"
        else (
            f"{motion.movement_kind.value.replace('_', ' ')} "
            f"with {motion.amplitude_class.value} amplitude "
            f"at {motion.speed_class.value.replace('_', ' ')} speed "
            f"toward {motion.direction}"
        )
    )
    visual = (
        "[Shot 1] "
        f"scene {requirement.scene.scene_id}; open state {_state_text(intent.open_state)}; "
        f"action {intent.subject_action.start_state} -> {intent.subject_action.progression} "
        f"-> {_state_text(intent.subject_action.endpoint)}; "
        f"close state {_state_text(intent.close_state)}; "
        f"performance trigger {performance.trigger}; "
        f"visible response {performance.visible_response}; "
        f"gaze {performance.gaze_target}; body {performance.body_behavior}; "
        f"hands {performance.hand_behavior}; "
        f"terminal performance {performance.terminal_performance_state}; "
        f"visual treatment {treatment.medium_look}; palette {treatment.palette}; "
        f"materials {treatment.material_treatment}; "
        f"prohibit {', '.join(treatment.prohibited_visual_drift)}; "
        f"lighting from {lighting.motivated_source}, {lighting.direction}, "
        f"exposure priority {lighting.exposure_priority}, "
        f"continuity {lighting.continuity_state}; "
        f"screen direction {intent.space_continuity.screen_direction}; "
        f"camera axis {intent.axis_continuity.camera_axis}; "
        f"start framing {intent.camera_endpoint.start_framing}; "
        f"{camera_motion_text}; "
        f"maintain {relation.relation_kind.value.replace('_', ' ')} "
        f"to subject {relation.subject_id} "
        f"from {relation.start_relation} to {relation.end_relation}; "
        f"end framing {intent.camera_endpoint.end_framing}; "
        f"terminal motion state {motion.end_motion_state.value}"
    )
    prompt = unicodedata.normalize(
        "NFC",
        "\n".join(
            (
                f"integrated_multimodal_description: {visual}",
                f"overall_soundscape: ambience {ambience.environment_bed}; "
                f"foley {foley}; dialogue {dialogue_text}",
                f"non_diegetic_music: {music_text}",
            )
        ),
    )
    if (
        prompt.count("[Shot 1]") != 1
        or prompt.count("integrated_multimodal_description:") != 1
        or prompt.count("overall_soundscape:") != 1
        or prompt.count("non_diegetic_music:") != 1
    ):
        return H3PromptUnsupported(
            unsupported_field_paths=("generation_intent",)
        )
    return H3PromptCompilation(
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    )


__all__ = [
    "H3PromptCompilation",
    "H3PromptResult",
    "H3PromptUnsupported",
    "compile_h3_prompt",
]
