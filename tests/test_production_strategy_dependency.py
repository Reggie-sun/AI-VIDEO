from __future__ import annotations

import yaml
from dataclasses import replace

from ai_video.production_planning import ProductionPlanningService
from ai_video.production.dependency import DependencyLifecycle
from ai_video.production.models import ProductionProject, Shot, Storyboard
from ai_video.production.production_strategy_dependency import (
    prepare_strategy_dependency_transition,
)
from ai_video.production.production_strategy_materialization import prepare_strategy_commit
from ai_video.production.project import load_production_project
from production_strategy_factory import make_persisted_strategy_fixture


def _candidate_loaded(base, request):
    payloads = {artifact.relative_path: artifact.payload for artifact in request.artifacts}
    project_payload = next(
        payload for path, payload in payloads.items()
        if path.as_posix().startswith("state/projects/")
    )
    project = ProductionProject.model_validate(yaml.safe_load(project_payload))
    storyboard = Storyboard.model_validate(yaml.safe_load(
        payloads[project.artifacts.storyboard.path]
    ))
    shots = tuple(
        Shot.model_validate(yaml.safe_load(
            payloads[reference.path]
            if reference.path in payloads
            else (base.root / reference.path).read_bytes()
        ))
        for reference in project.artifacts.shots
    )
    return base.model_copy(update={
        "project": project,
        "storyboard": storyboard,
        "shots": shots,
    })


def _strategy_candidate(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    base = load_production_project(tmp_path / "project.yaml")
    decision = ProductionPlanningService(committer=fixture.committer).prepare(
        parent_shot_id=fixture.parent_shot_id,
    )
    prepared_request = prepare_strategy_commit(
        loaded=base, decision=decision, attempt_id="strategy-dependency"
    )
    assert prepared_request.dependency_graph_transition is not None
    graph_path = prepared_request.dependency_graph_transition.candidate_dependency_graph.path
    request = replace(
        prepared_request,
        dependency_graph_transition=None,
        artifacts=tuple(
            artifact for artifact in prepared_request.artifacts
            if artifact.relative_path != graph_path
        ),
    )
    candidate = _candidate_loaded(base, request)
    return fixture, base, candidate, request


def test_rebase_retires_old_render_domain_but_preserves_registered_assets(tmp_path):
    _, base, candidate, request = _strategy_candidate(tmp_path)
    prepared = prepare_strategy_dependency_transition(
        base_loaded=base,
        candidate_loaded=candidate,
        request=request,
    )
    transition = prepared.dependency_graph_transition
    assert transition is not None
    active_ids = {node.node_id for node in transition.candidate_dependency_states
                  if node.lifecycle is not DependencyLifecycle.SUPERSEDED}
    old_render_domain = {
        node.node_id for node in base.dependency_graph.nodes
        if node.node_id.startswith(("composition:", "timeline:", "renderer-source:", "render:"))
    }
    assert old_render_domain.isdisjoint(active_ids)
    assert {
        node.node_id
        for node in base.dependency_graph.nodes
        if node.node_id.startswith("asset:")
    } <= active_ids
    before = {s.node_id: s for s in base.manifest.dependency_states}
    after = {s.node_id: s for s in transition.candidate_dependency_states}
    for node_id in ("asset:image-shot-2", "asset:voice-narration"):
        assert after[node_id].desired_fingerprint == before[node_id].desired_fingerprint
        assert after[node_id].lifecycle == before[node_id].lifecycle == DependencyLifecycle.FRESH
    assert any(
        state.node_id in old_render_domain
        and state.lifecycle is DependencyLifecycle.SUPERSEDED
        for state in transition.candidate_dependency_states
    )


def test_transition_commits_graph_with_strategy_project_and_reopens_normally(tmp_path):
    fixture, base, candidate, request = _strategy_candidate(tmp_path)
    prepared = prepare_strategy_dependency_transition(
        base_loaded=base,
        candidate_loaded=candidate,
        request=request,
    )

    manifest = fixture.committer.commit(prepared)
    reopened = load_production_project(tmp_path / "project.yaml")

    assert reopened.manifest == manifest
    assert reopened.manifest.active_dependency_graph == prepared.dependency_graph_transition.candidate_dependency_graph
    assert any(shot.production_lineage is not None for shot in reopened.shots)
