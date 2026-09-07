from __future__ import annotations

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production_planning import ProductionPlanningService
from ai_video.production.project import load_production_project
from production_strategy_factory import make_persisted_strategy_fixture


def test_qualified_reuse_materializes_reopens_and_resolves_audio_caption_timeline(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)

    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    assert decision.disposition == "selected"
    assert decision.selected is not None
    assert decision.selected.new_generation_count == 0
    assert decision.selected.operations

    service.materialize(decision=decision, attempt_id="strategy-materialize")
    reopened = load_production_project(tmp_path / "project.yaml")
    child = next(shot for shot in reopened.shots if shot.shot_id == fixture.child_shot_id)
    assert child.production_lineage is not None
    assert child.production_lineage.parent_shot_id == fixture.parent_shot_id

    spec, timeline = service.composition(
        decision=decision, renderer_version="hyperframes-test/1",
    )
    assert spec.schema_version == "2.1"
    assert spec.shot_ids == (fixture.child_shot_id,)
    assert len(timeline.visual_spans) == 1
    assert timeline.visual_spans[0].duration_frames == 72
    assert len(timeline.audio_spans) == 1
    assert len(timeline.caption_cues) == 2


def test_stale_decision_does_not_start_a_commit_attempt(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    stale = decision.model_copy(update={"input_hash": "0" * 64})
    before = (tmp_path / "state/manifest.json").read_bytes()

    with pytest.raises(AiVideoError) as error:
        service.materialize(decision=stale, attempt_id="strategy-stale")
    assert error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert (tmp_path / "state/manifest.json").read_bytes() == before


def test_reuse_component_cannot_reach_generation_orchestration(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="strategy-materialize")

    with pytest.raises(AiVideoError) as error:
        service.prepare_generation(
            component_shot_id=fixture.child_shot_id,
            context_loader=lambda *_: (_ for _ in ()).throw(AssertionError("must not load context")),
            limits=object(), generation_policy=object(),
        )
    assert error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_failed_source_qualification_blocks_strategy_selection(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path, source_verdict="FAIL")
    decision = ProductionPlanningService(committer=fixture.committer).prepare(
        parent_shot_id=fixture.parent_shot_id,
    )

    assert decision.selected is None
    assert decision.disposition == "evidence_required"
    assert "evidence_required:source_fail" in decision.reasons


def test_reassessment_reopens_same_intent_and_can_rematerialize_without_losing_family(tmp_path):
    from types import SimpleNamespace

    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    first = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=first, attempt_id="first-production")
    resumed = ProductionPlanningService(committer=fixture.committer)
    next_decision = resumed.reassess_generation(component_shot_id=fixture.child_shot_id,
        prepared_generation=SimpleNamespace(target_shot_id=fixture.child_shot_id,
            decision=SimpleNamespace(disposition="SPLIT_SHOT")))
    assert next_decision.parent_shot_content_hash == first.parent_shot_content_hash
    assert next_decision.task_id == first.task_id
    assert next_decision.input_hash != first.input_hash
    resumed.materialize(decision=next_decision, attempt_id="reassessed-production")
    loaded = load_production_project(tmp_path / "project.yaml")
    assert loaded.shots[0].revision == 2
    assert loaded.shots[0].production_lineage.parent.content_hash == first.parent_shot_content_hash
    assert len([a for a in loaded.manifest.attempts if a.attempt_id in
                {"first-production", "reassessed-production"}]) == 2


def test_later_source_failure_blocks_old_composition_with_current_policy(tmp_path):
    import json
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.source_use_evidence import SourceUseEvidence
    from ai_video.production.composition import resolve_composition
    from ai_video.production.production_strategy_materialization import build_strategy_composition

    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="source-qualified")
    loaded = load_production_project(tmp_path / "project.yaml")
    evidence = loaded.qa_policy.production_source_evidence[0]
    raw = json.loads(evidence.response_json)
    raw["observations"][0]["verdict"] = "FAIL"
    failed = SourceUseEvidence.model_validate({**evidence.model_dump(),
        "evidence_id": "later-failure", "response_json": json.dumps(raw)})
    policy = seal_artifact(loaded.qa_policy.model_copy(update={"revision": loaded.qa_policy.revision + 1,
        "production_source_evidence": (*loaded.qa_policy.production_source_evidence, failed)}))
    fixture.committer.activate_qa_policy(policy,
        expected_manifest_revision=loaded.manifest.manifest_revision, attempt_id="later-source-review")
    current = load_production_project(tmp_path / "project.yaml")
    spec = build_strategy_composition(loaded=current, decision=decision)
    with pytest.raises(AiVideoError, match="not currently qualified"):
        resolve_composition(current, spec, "hyperframes-test/1")


