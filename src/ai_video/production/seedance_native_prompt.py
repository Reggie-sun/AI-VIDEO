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
    if requirement.target_shot.preserved_source_expression is not None:
        from ai_video.production.seedance_source_expression import compile_preserved_seedance_source

        native_prompt = compile_preserved_seedance_source(provider_bound, requirement,
            continuity_expression=continuity_expression)
        if binding is not None:
            binding._exact_text()
            if (not binding.source_preservation or binding.provider_bound_request_hash
                    != provider_bound.provider_bound_request_hash
                    or binding.prompt_text != native_prompt.prompt_text):
                raise ValueError("Seedance binding differs from its approved preserved source")
        return compile_provider_video_request(provider_bound=provider_bound, requirement=requirement,
            compiler_id="seedance-video-compiler", compiler_version="3", capabilities=capabilities,
            native_prompt=native_prompt, continuity_expression=continuity_expression)
    if provider_bound.compiler_contract.compiler_version == "4":
        if binding is None or binding.source_preservation or provider_bound.generation_recipe is None:
            return _expression_unsupported(provider_bound, requirement, ("native_prompt_binding",))
        native_prompt, issues = _authored_final_prompt(binding, provider_bound, requirement,
            continuity_expression=continuity_expression)
        if issues:
            return _expression_unsupported(provider_bound, requirement, issues, binding=binding)
        result = compile_provider_video_request(provider_bound=provider_bound, requirement=requirement,
            compiler_id="seedance-video-compiler", compiler_version="4", capabilities=capabilities,
            native_prompt=native_prompt, continuity_expression=continuity_expression)
        if isinstance(result, ProviderRequirementUnsupported):
            return result.model_copy(update={"input_expression_report": _input_expression_report(
                binding, result.unsupported_field_paths)})
        return result
    if binding is not None and binding.source_preservation and provider_bound.generation_recipe is None:
        raise ValueError("Seedance source preservation requires a sealed recipe")
    if provider_bound.generation_recipe is not None:
        compiler_version = "2"
        if binding is not None and binding.source_preservation:
            native_prompt = binding.compile_source(provider_bound, requirement)
        else:
            compiled = compile_remote_video_prompt(requirement, voice_route=provider_bound.voice_route,
                provider_bound=provider_bound, continuity_expression=continuity_expression,
                max_prompt_characters=None)
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


def _input_expression_report(binding, paths):
    from ai_video.production.generation_input_control import NativeTextExpressionReport
    if not isinstance(binding.prompt_text, str):
        return None
    return NativeTextExpressionReport(prompt_text=binding.prompt_text,
        prompt_sha256=hashlib.sha256(binding.prompt_text.encode()).hexdigest(),
        missing_requirement_paths=tuple(sorted(set(paths))))


def _expression_unsupported(bound, requirement, paths, *, binding=None):
    from ai_video.production.video_compiler import (
        ProviderRequirementUnsupported, ProviderRequirementUnsupportedReason,
    )
    return ProviderRequirementUnsupported(requirement_hash=requirement.requirement_hash,
        provider_bound_request_hash=bound.provider_bound_request_hash,
        selected_capability_id=bound.capability_id,
        reason=ProviderRequirementUnsupportedReason.PROMPT_EXPRESSION_UNSUPPORTED,
        unsupported_field_paths=tuple(sorted(set(paths))),
        input_expression_report=_input_expression_report(binding, paths) if binding is not None else None)


