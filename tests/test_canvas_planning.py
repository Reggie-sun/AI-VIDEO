"""Canvas planning consumes actual accepted sources through the sequence owner."""
import pytest

from ai_video.canvas_planning import canvas_feedback_context
from ai_video.production.project import load_production_project
from ai_video.production.video_transition import BoundaryKind, CausalEdgeSemantics, ContinuityObligation
from test_planning_sequence_continuity import activated_source, _edge_inputs


@pytest.mark.parametrize("kind", ["continuous", "hard_cut", "reset"])
def test_director_data_reaches_real_sequence_source_and_current_router_context(activated_source, kind):
    kwargs = {}
    if kind == "continuous":
        kwargs.update(boundary=BoundaryKind.WITHIN_CONTINUOUS_TAKE, roles=())
    elif kind == "reset":
        kwargs.update(obligation=ContinuityObligation.SUBSTANTIAL_RESET,
            boundary=BoundaryKind.SCENE_BOUNDARY, semantics=CausalEdgeSemantics.SCENE_RESET)
    inputs = _edge_inputs(activated_source, **kwargs)
    loaded = load_production_project(activated_source["root"] / "project.yaml")
    seed = inputs["current_request"]
    generation = seed.generation_intent.model_dump(mode="json", exclude={"projection_hash", "contract_version"})
    generation["references"] = []
    generation["intent_evidence"] = {"character_action_required": True}
    edge = {k: inputs[k].value for k in ("boundary_kind", "continuity_obligation", "causal_edge_semantics")}
    edge.update(causal_state_changes=[c.model_dump(mode="json") for c in inputs["causal_state_changes"]],
        required_carryover_dimensions=list(inputs["required_carryover_dimensions"]), take_id=inputs["take_id"])
    row = {"shot": {"shot_id": seed.target_shot.shot_id}, "generation": generation, "boundary": edge}
    def materialized_handoff(current, decisions, accepted, lifecycle):
        assert accepted.projection == activated_source["binding"].projection
        return {"lifecycle": inputs["lifecycle"], "anchors": inputs["anchors"], "current_request": seed}
    current = canvas_feedback_context(loaded=loaded, row=row, policy=activated_source["binding"].policy,
        execution_stack=activated_source["stack"], handoff_preparer=materialized_handoff)
    assert current["continuity_routing"].transition_policy.continuity_obligation.value == edge["continuity_obligation"]
    assert current["projection"].requirement.target_shot == seed.target_shot
    assert current["planning_request"].target_shot == seed.target_shot
    if kind == "continuous":
        assert current["context"].upstream_terminal.asset_id == activated_source["terminal"].extracted_asset_id
    elif kind == "hard_cut":
        assert current["context"].shot_keyframe.asset_id == inputs["lifecycle"].hard_cut_keyframe_binding.keyframe_asset_id
    else:
        assert current["projection"].requirement.continuity_mode.value == "none"


def test_missing_materialized_execution_stack_is_not_silently_independent(activated_source):
    inputs = _edge_inputs(activated_source)
    row = {"shot": {"shot_id": inputs["current_request"].target_shot.shot_id},
        "generation": {"generation_intent": {"subject_action": {"progression": "continue walking right"}},
                       "audio_need": "forbidden", "quality_need": {}},
        "boundary": {"causal_state_changes": [c.model_dump(mode="json") for c in inputs["causal_state_changes"]]}}
    with pytest.raises(ValueError, match="execution stack"):
        canvas_feedback_context(loaded=load_production_project(activated_source["root"] / "project.yaml"),
            row=row, policy=activated_source["binding"].policy)


@pytest.mark.parametrize("preserved_source,explicit_mode,accepts_nominal", [
    (True, None, True),
    (True, "fixed", False),
    (False, None, False),
])
def test_canvas_timing_default_accepts_nominal_without_changing_explicit_exact(
    tmp_path, preserved_source, explicit_mode, accepts_nominal,
):
    from copy import deepcopy
    from ai_video.canvas_authoring import author_canvas_project
    from ai_video.canvas_dependencies import initialize_canvas_graph
    from ai_video.production.hashing import canonical_sha256
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production._video_requirement_routing import requirement_output_matches
    from ai_video.production.video_contracts import VideoFlexibleOutputRequirement
    from test_canvas_authoring import direction
    from test_canvas_sequence_packet import document
    from test_production_shot_router import _policy
    from scripts.canvas_sequence_packet import build_sequence_packet

    raw = document()
    raw["edges"] = []
    for node in raw["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft is not None:
            draft["parts"] = [p for p in draft["parts"] if p["type"] == "text"]
            draft["references"] = []
    packet = build_sequence_packet(raw, {"node_ids": ["a", "b"]})
    data = direction()
    data["delivery_profile"] = {"width": 854, "height": 480, "fps": 24}
    row = data["shots"][0]
    row["shot"]["duration_policy"]["seconds"] = 15
    if preserved_source:
        parts = packet["units"][0]["prompt_source"]["parts"]
        row["shot"]["intent"] = "".join(p["text"] for p in parts)
        row["shot"]["preserved_source_expression"] = {
            "source_sha256": canonical_sha256({"parts": parts, "implicit_references": []}),
            "parts": parts,
        }
    row["generation"] = {
        "generation_intent": {"subject_action": {"progression": row["shot"]["intent"]}},
        "audio_need": "forbidden", "quality_need": {},
    }
    if explicit_mode is not None:
        row["generation"]["output_need"] = {"timing_mode": explicit_mode, "duration_seconds": 15,
            "width": 854, "height": 480, "fps": 24, "container_mime": "video/mp4"}
    bundle = author_canvas_project(packet=packet, direction=data)
    committer = ProductionStateCommitter(tmp_path)
    bundle.bootstrap(committer=committer, attempt_id="timing-default")
    initialize_canvas_graph(committer, "timing-default-graph")
    loaded = load_production_project(tmp_path / "project.yaml")
    original = deepcopy(row)
    context = canvas_feedback_context(loaded=loaded, row=row, policy=_policy())
    requirement = context["projection"].requirement
    nominal = VideoFlexibleOutputRequirement(
        timing_mode="nominal_seconds", duration_seconds=15, dimension_mode="exact",
        width=854, height=480, resolution_label="480p", ratio="16:9", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=False,
    )
    assert requirement_output_matches(requirement, nominal) is accepts_nominal
    assert not requirement_output_matches(
        requirement, nominal.model_copy(update={"duration_seconds": 14}),
    )
    assert row == original
