"""Read-only accepted source lineage for the existing sequence edge contract."""

from typing import Literal

from ai_video.production._generation_feedback_reader import (
    load_generation_execution_binding, load_generation_experience,
)
from ai_video.production._video_project_reader import (
    load_terminal_frame_evidence, load_video_request_receipt,
)
from ai_video.production.generation_diagnosis import diagnose_exact_result
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
from ai_video.production.video_requirement import ContinuityStateKind
from ai_video.production.video_transition import (
    CausalDimension, CausalStateChange, CausalTransitionMode, ContinuityObligation,
)


def causal_state_column_hash(
    changes: tuple[CausalStateChange, ...], *, endpoint: Literal["source_close", "target_open"],
) -> str:
    """Seal an explicit complete column in the existing TypedStateReference."""
    if endpoint not in {"source_close", "target_open"}:
        raise ValueError("unknown causal endpoint")
    if (len(changes) != len(CausalDimension)
            or {item.dimension for item in changes} != set(CausalDimension)):
        raise ValueError("complete causal declaration requires every dimension exactly once")
    if any(not getattr(item, endpoint).strip() or getattr(item, endpoint) == "unspecified"
           for item in changes):
        raise ValueError("complete causal declaration cannot contain unresolved values")
    return canonical_sha256({
        dimension.value: getattr(item, endpoint)
        for item in changes for dimension in (item.dimension,)
    })


def accepted_sequence_source(loaded, source, *, require_causal_close=False):
    """Only the selected source output can select an activated attempt."""
    output_ids = {asset_id for role in source.required_asset_roles for asset_id in role.asset_ids}
    matches = tuple(a for a in loaded.manifest.attempts
        if a.status is StateCommitStatus.SUCCEEDED and a.video_generation_state is not None
        and a.video_generation_state.phase is VideoAttemptPhase.ACTIVATE
        and a.video_generation_state.candidate_video_asset_ids
        and set(a.video_generation_state.candidate_video_asset_ids) <= output_ids)
    if len(matches) != 1:
        raise ValueError("source Shot requires one exact activated generation")
    attempt = matches[0]
    state = attempt.video_generation_state
    if state.execution_binding is None or not state.generation_experiences:
        raise ValueError("source Shot requires accepted typed intent and media evaluation evidence")
    request = load_video_request_receipt(loaded.root, state.request)
    binding = load_generation_execution_binding(loaded.root, state.execution_binding)
    binding.validate_request(request)
    authored = binding.projection.requirement.target_shot
    if (authored.shot_id != source.shot_id or authored.artifact_id != source.artifact_id
            or source.revision != authored.revision + 1
            or request.output_asset_id not in output_ids):
        raise ValueError("source Shot activation lineage is not current")
    experiences = tuple(load_generation_experience(loaded.root, p) for p in state.generation_experiences)
    entries = tuple(e for x in experiences for e in x.evidence)
    assets = {a.asset_id: a for a in loaded.registry.assets}
    video = assets[request.output_asset_id]
    close_hash = binding.projection.requirement.generation_intent.close_state.state_hash
    accepted = []
    for experience in experiences:
        if experience.projection != binding.projection:
            raise ValueError("source evaluation intent is stale")
        for entry in experience.evidence:
            if (entry.outcome != "media" or entry.stage != "raw_generation"
                    or entry.request_hash != request.request_input_hash
                    or entry.artifact_sha256 != video.sha256):
                continue
            close_rules = tuple(r.requirement_id for r in experience.candidate.recipe.expressions
                if r.level == "acceptance" and r.stage == "raw_generation"
                and r.proof in {"analyzer", "human"}
                and r.intent_paths == ("generation_intent.close_state.state_hash",)
                and r.observable == close_hash and r.tolerance == "exact")
            if require_causal_close and not close_rules:
                raise ValueError("source causal close state lacks exact semantic acceptance criterion")
            diagnosis = diagnose_exact_result(entry, entries, experience.candidate.recipe,
                evaluation_sources=tuple(s for x in experiences for s in x.evaluation_sources))
            if not diagnosis.all_required_observed_pass:
                raise ValueError("source exact media evaluation is not PASS")
            if require_causal_close and not set(close_rules) <= set(diagnosis.preserved_requirements):
                raise ValueError("source causal close state is NOT_EVALUATED")
            accepted.append(entry.evidence_hash)
    if not accepted:
        raise ValueError("source exact media evaluation is missing")
    terminal = (load_terminal_frame_evidence(loaded.root, state.terminal_frame_evidence)
                if state.terminal_frame_evidence is not None else None)
    return binding, request, terminal, tuple(sorted(accepted)), attempt.candidate_registry


