"""Read-only canvas authoring handoff to existing sequence Planning ownership.

Caller supplies approved Shots and genuine execution evidence. This module never
authors Production state, infers accepted media, selects a route or submits work.
"""
from pathlib import Path

from ai_video.planning.sequence_continuity import build_sequence_video_planning_request
from ai_video.planning.video_planner import VideoPlanningRequest
from ai_video.production.project import load_production_project
from ai_video.production.video_transition import (
    BoundaryKind, CausalEdgeSemantics, CausalStateChange, ContinuityObligation, CreativeArtifactIdentity,
)
from scripts.canvas_sequence_packet import build_sequence_packet


def build_canvas_sequence_planning_request(
    *, source: dict, selection: dict, project_root: str | Path,
    current_request: VideoPlanningRequest, target_occurrence_id: str,
    shot_bindings: dict[str, CreativeArtifactIdentity], execution_evidence: dict,
    resolution: str = "480p",
):
    """Recheck source/order and pass one authored edge to the canonical adapter.

    Occurrences (including repeated canvas nodes) bind distinct approved Shots.
    Resolution is an assertion on the approved request, never an implicit edit.
    The first selected unit uses the ordinary existing single-Shot path instead.
    """
    packet = build_sequence_packet(source, selection, resolution=resolution)
    units = packet["units"]
    occurrences = [u["occurrence_id"] for u in units]
    if set(shot_bindings) != set(occurrences):
        raise ValueError("exact occurrence to Shot bindings required")
    target_index = occurrences.index(target_occurrence_id)
    if target_index == 0:
        raise ValueError("first unit has no selected predecessor; use existing single-Shot planning")
    edge = packet["boundaries"][target_index - 1]
    if edge["status"] != "AUTHORED_NOT_MEDIA_VERIFIED":
        raise ValueError("canvas boundary is blocked")
    loaded = load_production_project(Path(project_root) / "project.yaml")
    shots = {s.artifact_id: s for s in loaded.shots}
    selected = []
    identities = {}
    for occurrence in occurrences:
        identity = CreativeArtifactIdentity.model_validate(shot_bindings[occurrence])
        shot = shots.get(identity.artifact_id)
        if shot is None or (shot.revision, shot.content_hash) != (identity.revision, identity.content_hash):
            raise ValueError("stale canvas Shot binding")
        selected.append(shot.shot_id)
        identities[occurrence] = identity
    order = [s for beat in loaded.storyboard.beats for s in beat.shot_ids]
    if len(set(selected)) != len(selected) or not any(
            order[i:i + len(selected)] == selected for i in range(len(order))):
        raise ValueError("canvas selection differs from contiguous Storyboard order")
    if current_request.target_shot.shot_id != selected[target_index]:
        raise ValueError("canvas target differs from planning target")
    output = current_request.generation_intent.output_need
    if output.width is None or output.height is None or min(output.width, output.height) != int(resolution[:-1]):
        raise ValueError("approved output dimensions differ from canvas preparation resolution")
    allowed_evidence = {"source_shot", "source_generation_intent_hash", "anchors", "source_execution_stack",
                        "destination_execution_stack", "destination_route", "destination_selection_binding",
                        "lifecycle", "take_id"}
    if set(execution_evidence) - allowed_evidence:
        raise ValueError("execution evidence cannot override canvas authoring")
    accepted_identity = CreativeArtifactIdentity.model_validate(execution_evidence["source_shot"])
    if accepted_identity.artifact_id != identities[occurrences[target_index - 1]].artifact_id:
        raise ValueError("accepted source belongs to another canvas Shot")
    evidence = {**execution_evidence, "source_shot": accepted_identity}
    args = edge["planning_arguments"]
    return build_sequence_video_planning_request(
        project_root=project_root, current_request=current_request,
        boundary_kind=BoundaryKind(args["boundary_kind"]),
        continuity_obligation=ContinuityObligation(args["continuity_obligation"]),
        causal_edge_semantics=CausalEdgeSemantics(args["causal_edge_semantics"]),
        causal_state_changes=tuple(CausalStateChange.model_validate(c) for c in args["causal_state_changes"]),
        required_carryover_dimensions=tuple(args["required_carryover_dimensions"]),
        **evidence,
    )
