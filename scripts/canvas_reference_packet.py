"""Preserve observed canvas inputs and bind chips by identity, never display order.

Offline preparation only: this does not create a ProductionProject, upload assets,
compile a provider request, or prove historical submission/output equivalence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def _index(items: list[dict], key: str) -> dict[str, dict]:
    result = {}
    for item in items:
        identity = item[key]
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError(f"missing or duplicate {key}")
        result[identity] = item
    return result


def _chips(node: dict):
    if node.get("type") not in {"doc", "paragraph", "text", "composerChip"}:
        raise ValueError("unsupported rich prompt node")
    if node["type"] == "composerChip":
        yield node["attrs"]
    for child in node.get("content", []):
        yield from _chips(child)


def build_packet(graph: dict, composers: dict) -> dict:
    """Keep all observed source fields; add validated, explicit reference bindings."""
    nodes = _index(graph["nodes"], "id")
    _index(graph["edges"], "id")
    observed = _index(composers["results"], "nodeId")
    if set(observed) != {n["id"] for n in nodes.values() if n["type"] == "video"}:
        raise ValueError("video composer coverage mismatch")
    incoming: dict[str, list[str]] = {identity: [] for identity in nodes}
    for edge in graph["edges"]:
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise ValueError("dangling canvas edge")
        if edge["type"] != "reference":
            raise ValueError("unsupported canvas edge")
        incoming[edge["target"]].append(edge["source"])
    packets = []
    for identity, composer in observed.items():
        node = nodes[identity]
        if node["data"]["source"] != "model_generated":
            if composer["document"] is not None:
                raise ValueError("unexpected composer on uploaded video")
            continue
        if not composer["document"] or not composer["prompt"] or not composer["parameters"]:
            raise ValueError("incomplete generated video composer")
        materials = [m for m in composer["materials"] if m is not None]
        by_slot = _index(materials, "id")
        sources = incoming[identity]
        if len(sources) != len(set(sources)):
            raise ValueError("duplicate reference edge")
        bindings = {}
        chip_bindings = []
        for attrs in _chips(composer["document"]):
            if attrs["kind"] != "generation-image":
                raise ValueError("unsupported composer chip kind")
            data = attrs["data"]
            wire = data["part"]["extra"]["generationPromptWireMaterial"]
            portable = data["portablePromptReference"]["data"]
            source_id = data["generationClipboardNode"]["nodeId"]
            slot = data["reference"]["slotId"]
            if source_id not in sources or slot not in by_slot:
                raise ValueError("chip is not a connected material")
            source = nodes[source_id]
            resource_id = source["data"]["resourceId"]
            if (wire["referenceSource"]["nodeId"] != source_id
                    or portable["resourceId"] != resource_id
                    or wire["imageUri"] != portable["storageKey"]
                    or data["reference"]["uri"] != portable["storageKey"]
                    or wire["draftSlotId"] != slot
                    or data["part"]["object_id"] != slot
                    or source["type"] != "image"
                    or by_slot[slot]["type"] != 2):
                raise ValueError("chip reference identity mismatch")
            binding = {"slot_id": slot, "node_id": source_id,
                       "resource_id": resource_id, "kind": "image",
                       "storage_key": portable["storageKey"]}
            if slot in bindings and bindings[slot] != binding:
                raise ValueError("conflicting chip slot")
            bindings[slot] = binding
            chip_bindings.append({**binding, "chip_id": attrs["chipId"],
                                  "chip_material_index": wire["materialIndex"]})
        used_sources = {b["node_id"] for b in bindings.values()}
        # Connected media may be absent from prose (e.g. the short motion guide).
        # Resolve only within this target's remaining incoming edges. Ambiguity stops.
        for material in materials:
            if material["id"] in bindings:
                continue
            kind = {2: "image", 3: "video"}.get(material["type"])
            candidates = [nodes[s] for s in sources if s not in used_sources
                          and nodes[s]["type"] == kind
                          and nodes[s]["data"]["title"] == material["label"]]
            if len(candidates) != 1:
                raise ValueError("unmentioned reference is missing or ambiguous")
            source = candidates[0]
            bindings[material["id"]] = {
                "slot_id": material["id"], "node_id": source["id"],
                "resource_id": source["data"]["resourceId"], "kind": kind,
                "binding_evidence": "unique incoming edge plus exact tray label",
            }
            used_sources.add(source["id"])
        if used_sources != set(sources):
            raise ValueError("unrepresented incoming reference")
        packets.append({
            "node_id": identity,
            "prompt_sha256": hashlib.sha256(composer["prompt"].encode()).hexdigest(),
            "prompt": composer["prompt"], "parameters": composer["parameters"],
            "document": deepcopy(composer["document"]),
            "chip_bindings": chip_bindings,
            "tray_bindings": [bindings[m["id"]] for m in materials],
        })
    return {"authority": "observed_inputs_only_not_provider_payload",
            "source_graph": deepcopy(graph), "source_composers": deepcopy(composers),
            "generation_nodes": packets}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--composers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = build_packet(json.loads(args.graph.read_text()),
                              json.loads(args.composers.read_text()))
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(packet, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Canvas preparation failed ({type(error).__name__}); no provider call.\n")
    print(f"Preserved {len(packet['source_graph']['nodes'])} nodes; "
          f"bound {len(packet['generation_nodes'])} generation composers. No provider call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
