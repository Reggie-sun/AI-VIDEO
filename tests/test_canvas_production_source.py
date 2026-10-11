from copy import deepcopy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.canvas_production_source import inspect_canvas_source


def source_document():
    references = [{
        "slotId": "room-slot", "nodeId": "room", "sourceInstanceId": "room",
        "type": "extension", "extensionType": "node", "role": "reference",
    }]
    video = {
        "id": "shot", "type": "video", "data": {
            "title": "Shot", "source": "model_generated", "resourceId": "shot-v1",
            "resourceBatches": [
                {"id": "batch-old", "resourceIds": ["shot-v0"]},
                {"id": "batch-new", "resourceIds": ["shot-v1", "shot-v2"]},
            ],
            "generationDraft": {
                "kind": "video",
                "parts": [
                    {"type": "text", "text": "Keep the room quiet."},
                    {"type": "extension", "extension_type": "node", "object_id": "room-slot"},
                ],
                "contentSettings": {"modelName": "example", "resolution": "720p"},
                "outputCount": 1,
                "references": deepcopy(references),
            },
        },
    }
    timeline = {
        "id": "edit", "type": "timeline", "data": {"title": "Edit", "tracks": [
            {"kind": "visual", "muted": False, "clips": [
                {"clipId": "visual-0", "kind": "video", "source": {"kind": "canvas-node", "nodeId": "shot"},
                 "sourceRange": {"startTick": 5, "durationTick": 60}, "speed": 1.25,
                 "muted": False, "volume": 0.8, "curve": "ease-in"},
                {"clipId": "visual-1", "kind": "video", "source": {"kind": "canvas-node", "nodeId": "shot"},
                 "sourceRange": {"startTick": 10, "durationTick": 40}, "speed": 1,
                 "muted": True, "volume": 0.25},
            ], "transitionMode": "manual"},
            {"kind": "audio", "muted": False, "clips": [
                {"clipId": "audio-0", "kind": "audio", "source": {"kind": "canvas-node", "nodeId": "music"},
                 "sourceRange": {"startTick": 0, "durationTick": 100}, "startTick": 20,
                 "speed": 0.9, "muted": False, "volume": 0.3, "fade": {"in": 5}},
            ]},
        ]},
    }
    return {
        "canvas_url": "https://example.invalid/canvas",
        "nodes": [
            {"id": "room", "type": "image", "data": {
                "title": "Room", "source": "uploaded", "resourceId": "room-v2",
                "resourceBatches": [
                    {"id": "room-batch-1", "resourceIds": ["room-v1"]},
                    {"id": "room-batch-2", "resourceIds": ["room-v2"]},
                ],
            }},
            video,
            {"id": "music", "type": "audio", "data": {
                "title": "Music", "source": "uploaded", "resourceId": "music-v1",
                "resourceBatches": [{"id": "music-batch", "resourceIds": ["music-v1"]}],
            }},
            timeline,
            {"id": "unused-video", "type": "video", "data": {
                "title": "Unused", "source": "model_generated", "resourceId": "unused-v1",
            }},
            {"id": "subject", "type": "subject", "data": {"title": "Subject", "main": {"resourceId": "subject-v1"}}},
            {"id": "future-kind", "type": "compositor", "data": {"title": "Unknown"}},
        ],
        "edges": [{"id": "room-shot", "source": "room", "target": "shot", "type": "reference"}],
    }


def issue_codes(report, node_id=None):
    return {i["code"] for i in report["issues"] if node_id is None or i.get("node_id") == node_id}


