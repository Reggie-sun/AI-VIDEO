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


def validate_abandoned_baseline(committer, by_id, receipt, shot_id):
    """Verify a historical abandonment against its own durable attempt evidence."""
    from ai_video.production.generation_rejection import validate_abandoned_result

    attempt = by_id.get(receipt.attempt_id)
    state = attempt.video_generation_state if attempt is not None else None
    if (attempt is None or attempt.status is not StateCommitStatus.FAILED
            or state is None or state.quality_rejection is None
            or not state.generation_experiences):
        raise ValueError("Abandoned baseline has no matching failed attempt.")
    stored_receipt = committer._reopen_generation_quality_rejection(state.quality_rejection)
    experience_pointer = state.generation_experiences[-1]
    experience = committer._reopen_generation_experience(experience_pointer)
    evidence = next((item for item in experience.evidence
                     if item.evidence_hash == receipt.evidence_hash), None)
    request = committer._reopen_video_request(state.request)
    fetch_pointer = state.local_fetch_receipt or state.fetch_receipt
    if fetch_pointer is None:
        raise ValueError("Abandoned baseline has no exact fetched media.")
    fetch = (committer._reopen_local_video_fetch(fetch_pointer)
             if state.local_fetch_receipt is not None
             else committer._reopen_video_fetch(fetch_pointer))
    histories = committer.read_generation_experiences()
    history = tuple(item for stored in histories for item in stored.evidence)
    sources = tuple(source for stored in histories for source in stored.evaluation_sources)
    if (stored_receipt != receipt
            or receipt.experience_content_hash != experience_pointer.content_hash
            or receipt.request_fingerprint != request.request_input_hash
            or receipt.artifact_sha256 != fetch.artifact_sha256
            or receipt.artifact_size_bytes != fetch.size_bytes
            or evidence is None or evidence.attempt_id != attempt.attempt_id
            or evidence.shot_id != shot_id or evidence.request_hash != request.request_input_hash
            or evidence.outcome != "media" or evidence.artifact_sha256 != fetch.artifact_sha256):
        raise ValueError("Abandoned baseline differs from its canonical stored evidence.")
    validate_abandoned_result(
        receipt, experience=experience, evidence=evidence,
        history=history, evaluation_sources=sources,
    )


def current_canvas_attempt(committer, attempts):
    if len(attempts) == 1:
        return attempts[0]
    message = "Multiple attempts require explicit adopted-version/recovery decisions."
    by_id = {attempt.attempt_id: attempt for attempt in attempts}
    predecessors, successors = {}, {}
    validated_runtime_repairs = {}
    for attempt in attempts:
        state = attempt.video_generation_state
        if state.execution_binding is None:
            raise ValueError(message)
        binding = committer._reopen_generation_execution_binding(state.execution_binding)
        if binding.inputs.abandoned_result is not None:
            validate_abandoned_baseline(
                committer, by_id, binding.inputs.abandoned_result, binding.context.target_shot_id,
            )
        predecessor_hash = (
            binding.unsubmitted_predecessor_evidence_hash
            or binding.inputs.latest_attempt_hash
        )
        if predecessor_hash is None:
            continue
        evidence = next((e for e in binding.inputs.evidence
                         if e.evidence_hash == predecessor_hash), None)
        parent = by_id.get(evidence.attempt_id) if evidence is not None else None
        if (parent is None or parent.attempt_id == attempt.attempt_id
                or parent.status is not StateCommitStatus.FAILED):
            raise ValueError(message)
        if parent.attempt_id in successors:
            raise ValueError(message)
        if parent.video_generation_state.quality_rejection is not None:
            receipt = committer._reopen_generation_quality_rejection(
                parent.video_generation_state.quality_rejection)
            if (receipt.evidence_hash != predecessor_hash
                    or receipt.request_fingerprint != evidence.request_hash
                    or receipt.artifact_sha256 != evidence.artifact_sha256
                    or binding.inputs.abandoned_result is not None
                        and binding.inputs.abandoned_result != receipt):
                raise ValueError(message)
        elif (unsubmitted := closed_unsubmitted_evidence(committer, parent)) is not None:
            repair = binding.decision.runtime_repair
            if (unsubmitted != evidence or evidence.outcome != "not_submitted"
                    or (repair is not None and (
                        validated_runtime_repairs.get(repair.content_hash) != repair
                        or binding.inputs.latest_attempt_hash != repair.evidence_hash
                    ))):
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
                    or repair.evidence_hash != predecessor_hash or evidence.outcome != "runtime_failure"
                    or evidence.artifact_sha256 is not None
                    or committer._reopen_video_request(parent.video_generation_state.request).request_input_hash
                        != evidence.request_hash
                    or committer._reopen_runtime_repair_authorization(pointer) != repair):
                raise ValueError(message)
            consumers = [
                candidate for candidate in attempts
                if candidate.paid_provider_state is not None
                and candidate.video_generation_state.execution_binding is not None
                and committer._reopen_generation_execution_binding(
                    candidate.video_generation_state.execution_binding
                ).decision.runtime_repair == repair
            ]
            if (len(consumers) > 1 or pointer.consumed != bool(consumers)
                    or (attempt.paid_provider_state is not None and attempt not in consumers)):
                raise ValueError(message)
            validated_runtime_repairs[repair.content_hash] = repair
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
