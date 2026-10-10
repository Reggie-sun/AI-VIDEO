from copy import deepcopy
import json
import subprocess
import sys
import hashlib
from pathlib import Path

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
            "causal_edge_semantics": "causal_ellipsis", "source_close_quote": "生物遮满镜头",
            "target_open_quote": "从遮挡中继续前冲", "required_carryover_dimensions": ["screen_motion_axis"],
            "causal_state_changes": [{"dimension": "screen_motion_axis", "source_close": "向前",
                                      "target_open": "向前", "transition_mode": "carry"}]}


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
                required_carryover_dimensions=sorted(d.value for d in CausalDimension),
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


def test_raw_source_cannot_override_prompt_with_observed_nodes():
    source = document()
    source["generation_nodes"] = []
    with pytest.raises(ValueError, match="mixed"):
        build_sequence_packet(source, {"node_ids": ["a", "b"]})


@pytest.mark.parametrize("kind,obligation,semantics", [
    ("within_continuous_take", "identity_style_carryover", "direct_continuity"),
    ("scene_boundary", "identity_style_carryover", "scene_reset"),
    ("scene_boundary", "substantial_reset", "causal_ellipsis"),
    ("scene_boundary", "identity_style_carryover", "commercial_cut"),
])
def test_illegal_canonical_combination_rejected(kind, obligation, semantics):
    edge = boundary()
    edge.update(boundary_kind=kind, continuity_obligation=obligation, causal_edge_semantics=semantics)
    with pytest.raises(ValueError):
        build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [edge]})


def test_preserves_carryover_and_output_resource_identity():
    result = build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [boundary()]})
    assert result["boundaries"][0]["planning_arguments"]["required_carryover_dimensions"] == ["screen_motion_axis"]
    assert result["units"][0]["output_resource_id"] == "a-output"


@pytest.mark.parametrize("bad", [[], None, "invalid", 42])
def test_cli_invalid_source_shape_is_sanitized(tmp_path, bad):
    source, selection, output = [tmp_path / p for p in ["source.json", "selection.json", "packet.json"]]
    source.write_text(json.dumps(bad))
    selection.write_text(json.dumps({"node_ids": ["a", "b"]}))
    result = subprocess.run([sys.executable, "-m", "scripts.canvas_sequence_packet", "--source", str(source),
                            "--selection", str(selection), "--output", str(output)], capture_output=True, text=True)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_analysis_does_not_erase_conflict_or_invent_verbatim_quote():
    edge = boundary()
    edge["source_analysis"] = {"source_quotes": ["生物遮满镜头"], "target_quotes": ["从遮挡中继续前冲"],
        "planned_source_close": "前进遮挡", "planned_target_open": "揭开前进", "carryover": ["前进"],
        "gaps": [], "conflicts": ["必须明确的未解决冲突"]}
    selection = {"node_ids": ["a", "b"], "boundaries": [edge]}
    result = build_sequence_packet(document(), selection)
    assert result["boundaries"][0]["status"] == "BLOCKED_SOURCE_CONFLICT"
    assert "planning_arguments" not in result["boundaries"][0]
    edge["source_analysis"]["conflicts"] = []
    edge.pop("boundary_kind")
    pending = build_sequence_packet(document(), selection)["boundaries"][0]
    assert pending["status"] == "ANALYZED_PENDING_SHOT_AUTHORING"
    assert "planning_arguments" not in pending
    edge["source_analysis"]["source_quotes"] = ["不存在的引文"]
    with pytest.raises(ValueError, match="verbatim"):
        build_sequence_packet(document(), selection)


def test_reference_chip_cannot_create_a_fake_contiguous_quote():
    source = document()
    parts = source["nodes"][2]["data"]["generationDraft"]["parts"]
    parts[:] = [{"type": "text", "text": "前段"}, parts[1], {"type": "text", "text": "结束"}]
    edge = boundary()
    edge["source_close_quote"] = "前段结束"
    with pytest.raises(ValueError, match="verbatim"):
        build_sequence_packet(source, {"node_ids": ["a", "b"], "boundaries": [edge]})


@pytest.mark.parametrize("name,count", [("fanxiang", 3), ("baidaizi", 7)])
def test_preserved_real_source_boundary_evidence(name, count):
    from scripts.canvas_sequence_packet import _boundary
    selection = json.loads(Path(f"docs/canvas-sequences/{name}.json").read_text())
    units = selection["evidence_units"]
    assert len(units) == count + 1
    assert len(selection["boundaries"]) == count
    for unit in units:
        assert hashlib.sha256(unit["source_text"].encode()).hexdigest() == unit["source_text_sha256"]
        assert unit["reference_role_evidence"] in unit["source_text"]
        assert unit["output_resource_id"]
    results = [_boundary(a, b, e) for a, b, e in zip(units, units[1:], selection["boundaries"])]
    assert all(r["source_analysis"]["source_quotes"] and r["source_analysis"]["target_quotes"] for r in results)
    if name == "fanxiang":
        assert results[1]["status"] == "BLOCKED_SOURCE_CONFLICT"
        assert "小龙握着长杆" in results[1]["source_analysis"]["source_quotes"][0]
        assert "双手仍然空着" in results[1]["source_analysis"]["target_quotes"][0]


def test_bound_source_snapshot_rejects_drift():
    from scripts.canvas_sequence_packet import _hash
    source = document()
    selection = {"node_ids": ["a", "b"], "expected_source_snapshot_sha256": _hash(source)}
    source["nodes"][2]["data"]["resourceId"] = "other-output"
    with pytest.raises(ValueError, match="snapshot changed"):
        build_sequence_packet(source, selection)


@pytest.mark.parametrize("damage", ["empty_changes", "no_carries", "release_direct"])
def test_incomplete_authoring_is_not_prepared(damage):
    edge = boundary()
    if damage == "empty_changes":
        edge["causal_state_changes"] = []
    elif damage == "no_carries":
        edge["required_carryover_dimensions"] = []
    else:
        edge["causal_edge_semantics"] = "direct_continuity"
        edge["causal_state_changes"][0]["transition_mode"] = "authorized_release"
    with pytest.raises(ValueError):
        build_sequence_packet(document(), {"node_ids": ["a", "b"], "boundaries": [edge]})
