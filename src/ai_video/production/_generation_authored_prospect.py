"""Planning recognition only; compiled admission and the /4 lock authorize execution."""

from ai_video.production.generation_visual_revision import validate_visual_revision_goal
from ai_video.production.video import VideoGenerationMode
from ai_video.production.generation_authored_retarget import _same_goal_with_new_version


def is_same_rubric_authored_prospect(*, inputs, projection, policy, latest, prior):
    """Retain failed/unevaluated evidence while considering one new authored intent."""
    try:
        limits = inputs.limits
        if (policy.execution_purpose != "qualification" or inputs.policy.version != "3"
                or inputs.policy.max_resamples != 0 or not inputs.policy.allow_bounded_exploration
                or len(inputs.candidates) != 1 or latest.outcome != "media"
                or latest.artifact_sha256 is None or latest.task_id != limits.task_id
                or limits.paid_submits_used < 1
                or limits.paid_submit_ceiling != limits.paid_submits_used + 1
                or any(e.outcome == "unknown_outcome" for e in inputs.evidence)):
            return False
        target = inputs.candidates[0]
        if (prior is None or limits.allowed_remote_candidates != (target.candidate_id,)
                or prior.candidate_id != target.candidate_id
                or prior.capabilities != target.capabilities
                or prior.capability_id != target.capability_id
                or prior.output_requirement != target.output_requirement
                or prior.recipe.acceptance_policy != target.recipe.acceptance_policy
                or inputs.baseline_request is None
                or inputs.baseline_request.request_input_hash != latest.request_hash):
            return False
        variant = next(v for v in target.capabilities.variants
                       if v.capability_id == target.capability_id)
        if variant.mode != VideoGenerationMode.IMAGE_TO_VIDEO:
            return False
        sources = [x for x in inputs.experiences if latest in x.evidence
                   and x.candidate.scope_hash == prior.scope_hash]
        if (len(sources) != 1 or sources[0].projection.requirement.generation_intent
                == projection.requirement.generation_intent):
            return False
        validate_visual_revision_goal(prior.final_output_goal, target.final_output_goal)
        return True
    except (AttributeError, TypeError, ValueError, StopIteration):
        return False


def is_authored_generation_retarget_prospect(*, inputs, projection, policy, latest, prior):
    """Recognize an exact same-QA Seedance 2.0 R2V target during diagnosis."""
    try:
        limits = inputs.limits
        if (
            policy.execution_purpose != "qualification"
            or inputs.policy.version != "3"
            or inputs.policy.max_resamples != 0
            or not inputs.policy.allow_bounded_exploration
            or len(inputs.candidates) != 1
            or prior is None
            or latest.outcome != "media"
            or latest.artifact_sha256 is None
            or not any(item.verdict == "FAIL" for item in latest.findings)
            or latest.task_id != limits.task_id
            or latest.shot_id != projection.requirement.target_shot.shot_id
            or limits.paid_submits_used < 1
            or limits.paid_submit_ceiling != limits.paid_submits_used + 1
            or limits.allowed_remote_candidates != (inputs.candidates[0].candidate_id,)
            or any(item.outcome == "unknown_outcome" for item in inputs.evidence)
            or inputs.baseline_request is None
            or inputs.baseline_request.request_input_hash != latest.request_hash
        ):
            return False
        target = inputs.candidates[0]
        source = tuple(item for item in inputs.experiences
                       if latest in item.evidence and item.candidate == prior)
        old_variants = tuple(item for item in prior.capabilities.variants
                             if item.capability_id == prior.capability_id)
        new_variants = tuple(item for item in target.capabilities.variants
                             if item.capability_id == target.capability_id)
        if len(source) != 1 or len(old_variants) != 1 or len(new_variants) != 1:
            return False
        old_variant, new_variant = old_variants[0], new_variants[0]
        if (
            prior.capabilities.provider_name != target.capabilities.provider_name
            or old_variant.provider_kind != new_variant.provider_kind
            or old_variant.model_id == new_variant.model_id
            or new_variant.mode is not VideoGenerationMode.REFERENCE_TO_VIDEO
            or prior.recipe.acceptance_policy != target.recipe.acceptance_policy
            or not _same_goal_with_new_version(prior.final_output_goal, target.final_output_goal)
            or source[0].projection.requirement.generation_intent == projection.requirement.generation_intent
            or new_variant.output_capability is None
            or not new_variant.output_capability.supports(target.output_requirement)
            or "reference" not in new_variant.allowed_image_roles
        ):
            return False
        return True
    except (AttributeError, TypeError, ValueError, StopIteration):
        return False