def test_inspection_preserves_full_source_and_separates_current_pointer_from_version_selection():
    source = source_document()
    before = deepcopy(source)
    report = inspect_canvas_source(source)

    assert source == before
    assert report["source_snapshot"] == source
    assert report["source_snapshot_sha256"] == hashlib.sha256(
        json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    room = next(n for n in report["inventory"]["nodes"] if n["node_id"] == "room")
    assert room["resource_versions"] == source["nodes"][0]["data"]["resourceBatches"]
    assert room["current_resource_id"] == "room-v2"
    assert room["version_selection"] == {
        "status": "current_pointer_only", "current_pointer_batch_ids": ["room-batch-2"],
        "selected_version_id": None,
    }
    shot = next(n for n in report["inventory"]["nodes"] if n["node_id"] == "shot")
    assert shot["generation"]["parts"] == source["nodes"][1]["data"]["generationDraft"]["parts"]
    assert shot["generation"]["parameters"] == {"modelName": "example", "resolution": "720p"}
    assert shot["generation"]["references"] == source["nodes"][1]["data"]["generationDraft"]["references"]


def test_unselected_source_gaps_do_not_block_an_explicit_supported_chain():
    source = source_document()
    source["edges"].append({"id": "unselected-dangling", "source": "deleted-node", "target": "unused-video", "type": "reference"})
    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "CANONICAL_PACKET_AVAILABLE"
    assert report["selection"]["blockers"] == []
    assert "missing_generation_draft" in issue_codes(report, "unused-video")
    assert "unsupported_node_kind" in issue_codes(report, "future-kind")
    assert "dangling_edge" in issue_codes(report, "unused-video")
    assert report["selection"]["sequence_packet"]["units"][0]["node_id"] == "shot"
    assert report["production_acceptance"] == "NOT_EVALUATED"


def test_materialized_image_ancestry_is_preserved_without_becoming_an_execution_dependency():
    source = source_document()
    room = source["nodes"][0]
    room["data"].update(source="model_generated", generationDraft={
        "parts": [{"type": "extension", "extension_type": "subject", "object_id": "missing-history-slot"}],
        "contentSettings": {"modelName": "image-model"},
        "references": [],
    })
    source["nodes"].append({"id": "ancestor", "type": "image", "data": {
        "resourceId": "ancestor-v1", "resourceBatches": [{"id": "ancestor-batch", "resourceIds": ["ancestor-v1"]}],
        "source": "model_generated", "generationDraft": {
            "parts": [{"type": "extension", "extension_type": "subject", "object_id": "subject-slot"}],
            "contentSettings": {}, "references": [],
        },
    }})
    source["edges"].append({"id": "ancestor-room", "source": "ancestor", "target": "room", "type": "reference"})
    report = inspect_canvas_source(source, {"node_ids": ["shot"]})
    assert "unbound_prompt_slot" in issue_codes(report, "ancestor")
    assert "unbound_prompt_slot" in issue_codes(report, "room")
    assert report["source_snapshot"] == source
    assert report["selection"]["status"] == "CANONICAL_PACKET_AVAILABLE"
    assert report["selection"]["blockers"] == []
    assert any(item.get("node_id") == "room" and item["code"] == "unbound_prompt_slot"
               and item.get("relevance") == "materialized_reference_ancestry"
               for item in report["selection"]["related_issues"])
    assert [a["id"] for a in report["selection"]["sequence_packet"]["assets"]] == ["room"]

    source["edges"].append({"id": "dangling-room", "source": "missing-node", "target": "room", "type": "reference"})
    structurally_blocked = inspect_canvas_source(source, {"node_ids": ["shot"]})
    assert structurally_blocked["selection"]["status"] == "BLOCKED_SOURCE_GAPS"
    assert "dangling_edge" in {b["code"] for b in structurally_blocked["selection"]["blockers"]}
    source["edges"].pop()

    room["data"].pop("resourceId")
    blocked = inspect_canvas_source(source, {"node_ids": ["shot"]})
    assert blocked["selection"]["status"] != "CANONICAL_PACKET_AVAILABLE"
    assert "missing_resource_id" in {b["code"] for b in blocked["selection"]["blockers"]}


@pytest.mark.parametrize("damage", ["none", "packet", "source", "blocker"])
def test_workflow_rejects_modified_inspection_projection_before_writes(tmp_path, damage):
    from ai_video.canvas_production import CanvasProductionService
    from ai_video.errors import AiVideoError
    from ai_video.production.state_commit import ProductionStateCommitter
    report = inspect_canvas_source(source_document(), {"node_ids": ["shot"]})
    if damage == "packet": report["selection"]["sequence_packet"]["units"][0]["source_text"] = "edited"
    elif damage == "source": report["source_snapshot"]["nodes"][0]["data"]["resourceId"] = "edited"
    elif damage == "blocker": report["selection"]["status"] = "BLOCKED_SOURCE_GAPS"
    configuration = {"inspection": report, "committer": ProductionStateCommitter(tmp_path), "direction": {}}
    if damage == "none":
        assert CanvasProductionService.from_inspection(**configuration).packet["units"][0]["node_id"] == "shot"
    else:
        with pytest.raises(AiVideoError): CanvasProductionService.from_inspection(**configuration)
    assert list(tmp_path.iterdir()) == []


def test_no_selection_is_a_decision_point_and_never_chooses_a_timeline():
    report = inspect_canvas_source(source_document())

    assert report["selection"]["status"] == "NEEDS_EXPLICIT_SELECTION"
    assert report["selection"]["sequence_packet"] is None
    assert report["selection"]["candidate_timeline_ids"] == ["edit"]
    assert report["selection"]["selected_timeline_id"] is None


def test_timeline_keeps_each_visual_and_audio_occurrence_and_unhandled_fields():
    report = inspect_canvas_source(source_document(), {"timeline_id": "edit"})
    timeline = report["inventory"]["timelines"][0]
    visual = timeline["tracks"][0]["clips"]
    audio = timeline["tracks"][1]["clips"][0]

    assert [c["occurrence_id"] for c in visual] == ["visual-0", "visual-1"]
    assert [c["node_id"] for c in visual] == ["shot", "shot"]
    assert visual[0]["source_range"] == {"startTick": 5, "durationTick": 60}
    assert (visual[0]["speed"], visual[0]["muted"], visual[0]["volume"]) == (1.25, False, 0.8)
    assert visual[0]["unsupported_fields"] == ["curve"]
    assert timeline["tracks"][0]["unsupported_fields"] == ["transitionMode"]
    assert audio["occurrence_id"] == "audio-0"
    assert audio["node_id"] == "music"
    assert audio["start_tick"] == 20
    assert (audio["speed"], audio["muted"], audio["volume"]) == (0.9, False, 0.3)
    assert audio["unsupported_fields"] == ["fade"]
    assert report["selection"]["status"] == "BLOCKED_SOURCE_GAPS"
    assert report["selection"]["sequence_packet"] is not None
    assert [u["occurrence_id"] for u in report["selection"]["sequence_packet"]["units"]] == ["visual-0", "visual-1"]


@pytest.mark.parametrize("damage,expected", [
    ("draft", "missing_generation_draft"),
    ("slot", "unbound_prompt_slot"),
    ("resource", "missing_resource_id"),
    ("edge", "dangling_edge"),
    ("subject", "invalid_subject_resource_snapshot"),
])
def test_selected_chain_damage_is_reported_as_a_blocker(damage, expected):
    source = source_document()
    if damage == "draft":
        source["nodes"][1]["data"].pop("generationDraft")
    elif damage == "slot":
        source["nodes"][1]["data"]["generationDraft"]["parts"][1]["object_id"] = "absent-slot"
    elif damage == "resource":
        source["nodes"][0]["data"].pop("resourceId")
    elif damage == "edge":
        source["edges"][0]["source"] = "deleted-room"
    else:
        draft = source["nodes"][1]["data"]["generationDraft"]
        draft["parts"].append({"type": "extension", "extension_type": "subject", "object_id": "subject-slot"})
        draft["references"].append({
            "slotId": "subject-slot", "nodeId": "subject", "sourceInstanceId": "subject",
            "type": "extension", "extensionType": "subject", "role": "reference",
        })
        source["edges"].append({"id": "subject-shot", "source": "subject", "target": "shot", "type": "reference"})

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "BLOCKED"
    assert expected in {b["code"] for b in report["selection"]["blockers"]}
    assert report["production_acceptance"] == "NOT_EVALUATED"


def test_subject_reference_keeps_grouped_resource_snapshots_and_original_node():
    source = source_document()
    subject = next(node for node in source["nodes"] if node["id"] == "subject")
    subject["data"].update(
        main={"refType": "resource_snapshot", "resourceId": "subject-main"},
        auxiliaries=[{"refType": "resource_snapshot", "resourceId": "subject-aux"}],
        provenance={"origin_subject_id": "original-subject"},
    )
    draft = next(node for node in source["nodes"] if node["id"] == "shot")["data"]["generationDraft"]
    draft["parts"].append({"type": "extension", "extension_type": "subject", "object_id": "subject-slot"})
    draft["references"].append({
        "slotId": "subject-slot", "nodeId": "subject", "sourceInstanceId": "subject",
        "type": "extension", "extensionType": "subject", "role": "reference",
    })
    source["edges"].append({"id": "subject-shot", "source": "subject", "target": "shot", "type": "reference"})

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "CANONICAL_PACKET_AVAILABLE"
    unit = report["selection"]["sequence_packet"]["units"][0]
    assert unit["source_text"] == "Keep the room quiet.\n\n"
    subject_reference = unit["references"][1]
    assert subject_reference == {
        "slot_id": "subject-slot",
        "node_id": "subject",
        "canvas_role": "reference",
        "kind": "subject",
        "extension_type": "subject",
        "semantic_role": "identity",
        "material_references": {
            "main": {"ref_type": "resource_snapshot", "resource_id": "subject-main"},
            "auxiliaries": [{"index": 0, "ref_type": "resource_snapshot", "resource_id": "subject-aux"}],
        },
        "provenance": {"origin_subject_id": "original-subject"},
    }
    assert next(asset for asset in report["selection"]["sequence_packet"]["assets"]
                if asset["id"] == "subject") == subject


@pytest.mark.parametrize("damage,expected", [
    ("unbound_slot", "unbound_prompt_slot"),
    ("extension_type", "prompt_reference_extension_type_mismatch"),
    ("node_type", "prompt_reference_node_type_mismatch"),
])
def test_subject_prompt_chip_must_match_declared_slot_and_node_type(damage, expected):
    source = source_document()
    subject = next(node for node in source["nodes"] if node["id"] == "subject")
    subject["data"].update(main={"refType": "resource_snapshot", "resourceId": "subject-main"})
    draft = next(node for node in source["nodes"] if node["id"] == "shot")["data"]["generationDraft"]
    draft["parts"].append({"type": "extension", "extension_type": "subject", "object_id": "subject-slot"})
    draft["references"].append({
        "slotId": "subject-slot", "nodeId": "subject", "sourceInstanceId": "subject",
        "type": "extension", "extensionType": "subject", "role": "reference",
    })
    source["edges"].append({"id": "subject-shot", "source": "subject", "target": "shot", "type": "reference"})
    if damage == "unbound_slot":
        draft["parts"][-1]["object_id"] = "missing-slot"
    elif damage == "extension_type":
        draft["references"][-1]["extensionType"] = "node"
    else:
        draft["references"][-1]["nodeId"] = "room"
        draft["references"][-1]["sourceInstanceId"] = "room"

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "BLOCKED"
    assert expected in {item["code"] for item in report["selection"]["blockers"]}


def test_mixed_raw_and_rich_source_is_explicitly_blocked():
    source = source_document()
    source["generation_nodes"] = []
    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["source_format"] == "mixed_raw_and_rich"
    assert "mixed_raw_and_rich_source" in issue_codes(report)
    assert report["selection"]["status"] == "BLOCKED"


def test_observed_packet_keeps_rich_prompt_and_runs_selected_canonical_packet():
    from scripts.canvas_reference_packet import build_packet
    from test_canvas_reference_packet import fixture

    graph, composers = fixture()
    packet = build_packet(graph, composers)
    report = inspect_canvas_source(packet, {"node_ids": ["shot"]})

    assert report["source_format"] == "observed_packet"
    shot = next(n for n in report["inventory"]["nodes"] if n["node_id"] == "shot")
    assert shot["generation"]["observed_prompt"] == "原文\n不删对白。"
    assert shot["generation"]["observed_generation"]["document"] == composers["results"][0]["document"]
    assert report["selection"]["sequence_packet"]["units"][0]["source_text"] == "原文\n不删对白。"
    assert report["selection"]["status"] == "BLOCKED_SOURCE_GAPS"
    assert "missing_resource_batches" in {i["code"] for i in report["selection"]["blockers"]}


def test_missing_reference_edge_is_located_at_selected_generation_node():
    source = source_document()
    source["edges"].clear()

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "BLOCKED"
    assert any(i["code"] == "missing_reference_edge" and i["node_id"] == "shot"
               for i in report["selection"]["blockers"])


def test_selected_non_reference_dependency_is_reported_as_uninterpreted():
    source = source_document()
    source["edges"].append({"id": "future-edge", "source": "room", "target": "shot", "type": "compositor_input"})

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "BLOCKED_SOURCE_GAPS"
    assert any(i["code"] == "uninterpreted_non_reference_edge" and i["edge_type"] == "compositor_input"
               for i in report["selection"]["blockers"])
    assert report["selection"]["sequence_packet"] is not None


def test_post_edit_provenance_is_reported_as_media_derivation_without_becoming_a_reference():
    source = source_document()
    source["nodes"].append({"id": "trim", "type": "video", "data": {
        "title": "Shot trim", "source": "post_edit_generated", "resourceId": "trim-v1",
        "resourceBatches": [{"id": "trim-batch", "resourceIds": ["trim-v1"]}],
    }})
    edge = {"id": "shot-trim", "source": "shot", "target": "trim", "type": "post_edit_provenance"}
    source["edges"].append(edge)

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert report["selection"]["status"] == "CANONICAL_PACKET_AVAILABLE"
    assert any(item["source_edge"] == edge for item in report["inventory"]["edges"])
    assert not any(item["code"] == "uninterpreted_non_reference_edge"
                   and item.get("edge_type") == "post_edit_provenance"
                   for item in report["selection"]["blockers"])
    assert report["selection"]["sequence_packet"]["units"][0]["node_id"] == "shot"


@pytest.mark.parametrize("damage,expected", [
    ("non_media", "invalid_post_edit_provenance"),
    ("not_materialized", "invalid_post_edit_provenance"),
    ("cycle", "post_edit_provenance_cycle"),
])
def test_invalid_post_edit_provenance_is_reported_and_blocks_related_selection(damage, expected):
    source = source_document()
    source["nodes"].append({"id": "trim", "type": "video", "data": {
        "title": "Shot trim", "source": "post_edit_generated", "resourceId": "trim-v1",
        "resourceBatches": [{"id": "trim-batch", "resourceIds": ["trim-v1"]}],
    }})
    source["edges"].append({"id": "shot-trim", "source": "shot", "target": "trim", "type": "post_edit_provenance"})
    if damage == "non_media":
        source["edges"][-1]["target"] = "subject"
    elif damage == "not_materialized":
        source["nodes"][-1]["data"]["source"] = "model_generated"
    else:
        source["edges"].append({"id": "trim-shot", "source": "trim", "target": "shot", "type": "post_edit_provenance"})

    report = inspect_canvas_source(source, {"node_ids": ["shot"]})

    assert expected in {item["code"] for item in report["selection"]["blockers"]}


def test_post_edit_child_without_own_draft_is_not_a_generation_unit():
    source = source_document()
    source["nodes"].append({"id": "trim", "type": "video", "data": {
        "title": "Shot trim", "source": "post_edit_generated", "resourceId": "trim-v1",
        "resourceBatches": [{"id": "trim-batch", "resourceIds": ["trim-v1"]}],
    }})
    source["edges"].append({"id": "shot-trim", "source": "shot", "target": "trim", "type": "post_edit_provenance"})

    report = inspect_canvas_source(source, {"node_ids": ["trim"]})

    assert report["selection"]["status"] == "BLOCKED"
    assert any(item["code"] == "missing_generation_draft" for item in report["selection"]["blockers"])


def test_unknown_timeline_media_kind_is_explicitly_reported():
    source = source_document()
    source["nodes"][3]["data"]["tracks"][0]["clips"][0]["kind"] = "sticker"

    report = inspect_canvas_source(source, {"timeline_id": "edit"})

    assert report["selection"]["status"] == "BLOCKED"
    assert any(i["code"] == "unsupported_clip_kind" and i["occurrence_id"] == "visual-0"
               for i in report["selection"]["blockers"])


def test_invalid_input_returns_contextual_blocker_without_raising():
    report = inspect_canvas_source(["not", "a", "canvas"])

    assert report["source_format"] == "unsupported"
    assert report["selection"]["status"] == "BLOCKED"
    assert report["selection"]["blockers"][0]["code"] == "unsupported_source_shape"


def test_cli_records_exact_input_bytes_hash_and_preserves_snapshot(tmp_path):
    source_path, output_path = tmp_path / "source.json", tmp_path / "report.json"
    raw = json.dumps(source_document(), ensure_ascii=False, indent=3).encode()
    source_path.write_bytes(raw)

    result = subprocess.run([
        sys.executable, "-m", "scripts.canvas_production_source",
        "--source", str(source_path), "--output", str(output_path),
    ], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    report = json.loads(output_path.read_text())
    assert report["source_bytes_sha256"] == hashlib.sha256(raw).hexdigest()
    assert report["source_snapshot"] == source_document()
    assert "No provider call" in result.stdout
