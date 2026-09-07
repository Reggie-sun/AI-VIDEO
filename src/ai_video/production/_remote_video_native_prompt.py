"""Deterministic native prose for sealed remote video recipes.

This grammar is deliberately shared only by the remote adapters that expose
the same prompt surface.  It renders every supported authored control as
provider-facing prose and refuses incomplete or unversioned intent instead of
letting a recipe fall back to the legacy neutral prompt.
"""

from __future__ import annotations

import hashlib
import unicodedata
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.production._video_intent_validation import (
    validate_camera_subject_relation,
    validate_generation_intent_for_continuity,
)
from ai_video.production.models import StrictModel
from ai_video.production.video_requirement import (
    ContinuityStateKind,
    ProviderNeutralVideoRequirement,
)


class _RemotePromptModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class RemoteVideoPromptUnsupported(_RemotePromptModel):
    outcome: Literal["unsupported"] = "unsupported"
    unsupported_field_paths: tuple[str, ...] = Field(min_length=1)
    prompt_text: None = None


class RemoteVideoPromptCompilation(_RemotePromptModel):
    outcome: Literal["compiled"] = "compiled"
    prompt_text: str = Field(min_length=1)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expressed_control_paths: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _validate_hash(self) -> "RemoteVideoPromptCompilation":
        if self.prompt_sha256 != hashlib.sha256(
            self.prompt_text.encode("utf-8")
        ).hexdigest():
            raise ValueError("prompt_sha256 does not match prompt_text")
        return self


RemoteVideoPromptResult = RemoteVideoPromptCompilation | RemoteVideoPromptUnsupported

_DIALOGUE_LANGUAGE_NAMES = {
    "en": "English",
    "zh": "Chinese",
}


def _state_text(state: object, path: str) -> tuple[str | None, tuple[str, ...]]:
    kind = getattr(state, "kind", None)
    if kind is ContinuityStateKind.UNSPECIFIED:
        return (None, (path,)) if getattr(state, "required_change", False) else (None, ())
    text = getattr(state, "state_text", None)
    if kind is ContinuityStateKind.TYPED_TEXT and isinstance(text, str) and text:
        return text, ()
    return None, (path,)


def _endpoint_text(endpoint: object) -> tuple[str | None, tuple[str, ...]]:
    text = getattr(endpoint, "state_text", None)
    if isinstance(text, str) and text:
        return text, ()
    return None, ("generation_intent.subject_action.endpoint",)


def _append(sentences: list[str], sentence: str | None) -> None:
    if sentence:
        sentences.append(sentence)


def _optional(label: str, value: str | None) -> str | None:
    if value is None or value == "unspecified":
        return None
    return f"{label}: {value}."


