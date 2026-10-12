"""URI-only history images retain their source identity without inventing nodes."""
from copy import deepcopy
from pathlib import Path

import pytest

from ai_video.canvas_project_data import open_canvas_project
from ai_video.production.state_commit import ProductionStateCommitter
from scripts.canvas_production_source import inspect_canvas_source
from scripts.canvas_sequence_packet import build_sequence_packet
from test_canvas_project_data import text_data


def external_source():
    source, data = text_data()
    reference = {"slotId": "history-slot", "role": "reference", "type": "image",
        "uri": "tos-cn-i-example/history/image", "sourceInstanceId": 'history-material:["history-id",0]'}
    for node in source["nodes"]:
        draft = node["data"].get("generationDraft")
        if draft:
            draft["references"] = [deepcopy(reference)]
            draft["parts"][0]["text"] += " 参考[图片1]。"
    return source, data


def test_uri_reference_preserves_descriptor_and_does_not_change_original_graph(tmp_path):
    source, data = external_source()
    before = deepcopy(source)
    inspection = inspect_canvas_source(source, data["selection"])
    assert inspection["selection"]["status"] == "CANONICAL_PACKET_AVAILABLE"
    packet = inspection["selection"]["sequence_packet"]
    asset = packet["assets"][0]
    assert asset["source_binding_kind"] == "external_uri"
    assert asset["id"].startswith("external-image-")
    assert all(n["id"] != asset["id"] for n in source["nodes"])
    assert source == before and source["edges"] == []
    for unit in packet["units"]:
        assert unit["references"][0]["source_reference"] == before["nodes"][2]["data"]["generationDraft"]["references"][0]
        assert unit["prompt_source"]["parts"][0]["text"].endswith("参考[图片1]。")
    image = Path(__file__).resolve().parents[1] / "docs/canvas-projects/subject-reference/room.png"
    (tmp_path / "room.png").write_bytes(image.read_bytes())
    data["images"] = [{"asset_id": "history-image", "node_id": asset["id"],
        "resource_id": asset["data"]["resourceId"], "path": "room.png", "usage_license": "fixture"}]
    data["reference_aliases"] = {}
    data["direction"]["scenes"][0]["visual_reference_asset_ids"] = ["history-image"]
    for row in data["direction"]["shots"]:
        row["generation"] = {"references": [{"asset_id": "history-image", "role": "scene_reference"}]}
        data["reference_aliases"][row["occurrence_id"]] = [{"label": "图片1", "slot_id": "history-slot"}]
    (tmp_path / "project").mkdir()
    service, registry, artifacts = open_canvas_project(inspection=inspection, definition=data,
        data_root=tmp_path, committer=ProductionStateCommitter(tmp_path / "project"))
    bundle = service.author(registry=registry, asset_artifacts=artifacts)
    bundle.bootstrap(committer=service.committer, attempt_id="uri-author")
    resumed, _, _ = open_canvas_project(inspection=inspection, definition=data,
        data_root=tmp_path, committer=service.committer)
    assert resumed.direction == service.direction
    assert len(registry.assets) == 1


@pytest.mark.parametrize("damage", ["history", "uri", "unexpected_field", "wrong_extension", "extra_edge"])
def test_damaged_uri_reference_fails_closed_without_state(tmp_path, damage):
    source, data = external_source()
    draft = source["nodes"][2]["data"]["generationDraft"]
    if damage == "history":
        draft["references"][0]["sourceInstanceId"] = 'history-material:["history-id",-1]'
    elif damage == "uri":
        draft["references"][0]["uri"] = "https://untrusted.example/image?credential=value"
    elif damage == "unexpected_field":
        draft["references"][0]["nodeId"] = "room"
    elif damage == "wrong_extension":
        draft["parts"].append({"type": "extension", "extension_type": "node", "object_id": "history-slot"})
    else:
        source["edges"].append({"id": "invented-edge", "source": "room", "target": "a", "type": "reference"})
    inspection = inspect_canvas_source(source, data["selection"])
    assert inspection["selection"]["status"] != "CANONICAL_PACKET_AVAILABLE"
    with pytest.raises((ValueError, KeyError)):
        build_sequence_packet(source, data["selection"])
    assert list(tmp_path.iterdir()) == []