def _authored_final_prompt(binding, bound, requirement, *, continuity_expression=None):
    """v4 evidence is selected QA plus the final bytes, never replaced prose."""
    from pydantic import ValidationError
    from ai_video.production.generation_input_control import native_text_mapping_evidence
    from ai_video.production.performance_authoring import _actor_paths
    from ai_video.production.performance_direction import render_performance_direction
    from ai_video.production.shot_router import ProviderBoundVideoRequest
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    try:
        binding = SeedanceNativePromptBinding.model_validate(binding.model_dump(mode="python"))
    except (TypeError, ValueError):
        return None, ("native_prompt_binding.prompt_sha256",)
    if binding.provider_bound_request_hash != bound.provider_bound_request_hash:
        return None, ("native_prompt_binding.provider_bound_request_hash",)
    try:
        bound = ProviderBoundVideoRequest.model_validate(bound.model_dump(mode="python"))
        requirement = ProviderNeutralVideoRequirement.model_validate(requirement.model_dump(mode="python"))
    except (ValueError, ValidationError):
        return None, ("generation_recipe", "requirement_hash")
    recipe = bound.generation_recipe
    if recipe.requirement_hash != requirement.requirement_hash or bound.requirement_hash != requirement.requirement_hash:
        return None, ("generation_recipe.requirement_hash",)
    prompt, intent = binding.prompt_text, requirement.generation_intent
    mapped, mapping_issues = native_text_mapping_evidence(recipe.expressions, intent, prompt)
    controls = set(mapped)
    mapping_problems = [value for identifier, paths in mapping_issues.items() for value in (identifier, *paths)]
    issues = list(mapping_problems)

    # Exact canonical literal text can express itself. Direction/beat obligations
    # need individual QA duties; a repeated adjective is no per-actor evidence.
    def literal_paths(node, path="generation_intent"):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "character_directions" or key.endswith(("_id", "_ids", "_hash")):
                    continue
                literal_paths(value, path + "." + key)
        elif isinstance(node, str) and node.strip() and node not in {"none", "unspecified"} and node in prompt:
            controls.add(path)

    literal_paths(intent.model_dump(mode="json"))
    duration = intent.pacing.shot_duration_seconds
    if duration is not None and duration == bound.output_requirement.duration_seconds:
        controls.add("generation_intent.pacing.shot_duration_seconds")
    performance = intent.performance_intent
    if performance is not None and performance.character_directions:
        block = render_performance_direction(performance)
        if block and block in prompt:
            controls.add("generation_intent.performance_intent.character_directions")
        else:
            for index, actor in enumerate(performance.character_directions):
                required = (*_actor_paths(actor, index), *(f"generation_intent.performance_intent."
                    f"character_directions.{index}.beats.{beat}.phase" for beat in range(len(actor.beats))))
                # Metadata may also be expressed by an exact actor identity in
                # final prose; role and visibility stay canonical author choices.
                base = f"generation_intent.performance_intent.character_directions.{index}"
                if actor.screen_identity in prompt:
                    controls.add(base + ".screen_identity")
                for field in ("role", "visibility"):
                    if getattr(actor, field) in prompt:
                        controls.add(base + "." + field)
                for path in required:
                    if path in controls:
                        continue
                    issues.append(path)
                    issues.extend(item.requirement_id for item in recipe.expressions
                        if any(path == target or path.startswith(target + ".") for target in item.intent_paths))

    # Keeping the *entire* deterministic result is an exact check against the
    # actual final bytes. It preserves existing voice/continuity support without
    # allowing partially overlapping or shortened text to inherit its claims.
    from ai_video.production._remote_video_native_prompt import compile_remote_video_prompt
    compiled = compile_remote_video_prompt(requirement, voice_route=bound.voice_route,
        provider_bound=bound, continuity_expression=continuity_expression, max_prompt_characters=None)
    grammar = "seedance-authored-prose-v4"
    if compiled.outcome == "compiled" and compiled.prompt_text == prompt:
        return ProviderNativePrompt(grammar_contract="remote-video-prose-v1", prompt_text=prompt,
            prompt_sha256=binding.prompt_sha256,
            expressed_control_paths=compiled.expressed_control_paths), tuple(mapping_problems)
    return ProviderNativePrompt(grammar_contract=grammar, prompt_text=prompt,
        prompt_sha256=binding.prompt_sha256, expressed_control_paths=tuple(sorted(controls))), tuple(issues)


def require_fresh_seedance_request(bound, requirement, request, capabilities, *, continuity_expression=None):
    """Fresh execution cannot mint a v2 replacement; old readers never call this."""
    if bound.provider_name != "seedance":
        return
    from ai_video.errors import AiVideoError, ErrorCode
    from ai_video.production.video_compiler import CompiledProviderVideoRequest

    version = request.adapter_compiler_version
    if version not in {"1", "2", "3", "4"} or (
            version == "3" and requirement.target_shot.preserved_source_expression is None):
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Fresh Seedance requires a supported compiler contract; compiler/3 requires preserved-source evidence.")
    text = request.prompt_text
    digest = hashlib.sha256(text.encode()).hexdigest()
    binding = None
    if version == "4" or (version == "2" and text == requirement.target_shot.intent):
        binding = SeedanceNativePromptBinding(provider_bound_request_hash=bound.provider_bound_request_hash,
            prompt_text=text, prompt_sha256=digest, source_evidence_sha256=digest,
            source_preservation=request.adapter_compiler_version == "2")
    try:
        result = compile_seedance_request(bound, requirement, capabilities=capabilities, binding=binding,
            continuity_expression=continuity_expression)
    except (TypeError, ValueError):
        result = None
    sealed = request.activation_scope.request if request.activation_scope else None
    if not isinstance(result, CompiledProviderVideoRequest) or result.request != sealed:
        paths = getattr(result, "unsupported_field_paths", ())
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Fresh Seedance authored text requires compiler/4 and current final-text QA evidence."
                + (" Missing: " + ", ".join(paths) if paths else ""))


class SeedanceNativePromptBinding(StrictModel):
    provider_bound_request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    # Official length guidance is advisory; preserve exact text and its seal.
    prompt_text: str = Field(min_length=1)
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
