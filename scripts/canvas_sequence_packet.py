"""Offline continuous-canvas preparation; never a Production writer or executor.

Read a preserved canvas packet or raw canvas document plus an explicit selection.
Reference edges do not establish story order or accepted terminal state.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from ai_video.production.video_transition import (
    BoundaryKind, CausalDimension, CausalEdgeSemantics, CausalStateChange,
    ContinuityObligation,
)
from scripts.canvas_reference_packet import _index, build_packet


def _hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _occurrences(nodes: dict, selection: dict) -> tuple[list[dict], dict | None]:
    if ("node_ids" in selection) == ("timeline_id" in selection):
        raise ValueError("select explicit node_ids or one timeline_id")
    if "node_ids" in selection:
        ids = selection["node_ids"]
        if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids):
            raise ValueError("explicit node order must be nonempty and unique")
        return [{"occurrence_id": n, "node_id": n} for n in ids], None
    timeline = nodes[selection["timeline_id"]]
    if timeline["type"] != "timeline":
        raise ValueError("selected node is not a timeline")
    data = timeline["data"]
    if "tracks" in data:
        tracks = [t for t in data["tracks"] if t["kind"] == "visual"]
        if len(tracks) != 1:
            raise ValueError("exactly one visual track is required")
        clips = tracks[0]["clips"]
    else:
        clips = data["clips"]
    if not clips:
        raise ValueError("empty timeline")
    _index(clips, "clipId")
    result = []
    for clip in clips:
        if clip["kind"] != "video" or clip["source"]["kind"] != "canvas-node":
            raise ValueError("timeline contains an unresolved non-video source")
        result.append({"occurrence_id": clip["clipId"], "node_id": clip["source"]["nodeId"]})
    return result, deepcopy(timeline)


def _unit_source(node: dict, observed: dict | None) -> tuple[dict, str, object, list[dict]]:
    if observed is not None:
        text = observed["prompt"]
        if hashlib.sha256(text.encode()).hexdigest() != observed["prompt_sha256"]:
            raise ValueError("observed prompt hash mismatch")
        return (deepcopy(observed), text, deepcopy(observed["parameters"]),
                deepcopy(observed["tray_bindings"]))
    draft = node["data"].get("generationDraft")
    if not draft or draft.get("kind", "video") != "video":
        raise ValueError("selected video lacks its generation draft")
    refs = draft["references"]
    slots = _index(refs, "slotId")
    text = []
    for part in draft["parts"]:
        if part["type"] == "text":
            text.append(part["text"])
        elif (part["type"] == "extension" and part.get("extension_type") == "node"
              and part["object_id"] in slots):
            continue
        else:
            raise ValueError("unsupported or unbound prompt part")
    for ref in refs:
        if ref.get("sourceInstanceId", ref["nodeId"]) != ref["nodeId"]:
            raise ValueError("draft reference instance mismatch")
    return (deepcopy(draft), "".join(text), deepcopy(draft["contentSettings"]),
            [{"slot_id": r["slotId"], "node_id": r["nodeId"],
              "canvas_role": r.get("role")} for r in refs])


def _boundary(source: dict, target: dict, authored: dict | None) -> dict:
    result = {"source_occurrence_id": source["occurrence_id"],
              "target_occurrence_id": target["occurrence_id"],
              "source_prompt_sha256": source["source_text_sha256"],
              "target_prompt_sha256": target["source_text_sha256"],
              "status": "BLOCKED_MISSING_AUTHORING"}
    if authored is None:
        return result
    for key, unit in [("source_close_quote", source), ("target_open_quote", target)]:
        quote = authored[key]
        if not isinstance(quote, str) or not quote.strip() or quote not in unit["source_text"]:
            raise ValueError("continuity quote is not verbatim source evidence")
        result[key] = quote
    obligation = ContinuityObligation(authored["continuity_obligation"])
    changes = [CausalStateChange.model_validate(c) for c in authored["causal_state_changes"]]
    dimensions = [c.dimension for c in changes]
    if len(set(dimensions)) != len(dimensions):
        raise ValueError("duplicate causal dimensions")
    if obligation is ContinuityObligation.FULL_CONTINUITY and set(dimensions) != set(CausalDimension):
        raise ValueError("full continuity requires all causal dimensions")
    result["planning_arguments"] = {
        "boundary_kind": BoundaryKind(authored["boundary_kind"]).value,
        "continuity_obligation": obligation.value,
        "causal_edge_semantics": CausalEdgeSemantics(authored["causal_edge_semantics"]).value,
        "causal_state_changes": [c.model_dump(mode="json") for c in changes],
    }
    result["status"] = "AUTHORED_NOT_MEDIA_VERIFIED"
    return result


def build_sequence_packet(source: dict, selection: dict, *, resolution: str = "480p") -> dict:
    """Keep source facts separate from authored transitions and generation defaults.

