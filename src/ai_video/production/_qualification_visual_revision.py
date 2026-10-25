"""One new authored first-frame version, never a retry or model qualification.

The pure binding checks the prospective scope. Only the committer may join it
to the prior version's exact, explicit supersession receipt under its lock.
"""
from __future__ import annotations

from ai_video.production.generation_diagnosis import compare_compiled_requests


def allows_authored_visual_revision(binding, selected) -> bool:
    if selected is None:
        return False
    inputs = binding.inputs
    limits = inputs.limits
    if (limits.paid_submits_used < 1
            or limits.paid_submit_ceiling != limits.paid_submits_used + 1
            or binding.decision.runtime_repair is not None
            or binding.decision.intervention is not None
            or inputs.policy.max_resamples != 0
            or any(e.outcome == 'unknown_outcome' for e in inputs.evidence)):
        return False
    submitted = {(e.attempt_id, e.request_hash) for e in inputs.evidence
                 if e.task_id == limits.task_id and e.outcome != 'not_submitted'}
    latest = next((e for e in inputs.evidence
                   if e.evidence_hash == inputs.latest_attempt_hash), None)
    prior = next((x for x in inputs.experiences if latest in x.evidence), None)
    baseline = inputs.baseline_request
    scope = binding.compiled_request.activation_scope
    if (len(submitted) != limits.paid_submits_used
            or latest is None or latest.outcome != 'media'
            or latest.artifact_sha256 is None or prior is None
            or latest.task_id != limits.task_id
            or latest.shot_id != binding.context.target_shot_id
            or baseline is None or scope is None
            or baseline.request_input_hash != latest.request_hash
            or prior.candidate.capabilities.provider_name != selected.capabilities.provider_name
            or prior.candidate.capability_id != selected.capability_id):
        return False
    from ai_video.production.generation_visual_revision import validate_visual_revision_goal

    try:
        validate_visual_revision_goal(prior.candidate.final_output_goal, selected.final_output_goal)
    except (AttributeError, TypeError, ValueError):
        return False
    before, after = baseline, scope.request
    old_frames = tuple(x for x in before.image_bindings if x.role == 'first_frame')
    new_frames = tuple(x for x in after.image_bindings if x.role == 'first_frame')
    if (len(before.image_bindings) != 1 or len(after.image_bindings) != 1
            or len(old_frames) != 1 or len(new_frames) != 1
            or old_frames[0].asset_sha256 == new_frames[0].asset_sha256):
        return False
    # Preserve the actual action, speech, camera and sound contract. This route
    # changes visual treatment; unrelated creative changes require another scope.
    old_intent = prior.projection.requirement.generation_intent
    new_intent = binding.projection.requirement.generation_intent
    if (old_intent is None or new_intent is None
            or old_intent.model_dump(mode='json', exclude={'visual_treatment'})
            != new_intent.model_dump(mode='json', exclude={'visual_treatment'})):
        return False
    old_rules = {r.requirement_id: r for r in prior.candidate.recipe.expressions
                 if r.level == 'acceptance' and r.stage == 'raw_generation'}
    new_rules = {r.requirement_id: r for r in selected.recipe.expressions
                 if r.level == 'acceptance' and r.stage == 'raw_generation'}
    if not old_rules or any(new_rules.get(k) != v for k, v in old_rules.items()):
        return False
    delta = set(compare_compiled_requests(before, after)['changed_variables'])
    return ('image_bindings' in delta
            and delta <= {'image_bindings', 'prompt_text', 'provider_profile'})


def require_authored_visual_revision_predecessor(committer, manifest, binding):
    """Reopen the authorization at the existing one-use submit boundary."""
    if binding.policy.execution_purpose != 'qualification':
        return
    selected = next((c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id), None)
    if not allows_authored_visual_revision(binding, selected):
        return
    from ai_video.production._state_commit_common import _state_invalid
    from ai_video.production.generation_visual_revision import load_generation_visual_supersession

    latest = next(e for e in binding.inputs.evidence
                  if e.evidence_hash == binding.inputs.latest_attempt_hash)
    previous = next((a for a in manifest.attempts if a.attempt_id == latest.attempt_id), None)
    state = previous.video_generation_state if previous else None
    if (previous is None or previous.status.value != 'failed'
            or previous.error_code != 'generation_visual_superseded'
            or state is None or state.visual_supersession is None):
        raise _state_invalid('Authored visual revision requires its exact canonical supersession.')
    receipt = load_generation_visual_supersession(committer.project_root, state.visual_supersession)
    request = binding.compiled_request.activation_scope.request
    frame = next(x for x in request.image_bindings if x.role == 'first_frame')
    if (receipt.target_goal != selected.final_output_goal
            or receipt.target_first_frame_sha256 != frame.asset_sha256
            or receipt.request_fingerprint != latest.request_hash
            or receipt.artifact_sha256 != latest.artifact_sha256
            or receipt.task_id != binding.inputs.limits.task_id
            or receipt.shot_id != binding.context.target_shot_id
            or request.base_project == receipt.base_project
            or request.base_project.revision <= receipt.base_project.revision
            or state.generation_experiences[-1].content_hash != receipt.experience_content_hash):
        raise _state_invalid('Authored visual revision differs from its sealed target or retained history.')
