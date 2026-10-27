"""QA-selected final Shot prose; no transport, mutation or template fallback."""

import hashlib


def has_authored_text(bound):
    recipe = bound.generation_recipe
    return recipe is not None and any(
        item.stage == "raw_generation" and item.level != "diagnostic"
        and item.native_text_mapping is not None for item in recipe.expressions)


def compile_authored_text(bound, requirement, *, continuity_expression=None):
    from ai_video.production.generation_recipe import expression_errors
    from ai_video.production.seedance_native_prompt import (
        SeedanceNativePromptBinding, _authored_final_prompt, _expression_unsupported,
    )
    from ai_video.production.video_requirement import ContinuityStateKind

    text = requirement.target_shot.intent
    binding = SeedanceNativePromptBinding(
        provider_bound_request_hash=bound.provider_bound_request_hash,
        prompt_text=text, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source_evidence_sha256=requirement.target_shot.content_hash)
    # Scalar QA mappings cannot replace the canonical causal endpoint owner.
    intent = requirement.generation_intent
    if (continuity_expression is not None or any(state.kind is ContinuityStateKind.TYPED_HASH
            for state in (intent.open_state, intent.close_state))):
        return _expression_unsupported(bound, requirement, ("generation_intent.causal_endpoints",),
                                       binding=binding)
    native, issues = _authored_final_prompt(binding, bound, requirement)
    if not issues:
        issues = expression_errors(bound.generation_recipe, requirement, text,
                                   native.expressed_control_paths)
    if issues:
        return _expression_unsupported(bound, requirement, issues, binding=binding)
    return native