@pytest.mark.parametrize("change", ["window", "transform", "audio"])
def test_actual_composition_cannot_change_qualified_source_use(tmp_path, change):
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.composition import resolve_composition
    from ai_video.production.production_strategy_materialization import build_strategy_composition

    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="qualified-window")
    current = load_production_project(tmp_path / "project.yaml")
    spec = build_strategy_composition(loaded=current, decision=decision)
    if change == "window":
        spec = spec.model_copy(update={"layers": (spec.layers[0].model_copy(update={"trim_start_frame": 20}),)})
    elif change == "transform":
        transform = spec.layers[0].transform.model_copy(update={"translate_x_px": 20})
        spec = spec.model_copy(update={"layers": (spec.layers[0].model_copy(update={"transform": transform}),)})
    else:
        spec = spec.model_copy(update={"audio_tracks": (spec.audio_tracks[0].model_copy(update={"start_sample": 20}),)})
    with pytest.raises(AiVideoError, match="Actual composition"):
        resolve_composition(current, seal_artifact(spec), "hyperframes-test/1")


def test_explicit_allocation_revision_remains_readable_and_reassessable(tmp_path):
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.generation_recipe import RequirementExpression
    from test_production_generation_decision import acceptance_policy

    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    first = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=first, attempt_id="before-allocation-change")
    current = load_production_project(tmp_path / "project.yaml")
    old_pointer = current.shots[0].production_lineage.allocation_policy
    allocation = current.qa_policy.production_allocations[0]
    raw_policy = acceptance_policy((RequirementExpression(requirement_id="visual", level="acceptance",
        stage="raw_generation", dimension="action", observable="visible action", tolerance="exact",
        measurement="probe", proof="technical", production_owner="generation"),))
    allocation = allocation.model_copy(update={"components": (
        allocation.components[0].model_copy(update={"generation_acceptance": raw_policy}),
        *allocation.components[1:])})
    qa = seal_artifact(current.qa_policy.model_copy(update={"revision": current.qa_policy.revision + 1,
        "production_allocations": (allocation,)}))
    fixture.committer.activate_qa_policy(qa,
        expected_manifest_revision=current.manifest.manifest_revision, attempt_id="new-allocation")
    reopened = load_production_project(tmp_path / "project.yaml")
    assert reopened.shots[0].production_lineage.allocation_policy == old_pointer
    revised = service.prepare(parent_shot_id=fixture.child_shot_id)
    assert revised.selected.allocation_hash == allocation.allocation_hash
    service.materialize(decision=revised, attempt_id="apply-new-allocation")
    latest = load_production_project(tmp_path / "project.yaml")
    assert latest.shots[0].production_lineage.allocation_policy == latest.manifest.active_qa_policy
    assert (tmp_path / old_pointer.path).is_file()


@pytest.mark.parametrize("change", ["remove", "scope"])
def test_global_production_caption_must_survive_actual_composition(tmp_path, change):
    from ai_video.production.hashing import seal_artifact
    from ai_video.production.composition import resolve_composition

    fixture = make_persisted_strategy_fixture(tmp_path, global_caption=True)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="global-caption")
    spec, timeline = service.composition(decision=decision, renderer_version="hyperframes-test/1")
    assert len(timeline.caption_cues) == 2
    binding = spec.caption_tracks[0]
    assert binding.shot_id is None
    tracks = () if change == "remove" else (binding.model_copy(update={"shot_id": fixture.child_shot_id}),)
    changed = seal_artifact(spec.model_copy(update={"caption_tracks": tracks}))
    loaded = load_production_project(tmp_path / "project.yaml")
    with pytest.raises(AiVideoError, match="Actual composition captions"):
        resolve_composition(loaded, changed, "hyperframes-test/1")
