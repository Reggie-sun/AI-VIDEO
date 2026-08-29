from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production._video_intent_validation import (
    validate_camera_subject_relation,
    validate_generation_intent_for_continuity,
)
from ai_video.production.models import StrictModel
from ai_video.production.video_requirement import (
    ContinuityMode,
    GenerationIntent,
    GenerationMode,
    ProviderNeutralVideoRequirement,
)


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
_RESERVED_H3_DIALOGUE_TAG = re.compile(r"</?d(?:\s[^>]*)?>", flags=re.IGNORECASE)


def _reserved_field_paths(
    value: object,
    *,
    path: str,
    reject_h3_dialogue_tags: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, str):
        has_line_boundary = value.splitlines() != [value]
        is_dialogue_text = path.endswith("dialogue_intent.verbatim_text")
        return (
            (path,)
            if (
                has_line_boundary
                or _RESERVED_PROMPT_STRUCTURE.search(value)
                or (
                    reject_h3_dialogue_tags
                    and _RESERVED_H3_DIALOGUE_TAG.search(value)
                )
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
            for field_path in _reserved_field_paths(
                item,
                path=f"{path}.{key}",
                reject_h3_dialogue_tags=reject_h3_dialogue_tags,
            )
        )
    if isinstance(value, (list, tuple)):
        return tuple(
            field_path
            for index, item in enumerate(value)
            for field_path in _reserved_field_paths(
                item,
                path=f"{path}.{index}",
                reject_h3_dialogue_tags=reject_h3_dialogue_tags,
            )
        )
    return ()


def _state_text(state: object) -> str:
    for field in ("state_ref", "state_text", "state_hash"):
        value = getattr(state, field, None)
        if value:
            return str(value)
    return "unspecified"


def _readable_structured_text(value: str) -> str:
    stripped = value.strip()
    if not stripped.startswith(("{", "[")):
        return value
    try:
        parsed = json.loads(stripped)
    except (TypeError, ValueError):
        return value

    def render(item: object) -> str:
        if isinstance(item, dict):
            return "; ".join(
                f"{str(key).replace('_', ' ')}: {render(item[key])}"
                for key in sorted(item)
            )
        if isinstance(item, list):
            return ", ".join(render(entry) for entry in item)
        if item is None:
            return "none"
        if isinstance(item, bool):
            return str(item).lower()
        return str(item)

    return render(parsed)


def _identity_scene_prompt_text(intent: GenerationIntent) -> str:
    identity = intent.identity_continuity
    identity_characters = ", ".join(identity.character_ids) or "none"
    identity_variation = ", ".join(identity.allowed_variation) or "none"
    scene = intent.scene_continuity
    scene_text = "scene continuity none"
    if scene is not None:
        scene_constraints = " / ".join(
            _readable_structured_text(item) for item in scene.state_constraints
        ) or "none"
        scene_text = (
            f"scene continuity {scene.scene_id}; "
            f"time of day {_readable_structured_text(scene.time_of_day or 'unspecified')}; "
            f"mood {_readable_structured_text(scene.mood or 'unspecified')}; "
            f"constraints {scene_constraints}"
        )
    return (
        f"identity preservation {identity.preservation.value}; "
        f"identity characters {identity_characters}; "
        f"allowed identity variation {identity_variation}; "
        f"{scene_text}"
    )


def compile_h3_prompt(requirement: ProviderNeutralVideoRequirement) -> H3PromptResult:
    if (
        requirement.contract_version == "provider-neutral-video-requirement/1"
        and requirement.generation_mode is GenerationMode.TEXT_TO_VIDEO
        and requirement.continuity_mode is ContinuityMode.NONE
    ):
        return _compile_h3_t2va_prompt(requirement)

    intent = requirement.generation_intent
    t2v_context = (
        _identity_scene_prompt_text(intent)
        if requirement.generation_mode is GenerationMode.TEXT_TO_VIDEO
        else ""
    )
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
    if t2v_context:
        diagnostics.extend(
            _reserved_field_paths(
                t2v_context,
                path="generation_intent.scene_continuity.rendered",
                reject_h3_dialogue_tags=True,
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
        f"{t2v_context + '; ' if t2v_context else ''}"
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
        len(prompt.splitlines()) != 3
        or prompt.count("[Shot 1]") != 1
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


def _compile_h3_t2va_prompt(
    requirement: ProviderNeutralVideoRequirement,
) -> H3PromptResult:
    """Compile the legacy T2V intent into H3's native three-field grammar.

    The local T8 T2VA lanes have no image-conditioning surface, so they cannot
    use the conditioning-bound v4 compiler.  This compiler emits only authored
    visible action, identity, readable scene continuity, camera, lighting,
    ambience, and exact dialogue without exposing raw structured JSON.
    """

    intent = requirement.generation_intent
    performance = intent.performance_intent
    treatment = intent.visual_treatment
    lighting = intent.lighting_intent
    ambience = intent.ambience_intent
    dialogue = intent.dialogue_intent
    music = intent.music_intent
    endpoint = intent.camera_endpoint
    diagnostics = list(
        validate_generation_intent_for_continuity(
            intent,
            audio_need=requirement.audio_need,
        )
    )
    legacy_absent_fields = {
        "generation_intent.primary_camera_motion",
        "generation_intent.camera_subject_relation",
    }
    diagnostics = [
        path for path in diagnostics if path not in legacy_absent_fields
    ]
    if requirement.contract_version != "provider-neutral-video-requirement/1":
        diagnostics.append("contract_version")
    if requirement.generation_mode is not GenerationMode.TEXT_TO_VIDEO:
        diagnostics.append("generation_mode")
    if requirement.continuity_mode is not ContinuityMode.NONE:
        diagnostics.append("continuity_mode")
    if requirement.semantic_reference_roles:
        diagnostics.append("semantic_reference_roles")
    if requirement.asset_evidence:
        diagnostics.append("asset_evidence")
    if intent.camera_intent.movement not in {"locked", "unspecified"}:
        diagnostics.append("generation_intent.camera_intent.movement")
    emitted_values = {
        "target_shot.intent": requirement.target_shot.intent,
        "generation_intent.open_state": _state_text(intent.open_state),
        "generation_intent.close_state": _state_text(intent.close_state),
        "generation_intent.identity_continuity": (
            intent.identity_continuity.model_dump(mode="python")
        ),
        "generation_intent.scene_continuity": (
            intent.scene_continuity.model_dump(mode="python")
            if intent.scene_continuity is not None
            else None
        ),
        "generation_intent.scene_continuity.rendered": (
            _identity_scene_prompt_text(intent)
        ),
        "generation_intent.camera_intent": intent.camera_intent.model_dump(mode="python"),
        "generation_intent.camera_endpoint": endpoint.model_dump(mode="python"),
        "generation_intent.subject_action": intent.subject_action.model_dump(
            mode="python"
        ),
        "generation_intent.motion_envelope": intent.motion_envelope.model_dump(
            mode="python"
        ),
        "generation_intent.pacing": intent.pacing.model_dump(mode="python"),
        "generation_intent.space_continuity": intent.space_continuity.model_dump(
            mode="python"
        ),
        "generation_intent.axis_continuity": intent.axis_continuity.model_dump(
            mode="python"
        ),
        "generation_intent.performance_intent": (
            performance.model_dump(mode="python") if performance is not None else None
        ),
        "generation_intent.visual_treatment": (
            treatment.model_dump(mode="python") if treatment is not None else None
        ),
        "generation_intent.lighting_intent": (
            lighting.model_dump(mode="python") if lighting is not None else None
        ),
        "generation_intent.ambience_intent": (
            ambience.model_dump(mode="python") if ambience is not None else None
        ),
        "generation_intent.dialogue_intent": (
            dialogue.model_dump(mode="python") if dialogue is not None else None
        ),
        "generation_intent.music_intent": (
            music.model_dump(mode="python") if music is not None else None
        ),
    }
    diagnostics.extend(
        field_path
        for path, value in emitted_values.items()
        for field_path in _reserved_field_paths(
            value,
            path=path,
            reject_h3_dialogue_tags=True,
        )
    )
    if diagnostics:
        return H3PromptUnsupported(
            unsupported_field_paths=tuple(dict.fromkeys(diagnostics))
        )

    assert performance is not None
    assert treatment is not None
    assert lighting is not None
    assert ambience is not None
    assert dialogue is not None
    assert music is not None
    camera = intent.camera_intent
    camera_text = (
        "locked-off camera"
        if camera.movement == "locked"
        else f"{camera.movement.replace('_', ' ')} camera"
    )
    prohibited = ", ".join(treatment.prohibited_visual_drift) or "none"
    identity_scene_text = _identity_scene_prompt_text(intent)
    visual = (
        f"[Shot 1] {treatment.medium_look}; scene {requirement.scene.scene_id}; "
        f"shot intent {requirement.target_shot.intent}; "
        f"{identity_scene_text}; "
        f"open state {intent.open_state.kind.value} "
        f"{_state_text(intent.open_state)}; "
        f"open state change required {str(intent.open_state.required_change).lower()}; "
        f"action {intent.subject_action.start_state} -> "
        f"{intent.subject_action.progression} -> "
        f"{_state_text(intent.subject_action.endpoint)}; "
        f"action endpoint change required "
        f"{str(intent.subject_action.endpoint.required_change).lower()}; "
        f"close state {intent.close_state.kind.value} "
        f"{_state_text(intent.close_state)}; "
        f"close state change required {str(intent.close_state.required_change).lower()}; "
        f"performance trigger {performance.trigger}; "
        f"visible response {performance.visible_response}; "
        f"gaze {performance.gaze_target}; body {performance.body_behavior}; "
        f"hands {performance.hand_behavior}; "
        f"terminal performance {performance.terminal_performance_state}; "
        f"palette {treatment.palette}; materials {treatment.material_treatment}; "
        f"lighting from {lighting.motivated_source}, {lighting.direction}; "
        f"exposure priority {lighting.exposure_priority}; "
        f"lighting continuity {lighting.continuity_state}; "
        f"subject positions {intent.space_continuity.subject_position}; "
        f"screen direction {intent.space_continuity.screen_direction}; "
        f"entrance {intent.space_continuity.entrance_state or 'none'}; "
        f"exit {intent.space_continuity.exit_state or 'none'}; "
        f"space crossing policy {intent.space_continuity.crossing_policy}; "
        f"camera axis {intent.axis_continuity.camera_axis}; "
        f"framing continuity {intent.axis_continuity.framing_continuity}; "
        f"axis crossing policy {intent.axis_continuity.crossing_policy}; "
        f"camera framing intent {camera.framing_intent}; "
        f"start framing {endpoint.start_framing}; {camera_text}; "
        f"camera stability {camera.stability}; "
        f"position lock {str(endpoint.position_lock).lower()}; "
        f"orientation lock {str(endpoint.orientation_lock).lower()}; "
        f"end framing {endpoint.end_framing}; "
        f"motion {intent.motion_envelope.onset} -> {intent.motion_envelope.peak} "
        f"-> {intent.motion_envelope.settle}; "
        f"motion direction {intent.motion_envelope.direction}; "
        f"motion amplitude {intent.motion_envelope.amplitude_class}; "
        f"pacing {intent.pacing.cadence}; tempo {intent.pacing.tempo_class}; "
        f"duration {intent.pacing.shot_duration_seconds:.3f}s; "
        f"prohibit {prohibited}; no visible text, captions, or subtitles"
    )
    foley = ", ".join(ambience.foley_cues) if ambience.foley_cues else "none"
    if dialogue.mode == "dialogue":
        assert dialogue.verbatim_text is not None
        language = (
            "Chinese"
            if any("\u4e00" <= character <= "\u9fff" for character in dialogue.verbatim_text)
            else "English"
        )
        dialogue_text = (
            f"speaker {dialogue.speaker_id} says once "
            f"<d>[{language}]{dialogue.verbatim_text}</d> "
            f"from {dialogue.start_seconds:.3f}s to {dialogue.end_seconds:.3f}s; "
            f"on_screen={str(dialogue.on_screen).lower()}; "
            f"response obligation {dialogue.response_obligation}; "
            f"lip_sync_required={str(dialogue.lip_sync_required).lower()}; "
            "no narration and no extra speech"
        )
    else:
        dialogue_text = "no speech, no dialogue, no narration, and no voices"
    music_text = "none"
    if music.mode == "music":
        music_text = f"{music.instrumentation}; {music.tempo_rhythm}; {music.dynamics}"
    prompt = unicodedata.normalize(
        "NFC",
        "\n".join(
            (
                f"integrated_multimodal_description: {visual}",
                f"overall_soundscape: ambience {ambience.environment_bed}; "
                f"explicitly silent {str(ambience.explicitly_silent).lower()}; "
                f"foley {foley}; {dialogue_text}",
                f"non_diegetic_music: {music_text}",
            )
        ),
    )
    if (
        len(prompt.splitlines()) != 3
        or prompt.count("[Shot 1]") != 1
        or prompt.count("integrated_multimodal_description:") != 1
        or prompt.count("overall_soundscape:") != 1
        or prompt.count("non_diegetic_music:") != 1
    ):
        return H3PromptUnsupported(unsupported_field_paths=("generation_intent",))
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
