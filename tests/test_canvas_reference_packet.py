from copy import deepcopy

import pytest

from scripts.canvas_reference_packet import build_packet


def fixture():
    def chip(name):
        return {"type": "composerChip", "attrs": {
            "kind": "generation-image", "chipId": name, "data": {
                "part": {"object_id": name, "extra": {"generationPromptWireMaterial": {
                    "draftSlotId": name, "imageUri": name, "materialIndex": 0,
                    "referenceSource": {"nodeId": name}}}},
                "reference": {"slotId": name, "uri": name},
                "portablePromptReference": {"data": {"resourceId": name, "storageKey": name}},
                "generationClipboardNode": {"nodeId": name}}}}
    nodes = [{"id": name, "type": "image", "data": {
        "resourceId": name, "source": "uploaded", "title": name}}
        for name in ("panzi", "zengliang")]
    nodes += [{"id": "shot", "type": "video", "data": {"source": "model_generated"}}]
    graph = {"nodes": nodes, "edges": [{"id": name, "source": name,
        "target": "shot", "type": "reference"} for name in ("panzi", "zengliang")]}
    composer = {"nodeId": "shot", "prompt": "原文\n不删对白。", "parameters": "15s",
        "document": {"type": "doc", "content": [chip("zengliang"), chip("panzi")]},
        "materials": [{"id": name, "type": 2, "label": name}
                      for name in ("panzi", "zengliang")]}
    return graph, {"results": [composer]}


def test_reference_binding_does_not_zip_chip_and_tray_order():
    graph, composers = fixture()
    before = deepcopy((graph, composers))
    packet = build_packet(graph, composers)
    unit = packet["generation_nodes"][0]
    assert [b["node_id"] for b in unit["chip_bindings"]] == ["zengliang", "panzi"]
    assert [b["node_id"] for b in unit["tray_bindings"]] == ["panzi", "zengliang"]
    assert packet["source_graph"] == graph
    assert packet["source_composers"] == composers
    assert (graph, composers) == before
    assert unit["prompt"] == "原文\n不删对白。"


def test_repeated_reference_occurrence_keeps_single_material_identity():
    graph, composers = fixture()
    doc = composers["results"][0]["document"]
    repeated = deepcopy(doc["content"][0])
    repeated["attrs"]["chipId"] += ":occurrence:1"
    doc["content"].append(repeated)
    unit = build_packet(graph, composers)["generation_nodes"][0]
    assert len(unit["tray_bindings"]) == 2
    assert len(unit["chip_bindings"]) == 3
    assert unit["chip_bindings"][-1]["node_id"] == "zengliang"


@pytest.mark.parametrize("damage", ["resource", "node", "edge", "coverage", "slot", "unknown"])
def test_missing_or_conflicting_inputs_stop_preparation(damage):
    graph, composers = fixture()
    chip = composers["results"][0]["document"]["content"][0]
    if damage == "resource":
        chip["attrs"]["data"]["portablePromptReference"]["data"]["resourceId"] = "wrong"
    elif damage == "node":
        graph["nodes"].pop(0)
    elif damage == "edge":
        graph["edges"].pop()
    elif damage == "coverage":
        composers["results"] = []
    elif damage == "slot":
        chip["attrs"]["data"]["part"]["object_id"] = "wrong"
    else:
        chip["type"] = "unsupported"
    with pytest.raises(ValueError):
        build_packet(graph, composers)


def test_reference_video_is_kept_when_absent_from_prompt():
    graph, composers = fixture()
    graph["nodes"].append({"id": "guide", "type": "video", "data": {
        "title": "guide", "resourceId": "guide-resource", "source": "uploaded"}})
    graph["edges"].append({"id": "guide", "source": "guide", "target": "shot", "type": "reference"})
    composers["results"][0]["materials"].append({"id": "guide-slot", "type": 3, "label": "guide"})
    composers["results"].append({"nodeId": "guide", "document": None})
    binding = build_packet(graph, composers)["generation_nodes"][0]["tray_bindings"][-1]
    assert binding["resource_id"] == "guide-resource"
    assert binding["kind"] == "video"


def test_ambiguous_unmentioned_reference_is_not_guessed():
    graph, composers = fixture()
    composers["results"][0]["document"]["content"] = []
    for node in graph["nodes"][:2]:
        node["data"]["title"] = "same"
    for material in composers["results"][0]["materials"]:
        material["label"] = "same"
    with pytest.raises(ValueError, match="ambiguous"):
        build_packet(graph, composers)
