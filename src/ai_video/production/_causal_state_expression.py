"""Pure projections of authored causal truth; never infer facts from prompts."""

import re
import unicodedata

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_transition import CausalDimension


def has_current_close_facts(requirement):
    expression = requirement.target_shot.preserved_source_expression
    return requirement.generation_intent.close_causal_facts is not None or bool(expression and expression.closing)


def canonical_close_facts(facts):
    if facts is None or set(facts) != set(CausalDimension):
        raise ValueError("current close requires every causal dimension exactly once")
    ordered = tuple(sorted(facts.items(), key=lambda item: item[0].value))
    if any(not value.strip() or value.strip().casefold() == "unspecified"
           or unicodedata.normalize("NFC", value) != value
           or re.fullmatch(r"[0-9a-f]{64}", value.strip()) for _, value in ordered):
        raise ValueError("current close requires resolved semantic facts, never digests")
    return ordered


def require_current_close_facts(intent):
    """Authoring validator shared by expression and evaluation projections."""
    ordered = canonical_close_facts(intent.close_causal_facts)
    if (intent.close_state.kind.value != "typed_hash"
            or canonical_sha256({d.value: fact for d, fact in ordered}) != intent.close_state.state_hash):
        raise ValueError("current close column does not match its typed hash")
    return ordered


def current_close_facts(requirement):
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement

    reopened = ProviderNeutralVideoRequirement.model_validate(requirement.model_dump(mode="python"))
    if reopened.target_shot.preserved_source_expression is not None:
        from ai_video.production.seedance_source_expression import source_state_facts

        facts = source_state_facts(reopened.target_shot.preserved_source_expression, "closing")
        if (not facts or reopened.generation_intent.close_causal_facts is not None
                or reopened.generation_intent.close_state.kind.value != "typed_hash"
                or reopened.generation_intent.close_state.state_hash
                != canonical_sha256({d.value: fact for d, fact in facts.items()})):
            raise ValueError("source-grounded close must match its sole approved preimage")
        return tuple(sorted(facts.items(), key=lambda item: item[0].value))
    return require_current_close_facts(reopened.generation_intent)


def render_causal_facts(facts):
    return "; ".join(f"{dimension.value.replace('_', ' ')}: {fact}" for dimension, fact in facts)


def native_recipe_expression_view(recipe, requirement, expressed_control_paths):
    """Keep verified state seals in the recipe, outside native prose/coverage.

    This is an ephemeral projection shared by native authors and the common
    compiler. Only an exact endpoint seal already expressed by its native
    grammar is removed; other fragments and the original recipe stay intact.
    """
    for endpoint in ("open_state", "close_state"):
        path = f"generation_intent.{endpoint}.state_hash"
        if path not in expressed_control_paths:
            continue
        state_hash = getattr(requirement.generation_intent, endpoint).state_hash
        recipe = recipe.model_copy(update={"expressions": tuple(
            item.model_copy(update={"native_text": tuple(
                text for text in item.native_text if text != state_hash)})
            if path in item.intent_paths else item for item in recipe.expressions)})
    return recipe


def causal_endpoint_text(requirement, provider_bound, *, endpoint, opening_expression=None):
    """Separate opening authority from independently authored current closing."""
    from ai_video.production._shot_router_contracts import ProviderBoundVideoRequest
    from ai_video.production.video_requirement import ProviderNeutralVideoRequirement
    from ai_video.production._causal_prompt_context import VerifiedCausalOpeningExpression

    if endpoint not in {"open_state", "close_state"}:
        raise ValueError("unknown causal expression endpoint")
    requirement = ProviderNeutralVideoRequirement.model_validate(requirement.model_dump(mode="python"))
    bound = ProviderBoundVideoRequest.model_validate(provider_bound.model_dump(mode="python"))
    shot = requirement.target_shot
    if (bound.requirement_hash != requirement.requirement_hash
            or (bound.target_shot_id, bound.target_shot_revision, bound.target_shot_content_hash)
            != (shot.shot_id, shot.revision, shot.content_hash)):
        raise ValueError("causal expression is not bound to the exact Shot/intent/request")
    if endpoint == "open_state":
        if type(opening_expression) is not VerifiedCausalOpeningExpression:
            raise ValueError("opening requires its sequence-issued evidence")
        facts = opening_expression.opening_facts(requirement, bound)
    else:
        facts = current_close_facts(requirement)
    return render_causal_facts(facts)


def close_evaluation_measurement(rule, requirement):
    """Derived question projection; the selected QA seal remains the observable."""
    facts = current_close_facts(requirement)
    if (rule.intent_paths != ("generation_intent.close_state.state_hash",)
            or rule.observable != requirement.generation_intent.close_state.state_hash
            or rule.tolerance != "exact" or rule.proof not in {"analyzer", "human"}
            or rule.level != "acceptance" or rule.stage != "raw_generation"):
        raise ValueError("current close requires exact raw semantic acceptance")
    shot = requirement.target_shot
    return (rule.measurement + f"\nSealed requirement: {requirement.requirement_hash}; "
        f"Shot: {shot.shot_id}@{shot.revision}/{shot.content_hash}."
        + "\nExact current Shot closing facts: " + render_causal_facts(facts))
