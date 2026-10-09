from copy import deepcopy
import json
import subprocess
import sys

import pytest

from scripts.canvas_sequence_packet import build_sequence_packet


def document():
    refs = [{"slotId": "room-slot", "nodeId": "room", "role": "reference"},
            {"slotId": "voice-slot", "nodeId": "voice", "role": "reference"}]
    nodes = [{"id": k, "type": t, "data": {"resourceId": k + "-resource"}}
             for k, t in [("room", "image"), ("voice", "audio")]]
    for name, text in [("a", "前段：生物遮满镜头。"), ("b", "后段：从遮挡中继续前冲。")]:
        nodes.append({"id": name, "type": "video", "data": {
            "resourceId": name + "-output", "generationDraft": {
                "parts": [{"type": "text", "text": text},
                          {"type": "extension", "extension_type": "node", "object_id": "room-slot"}],
                "contentSettings": {"resolution": "720p", "durationSeconds": 15},
                "references": deepcopy(refs)}}})
    clips = [{"clipId": "clip-" + str(i), "kind": "video", "source": {
        "kind": "canvas-node", "nodeId": n}, "sourceRange": {"startTick": 11, "durationTick": 101},
        "speed": 1, "volume": 0.5, "muted": False} for i, n in enumerate(["a", "b", "a"])]
    nodes.append({"id": "timeline", "type": "timeline", "data": {
        "tracks": [{"kind": "visual", "muted": True, "clips": clips}]}})
    edges = [{"id": s + t, "source": s, "target": t, "type": "reference"}
             for s in ["room", "voice"] for t in ["a", "b"]]
    return {"nodes": nodes, "edges": edges}


def boundary():
    return {"source_occurrence_id": "a", "target_occurrence_id": "b",
            "boundary_kind": "scene_boundary", "continuity_obligation": "identity_style_carryover",
            "causal_edge_semantics": "scene_reset", "source_close_quote": "生物遮满镜头",
            "target_open_quote": "从遮挡中继续前冲", "causal_state_changes": []}


def test_shared_assets_do_not_imply_continuity_or_acceptance():
    source = document()
    before = deepcopy(source)
    result = build_sequence_packet(source, {"node_ids": ["a", "b"]})
    assert source == before
    assert len(result["assets"]) == 2
    assert [u["node_id"] for u in result["units"]] == ["a", "b"]
    assert result["generation_defaults"]["resolution"] == "480p"
    assert result["units"][0]["observed_parameters"]["resolution"] == "720p"
    assert result["boundaries"][0]["status"] == "BLOCKED_MISSING_AUTHORING"
    assert result["production_acceptance"] == "NOT_EVALUATED"


def test_timeline_preserves_order_repeated_occurrence_and_raw_edit():
    source = document()
    result = build_sequence_packet(source, {"timeline_id": "timeline"})
    assert [u["node_id"] for u in result["units"]] == ["a", "b", "a"]
    assert [u["occurrence_id"] for u in result["units"]] == ["clip-0", "clip-1", "clip-2"]
    assert result["timeline_source"] == source["nodes"][-1]
    assert len(result["boundaries"]) == 2


def test_explicit_boundaries_use_existing_types_without_fabricating_accepted_source():
    result = build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [boundary()]}, resolution="1080p")
    edge = result["boundaries"][0]
    assert edge["status"] == "AUTHORED_NOT_MEDIA_VERIFIED"
    assert edge["planning_arguments"]["continuity_obligation"] == "identity_style_carryover"
    assert result["generation_defaults"]["resolution"] == "1080p"
    assert result["next_owner"] == "ai_video.planning.sequence_continuity.build_sequence_video_planning_request"


@pytest.mark.parametrize("damage", ["unknown", "duplicate", "both", "slot", "edge", "resource", "quote", "boundary", "order"])
def test_mismatch_fails_closed(damage):
    source = document()
    selection = {"node_ids": ["a", "b"], "boundaries": [boundary()]}
    if damage == "unknown": selection["node_ids"][0] = "missing"
    elif damage == "duplicate": selection["node_ids"] = ["a", "a"]
    elif damage == "both": selection["timeline_id"] = "timeline"
    elif damage == "slot": source["nodes"][2]["data"]["generationDraft"]["parts"][1]["object_id"] = "missing"
    elif damage == "edge": source["edges"].pop(0)
    elif damage == "resource": source["nodes"][0]["data"].pop("resourceId")
    elif damage == "quote": selection["boundaries"][0]["target_open_quote"] = "伪造正文"
    elif damage == "boundary": selection["boundaries"][0]["continuity_obligation"] = "invented"
    else: selection["boundaries"][0]["source_occurrence_id"] = "b"
    with pytest.raises((ValueError, KeyError)):
        build_sequence_packet(source, selection)


def test_existing_rich_packet_uses_identity_not_chip_order():
    from scripts.canvas_reference_packet import build_packet
    from test_canvas_reference_packet import fixture
    graph, composers = fixture()
    packet = build_packet(graph, composers)
    result = build_sequence_packet(packet, {"node_ids": ["shot"]})
    unit = result["units"][0]
    assert unit["source_text"] == composers["results"][0]["prompt"]
    assert [r["node_id"] for r in unit["references"]] == ["panzi", "zengliang"]
    assert unit["prompt_source"]["document"] == composers["results"][0]["document"]


def test_full_continuity_requires_all_causal_dimensions():
    edge = boundary()
    edge["continuity_obligation"] = "full_continuity"
    with pytest.raises(ValueError, match="causal dimensions"):
        build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [edge]})


def test_complete_causal_inventory_is_only_an_authored_handoff():
    from ai_video.production.video_transition import CausalDimension
    edge = boundary()
    edge.update(continuity_obligation="full_continuity", boundary_kind="within_continuous_take",
                causal_edge_semantics="direct_continuity", causal_state_changes=[
                    {"dimension": d.value, "source_close": "已锁定状态", "target_open": "已锁定状态",
                     "transition_mode": "carry"} for d in CausalDimension])
    result = build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [edge]})
    assert len(result["boundaries"][0]["planning_arguments"]["causal_state_changes"]) == 10
    assert result["production_acceptance"] == "NOT_EVALUATED"


def test_modified_preserved_packet_is_rejected_against_original_composers():
    from scripts.canvas_reference_packet import build_packet
    from test_canvas_reference_packet import fixture
    graph, composers = fixture()
    packet = build_packet(graph, composers)
    packet["generation_nodes"][0]["tray_bindings"].reverse()
    with pytest.raises(ValueError, match="differs"):
        build_sequence_packet(packet, {"node_ids": ["shot"]})


def test_cli_is_offline_and_does_not_overwrite(tmp_path):
    source, selection, output = [tmp_path / p for p in ["source.json", "selection.json", "packet.json"]]
    source.write_text(json.dumps(document()))
    selection.write_text(json.dumps({"node_ids": ["a", "b"]}))
    argv = [sys.executable, "-m", "scripts.canvas_sequence_packet", "--source", str(source),
            "--selection", str(selection), "--output", str(output)]
    first = subprocess.run(argv, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    assert "No provider call" in first.stdout
    original = output.read_bytes()
    assert subprocess.run(argv, capture_output=True).returncode == 2
    assert output.read_bytes() == original
