"""Pure projections of authored causal truth; never infer facts from prompts."""

import re
import unicodedata

from ai_video.production.hashing import canonical_sha256
from ai_video.production.video_transition import CausalDimension


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
    return require_current_close_facts(reopened.generation_intent)


def render_causal_facts(facts):
    return "; ".join(f"{dimension.value.replace('_', ' ')}: {fact}" for dimension, fact in facts)


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
