"""Inspect a preserved canvas source without inferring order or production acceptance.

This offline report keeps the input snapshot intact. A supplied selection is sent
through the existing sequence packet builder; source inspection itself never
creates Production state, fetches media, or calls a Provider.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.canvas_reference_packet import build_packet
from scripts.canvas_sequence_packet import build_sequence_packet


MEDIA_TYPES = {"image", "video", "audio"}
KNOWN_NODE_TYPES = MEDIA_TYPES | {"timeline", "group", "text", "subject"}
CLIP_FIELDS = {"clipId", "kind", "source", "sourceRange", "speed", "muted", "volume", "startTick"}
TRACK_FIELDS = {"kind", "muted", "clips"}


def _hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _issue(code: str, message: str, **context: Any) -> dict:
    return {"code": code, "message": message, **context}


def _source_graph(source: dict) -> tuple[dict | None, str, list[dict]]:
    issues = []
    raw_fields = "nodes" in source or "edges" in source
    rich_fields = "generation_nodes" in source or "source_composers" in source
    if "source_graph" in source:
        if raw_fields:
            return source.get("source_graph"), "mixed_raw_and_rich", [
                _issue("mixed_raw_and_rich_source", "Input contains a wrapped graph and top-level raw graph fields.")]
        if not rich_fields or not {"generation_nodes", "source_composers"} <= source.keys():
            issues.append(_issue("incomplete_observed_packet", "Observed packet must contain source_composers and generation_nodes."))
            return source.get("source_graph"), "rich_incomplete", issues
        return source.get("source_graph"), "observed_packet", issues
    if raw_fields and rich_fields:
        return source, "mixed_raw_and_rich", [
            _issue("mixed_raw_and_rich_source", "Raw graph fields cannot be combined with observed packet fields.")]
    if raw_fields:
        return source, "raw_graph", issues
    return None, "unsupported", [_issue("unsupported_source_shape", "Expected a raw nodes/edges graph or a preserved observed packet.")]


def _version_selection(data: dict, node_id: str | None, issues: list[dict]) -> tuple[list, dict]:
    batches = data.get("resourceBatches")
    current = data.get("resourceId")
    batch_ids = []
    if not isinstance(batches, list):
        code = "missing_resource_batches" if "resourceBatches" not in data else "invalid_resource_batches"
        issues.append(_issue(code, "Media node has no readable resource batch history.", node_id=node_id))
        batches = []
    memberships = []
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            issues.append(_issue("invalid_resource_batch", "Resource batch must be an object.", node_id=node_id, batch_index=index))
            continue
        batch_id = batch.get("id")
        if isinstance(batch_id, str) and batch_id:
            batch_ids.append(batch_id)
        else:
            issues.append(_issue("missing_resource_batch_id", "Resource batch has no identity.", node_id=node_id, batch_index=index))
        resource_ids = batch.get("resourceIds")
        if not isinstance(resource_ids, list) or any(not isinstance(r, str) or not r for r in resource_ids):
            issues.append(_issue("invalid_resource_batch_ids", "Resource batch resourceIds must be nonempty string identities.",
                                 node_id=node_id, batch_index=index))
            continue
        if current in resource_ids:
            memberships.append(batch_id if isinstance(batch_id, str) else None)
    if current is None or not isinstance(current, str) or not current:
        status = "missing_current_pointer"
    elif not batches:
        status = "current_pointer_only_no_history"
    elif memberships:
        status = "current_pointer_only"
    else:
        status = "current_pointer_not_in_history"
    return deepcopy(data.get("resourceBatches", [])), {
        "status": status,
        "current_pointer_batch_ids": memberships,
        "selected_version_id": None,
    }


def _generation_inventory(node: dict, data: dict, observed: dict | None, issues: list[dict]) -> dict:
    node_id = node.get("id")
    node_type = node.get("type")
    draft = data.get("generationDraft")
    if (draft is None and data.get("source") == "model_generated"
            and isinstance(node_type, str) and node_type in {"video", "image"}):
        issues.append(_issue("missing_generation_draft", "Model-generated media has no preserved generation draft.", node_id=node_id))
    if draft is not None and not isinstance(draft, dict):
        issues.append(_issue("invalid_generation_draft", "generationDraft must be an object.", node_id=node_id))
        draft = None
    if draft:
        for key, code, label in (("parts", "missing_generation_parts", "parts"),
                                 ("contentSettings", "missing_generation_parameters", "contentSettings"),
                                 ("references", "missing_generation_references", "references")):
            if key not in draft:
                issues.append(_issue(code, f"Generation draft is missing {label}.", node_id=node_id))
    if observed:
        for key, code, label in (("prompt", "missing_observed_prompt", "prompt"),
                                 ("parameters", "missing_observed_parameters", "parameters"),
                                 ("tray_bindings", "missing_observed_references", "tray bindings")):
            if key not in observed:
                issues.append(_issue(code, f"Observed generation packet is missing {label}.", node_id=node_id))
    parts = draft.get("parts", []) if draft else []
    references = draft.get("references", []) if draft else []
    slot_ids = []
    if draft:
        if not isinstance(parts, list):
            issues.append(_issue("invalid_generation_parts", "generationDraft.parts must be a list.", node_id=node_id))
            parts = []
        if not isinstance(references, list):
            issues.append(_issue("invalid_generation_references", "generationDraft.references must be a list.", node_id=node_id))
            references = []
        for index, reference in enumerate(references):
            if not isinstance(reference, dict) or not isinstance(reference.get("slotId"), str) or not reference.get("slotId"):
                issues.append(_issue("invalid_reference_slot", "Generation reference is missing a slot identity.",
                                     node_id=node_id, reference_index=index))
                continue
            slot = reference["slotId"]
            if slot in slot_ids:
                issues.append(_issue("duplicate_reference_slot", "Generation draft repeats a reference slot.",
                                     node_id=node_id, slot_id=slot))
            slot_ids.append(slot)
        for index, part in enumerate(parts):
            if not isinstance(part, dict):
                issues.append(_issue("invalid_generation_part", "Prompt part must be an object.", node_id=node_id, part_index=index))
                continue
            if part.get("type") == "text":
                if not isinstance(part.get("text"), str):
                    issues.append(_issue("invalid_prompt_text", "Text prompt part is missing string text.",
                                         node_id=node_id, part_index=index))
            elif part.get("type") == "extension" and part.get("extension_type") == "node":
                if part.get("object_id") not in slot_ids:
                    issues.append(_issue("unbound_prompt_slot", "Prompt node extension does not resolve to a declared slot.",
                                         node_id=node_id, part_index=index, object_id=part.get("object_id")))
            elif part.get("type") == "extension" and part.get("extension_type") == "subject":
                issues.append(_issue("unsupported_subject_capability", "Subject prompt extensions are preserved but unsupported by the sequence packet capability.",
                                     node_id=node_id, part_index=index, object_id=part.get("object_id")))
            else:
                issues.append(_issue("unsupported_prompt_part", "Prompt part kind is not supported by the sequence packet capability.",
                                     node_id=node_id, part_index=index, part_type=part.get("type")))
    return {
        "draft_kind": draft.get("kind") if draft else None,
        "parts": deepcopy(parts),
        "parameters": deepcopy(draft.get("contentSettings")) if draft else deepcopy((observed or {}).get("parameters")),
        "output_count": draft.get("outputCount") if draft else None,
        "references": deepcopy(references if draft else (observed or {}).get("tray_bindings", [])),
        "observed_prompt": deepcopy((observed or {}).get("prompt")),
        "observed_prompt_sha256": deepcopy((observed or {}).get("prompt_sha256")),
        "observed_generation": deepcopy(observed),
    }


def _node_inventory(graph: dict, observed_nodes: dict[str, dict], issues: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, list):
        issues.append(_issue("invalid_nodes", "Canvas graph nodes must be a list."))
        return [], {}
    inventory, by_id = [], {}
    for index, node in enumerate(raw_nodes):
        if not isinstance(node, dict):
            issues.append(_issue("invalid_node", "Canvas node must be an object.", node_index=index))
            inventory.append({"node_id": None, "node_type": None, "capability": "unsupported"})
            continue
        node_id, node_type = node.get("id"), node.get("type")
        if not isinstance(node_id, str) or not node_id:
            issues.append(_issue("missing_node_identity", "Canvas node is missing an identity.", node_index=index))
        elif node_id in by_id:
            issues.append(_issue("duplicate_node_identity", "Canvas node identity is duplicated.", node_id=node_id, node_index=index))
        else:
            by_id[node_id] = node
        data = node.get("data", {})
        if not isinstance(data, dict):
            issues.append(_issue("invalid_node_data", "Canvas node data must be an object.", node_id=node_id))
            data = {}
        if not isinstance(node_type, str) or not node_type:
            issues.append(_issue("missing_node_type", "Canvas node is missing a type.", node_id=node_id))
        if node_type == "subject":
            issues.append(_issue("unsupported_subject_capability", "Subject nodes are preserved but are not supported by the sequence packet capability.", node_id=node_id))
        elif not isinstance(node_type, str) or node_type not in KNOWN_NODE_TYPES:
            issues.append(_issue("unsupported_node_kind", "Canvas node type is not recognized by this source inspector.",
                                 node_id=node_id, node_type=node_type))
        media = isinstance(node_type, str) and node_type in MEDIA_TYPES
        resource_versions, version_selection = [], {"status": "not_applicable", "current_pointer_batch_ids": [], "selected_version_id": None}
        if media:
            current = data.get("resourceId")
            if not isinstance(current, str) or not current:
                issues.append(_issue("missing_resource_id", "Media node has no current resource identity.", node_id=node_id))
            resource_versions, version_selection = _version_selection(data, node_id, issues)
        generation = _generation_inventory(node, data, observed_nodes.get(node_id) if isinstance(node_id, str) else None, issues)
        entry = {
            "node_id": node_id,
            "node_type": node_type,
            "title": deepcopy(data.get("title", data.get("name"))),
            "parent_id": deepcopy(node.get("parentId")),
            "source_kind": deepcopy(data.get("source")),
            "current_resource_id": deepcopy(data.get("resourceId")),
            "resource_versions": resource_versions,
            "version_selection": version_selection,
            "generation": generation,
            "capability": "supported" if isinstance(node_type, str) and node_type in (MEDIA_TYPES | {"timeline", "group", "text"}) else "unsupported",
        }
        inventory.append(entry)
    return inventory, by_id


def _edge_inventory(graph: dict, nodes: dict[str, dict], issues: list[dict]) -> list[dict]:
    raw_edges = graph.get("edges")
    if not isinstance(raw_edges, list):
        issues.append(_issue("invalid_edges", "Canvas graph edges must be a list."))
        return []
    result, seen = [], set()
    for index, edge in enumerate(raw_edges):
        if not isinstance(edge, dict):
            issues.append(_issue("invalid_edge", "Canvas edge must be an object.", edge_index=index))
            continue
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            issues.append(_issue("missing_edge_identity", "Canvas edge is missing an identity.", edge_index=index))
        elif edge_id in seen:
            issues.append(_issue("duplicate_edge_identity", "Canvas edge identity is duplicated.", edge_id=edge_id))
        else:
            seen.add(edge_id)
        source_id, target_id = edge.get("source"), edge.get("target")
        if (not isinstance(source_id, str) or source_id not in nodes
                or not isinstance(target_id, str) or target_id not in nodes):
            issues.append(_issue("dangling_edge", "Canvas edge endpoint is absent from the node inventory.",
                                 edge_id=edge_id, source_node_id=source_id, target_node_id=target_id,
                                 node_id=target_id if isinstance(target_id, str) and target_id in nodes else None))
        if edge.get("type") != "reference":
            issues.append(_issue("uninterpreted_non_reference_edge", "Edge type is preserved but not interpreted as a selected reference dependency.",
                                 edge_id=edge_id, edge_type=edge.get("type"), target_node_id=target_id))
        result.append({"edge_id": edge_id, "source_node_id": source_id, "target_node_id": target_id,
                       "edge_type": deepcopy(edge.get("type")), "source_edge": deepcopy(edge)})
    return result


def _reference_issues(graph: dict, nodes: dict[str, dict], issues: list[dict]) -> None:
    edges = graph.get("edges", [])
    if not isinstance(edges, list):
        return
    incoming = {(edge.get("source"), edge.get("target")) for edge in edges
                if isinstance(edge, dict) and edge.get("type") == "reference"
                and isinstance(edge.get("source"), str) and isinstance(edge.get("target"), str)}
    for owner in graph.get("nodes", []):
        if not isinstance(owner, dict) or not isinstance(owner.get("data"), dict):
            continue
        draft = owner["data"].get("generationDraft")
        references = draft.get("references") if isinstance(draft, dict) else None
        if not isinstance(references, list):
            continue
        owner_id = owner.get("id")
        expected_sources = set()
        for index, reference in enumerate(references):
            if not isinstance(reference, dict):
                continue
            source_id = reference.get("nodeId")
            if isinstance(source_id, str):
                expected_sources.add(source_id)
                if source_id not in nodes:
                    issues.append(_issue("missing_reference_node", "Generation reference points to a missing node.",
                                         node_id=owner_id, referenced_node_id=source_id, reference_index=index))
                elif (source_id, owner_id) not in incoming:
                    issues.append(_issue("missing_reference_edge", "Generation reference has no matching canvas reference edge.",
                                         node_id=owner_id, referenced_node_id=source_id, reference_index=index))
            if reference.get("sourceInstanceId", source_id) != source_id:
                issues.append(_issue("reference_instance_mismatch", "Generation reference source instance differs from its node identity.",
                                     node_id=owner_id, referenced_node_id=source_id, reference_index=index))
        actual_sources = {source_id for source_id, target_id in incoming if target_id == owner_id}
        for source_id in sorted(actual_sources - expected_sources):
            issues.append(_issue("unrepresented_reference_edge", "Incoming reference edge has no declared generation slot.",
                                 node_id=owner_id, referenced_node_id=source_id))


def _clip_inventory(clip: dict, track: dict, track_index: int, clip_index: int,
                    nodes: dict[str, dict], timeline_id: str, issues: list[dict]) -> dict:
    occurrence_id = clip.get("clipId")
    source = clip.get("source") if isinstance(clip.get("source"), dict) else {}
    node_id = source.get("nodeId") if source.get("kind") == "canvas-node" else None
    track_kind = track.get("kind")
    clip_kind = clip.get("kind")
    context = {"timeline_id": timeline_id, "track_index": track_index,
               "occurrence_id": occurrence_id, "node_id": node_id}
    if not isinstance(occurrence_id, str) or not occurrence_id:
        issues.append(_issue("missing_occurrence_identity", "Timeline clip has no occurrence identity.", **context))
    if not isinstance(clip_kind, str) or clip_kind not in {"video", "audio"}:
        issues.append(_issue("unsupported_clip_kind", "Timeline clip media kind is not supported.",
                             **context, clip_kind=clip_kind))
    if source.get("kind") != "canvas-node":
        issues.append(_issue("unsupported_timeline_source_kind", "Timeline clip source is not a canvas-node reference.",
                             **context, source_kind=source.get("kind")))
    elif not isinstance(node_id, str) or node_id not in nodes:
        issues.append(_issue("dangling_timeline_source", "Timeline clip points to a missing canvas node.", **context))
    else:
        target_type = nodes[node_id].get("type")
        expected_type = "video" if track_kind == "visual" else "audio" if track_kind == "audio" else None
        if target_type == "subject":
            issues.append(_issue("unsupported_subject_capability", "Timeline source subject cannot be used as a media clip.", **context))
        elif expected_type is None or clip_kind != expected_type or target_type != expected_type:
            issues.append(_issue("timeline_media_kind_mismatch", "Timeline track, clip, and source node media kinds do not agree.",
                                 **context, track_kind=track_kind, clip_kind=clip_kind, source_node_type=target_type))
    extra_fields = sorted(set(clip) - CLIP_FIELDS)
    if extra_fields:
        issues.append(_issue("unsupported_timeline_clip_fields", "Timeline clip has fields this inspector does not interpret.",
                             **context, fields=extra_fields))
    if not isinstance(clip.get("sourceRange"), dict):
        issues.append(_issue("missing_or_invalid_clip_trim", "Timeline clip has no structured sourceRange trim.", **context))
    elif set(clip["sourceRange"]) - {"startTick", "durationTick"}:
        issues.append(_issue("unsupported_timeline_trim_fields", "Timeline sourceRange has fields this inspector does not interpret.",
                             **context, fields=sorted(set(clip["sourceRange"]) - {"startTick", "durationTick"}))
                       )
    if clip.get("speed") is None or isinstance(clip.get("speed"), bool) or not isinstance(clip.get("speed"), (int, float)):
        issues.append(_issue("missing_or_invalid_clip_speed", "Timeline clip speed is missing or not numeric.", **context))
    if "muted" not in clip:
        issues.append(_issue("missing_clip_mute_state", "Timeline clip mute state is absent.", **context))
    if "volume" not in clip:
        issues.append(_issue("missing_clip_volume", "Timeline clip volume is absent.", **context))
    return {
        "occurrence_id": occurrence_id,
        "clip_kind": deepcopy(clip_kind),
        "source_kind": deepcopy(source.get("kind")),
        "node_id": node_id,
        "source_range": deepcopy(clip.get("sourceRange")),
        "trim": deepcopy(clip.get("sourceRange")),
        "start_tick": deepcopy(clip.get("startTick")),
        "speed": deepcopy(clip.get("speed")),
        "muted": deepcopy(clip.get("muted")),
        "volume": deepcopy(clip.get("volume")),
        "unsupported_fields": extra_fields,
        "source_clip": deepcopy(clip),
    }


def _timeline_inventory(nodes: list[dict], by_id: dict[str, dict], issues: list[dict]) -> list[dict]:
    timelines = []
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != "timeline":
            continue
        timeline_id = node.get("id")
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        raw_tracks = data.get("tracks")
        if not isinstance(raw_tracks, list):
            issues.append(_issue("invalid_timeline_tracks", "Timeline tracks must be a list.", timeline_id=timeline_id))
            raw_tracks = []
        tracks = []
        for track_index, track in enumerate(raw_tracks):
            if not isinstance(track, dict):
                issues.append(_issue("invalid_timeline_track", "Timeline track must be an object.",
                                     timeline_id=timeline_id, track_index=track_index))
                continue
            track_kind = track.get("kind")
            if not isinstance(track_kind, str) or track_kind not in {"visual", "audio"}:
                issues.append(_issue("unsupported_timeline_track_kind", "Timeline track kind is not supported.",
                                     timeline_id=timeline_id, track_index=track_index, track_kind=track_kind))
            raw_clips = track.get("clips")
            if not isinstance(raw_clips, list):
                issues.append(_issue("invalid_timeline_clips", "Timeline track clips must be a list.",
                                     timeline_id=timeline_id, track_index=track_index))
                raw_clips = []
            clips, clip_ids = [], set()
            for clip_index, clip in enumerate(raw_clips):
                if not isinstance(clip, dict):
                    issues.append(_issue("invalid_timeline_clip", "Timeline clip must be an object.",
                                         timeline_id=timeline_id, track_index=track_index, clip_index=clip_index))
                    continue
                occurrence_id = clip.get("clipId")
                if isinstance(occurrence_id, str) and occurrence_id in clip_ids:
                    issues.append(_issue("duplicate_occurrence_identity", "Timeline repeats a clip occurrence identity.",
                                         timeline_id=timeline_id, track_index=track_index, occurrence_id=occurrence_id))
                if isinstance(occurrence_id, str):
                    clip_ids.add(occurrence_id)
                clips.append(_clip_inventory(clip, track, track_index, clip_index, by_id, timeline_id, issues))
            extra_fields = sorted(set(track) - TRACK_FIELDS)
            if extra_fields:
                issues.append(_issue("unsupported_timeline_track_fields", "Timeline track has fields this inspector does not interpret.",
                                     timeline_id=timeline_id, track_index=track_index, fields=extra_fields))
            tracks.append({"track_index": track_index, "track_kind": track_kind,
                           "muted": deepcopy(track.get("muted")), "clips": clips,
                           "unsupported_fields": extra_fields})
        timelines.append({"timeline_id": timeline_id, "title": deepcopy(data.get("title")), "tracks": tracks})
    return timelines


def _observed_nodes(source: dict, issues: list[dict]) -> dict[str, dict]:
    raw = source.get("generation_nodes", [])
    if not isinstance(raw, list):
        issues.append(_issue("invalid_observed_generation_nodes", "generation_nodes must be a list."))
        return {}
    result = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or not isinstance(item.get("node_id"), str):
            issues.append(_issue("invalid_observed_generation_node", "Observed generation item needs a node_id.", item_index=index))
        elif item["node_id"] in result:
            issues.append(_issue("duplicate_observed_generation_node", "Observed generation node identity is duplicated.", node_id=item["node_id"]))
        else:
            result[item["node_id"]] = item
    return result


def _selected_ids(graph: dict, selection: dict) -> list[str]:
    if isinstance(selection.get("node_ids"), list):
        return [item for item in selection["node_ids"] if isinstance(item, str)]
    timeline_id = selection.get("timeline_id")
    raw_nodes = graph.get("nodes", [])
    if not isinstance(raw_nodes, list):
        return []
    timeline = next((n for n in raw_nodes if isinstance(n, dict) and n.get("id") == timeline_id), None)
    if not timeline or not isinstance(timeline.get("data"), dict):
        return []
    tracks = timeline["data"].get("tracks", [])
    if not isinstance(tracks, list):
        return []
    selected = []
    for track in tracks:
        if not isinstance(track, dict) or track.get("kind") != "visual" or not isinstance(track.get("clips"), list):
            continue
        for clip in track["clips"]:
            if isinstance(clip, dict) and isinstance(clip.get("source"), dict):
                source = clip["source"]
                if source.get("kind") == "canvas-node" and isinstance(source.get("nodeId"), str):
                    selected.append(source["nodeId"])
    return selected


def _selection_error(selection: dict, by_id: dict[str, dict]) -> dict | None:
    has_nodes, has_timeline = "node_ids" in selection, "timeline_id" in selection
    if has_nodes == has_timeline:
        return _issue("invalid_selection", "Select either explicit node_ids or one timeline_id.", selection=deepcopy(selection))
    if has_nodes:
        ids = selection.get("node_ids")
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i for i in ids):
            return _issue("invalid_selected_node_ids", "node_ids must be a nonempty list of node identities.", selection=deepcopy(selection))
        if len(set(ids)) != len(ids):
            return _issue("duplicate_selected_node", "node_ids cannot repeat a node; use timeline occurrences for repeated clips.",
                          selection=deepcopy(selection))
        missing = [identity for identity in ids if identity not in by_id]
        if missing:
            return _issue("selected_node_missing", "Explicit selection names nodes absent from the source.", node_ids=missing)
        non_video = [{"node_id": identity, "node_type": by_id[identity].get("type")}
                     for identity in ids if by_id[identity].get("type") != "video"]
        if non_video:
            return _issue("selected_node_unsupported", "Sequence selection accepts video nodes only.", nodes=non_video)
    else:
        timeline_id = selection.get("timeline_id")
        if not isinstance(timeline_id, str) or timeline_id not in by_id:
            return _issue("selected_timeline_missing", "Selected timeline identity is absent from the source.", timeline_id=timeline_id)
        if by_id[timeline_id].get("type") != "timeline":
            return _issue("selected_node_not_timeline", "Selected timeline identity does not name a timeline node.", timeline_id=timeline_id)
    return None


def _project_selection(source: dict, graph: dict, selection: dict, by_id: dict[str, dict]) -> tuple[dict, dict]:
    """Scope canonical packet validation to the explicit chain and its direct references."""
    selected_ids = _selected_ids(graph, selection)
    unit_ids = set(selected_ids)
    timeline_ids = {selection["timeline_id"]} if "timeline_id" in selection else set()
    wanted = unit_ids | timeline_ids
    raw_edges = graph.get("edges", [])
    if isinstance(raw_edges, list):
        for edge in raw_edges:
            if (isinstance(edge, dict) and isinstance(edge.get("target"), str)
                    and edge.get("target") in unit_ids and isinstance(edge.get("source"), str)):
                wanted.add(edge["source"])
    for identity in unit_ids:
        node = by_id.get(identity)
        data = node.get("data") if isinstance(node, dict) else None
        draft = data.get("generationDraft") if isinstance(data, dict) else None
        references = draft.get("references", []) if isinstance(draft, dict) else []
        if isinstance(references, list):
            wanted.update(r["nodeId"] for r in references
                          if isinstance(r, dict) and isinstance(r.get("nodeId"), str))
    projected_graph = deepcopy(graph)
    raw_nodes = graph.get("nodes", [])
    if isinstance(raw_nodes, list):
        projected_graph["nodes"] = [deepcopy(n) for n in raw_nodes
                                    if isinstance(n, dict) and isinstance(n.get("id"), str)
                                    and n.get("id") in wanted]
    if isinstance(raw_edges, list):
        projected_graph["edges"] = [deepcopy(e) for e in raw_edges
                                    if isinstance(e, dict) and isinstance(e.get("target"), str)
                                    and e.get("target") in unit_ids]
    projected_selection = deepcopy(selection)
    projected_selection.pop("expected_source_snapshot_sha256", None)
    if source.get("source_graph") is not None:
        composers = deepcopy(source.get("source_composers"))
        if isinstance(composers, dict) and isinstance(composers.get("results"), list):
            projected_video_ids = {n.get("id") for n in projected_graph.get("nodes", [])
                                   if isinstance(n, dict) and n.get("type") == "video" and isinstance(n.get("id"), str)}
            composers["results"] = [r for r in composers["results"]
                                    if isinstance(r, dict) and isinstance(r.get("nodeId"), str)
                                    and r.get("nodeId") in projected_video_ids]
        return build_packet(projected_graph, composers), projected_selection
    projected_source = deepcopy(source)
    projected_source["nodes"] = projected_graph["nodes"]
    projected_source["edges"] = projected_graph["edges"]
    return projected_source, projected_selection


def _related_issues(issues: list[dict], selected_ids: set[str], timeline_id: str | None) -> list[dict]:
    related = []
    for item in issues:
        if "timeline_id" in item and item.get("timeline_id") != timeline_id:
            continue
        if (any(isinstance(item.get(key), str) and item.get(key) in selected_ids
                for key in ("node_id", "target_node_id", "source_node_id"))
                or (timeline_id is not None and item.get("timeline_id") == timeline_id)):
            related.append(deepcopy(item))
    return related


BLOCKING_SOURCE_ISSUES = {
    "missing_resource_id", "missing_resource_batches", "invalid_resource_batches",
    "missing_generation_draft", "invalid_generation_draft", "missing_generation_parts",
    "missing_generation_parameters", "missing_generation_references", "missing_observed_prompt",
    "missing_observed_parameters", "missing_observed_references", "unbound_prompt_slot",
    "unsupported_subject_capability", "unsupported_prompt_part", "missing_reference_node",
    "missing_reference_edge", "reference_instance_mismatch", "dangling_edge",
    "uninterpreted_non_reference_edge",
    "dangling_timeline_source", "unsupported_clip_kind", "unsupported_timeline_source_kind",
    "timeline_media_kind_mismatch", "unsupported_node_kind", "unsupported_timeline_clip_fields",
    "unsupported_timeline_track_fields", "unsupported_timeline_trim_fields", "current_pointer_not_in_history",
    "current_pointer_only_no_history",
}


def inspect_canvas_source(source: object, selection: dict | None = None) -> dict:
    """Return source facts, gaps, and (only when explicit) an existing sequence packet."""
    try:
        snapshot_hash = _hash(source)
    except (TypeError, ValueError):
        snapshot_hash = None
    report = {
        "authority": "canvas_source_inspection_only_no_production_state",
        "source_snapshot": deepcopy(source),
        "source_snapshot_sha256": snapshot_hash,
        "source_bytes_sha256": None,
        "source_format": "unsupported",
        "inventory": {"nodes": [], "node_type_counts": {}, "edges": [], "timelines": []},
        "issues": [],
        "selection": {"status": "BLOCKED", "requested": deepcopy(selection),
                      "candidate_timeline_ids": [], "selected_timeline_id": None,
                      "sequence_packet": None, "blockers": []},
        "production_acceptance": "NOT_EVALUATED",
    }
    if not isinstance(source, dict):
        issue = _issue("unsupported_source_shape", "Source must be an object containing a canvas graph.")
        report["issues"].append(issue)
        report["selection"]["blockers"] = [deepcopy(issue)]
        return report
    graph, source_format, format_issues = _source_graph(source)
    report["source_format"] = source_format
    report["issues"].extend(format_issues)
    if not isinstance(graph, dict):
        issue = _issue("unsupported_source_graph", "Canvas graph is missing or is not an object.")
        report["issues"].append(issue)
        report["selection"]["blockers"] = [deepcopy(issue)]
        return report
    observed = _observed_nodes(source, report["issues"])
    nodes, by_id = _node_inventory(graph, observed, report["issues"])
    edges = _edge_inventory(graph, by_id, report["issues"])
    timelines = _timeline_inventory(graph.get("nodes", []) if isinstance(graph.get("nodes"), list) else [],
                                    by_id, report["issues"])
    counts: dict[str, int] = {}
    for node in nodes:
        kind = node.get("node_type") if isinstance(node.get("node_type"), str) else "<missing_or_invalid>"
        counts[kind] = counts.get(kind, 0) + 1
    report["inventory"] = {"nodes": nodes, "node_type_counts": counts, "edges": edges, "timelines": timelines}
    _reference_issues(graph, by_id, report["issues"])
    report["selection"]["candidate_timeline_ids"] = [t["timeline_id"] for t in timelines]
    if selection is None:
        report["selection"]["status"] = "NEEDS_EXPLICIT_SELECTION"
        return report
    if not isinstance(selection, dict):
        issue = _issue("invalid_selection_shape", "Selection must be an object with node_ids or timeline_id.")
        report["issues"].append(issue)
        report["selection"]["status"] = "BLOCKED"
        report["selection"]["blockers"] = [deepcopy(issue)]
        return report
    if "timeline_id" in selection:
        report["selection"]["selected_timeline_id"] = selection.get("timeline_id")
    if source_format not in {"raw_graph", "observed_packet"}:
        blockers = [deepcopy(i) for i in format_issues]
        if not blockers:
            blockers = [_issue("unsupported_source_format", "Source format is not eligible for canonical sequence preparation.")]
        report["selection"]["status"] = "BLOCKED"
        report["selection"]["blockers"] = blockers
        return report
    selection_issue = _selection_error(selection, by_id)
    if selection_issue:
        report["issues"].append(selection_issue)
        report["selection"]["status"] = "BLOCKED"
        report["selection"]["blockers"] = [deepcopy(selection_issue)]
        return report
    expected_hash = selection.get("expected_source_snapshot_sha256")
    if expected_hash is not None and expected_hash != report["source_snapshot_sha256"]:
        issue = _issue("source_snapshot_mismatch", "Selection is bound to a different source snapshot.",
                       expected_source_snapshot_sha256=expected_hash,
                       actual_source_snapshot_sha256=report["source_snapshot_sha256"])
        report["issues"].append(issue)
        report["selection"]["status"] = "BLOCKED"
        report["selection"]["blockers"] = [deepcopy(issue)]
        return report
    selected_ids = set(_selected_ids(graph, selection))
    timeline_id = selection.get("timeline_id")
    selected_edges = [e for e in graph.get("edges", [])
                      if isinstance(e, dict) and isinstance(e.get("target"), str)
                      and e.get("target") in selected_ids]
    selected_ids.update(e.get("source") for e in selected_edges if isinstance(e.get("source"), str))
    for identity in list(selected_ids):
        node = by_id.get(identity)
        data = node.get("data") if isinstance(node, dict) else None
        draft = data.get("generationDraft") if isinstance(data, dict) else None
        references = draft.get("references", []) if isinstance(draft, dict) else []
        if isinstance(references, list):
            selected_ids.update(r["nodeId"] for r in references
                                if isinstance(r, dict) and isinstance(r.get("nodeId"), str))
    related = _related_issues(report["issues"], selected_ids, timeline_id)
    report["selection"]["related_issues"] = related
    try:
        selected_source, selected_selection = _project_selection(source, graph, selection, by_id)
        packet = build_sequence_packet(selected_source, selected_selection)
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        relevant = _related_issues(report["issues"], selected_ids, timeline_id)
        code = "canonical_sequence_packet_rejected"
        message = str(error) or type(error).__name__
        if "mixed raw" in message:
            code = "mixed_raw_and_rich_source"
        elif "snapshot changed" in message:
            code = "source_snapshot_mismatch"
        elif "generation draft" in message:
            code = "missing_generation_draft"
        elif "unbound prompt" in message or "unsupported" in message:
            code = "unsupported_or_unbound_selected_source"
        blocker = _issue(code, "Explicit selection could not be prepared: " + message,
                         selection=deepcopy(selection))
        if blocker["code"] not in {i["code"] for i in relevant}:
            relevant.append(blocker)
        report["selection"]["status"] = "BLOCKED"
        report["selection"]["blockers"] = relevant
        return report
    report["selection"]["sequence_packet"] = packet
    # Keep the selected closure identity distinct from the complete captured
    # document. The full immutable snapshot remains in this inspection report.
    packet["selected_closure_sha256"] = packet["source_snapshot_sha256"]
    packet["source_snapshot_sha256"] = report["source_snapshot_sha256"]
    report["selection"]["sequence_packet_sha256"] = _hash(packet)
    blockers = [deepcopy(i) for i in related if i["code"] in BLOCKING_SOURCE_ISSUES]
    if blockers:
        report["selection"]["status"] = "BLOCKED_SOURCE_GAPS"
        report["selection"]["blockers"] = blockers
    else:
        report["selection"]["status"] = "CANONICAL_PACKET_AVAILABLE"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw_source = args.source.read_bytes()
        source = json.loads(raw_source)
        selection = json.loads(args.selection.read_text(encoding="utf-8")) if args.selection else None
        report = inspect_canvas_source(source, selection)
        report["source_bytes_sha256"] = hashlib.sha256(raw_source).hexdigest()
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.exit(2, f"Canvas source inspection failed ({type(error).__name__}); no provider call.\n")
    print(f"Inspected {len(report['inventory']['nodes'])} nodes and {len(report['inventory']['edges'])} edges. No provider call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
