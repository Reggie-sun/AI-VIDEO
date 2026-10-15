"""Select a current Canvas attempt only from canonical closed-result lineage."""
from ai_video.production.models import StateCommitStatus


def closed_unsubmitted_evidence(committer, attempt):
    """Return evidence only after the sole committer's exact closure validation."""
    from ai_video.production._state_commit_video_unsubmitted import is_verified_closed_unsubmitted_video_attempt
    manifest = committer._read_manifest()
    current = next((a for a in manifest.attempts if a.attempt_id == attempt.attempt_id), None)
    if current != attempt or not is_verified_closed_unsubmitted_video_attempt(
            committer, manifest=manifest, attempt=attempt):
        return None
    state = attempt.video_generation_state
    experience = committer._reopen_generation_experience(state.generation_experiences[-1])
    return experience.evidence[-1]


def current_canvas_attempt(committer, attempts):
    if len(attempts) == 1:
        return attempts[0]
    message = "Multiple attempts require explicit adopted-version/recovery decisions."
    by_id = {attempt.attempt_id: attempt for attempt in attempts}
    predecessors, successors = {}, {}
    for attempt in attempts:
        state = attempt.video_generation_state
        if state.execution_binding is None:
            raise ValueError(message)
        binding = committer._reopen_generation_execution_binding(state.execution_binding)
        latest = binding.inputs.latest_attempt_hash
        if latest is None:
            continue
        evidence = next((e for e in binding.inputs.evidence if e.evidence_hash == latest), None)
        parent = by_id.get(evidence.attempt_id) if evidence is not None else None
        if (parent is None or parent.attempt_id == attempt.attempt_id
                or parent.status is not StateCommitStatus.FAILED):
            raise ValueError(message)
        if parent.attempt_id in successors:
            raise ValueError(message)
        if parent.video_generation_state.quality_rejection is not None:
            receipt = committer._reopen_generation_quality_rejection(
                parent.video_generation_state.quality_rejection)
            if (receipt.evidence_hash != latest or receipt.request_fingerprint != evidence.request_hash
                    or receipt.artifact_sha256 != evidence.artifact_sha256
                    or binding.inputs.abandoned_result is not None
                        and binding.inputs.abandoned_result != receipt):
                raise ValueError(message)
        elif (unsubmitted := closed_unsubmitted_evidence(committer, parent)) is not None:
            if (unsubmitted != evidence or evidence.outcome != "not_submitted"
                    or binding.decision.runtime_repair is not None
                    or binding.inputs.abandoned_result is not None):
                raise ValueError(message)
        else:
            repair = binding.decision.runtime_repair
            known_failure = repair.paid_known_failure_retarget if repair is not None else None
            cross_provider = (
                repair.paid_cross_provider_no_effect_retarget if repair is not None else None
            )
            if known_failure is not None:
                from ai_video.production._state_commit_video_runtime_repair import (
                    closed_paid_known_failure_proof,
                )
                from ai_video.production.generation_runtime_repair import (
                    paid_failure_retarget_preserves_strategy,
                )
                paid_receipt, _submission, observation, request = closed_paid_known_failure_proof(
                    committer, parent
                )
                old_binding = committer._reopen_generation_execution_binding(
                    parent.video_generation_state.execution_binding
                )
                old_candidate = next(c for c in old_binding.inputs.candidates
                    if c.candidate_id == old_binding.decision.selected_candidate_id)
                target_candidate = next(c for c in binding.inputs.candidates
                    if c.candidate_id == binding.decision.selected_candidate_id)
                if (
                    paid_receipt.submit_receipt_fingerprint
                        != known_failure.paid_submit_receipt_fingerprint
                    or observation.observation_fingerprint
                        != known_failure.failed_observation_fingerprint
                    or target_candidate.scope_hash != known_failure.target_scope_hash
                    or old_binding.inputs.limits.task_id != binding.inputs.limits.task_id
                    or old_binding.context.target_shot_id != binding.context.target_shot_id
                    or evidence.outcome != "runtime_failure"
                    or evidence.artifact_sha256 is not None
                    or evidence.request_hash != request.request_input_hash
                    or evidence.task_id != old_binding.inputs.limits.task_id
                    or evidence.shot_id != old_binding.context.target_shot_id
                    or binding.inputs.latest_attempt_hash != evidence.evidence_hash
                    or not paid_failure_retarget_preserves_strategy(old_candidate, target_candidate)
                ):
                    raise ValueError(message)
                receipt = observation
            elif cross_provider is not None:
                from ai_video.production._state_commit_video_runtime_repair import (
                    closed_paid_no_effect_receipt,
                )
                from ai_video.production.generation_runtime_repair import (
                    cross_provider_no_effect_retarget_preserves_strategy,
                )

                receipt = closed_paid_no_effect_receipt(committer, parent)
                old_binding = committer._reopen_generation_execution_binding(
                    parent.video_generation_state.execution_binding
                )
                old_candidate = next((c for c in old_binding.inputs.candidates
                    if c.candidate_id == old_binding.decision.selected_candidate_id), None)
                target_candidate = next((c for c in binding.inputs.candidates
                    if c.candidate_id == binding.decision.selected_candidate_id), None)
                if (
                    receipt.submit_receipt_fingerprint
                        != cross_provider.submit_receipt_fingerprint
                    or old_candidate is None
                    or old_candidate.scope_hash != cross_provider.source_scope_hash
                    or old_candidate.capabilities.provider_name
                        != cross_provider.source_provider_name
                    or target_candidate is None
                    or target_candidate.scope_hash != cross_provider.target_scope_hash
                    or target_candidate.capabilities.provider_name
                        != cross_provider.target_provider_name
                    or old_binding.projection.requirement.requirement_hash
                        != cross_provider.source_requirement_hash
                    or binding.projection.requirement.requirement_hash
                        != cross_provider.target_requirement_hash
                    or old_binding.inputs.limits.task_id != binding.inputs.limits.task_id
                    or old_binding.context.target_shot_id != binding.context.target_shot_id
                    or evidence.outcome != "runtime_failure"
                    or evidence.artifact_sha256 is not None
                    or evidence.request_hash
                        != committer._reopen_video_request(
                            parent.video_generation_state.request
                        ).request_input_hash
                    or evidence.task_id != old_binding.inputs.limits.task_id
                    or evidence.shot_id != old_binding.context.target_shot_id
                    or binding.inputs.latest_attempt_hash != evidence.evidence_hash
                    or old_binding.compiled_request.image_bindings
                        != binding.compiled_request.image_bindings
                    or old_binding.compiled_request.media_bindings
                        != binding.compiled_request.media_bindings
                    or binding.inputs.abandoned_result is not None
                    or not cross_provider_no_effect_retarget_preserves_strategy(
                        old_candidate, target_candidate,
                        old_binding.projection.requirement,
                        binding.projection.requirement,
                        cross_provider,
                    )
                ):
                    raise ValueError(message) from None
            else:
                from ai_video.production._state_commit_video_runtime_repair import closed_paid_no_effect_receipt
                receipt = closed_paid_no_effect_receipt(committer, parent)
            pointer = next((p for p in parent.video_generation_state.runtime_repairs
                            if repair is not None and p.content_hash == repair.content_hash), None)
            if (pointer is None or repair.attempt_id != parent.attempt_id
                    or repair.evidence_hash != latest or evidence.outcome != "runtime_failure"
                    or evidence.artifact_sha256 is not None
                    or committer._reopen_video_request(parent.video_generation_state.request).request_input_hash
                        != evidence.request_hash
                    or committer._reopen_runtime_repair_authorization(pointer) != repair
                    or binding.inputs.abandoned_result is not None):
                raise ValueError(message)
            if cross_provider is not None:
                # The grant is consumed atomically with the paid submit intent.
                # Reopening this successor validates that durable lineage; it
                # must not call the unconsumed-grant consumer a second time.
                if pointer.consumed != (attempt.paid_provider_state is not None):
                    raise ValueError(message)
        predecessors[attempt.attempt_id] = parent.attempt_id
        successors[parent.attempt_id] = attempt.attempt_id
    leaves = set(by_id) - set(successors)
    roots = set(by_id) - set(predecessors)
    if len(leaves) != 1 or len(roots) != 1:
        raise ValueError(message)
    leaf = next(iter(leaves))
    visited, node = set(), leaf
    while node not in visited:
        visited.add(node)
        if node not in predecessors:
            break
        node = predecessors[node]
    if visited != set(by_id):
        raise ValueError(message)
    return by_id[leaf]