def compile_remote_video_prompt(
    requirement: ProviderNeutralVideoRequirement,
) -> RemoteVideoPromptResult:
    """Compile the current complete intent into remote-provider prose.

    The grammar treats provider-specific request payload controls separately;
    this function owns only the native textual expression used by a recipe.
    """

    intent = requirement.generation_intent
    diagnostics = list(
        validate_generation_intent_for_continuity(
            intent, audio_need=requirement.audio_need
        )
    )
    if requirement.contract_version != "provider-neutral-video-requirement/4":
        diagnostics.append("contract_version")
    if intent.camera_subject_relation is not None:
        diagnostics.extend(validate_camera_subject_relation(intent.camera_subject_relation))
    if intent.camera_intent.expression_strength.value != "semantic_prompt_allowed":
        diagnostics.append("generation_intent.camera_intent.expression_strength")
    if diagnostics:
        return RemoteVideoPromptUnsupported(
            unsupported_field_paths=tuple(dict.fromkeys(diagnostics))
        )

    opening, opening_errors = _state_text(
        intent.open_state, "generation_intent.open_state"
    )
    closing, closing_errors = _state_text(
        intent.close_state, "generation_intent.close_state"
    )
    endpoint, endpoint_errors = _endpoint_text(intent.subject_action.endpoint)
    if opening_errors or closing_errors or endpoint_errors:
        return RemoteVideoPromptUnsupported(
            unsupported_field_paths=tuple(
                dict.fromkeys((*opening_errors, *closing_errors, *endpoint_errors))
            )
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
        for item in (performance, treatment, lighting, ambience, dialogue, music, motion, relation)
    )
    assert performance is not None and treatment is not None and lighting is not None
    assert ambience is not None and dialogue is not None and music is not None
    assert motion is not None and relation is not None

    sentences: list[str] = []
    controls: list[str] = []
    _append(sentences, f"Opening state: {opening}.")
    if intent.open_state.required_change:
        sentences.append("The opening state must visibly change during this shot.")
        controls.append("generation_intent.open_state.required_change")
    _append(sentences, f"Closing state: {closing}.")
    if intent.close_state.required_change:
        sentences.append("The closing state must be visibly reached during this shot.")
        controls.append("generation_intent.close_state.required_change")

    identity = intent.identity_continuity
    if identity.preservation.value == "exact":
        sentences.append("Keep the visible character identity exactly consistent.")
        controls.append("generation_intent.identity_continuity.preservation")
    elif identity.preservation.value == "bounded_variation":
        sentences.append("Keep identity consistent; allowed variation: " + ", ".join(identity.allowed_variation) + ".")
        controls.append("generation_intent.identity_continuity.preservation")

    scene = intent.scene_continuity
    if scene is not None:
        _append(sentences, _optional("Time of day", scene.time_of_day))
        _append(sentences, _optional("Scene mood", scene.mood))
        for constraint in scene.state_constraints:
            sentences.append(f"Scene constraint: {constraint}.")
    space = intent.space_continuity
    _append(sentences, _optional("Subject position", space.subject_position))
    _append(sentences, _optional("Screen direction", space.screen_direction))
    _append(sentences, _optional("Entrance state", space.entrance_state))
    _append(sentences, _optional("Exit state", space.exit_state))
    _append(sentences, _optional("Spatial crossing policy", space.crossing_policy))
    axis = intent.axis_continuity
    _append(sentences, _optional("Camera axis", axis.camera_axis))
    _append(sentences, _optional("Framing continuity", axis.framing_continuity))
    _append(sentences, _optional("Axis crossing policy", axis.crossing_policy))

    action = intent.subject_action
    _append(sentences, _optional("Action start", action.start_state))
    _append(sentences, _optional("Action progression", action.progression))
    _append(sentences, f"Action endpoint: {endpoint}.")
    if action.endpoint.required_change:
        sentences.append("The action must produce a visible state change.")
        controls.append("generation_intent.subject_action.endpoint.required_change")
    envelope = intent.motion_envelope
    _append(sentences, _optional("Motion onset", envelope.onset))
    _append(sentences, _optional("Motion peak", envelope.peak))
    _append(sentences, _optional("Motion settle", envelope.settle))
    _append(sentences, _optional("Motion direction", envelope.direction))
    _append(sentences, _optional("Motion amplitude", envelope.amplitude_class))
    pacing = intent.pacing
    _append(sentences, _optional("Pacing cadence", pacing.cadence))
    _append(sentences, _optional("Pacing tempo", pacing.tempo_class))
    assert pacing.shot_duration_seconds is not None
    sentences.append(f"Shot duration: {pacing.shot_duration_seconds:g} seconds.")
    controls.append("generation_intent.pacing.shot_duration_seconds")

    camera = intent.camera_intent
    _append(sentences, _optional("Camera movement", camera.movement))
    _append(sentences, _optional("Camera stability", camera.stability))
    _append(sentences, _optional("Camera framing intent", camera.framing_intent))
    camera_endpoint = intent.camera_endpoint
    _append(sentences, _optional("Camera start framing", camera_endpoint.start_framing))
    _append(sentences, _optional("Camera end framing", camera_endpoint.end_framing))
    if camera_endpoint.position_lock:
        sentences.append("Keep the camera position locked throughout the shot.")
        controls.append("generation_intent.camera_endpoint.position_lock")
    if camera_endpoint.orientation_lock:
        sentences.append("Keep the camera orientation locked throughout the shot.")
        controls.append("generation_intent.camera_endpoint.orientation_lock")

    sentences.extend(
        (
            f"Performance trigger: {performance.trigger}.",
            f"Visible response: {performance.visible_response}.",
            f"Gaze target: {performance.gaze_target}.",
            f"Body behavior: {performance.body_behavior}.",
            f"Hand behavior: {performance.hand_behavior}.",
            f"Terminal performance state: {performance.terminal_performance_state}.",
            f"Visual medium: {treatment.medium_look}.",
            f"Visual palette: {treatment.palette}.",
            f"Material treatment: {treatment.material_treatment}.",
            "Prohibit visual drift: " + ", ".join(treatment.prohibited_visual_drift) + ".",
            f"Lighting source: {lighting.motivated_source}.",
            f"Lighting direction: {lighting.direction}.",
            f"Lighting exposure priority: {lighting.exposure_priority}.",
            f"Lighting continuity: {lighting.continuity_state}.",
        )
    )
    if ambience.explicitly_silent:
        sentences.append("Use no ambience or foley.")
        controls.append("generation_intent.ambience_intent.explicitly_silent")
    else:
        sentences.append("Ambient sound is enabled.")
        controls.append("generation_intent.ambience_intent.explicitly_silent")
        sentences.append(f"Ambience bed: {ambience.environment_bed}.")
        for cue in ambience.foley_cues:
            sentences.append(f"Foley cue: {cue}.")

    if dialogue.mode == "dialogue":
        assert dialogue.language is not None
        language = _DIALOGUE_LANGUAGE_NAMES.get(dialogue.language.split("-", 1)[0])
        if language is None:
            return RemoteVideoPromptUnsupported(
                unsupported_field_paths=("generation_intent.dialogue_intent.language",)
            )
        assert dialogue.verbatim_text is not None
        assert dialogue.start_seconds is not None and dialogue.end_seconds is not None
        assert dialogue.on_screen is not None
        assert dialogue.response_obligation is not None
        sentences.extend(
            (
                f"Dialogue language: {language}.",
                f"Spoken dialogue, exactly once: {dialogue.verbatim_text}.",
                f"Dialogue timing: from {dialogue.start_seconds:g} seconds to {dialogue.end_seconds:g} seconds.",
                f"Dialogue response: {dialogue.response_obligation}.",
                "Dialogue is on-screen." if dialogue.on_screen else "Dialogue is off-screen.",
                "Lip synchronization is required."
                if dialogue.lip_sync_required
                else "Lip synchronization is not required.",
            )
        )
        controls.extend(
            (
                "generation_intent.dialogue_intent.start_seconds",
                "generation_intent.dialogue_intent.end_seconds",
                "generation_intent.dialogue_intent.on_screen",
                "generation_intent.dialogue_intent.lip_sync_required",
            )
        )
    else:
        sentences.extend(("Dialogue: none.", "Lip synchronization is not required."))
        controls.append("generation_intent.dialogue_intent.lip_sync_required")
    if music.mode == "none":
        sentences.append("Music: none.")
    else:
        assert music.instrumentation is not None
        assert music.tempo_rhythm is not None and music.dynamics is not None
        sentences.extend(
            (
                f"Music instrumentation: {music.instrumentation}.",
                f"Music tempo and rhythm: {music.tempo_rhythm}.",
                f"Music dynamics: {music.dynamics}.",
            )
        )
    sentences.extend(
        (
            f"Primary camera movement: {motion.movement_kind.value.replace('_', ' ')}.",
            f"Primary camera direction: {motion.direction}.",
            f"Primary camera amplitude: {motion.amplitude_class.value}.",
            f"Primary camera speed: {motion.speed_class.value.replace('_', ' ')}.",
            f"Primary camera starts {motion.start_motion_state.value.replace('_', ' ')}.",
            f"Primary camera ends {motion.end_motion_state.value.replace('_', ' ')}.",
            f"Camera relation: {relation.relation_kind.value.replace('_', ' ')}.",
            f"Camera relation starts: {relation.start_relation}.",
            f"Camera relation ends: {relation.end_relation}.",
        )
    )
    controls.extend(
        (
            "generation_intent.primary_camera_motion.movement_kind",
            "generation_intent.primary_camera_motion.amplitude_class",
            "generation_intent.primary_camera_motion.speed_class",
            "generation_intent.primary_camera_motion.start_motion_state",
            "generation_intent.primary_camera_motion.end_motion_state",
            "generation_intent.camera_subject_relation.relation_kind",
        )
    )
    prompt = unicodedata.normalize("NFC", " ".join(sentences))
    if not prompt or len(prompt) > 5_000:
        return RemoteVideoPromptUnsupported(
            unsupported_field_paths=("generation_intent",)
        )
    return RemoteVideoPromptCompilation(
        prompt_text=prompt,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        expressed_control_paths=tuple(sorted(set(controls))),
    )


__all__ = [
    "RemoteVideoPromptCompilation",
    "RemoteVideoPromptResult",
    "RemoteVideoPromptUnsupported",
    "compile_remote_video_prompt",
]
