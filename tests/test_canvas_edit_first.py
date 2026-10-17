"""Public Canvas uses the canonical production planner before quality regeneration."""
import pytest

from ai_video.canvas_authoring import direction_reference
from ai_video.canvas_production import CanvasProductionService
from ai_video.errors import AiVideoError
from ai_video.production.hashing import seal_artifact
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import prepare_project_registry_commit
from production_strategy_factory import make_persisted_strategy_fixture


def strategy_canvas(tmp_path):
    fixture = make_persisted_strategy_fixture(tmp_path)
    loaded = load_production_project(tmp_path / "project.yaml")
    packet = {"fixture": "canvas-strategy"}
    direction = {"project_id": loaded.project.project_id, "shots": [
        {"occurrence_id": shot_id, "shot": {"shot_id": shot_id}}
        for beat in loaded.storyboard.beats for shot_id in beat.shot_ids]}
    project = seal_artifact(loaded.project.model_copy(update={
        "revision": loaded.project.revision + 1, "content_hash": "0" * 64,
        "source_provenance": (*loaded.project.source_provenance, direction_reference(packet, direction))}))
    request = prepare_project_registry_commit(manifest=loaded.manifest, project=project,
        registry=loaded.registry, attempt_id="canvas-binding")
    from ai_video.production.production_strategy_dependency import prepare_strategy_dependency_transition
    request = prepare_strategy_dependency_transition(base_loaded=loaded,
        candidate_loaded=loaded.model_copy(update={"project": project}), request=request)
    fixture.committer.commit(request)
    return fixture, CanvasProductionService(committer=fixture.committer, packet=packet, direction=direction)


def test_canvas_plans_materializes_and_reopens_existing_owner_without_generation(tmp_path):
    fixture, service = strategy_canvas(tmp_path)
    before = (tmp_path / "state/manifest.json").read_bytes()
    assert service.position().next_action == "prepare_production"
    decision = service.prepare_production(parent_shot_id=fixture.parent_shot_id)
    assert decision.selected is not None and decision.selected.new_generation_count == 0
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    service.materialize_production(decision=decision.model_dump(mode="json"), attempt_id="canvas-means")
    assert service._load().shots[0].shot_id == fixture.child_shot_id
    spec, timeline = service.compose_production(decision=decision.model_dump(mode="json"))
    assert spec.shot_ids == (fixture.child_shot_id,)
    assert timeline.visual_spans[0].asset_id == decision.selected.units[0].source.asset_id
    assert not any(a.video_generation_state for a in service._load().manifest.attempts)


@pytest.mark.parametrize("action", ["prepare_repair", "start_repair"])
@pytest.mark.parametrize("include_generation_intervention", [True, False])
def test_closed_quality_cannot_skip_editing_authoring_and_regenerate(tmp_path, action, include_generation_intervention):
    from test_canvas_recovery import failed_canvas, close_failure
    service, provider, limits, old, _, intervention = failed_canvas(tmp_path)
    close_failure(service, old)
    before = (service.committer.project_root / "state/manifest.json").read_bytes()
    history = service.committer.read_generation_experiences()
    with pytest.raises(AiVideoError, match="ProductionIntent.*existing-source/edit"):
        getattr(service, action)(limits=limits, interventions=(intervention,) if include_generation_intervention else ())
    assert (service.committer.project_root / "state/manifest.json").read_bytes() == before
    assert service.committer.read_generation_experiences() == history
    assert provider.call_counts.submit == 1  # Only the scripted predecessor.


def test_canvas_time_map_requires_explicit_mute_and_preserves_resolved_segments(tmp_path):
    from ai_video.canvas_composition import compose_canvas
    from production_project_factory import make_loaded_project_and_spec
    from test_production_video_retime import _with_video_layer, _time_map
    loaded, spec = make_loaded_project_and_spec(tmp_path)
    loaded, spec = _with_video_layer(tmp_path, loaded, spec)
    mapping = _time_map((0, 0), (24, 12), (60, 48))
    rows = [{"occurrence_id": layer.shot_id, "shot": {"shot_id": layer.shot_id},
             "composition": {"asset_role": layer.asset_role, "asset_id": layer.asset_id}}
            for layer in spec.layers]
    rows[0]["composition"].update(trim_start_frame=12, trim_duration_frames=60,
        source_time_map=mapping.model_dump(mode="json"))
    with pytest.raises(ValueError, match="explicit muted"):
        compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103")
    rows[0]["composition"]["muted"] = True
    authored, timeline = compose_canvas(loaded=loaded, direction={"shots": rows}, renderer_version="0.7.103")
    assert authored.schema_version == timeline.schema_version == "2.3"
    pieces = [s for s in timeline.visual_spans if s.shot_id == rows[0]["shot"]["shot_id"]]
    assert [(s.trim_start_frame, s.trim_duration_frames, s.duration_frames) for s in pieces[:12]] == [
        (12 + 2 * n, 1, 1) for n in range(12)]
    assert (pieces[-1].trim_start_frame, pieces[-1].trim_duration_frames, pieces[-1].duration_frames) == (36, 36, 36)
