"""Narrow admission of one evaluated quality repair in a qualification trial.

This does not grant a permit or extend a paid ledger. The existing committer
must still retain the terminal rejection and authorize the exact +1 submit.
"""
from __future__ import annotations

from ai_video.production.generation_diagnosis import (
    compare_compiled_requests,
    diagnose_exact_result,
)


def allows_one_known_quality_repair(binding, selected) -> bool:
    """Keep the initial trial and runtime/no-effect recovery cases disjoint."""
    if selected is None:
        return False
    inputs = binding.inputs
    limits = inputs.limits
    intervention = binding.decision.intervention
    latest = next((e for e in inputs.evidence
                   if e.evidence_hash == inputs.latest_attempt_hash), None)
    if (limits.paid_submit_ceiling != 2 or limits.paid_submits_used != 1
            or binding.decision.runtime_repair is not None
            or inputs.runtime_repairs or inputs.policy.max_resamples != 0
            or intervention is None or intervention.purpose != 'production_repair'
            or intervention.disposition != 'GENERATE_ONCE'
            or intervention.candidate_id != selected.candidate_id
            or latest is None or latest.outcome != 'media'
            or latest.artifact_sha256 is None
            or latest.shot_id != binding.context.target_shot_id
            or latest.task_id != limits.task_id):
        return False
    # No second quality experiment, hidden same-task consumption, or unknown.
    submitted = {(e.attempt_id, e.request_hash) for e in inputs.evidence
                 if e.task_id == limits.task_id and e.outcome != 'not_submitted'}
    if (submitted != {(latest.attempt_id, latest.request_hash)}
            or any(e.outcome == 'unknown_outcome' for e in inputs.evidence)):
        return False
    prior = next((x for x in inputs.experiences if latest in x.evidence), None)
    baseline = inputs.baseline_request
    current = binding.compiled_request.activation_scope
    if (prior is None or baseline is None or current is None
            or baseline.request_input_hash != latest.request_hash
            or selected.recipe.rubric_hash != prior.candidate.recipe.rubric_hash
            or selected.final_output_goal != prior.candidate.final_output_goal
            or prior.candidate.capabilities.provider_name != selected.capabilities.provider_name
            or prior.candidate.capability_id != selected.capability_id):
        return False
    sources = tuple(s for x in inputs.experiences for s in x.evaluation_sources)
    diagnosis = diagnose_exact_result(latest, inputs.evidence, prior.candidate.recipe,
        evaluation_sources=sources, requirement=prior.projection.requirement)
    if (diagnosis.failure_classes != ('QUALITY_FAILURE',)
            or not diagnosis.failed_requirements
            or set(intervention.closes) != set(diagnosis.failed_requirements)
            or not set(diagnosis.preserved_requirements) <= set(intervention.protected_requirements)
            or intervention.known_requirement_violations
            or latest.evidence_hash not in intervention.support):
        return False
    # Prompt wording is the only creative variable. A new empty native node may
    # change the sealed profile pointer; model/mode, references, output, compiler
    # and seed remain exact. This never treats a provider switch as prompt repair.
    delta = compare_compiled_requests(baseline, current.request)
    changed = set(delta['changed_variables'])
    recipe = binding.decision.routing.provider_bound_request.generation_recipe
    return ('prompt_text' in changed
            and changed <= {'prompt_text', 'provider_profile'}
            and changed == set(intervention.changed_variables)
            and recipe is not None and recipe.comparison is not None
            and set(recipe.comparison.changed_variables) == changed)


def require_quality_repair_predecessor(committer, manifest, binding) -> None:
    """Called only by the existing committer while holding its submit lock."""
    from ai_video.errors import ErrorCode
    from ai_video.production._state_commit_common import _state_invalid

    if binding.policy.execution_purpose != 'qualification':
        return
    selected = next((c for c in binding.inputs.candidates
                     if c.candidate_id == binding.decision.selected_candidate_id), None)
    if not allows_one_known_quality_repair(binding, selected):
        return
    latest = next(e for e in binding.inputs.evidence
                  if e.evidence_hash == binding.inputs.latest_attempt_hash)
    previous = next((a for a in manifest.attempts if a.attempt_id == latest.attempt_id), None)
    state = previous.video_generation_state if previous else None
    if (previous is None or previous.status.value != 'failed'
            or previous.error_code != ErrorCode.VIDEO_QUALITY_REJECTED.value
            or state is None or state.quality_rejection is None
            or state.fetch_receipt is None or not state.generation_experiences):
        raise _state_invalid('Qualification quality repair requires its exact terminal quality rejection.')
    rejection = committer._reopen_generation_quality_rejection(state.quality_rejection)
    request = committer._reopen_video_request(state.request)
    fetch = committer._reopen_video_fetch(state.fetch_receipt)
    if (rejection.schema_version != 'generation-quality-rejection/1'
            or rejection.attempt_id != latest.attempt_id
            or rejection.evidence_hash != latest.evidence_hash
            or rejection.request_fingerprint != latest.request_hash
            or rejection.request_fingerprint != request.request_input_hash
            or rejection.artifact_sha256 != latest.artifact_sha256
            or rejection.artifact_sha256 != fetch.artifact_sha256
            or rejection.artifact_size_bytes != fetch.size_bytes
            or rejection.qa_policy != manifest.active_qa_policy
            or rejection.experience_content_hash != state.generation_experiences[-1].content_hash):
        raise _state_invalid('Qualification quality repair predecessor evidence is not exact.')
