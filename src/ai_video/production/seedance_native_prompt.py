"""Exact authored Seedance prose pinned to one provider-bound recipe.

The caller supplies already-approved source prose. This binding does not infer
approval, repair text, suppress recipe coverage checks, or change references.
"""
from __future__ import annotations

import hashlib
from pydantic import Field, model_validator

from ai_video.production.models import StrictModel
from ai_video.production.video_compiler import ProviderNativePrompt


def compile_seedance_request(provider_bound, requirement, *, capabilities, binding=None,
                             continuity_expression=None):
    """Pure adapter compilation; transport and lifecycle stay with their owners."""
    from ai_video.production._remote_video_native_prompt import (
        RemoteVideoPromptCompilation, compile_remote_video_prompt,
    )
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason, compile_provider_video_request,
    )

    native_prompt = None
    compiler_version = "1"
    if binding is not None and binding.source_preservation and provider_bound.generation_recipe is None:
        raise ValueError("Seedance source preservation requires a sealed recipe")
    if provider_bound.generation_recipe is not None:
        compiler_version = "2"
        if binding is not None and binding.source_preservation:
            native_prompt = binding.compile_source(provider_bound, requirement)
        else:
            compiled = compile_remote_video_prompt(requirement, voice_route=provider_bound.voice_route,
                provider_bound=provider_bound, continuity_expression=continuity_expression)
            if not isinstance(compiled, RemoteVideoPromptCompilation):
                return ProviderRequirementUnsupported(requirement_hash=requirement.requirement_hash,
                    provider_bound_request_hash=provider_bound.provider_bound_request_hash,
                    selected_capability_id=provider_bound.capability_id,
                    reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
                    unsupported_field_paths=compiled.unsupported_field_paths)
            native_prompt = ProviderNativePrompt(grammar_contract="remote-video-prose-v1",
                prompt_text=compiled.prompt_text, prompt_sha256=compiled.prompt_sha256,
                expressed_control_paths=compiled.expressed_control_paths)
            if binding is not None:
                native_prompt = binding.compile(provider_bound, compiled.expressed_control_paths,
                    requirement=requirement)
    return compile_provider_video_request(provider_bound=provider_bound, requirement=requirement,
        compiler_id="seedance-video-compiler", compiler_version=compiler_version,
        capabilities=capabilities, native_prompt=native_prompt, continuity_expression=continuity_expression)


class SeedanceNativePromptBinding(StrictModel):
    provider_bound_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    # Local bounded authoring guard, not a claim about the Provider text limit.
    prompt_text: str = Field(min_length=1, max_length=65536)
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_preservation: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def _exact_text(self):
        if hashlib.sha256(self.prompt_text.encode()).hexdigest() != self.prompt_sha256:
            raise ValueError("Seedance authored prompt seal does not match")
        if self.source_preservation and self.source_evidence_sha256 != self.prompt_sha256:
            raise ValueError("Seedance preserved source evidence must match the original text")
        return self

    def compile_source(self, provider_bound, requirement):
        """Express an approved standalone source without inventing rich controls.

        The common compiler still checks every non-default authored value and
        recipe requirement. Unknown rich intent stays absent, not attested.
        """
        if not self.source_preservation:
            raise ValueError("Seedance source compilation requires explicit preservation")
        self._exact_text()
        if self.prompt_text != requirement.target_shot.intent:
            raise ValueError("Seedance preserved text must equal the approved Shot intent")
        if (requirement.contract_version == "provider-neutral-video-requirement/4"
                or requirement.generation_mode.value not in {"text_to_video", "reference_to_video", "image_to_video"}
                or requirement.voice_routing is not None
                or provider_bound.voice_route is not None
                or requirement.conditioning_compatibility is not None):
            raise ValueError("Seedance source compilation cannot replace rich or conditioned intent")
        if requirement.generation_mode.value == "image_to_video":
            if (tuple(role.value for role in requirement.semantic_reference_roles) != ("first_frame",)
                    or len(requirement.asset_evidence) != 1
                    or requirement.asset_evidence[0].role.value != "first_frame"):
                raise ValueError("Seedance source I2V requires exactly one single first frame")
        intent = requirement.generation_intent
        if intent.subject_action.progression != self.prompt_text:
            raise ValueError("Seedance preserved progression must equal the approved Shot intent")
        duration = intent.pacing.shot_duration_seconds
        output_duration = provider_bound.output_requirement.duration_seconds
        if duration is None or output_duration is None or abs(duration - output_duration) > 1e-6:
            raise ValueError("Seedance source duration must match the bound output")
        controls = ["generation_intent.pacing.shot_duration_seconds"]
        for path, state in (("open_state", intent.open_state), ("close_state", intent.close_state),
                            ("subject_action.endpoint", intent.subject_action.endpoint)):
            if state.state_ref is not None or state.state_hash is not None:
                raise ValueError("Seedance source compilation cannot replace continuity evidence")
            if state.required_change:
                if not state.state_text or state.state_text not in self.prompt_text:
                    raise ValueError("Seedance source state change needs its original text")
                controls.append(f"generation_intent.{path}.required_change")
        ambience = intent.ambience_intent
        if ambience is not None and not ambience.explicitly_silent:
            if not provider_bound.output_requirement.native_audio:
                raise ValueError("Seedance source sound needs native audio output")
            controls.append("generation_intent.ambience_intent.explicitly_silent")
        if intent.dialogue_intent is not None and intent.dialogue_intent.mode == "none":
            controls.append("generation_intent.dialogue_intent.lip_sync_required")
        return self.compile(provider_bound, tuple(controls), requirement=requirement)

    def compile(self, provider_bound, mechanically_expressed_controls, *, requirement=None):
        if provider_bound.provider_bound_request_hash != self.provider_bound_request_hash:
            raise ValueError("Seedance authored prompt targets another provider-bound recipe")
        controls = mechanically_expressed_controls
        if requirement is not None:
            dialogue = requirement.generation_intent.dialogue_intent
            # Verbatim Chinese dialogue already expresses the language; do not
            # append an English language label to an exact authored prompt.
            if (dialogue is not None and dialogue.mode == "dialogue" and dialogue.language in {"zh", "zh-CN"}
                    and dialogue.verbatim_text and dialogue.verbatim_text in self.prompt_text
                    and any("\u4e00" <= char <= "\u9fff" for char in dialogue.verbatim_text)):
                controls = (*controls, "generation_intent.dialogue_intent.language",
                            "generation_intent.dialogue_intent.mode")
            motion = requirement.generation_intent.primary_camera_motion
            if (motion is not None and motion.movement_kind == "dolly_in"
                    and motion.direction == "forward" and "推近" in self.prompt_text):
                controls = (*controls, "generation_intent.primary_camera_motion.direction")
            if (motion is not None and motion.movement_kind == "orbit_left"
                    and motion.direction == "left" and "同一条逆时针弧线移动" in self.prompt_text):
                controls = (*controls, "generation_intent.primary_camera_motion.direction")
        return ProviderNativePrompt(
            grammar_contract="remote-video-prose-v1", prompt_text=self.prompt_text,
            prompt_sha256=self.prompt_sha256,
            expressed_control_paths=controls,
        )