The result cannot authorize submission or materialize accepted source state.
Original ticks are retained without inferring a timebase or rendering a timeline.
"""
    if resolution not in {"480p", "720p", "1080p"}:
        raise ValueError("unsupported preparation resolution")
    if "source_graph" in source and "source_composers" not in source:
        raise ValueError("preserved canvas packet is missing source composers")
    graph = source.get("source_graph", source)
    nodes = _index(graph["nodes"], "id")
    edges = _index(graph["edges"], "id")
    for e in edges.values():
        if e["source"] not in nodes or e["target"] not in nodes:
            raise ValueError("dangling canvas edge")
    if "source_composers" in source:
        rebuilt = build_packet(graph, source["source_composers"])
        if rebuilt["generation_nodes"] != source.get("generation_nodes"):
            raise ValueError("preserved canvas packet differs from its observed source")
    observed = _index(source.get("generation_nodes", []), "node_id")
    occurrences, timeline = _occurrences(nodes, selection)
    units, assets = [], {}
    for occurrence in occurrences:
        node = nodes[occurrence["node_id"]]
        if node["type"] != "video":
            raise ValueError("sequence must select video nodes")
        prompt, text, parameters, references = _unit_source(node, observed.get(node["id"]))
        if not text.strip():
            raise ValueError("empty video prompt")
        _index(references, "slot_id")
        incoming = [e["source"] for e in edges.values()
                    if e["target"] == node["id"] and e["type"] == "reference"]
        if len(set(incoming)) != len(incoming):
            raise ValueError("duplicate reference edge")
        if set(incoming) != {r["node_id"] for r in references}:
            raise ValueError("reference edges and material bindings differ")
        for ref in references:
            asset = nodes[ref["node_id"]]
            resource_id = asset["data"]["resourceId"]
            if (not isinstance(resource_id, str) or not resource_id
                    or asset["type"] not in {"image", "video", "audio"}
                    or ref.get("resource_id", resource_id) != resource_id
                    or ref.get("kind", asset["type"]) != asset["type"]):
                raise ValueError("reference resource identity mismatch")
            ref.update(resource_id=resource_id, kind=asset["type"])
            assets[asset["id"]] = deepcopy(asset)
        units.append({**occurrence, "title": node["data"].get("title"),
                      "prompt_source": prompt, "source_text": text,
                      "source_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                      "prompt_source_sha256": _hash(prompt),
                      "observed_parameters": parameters, "references": references})
    authored = {}
    pairs = {(a["occurrence_id"], b["occurrence_id"]) for a, b in zip(units, units[1:])}
    for edge in selection.get("boundaries", []):
        pair = (edge["source_occurrence_id"], edge["target_occurrence_id"])
        if pair not in pairs or pair in authored:
            raise ValueError("boundary is duplicate or does not follow selected order")
        authored[pair] = edge
    boundaries = [_boundary(a, b, authored.get((a["occurrence_id"], b["occurrence_id"])))
                  for a, b in zip(units, units[1:])]
    return {
        "authority": "development_preparation_only_not_production_state",
        "source_snapshot_sha256": _hash(source), "selection_sha256": _hash(selection),
        "generation_defaults": {"resolution": resolution},
        "order_evidence": "explicit_selection" if timeline is None else "observed_timeline",
        "timeline_source": timeline, "units": units,
        "assets": list(assets.values()), "boundaries": boundaries,
        "next_owner": "ai_video.planning.sequence_continuity.build_sequence_video_planning_request",
        "required_before_execution": ["approved Storyboard and Shot intents", "exact registered reference bytes",
                                      "accepted predecessor media and actual close-state evidence",
                                      "current Planner/Router and paid authorization"],
        "production_acceptance": "NOT_EVALUATED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resolution", choices=("480p", "720p", "1080p"), default="480p")
    args = parser.parse_args()
    try:
        result = build_sequence_packet(json.loads(args.source.read_text(encoding="utf-8")),
                                       json.loads(args.selection.read_text(encoding="utf-8")),
                                       resolution=args.resolution)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Canvas sequence preparation failed ({type(error).__name__}); no provider call.\n")
    print(f"Prepared {len(result['units'])} units and {len(result['boundaries'])} boundaries. No provider call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
