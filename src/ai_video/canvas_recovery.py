"""Select a current Canvas attempt only from canonical closed-result lineage."""
from ai_video.production.models import StateCommitStatus


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
                or parent.status is not StateCommitStatus.FAILED
                or parent.video_generation_state.quality_rejection is None):
            raise ValueError(message)
        receipt = committer._reopen_generation_quality_rejection(
            parent.video_generation_state.quality_rejection)
        if (receipt.evidence_hash != latest or receipt.request_fingerprint != evidence.request_hash
                or receipt.artifact_sha256 != evidence.artifact_sha256
                or parent.attempt_id in successors
                or binding.inputs.abandoned_result is not None
                   and binding.inputs.abandoned_result != receipt):
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