def require_causal_columns(changes, source_intent, target_intent):
    source_column = causal_state_column_hash(changes, endpoint="source_close")
    target_column = causal_state_column_hash(changes, endpoint="target_open")
    close, opening = source_intent.close_state, target_intent.open_state
    if (close.kind is not ContinuityStateKind.TYPED_HASH or close.state_hash != source_column
            or opening.kind is not ContinuityStateKind.TYPED_HASH or opening.state_hash != target_column):
        raise ValueError("source close / target open require exact complete causal state hashes")
    if any(c.transition_mode is CausalTransitionMode.CARRY and c.source_close != c.target_open for c in changes):
        raise ValueError("CARRY cannot change causal state")


def sequence_authoring_evidence_hash(*, loaded, binding, accepted_media, target_request_hash, changes):
    """Use one authoring seal at construction and Production reopen."""
    return canonical_sha256({"storyboard": loaded.storyboard.content_hash,
        "source_execution_binding": binding.binding_hash, "accepted_media": accepted_media,
        "target_request": target_request_hash,
        "causal_state_changes": [c.model_dump(mode="json") for c in changes]})


def require_sequence_source(*, loaded, routing, requirement, lifecycle):
    """Reopen exact activation evidence; a pointer alone is never authority."""
    if routing.source_activation_registry is None:
        raise ValueError("sequence activation pointer is required for new execution")
    policy = routing.transition_policy
    identity = policy.target_shot
    target = next((s for s in loaded.shots if (s.artifact_id, s.revision, s.content_hash)
        == (identity.artifact_id, identity.revision, identity.content_hash)), None)
    if (target is None or target != requirement.target_shot
            or policy.project != loaded.manifest.active_project
            or policy.registry != loaded.manifest.active_registry
            or lifecycle.base_project != loaded.manifest.active_project
            or lifecycle.base_registry != loaded.manifest.active_registry
            or lifecycle.base_dependency_graph != loaded.manifest.active_dependency_graph):
        raise ValueError("sequence target snapshot is stale")
    order = tuple(i for beat in loaded.storyboard.beats for i in beat.shot_ids)
    index = order.index(target.shot_id)
    if index == 0:
        raise ValueError("sequence activation requires an adjacent source")
    source = next(s for s in loaded.shots if s.shot_id == order[index - 1])
    accepted = accepted_sequence_source(loaded, source,
        require_causal_close=policy.continuity_obligation is ContinuityObligation.FULL_CONTINUITY)
    binding, request, _, accepted_hashes, registry = accepted
    if (routing.previous_shot != binding.projection.requirement.target_shot
            or routing.previous_provider_bound_request != binding.decision.routing.provider_bound_request
            or policy.source_generation_intent_hash != binding.projection.requirement.generation_intent_hash
            or policy.target_generation_intent_hash != requirement.generation_intent_hash
            or routing.source_activation_registry != registry):
        raise ValueError("sequence source activation or intent is stale")
    if (request.execution_stack_hash != policy.source_execution_stack_hash
            or lifecycle.execution_stack_hash != policy.destination_execution_stack_hash):
        raise ValueError("sequence execution stack is stale")
    if policy.source_execution_stack_hash != policy.destination_execution_stack_hash:
        from ai_video.production.generation_execution import require_sequence_destination_selection
        selection = require_sequence_destination_selection(selection=routing.destination_selection_binding,
            target_shot=target, target_generation_intent_hash=requirement.generation_intent_hash,
            destination_execution_stack=routing.destination_execution_stack, lifecycle=lifecycle,
            destination_route=routing.destination_route, project=loaded)
        if policy.authoring_evidence_hash != sequence_authoring_evidence_hash(
                loaded=loaded, binding=binding, accepted_media=accepted_hashes,
                target_request_hash=selection.projection.requirement.source_request_content_hash,
                changes=policy.causal_state_changes):
            raise ValueError("sequence authoring evidence seal has a stale planning seed")
    require_causal_columns(policy.causal_state_changes,
        binding.projection.requirement.generation_intent, requirement.generation_intent)
    if loaded.qa_policy is None or policy.qa_policy_hash != loaded.qa_policy.content_hash:
        raise ValueError("sequence QA policy is stale")
    return accepted
