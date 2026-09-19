"""Truthful asset-free dependency readiness for one generated-video Shot."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_video.production._dependency_authoring import (
    build_authoring_dependency_projection,
)
from ai_video.production._dependency_primitives import (
    fingerprint_items as _items,
    fingerprint_value as _fp,
    shot_projection_node_id,
)
from ai_video.production.dependency import (
    build_dependency_graph,
    desired_fingerprints,
)
from ai_video.production.models import (
    AssetType,
    DependencyEdge,
    DependencyGraphSnapshot,
    DependencyLifecycle,
    DependencyNode,
    DependencyNodeKind,
    DependencyNodeState,
    DependencyReason,
    DependencySemanticRole,
    FingerprintContribution,
    LoadedProductionProject,
    ProjectDependencyEvidence,
    VisualStrategy,
)
from ai_video.production.video import ResolvedVideoGenerationRequest


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def verified_fetched_prior_for_new_goal(committer, loaded, prior):
    """Reopen a fully NE paid result retained under an explicit new goal version.

    This admits preparation only; it neither ends the prior attempt nor admits
    a submit. The graph, budget and quota owners retain their own write gates.
    """
    from ai_video.errors import AiVideoError
    from ai_video.production.models import PaidProviderAttemptPhase, StateCommitStatus, VideoAttemptPhase

    state = prior.video_generation_state
    if (prior.status is not StateCommitStatus.RUNNING or state is None
            or state.phase is not VideoAttemptPhase.VALIDATE
            or state.fetch_receipt is None or state.local_fetch_receipt is not None
            or state.execution_binding is None or not state.generation_experiences
            or prior.paid_provider_state is None
            or prior.paid_provider_state.phase is not PaidProviderAttemptPhase.ACCEPTED
            or prior.paid_provider_state.submit_receipt != state.paid_submit_receipt
            or loaded.qa_policy is None or loaded.qa_policy.final_output is None):
        return None
    try:
        binding = committer._reopen_generation_execution_binding(state.execution_binding)
        request = committer._reopen_video_request(state.request)
        binding.validate_request(request)
        candidate = next(c for c in binding.inputs.candidates
                         if c.candidate_id == binding.decision.selected_candidate_id)
        old_goal, new_goal = candidate.final_output_goal, loaded.qa_policy.final_output
        if (old_goal is None or old_goal.goal_id != new_goal.goal_id
                or old_goal.goal_version == new_goal.goal_version
                or binding.inputs.rubric_hash
                == loaded.qa_policy.selected_generation_acceptance().profile_content_hash):
            return None
        fetched = committer._reopen_video_fetch(state.fetch_receipt)
        submit = committer._reopen_paid_submit(state.paid_submit_receipt)
        if (submit.outcome.value != "accepted"
                or submit.request_fingerprint != request.resolved_generation_hash
                or fetched.paid_submit_receipt_fingerprint != submit.submit_receipt_fingerprint):
            return None
        experiences = tuple(committer._reopen_generation_experience(p)
                            for p in state.generation_experiences)
        from ai_video.production.generation_evaluation import validate_generation_evaluation_sources

        for experience in experiences:
            if (experience.projection != binding.projection
                    or experience.candidate != candidate
                    or not experience.evaluation_sources):
                return None
            snapshot = experience.evaluation_sources[0].qa_policy_snapshot
            if snapshot is None:
                return None
            for evidence in experience.evidence:
                if (evidence.outcome != "media" or evidence.attempt_id != prior.attempt_id
                        or evidence.request_hash != request.request_input_hash
                        or evidence.artifact_sha256 != fetched.artifact_sha256
                        or evidence.rubric_hash != binding.inputs.rubric_hash):
                    return None
                validate_generation_evaluation_sources(
                    sources=experience.evaluation_sources, evidence=evidence,
                    qa_policy=snapshot, size_bytes=fetched.size_bytes,
                    acceptance=candidate.recipe.acceptance_policy,
                )
        required = {r.requirement_id for r in candidate.recipe.expressions
                    if r.level == "acceptance" and r.stage == "raw_generation"}
        sources = tuple(s for x in experiences for s in x.evaluation_sources)
        if (not required or not sources
                or any(o.verdict != "NOT_EVALUATED" for s in sources for o in s.observations)
                or not required <= {o.requirement_id for s in sources for o in s.observations}):
            return None
        matching = [e for x in experiences for e in x.evidence
                    if e.outcome == "media" and e.attempt_id == prior.attempt_id
                    and e.request_hash == request.request_input_hash
                    and e.artifact_sha256 == fetched.artifact_sha256
                    and e.rubric_hash == binding.inputs.rubric_hash]
        if not matching:
            return None
        return binding, request, experiences
    except (AiVideoError, AttributeError, OSError, StopIteration, TypeError, ValueError):
        return None


def permits_prospective_target_transition(committer, manifest, request, graph):
    """Allow only a pending generation-target graph change over one retained NE result."""
    from ai_video.production.models import StateCommitStatus
    from ai_video.production.project import load_production_project

    unresolved = tuple(a for a in manifest.attempts if a.status in {
        StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN})
    if (len(unresolved) != 1 or graph is None
            or request.operation != "commit_project_registry"
            or request.next_project != manifest.active_project
            or request.next_registry != manifest.active_registry):
        return False
    loaded = load_production_project(committer.project_root / "project.yaml")
    if loaded.manifest != manifest:
        return False
    verified = verified_fetched_prior_for_new_goal(committer, loaded, unresolved[0])
    if verified is None:
        return False
    binding, prior_request, _ = verified
    role = prior_request.activation_scope.request.target_asset_role
    node_id = generation_target_node_id(binding.context.target_shot_id, role)
    for candidate in (loaded.dependency_graph, graph):
        if candidate is None:
            return False
        target = next((n for n in candidate.nodes if n.node_id == node_id), None)
        if target is None:
            return False
        contributions = {c.key: c.fingerprint for c in target.contributions}
        try:
            expected = build_video_pre_generation_dependency_graph(VideoPreGenerationDependencyInputs(
                project=loaded, target_shot_id=binding.context.target_shot_id,
                target_asset_role=role,
                requirement_hash=contributions["generation_target.requirement"],
                planning_request_hash=contributions["generation_target.planning_request"],
                verified_projection_hash=contributions["generation_target.verified_projection"],
            ))
        except (KeyError, ValueError):
            return False
        if candidate != expected:
            return False
    allowed_paths = {manifest.active_project.path, manifest.active_registry.path,
                     request.dependency_graph_transition.candidate_dependency_graph.path}
    return (graph != loaded.dependency_graph
            and all(a.relative_path in allowed_paths for a in request.artifacts))


@dataclass(frozen=True)
class VideoPreGenerationDependencyInputs:
    project: LoadedProductionProject
    target_shot_id: str
    target_asset_role: str
    requirement_hash: str
    planning_request_hash: str
    verified_projection_hash: str


def generation_target_node_id(shot_id: str, asset_role: str) -> str:
    """Return the canonical pending generation-target node identity."""

    if not shot_id or not asset_role:
        raise ValueError("generation target requires non-empty Shot and asset role")
    return f"generation-target:{shot_id}:{asset_role}"


def _validated_target(inputs: VideoPreGenerationDependencyInputs):
    if any(
        _SHA256.fullmatch(value) is None
        for value in (
            inputs.requirement_hash,
            inputs.planning_request_hash,
            inputs.verified_projection_hash,
        )
    ):
        raise ValueError("pre-generation lineage hashes must be SHA-256 values")
    project = inputs.project
    if (
        project.manifest.active_project.revision != project.project.revision
        or project.manifest.active_project.content_hash != project.project.content_hash
        or project.manifest.active_registry.revision_id != project.registry.revision_id
        or project.manifest.active_registry.content_hash != project.registry.content_hash
    ):
        raise ValueError("pre-generation project and Registry must be active and exact")
    shots = tuple(
        shot for shot in project.shots if shot.shot_id == inputs.target_shot_id
    )
    if len(shots) != 1:
        raise ValueError("pre-generation target Shot identity is ambiguous")
    shot = shots[0]
    roles = tuple(
        role
        for role in shot.required_asset_roles
        if role.role == inputs.target_asset_role
    )
    if (
        shot.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        or len(roles) != 1
        or roles[0].asset_ids
        or roles[0].allowed_asset_types != (AssetType.VIDEO,)
    ):
        raise ValueError(
            "pre-generation target must be one empty generated-video role"
        )
    return shot


def build_video_pre_generation_dependency_graph(
    inputs: VideoPreGenerationDependencyInputs,
) -> DependencyGraphSnapshot:
    """Build one exact pending-video target without inventing media or render state."""

    shot = _validated_target(inputs)
    authoring = build_authoring_dependency_projection(inputs.project)
    target_id = generation_target_node_id(
        inputs.target_shot_id, inputs.target_asset_role
    )
    target = DependencyNode(
        node_id=target_id,
        kind=DependencyNodeKind.GENERATION_TARGET,
        semantic_role=DependencySemanticRole.VISUAL,
        artifact_id=shot.artifact_id,
        artifact_revision=shot.revision,
        contributions=_items(
            **{
                "generation_target.asset_role": _fp(
                    "ai-video-generation-target-asset-role/1",
                    inputs.target_asset_role,
                ),
                "generation_target.planning_request": inputs.planning_request_hash,
                "generation_target.requirement": inputs.requirement_hash,
                "generation_target.verified_projection": inputs.verified_projection_hash,
            }
        ),
    )
    source_id = authoring.shot_projection_ids[
        (inputs.target_shot_id, DependencySemanticRole.VISUAL)
    ]
    edge = DependencyEdge(
        source_node_id=source_id,
        target_node_id=target_id,
        reason=DependencyReason.GENERATION_INPUT,
        contribution=FingerprintContribution(
            key="video.pre_generation_target",
            fingerprint=_fp(
                "ai-video-edge-video.pre_generation_target/1",
                {
                    "shot_id": inputs.target_shot_id,
                    "shot_revision": shot.revision,
                    "shot_content_hash": shot.content_hash,
                    "asset_role": inputs.target_asset_role,
                    "requirement_hash": inputs.requirement_hash,
                },
            ),
        ),
    )
    return build_dependency_graph(
        (*authoring.nodes, target),
        (*authoring.edges, edge),
    )


def build_video_pre_generation_applied_evidence(
    inputs: VideoPreGenerationDependencyInputs,
) -> tuple[DependencyNodeState, ...]:
    """Project only exact current authoring bytes as applied evidence."""

    graph = build_video_pre_generation_dependency_graph(inputs)
    desired = desired_fingerprints(graph)
    pointer = inputs.project.manifest.active_project
    return tuple(
        DependencyNodeState(
            node_id=node.node_id,
            graph_revision_id=graph.revision_id,
            desired_fingerprint=desired[node.node_id],
            applied_fingerprint=desired[node.node_id],
            lifecycle=DependencyLifecycle.FRESH,
            applied_evidence=ProjectDependencyEvidence(
                owner="project_snapshot",
                pointer=pointer,
                artifact_id=node.artifact_id,
                artifact_fingerprint=desired[node.node_id],
            ),
        )
        for node in graph.nodes
        if node.kind is DependencyNodeKind.CREATIVE_ARTIFACT
    )


def verify_current_video_generation_lineage(
    project: LoadedProductionProject,
    request: ResolvedVideoGenerationRequest,
) -> None:
    """Fail closed before request persistence when current lineage drifted."""

    graph = project.dependency_graph
    targets = (
        ()
        if graph is None
        else tuple(
            node
            for node in graph.nodes
            if node.kind is DependencyNodeKind.GENERATION_TARGET
        )
    )
    if not targets:
        return
    scope = request.activation_scope
    if scope is None:
        raise ValueError("pre-generation request requires an activation scope")
    sealed = scope.request
    if (
        sealed.base_project != project.manifest.active_project
        or sealed.base_registry != project.manifest.active_registry
        or sealed.base_dependency_graph != project.manifest.active_dependency_graph
    ):
        raise ValueError("video request base Project, Registry, or graph is stale")
    shots = tuple(
        shot for shot in project.shots if shot.shot_id == sealed.target_shot_id
    )
    if len(shots) != 1:
        raise ValueError("video request target Shot is not current and unique")
    shot = shots[0]
    roles = tuple(
        role
        for role in shot.required_asset_roles
        if role.role == sealed.target_asset_role
    )
    if (
        sealed.target_shot_revision != shot.revision
        or sealed.target_shot_content_hash != shot.content_hash
        or shot.visual_strategy is not VisualStrategy.GENERATED_VIDEO
        or len(roles) != 1
        or roles[0].asset_ids
        or roles[0].allowed_asset_types != (AssetType.VIDEO,)
    ):
        raise ValueError("video request target Shot or role is stale")

    assert graph is not None
    expected_id = generation_target_node_id(
        sealed.target_shot_id, sealed.target_asset_role
    )
    if len(targets) != 1 or targets[0].node_id != expected_id:
        raise ValueError("active pre-generation target is not exact and unique")
    target = targets[0]
    contributions = {item.key: item.fingerprint for item in target.contributions}
    if (
        sealed.requirement_hash is None
        or target.artifact_id != shot.artifact_id
        or target.artifact_revision != shot.revision
        or contributions.get("generation_target.asset_role")
        != _fp("ai-video-generation-target-asset-role/1", sealed.target_asset_role)
        or contributions.get("generation_target.requirement")
        != sealed.requirement_hash
        or set(contributions)
        != {
            "generation_target.asset_role",
            "generation_target.planning_request",
            "generation_target.requirement",
            "generation_target.verified_projection",
        }
    ):
        raise ValueError("video request does not match the active generation target")
    expected = build_video_pre_generation_dependency_graph(
        VideoPreGenerationDependencyInputs(
            project=project,
            target_shot_id=sealed.target_shot_id,
            target_asset_role=sealed.target_asset_role,
            requirement_hash=sealed.requirement_hash,
            planning_request_hash=contributions[
                "generation_target.planning_request"
            ],
            verified_projection_hash=contributions[
                "generation_target.verified_projection"
            ],
        )
    )
    if graph != expected:
        raise ValueError("active pre-generation graph is not canonical and exact")
    states = tuple(
        state
        for state in project.manifest.dependency_states
        if state.node_id == expected_id
    )
    if (
        len(states) != 1
        or states[0].graph_revision_id != graph.revision_id
        or states[0].desired_fingerprint
        != desired_fingerprints(graph)[expected_id]
        or states[0].lifecycle is not DependencyLifecycle.STALE
        or states[0].applied_evidence is not None
        or states[0].blocked_by
    ):
        raise ValueError("active generation target is not submit-ready")
    active_states = {
        state.node_id: state
        for state in project.manifest.dependency_states
        if state.node_id in {node.node_id for node in graph.nodes}
    }
    if set(active_states) != {node.node_id for node in graph.nodes} or any(
        state.lifecycle is not DependencyLifecycle.FRESH
        for node_id, state in active_states.items()
        if node_id != expected_id
    ):
        raise ValueError("active pre-generation authoring state is not fully fresh")
