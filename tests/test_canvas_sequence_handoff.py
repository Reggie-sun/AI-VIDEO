"""Canvas entry through real Production reader/committer fixtures; no live media."""
import pytest

from ai_video.errors import AiVideoError
from ai_video.planning import VideoPlanningRequest
from ai_video.production.video_requirement import OutputNeed, ProviderNeutralGenerationIntentProjection
from ai_video.production.project import load_production_project
from scripts.canvas_sequence_handoff import build_canvas_sequence_planning_request
from test_canvas_sequence_packet import document, boundary
from test_planning_sequence_continuity import activated_source, _activated_source, _edge_inputs, _identity


def inputs_for(source):
    existing = _edge_inputs(source)
    request = existing["current_request"]
    intent = request.generation_intent
    intent = ProviderNeutralGenerationIntentProjection.create(**{
        **{n: getattr(intent, n) for n in type(intent).model_fields if n != "projection_hash"},
        "output_need": OutputNeed(duration_seconds=1, width=640, height=480, fps=24, container_mime="video/mp4")})
    request = VideoPlanningRequest.create(**{
        **{n: getattr(request, n) for n in type(request).model_fields if n != "request_content_hash"},
        "generation_intent": intent})
    edge = boundary()
    for key in ("boundary_kind", "continuity_obligation", "causal_edge_semantics"):
        edge[key] = existing.pop(key).value
    edge["causal_state_changes"] = [c.model_dump(mode="json") for c in existing.pop("causal_state_changes")]
    edge["required_carryover_dimensions"] = list(existing.pop("required_carryover_dimensions"))
    loaded = load_production_project(existing["project_root"] / "project.yaml")
    bindings = {"a": _identity(loaded.shots[0]), "b": _identity(request.target_shot)}
    existing.pop("current_request")
    root = existing.pop("project_root")
    return dict(source=document(), selection={"node_ids": ["a", "b"], "boundaries": [edge]},
                project_root=root, current_request=request, target_occurrence_id="b",
                shot_bindings=bindings, execution_evidence=existing)


def test_canvas_handoff_reaches_canonical_owner(activated_source):
    args = inputs_for(activated_source)
    before = {str(p.relative_to(args["project_root"])): p.read_bytes()
              for p in args["project_root"].rglob("*") if p.is_file()}
    # Reader/adapter owns validation; source was actually activated by the fixture committer.
    request, route = build_canvas_sequence_planning_request(**args)
    assert request.previous_shot_state is not None
    assert request.continuity_transition_policy is not None
    assert route is not None
    assert len(request.continuity_transition_policy.causal_state_changes) == 10
    assert request.generation_intent.output_need.height == 480
    assert before == {str(p.relative_to(args["project_root"])): p.read_bytes()
                      for p in args["project_root"].rglob("*") if p.is_file()}


@pytest.mark.parametrize("damage", ["order", "stale", "missing", "conflict", "override", "resolution", "source_intent"])
def test_handoff_fails_closed(activated_source, damage):
    args = inputs_for(activated_source)
    if damage == "order":
        args["shot_bindings"] = {"a": args["shot_bindings"]["b"], "b": args["shot_bindings"]["a"]}
    elif damage == "stale":
        args["shot_bindings"]["a"] = args["shot_bindings"]["a"].model_copy(update={"content_hash": "f" * 64})
    elif damage == "missing":
        args["selection"]["boundaries"] = []
    elif damage == "conflict":
        args["selection"]["boundaries"][0]["source_analysis"] = {
            "source_quotes": ["生物遮满镜头"], "target_quotes": ["从遮挡中继续前冲"],
            "planned_source_close": "遮挡", "planned_target_open": "前冲", "carryover": [],
            "gaps": [], "conflicts": ["fixture unresolved conflict"]}
    elif damage == "override":
        args["execution_evidence"]["continuity_obligation"] = None
    elif damage == "resolution":
        args["resolution"] = "720p"
    else:
        args["execution_evidence"]["source_generation_intent_hash"] = "f" * 64
    with pytest.raises((ValueError, AiVideoError)):
        build_canvas_sequence_planning_request(**args)


def test_canvas_cannot_replace_missing_accepted_close_proof(tmp_path):
    source = _activated_source(tmp_path, close_verdict=None)
    with pytest.raises(AiVideoError):
        build_canvas_sequence_planning_request(**inputs_for(source))
