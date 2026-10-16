"""Ordinary project data to the shared service; no story-specific executor."""
from copy import deepcopy
from pathlib import Path

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.canvas_assets import prepare_canvas_png_assets
from ai_video.canvas_authoring import input_hash
from ai_video.canvas_production import CanvasProductionService
from ai_video.canvas_source_expression import adapted_canvas_prompt
from ai_video.canvas_subject import subject_material_references
from ai_video.production.models import AssetRegistrySnapshot
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.seedance_source_expression import source_parts_sha256


def _source_error(unit, field, message):
    return AiVideoError(code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=f"Canvas occurrence {unit['occurrence_id']} ({field}): {message}")


def prepare_canvas_project_data(*, inspection, definition, data_root, ffprobe_executable=None):
    """Preserve source text/chips and compute all internal byte identities locally."""
    if set(definition) - {"schema_version", "source", "selection", "direction", "images", "videos",
            "source_grounding", "reference_aliases"}:
        raise ValueError("unknown canvas project data fields")
    if definition.get("schema_version") != "canvas-project-data/1":
        raise ValueError("unsupported canvas project data schema")
    # Validate the selected inspection via the same service entry, before files.
    service = CanvasProductionService.from_inspection(inspection=inspection,
        committer=None, direction=definition["direction"])
    packet = service.packet
    root = Path(data_root).resolve(strict=True)
    selections = deepcopy(definition.get("images", []))
    for image in selections:
        image["path"] = root / image["path"]
    registry, artifacts = prepare_canvas_png_assets(packet=packet, selections=selections,
        allowed_asset_root=root)
    imported = {(s["node_id"], s["resource_id"]): s["asset_id"] for s in selections}
    if len(imported) != len(selections):
        raise ValueError("duplicate canvas image resource selection")
    video_selections = deepcopy(definition.get("videos", []))
    if not isinstance(video_selections, list):
        raise ValueError("canvas videos must be an explicit selection list")
    if video_selections:
        if ffprobe_executable is None:
            raise ValueError("local video import requires an explicit absolute ffprobe executable")
        for selection in video_selections:
            if isinstance(selection, dict) and "path" in selection:
                selection["path"] = root / selection["path"]
        from ai_video.canvas_video_assets import prepare_canvas_video_assets

        video_registry, video_artifacts = prepare_canvas_video_assets(packet=packet,
            selections=video_selections, allowed_asset_root=root,
            ffprobe_executable=ffprobe_executable)
        image_ids = {asset.asset_id for asset in registry.assets}
        video_ids = {asset.asset_id for asset in video_registry.assets}
        if image_ids & video_ids:
            raise ValueError("canvas image/video asset label collision")
        combined = AssetRegistrySnapshot(schema_version="2.2", revision_id="0" * 64,
            content_hash="0" * 64,
            assets=tuple(sorted((*registry.assets, *video_registry.assets), key=lambda asset: asset.asset_id)))
        identity = registry_semantic_sha256(combined)
        registry = combined.model_copy(update={"revision_id": identity, "content_hash": identity})
        artifacts = (*artifacts, *video_artifacts)
    imported_videos = {(s["node_id"], s["resource_id"]): s["asset_id"] for s in video_selections}
    if len(imported_videos) != len(video_selections):
        raise ValueError("duplicate canvas video resource selection")
    assets = {a.asset_id: a for a in registry.assets}
    nodes = {a["id"]: a for a in packet["assets"]}
    direction = deepcopy(definition["direction"])
    rows = {r["occurrence_id"]: r for r in direction["shots"]}
    groundings = definition.get("source_grounding", {})
    aliases = definition.get("reference_aliases", {})
    if (set(groundings) | set(aliases)) - set(rows):
        raise ValueError("source grounding names an unselected occurrence")
    for unit in packet["units"]:
        row = rows[unit["occurrence_id"]]
        references = {r["slot_id"]: r for r in unit["references"]}
        generation = row.get("generation", {})
        roles = {r["asset_id"]: r["role"] for r in generation.get("references", [])}
        def materials(ref):
            node = nodes[ref["node_id"]]
            if node["type"] == "subject":
                members = subject_material_references(node)
                ids = [members["main"]["resource_id"], *[a["resource_id"] for a in members["auxiliaries"]]]
            elif node["type"] == "image":
                ids = [node["data"]["resourceId"]]
            elif node["type"] == "video":
                ids = [node["data"].get("resourceId")]
            else:
                raise _source_error(unit, "source.references", "Audio/video references need an explicit supported route")
            values = []
            for resource in ids:
                is_video = node["type"] == "video"
                aid = (imported_videos if is_video else imported).get((node["id"], resource))
                if aid is None:
                    raise _source_error(unit, "images", "Missing local bytes for an original reference material")
                if is_video:
                    selected = [r for r in generation.get("references", []) if r.get("asset_id") == aid]
                    if len(selected) != 1 or selected[0].get("role") != "existing_video":
                        raise _source_error(unit, "generation.references",
                            "A source video must be selected exactly once with the existing_video role")
                    role = "video_reference"
                else:
                    role = {"character_reference": "identity", "scene_reference": "scene",
                            "approved_keyframe": "first_frame", "terminal_frame": "last_frame"}.get(roles.get(aid))
                if role is None or (node["type"] == "subject" and role != "identity"):
                    raise _source_error(unit, "generation.references", "Reference responsibility must be explicit and retain subject identity")
                values.append({"asset_id": aid, "asset_sha256": assets[aid].sha256, "role": role})
            return values
        parts, used = [], set()
        raw_parts = unit["prompt_source"].get("parts")
        if not isinstance(raw_parts, list) or not raw_parts:
            raise _source_error(unit, "source.prompt.parts", "Reproduction requires the original structured prompt parts")
        for raw in raw_parts:
            if raw["type"] == "text":
                parts.append({"type": "text", "text": raw["text"]})
            elif raw["type"] == "extension":
                slot = raw["object_id"]
                parts.append({"type": "reference", "slot_id": slot, "materials": materials(references[slot])})
                used.add(slot)
            else:
                raise _source_error(unit, "source.prompt.parts", "Unsupported original prompt part")
        implicit = []
        for slot, ref in references.items():
            if slot not in used:
                implicit.extend(materials(ref))
        grounding = deepcopy(groundings.get(unit["occurrence_id"], {}))
        if set(grounding) - {"opening", "closing"}:
            raise _source_error(unit, "source_grounding", "Source grounding requires explicit opening/closing facts")
        for endpoint in grounding.values():
            for fact in endpoint:
                if fact.get("kind") == "reference":
                    if fact.get("asset_id") not in assets:
                        raise _source_error(unit, "source_grounding", "Grounding refers to an unselected asset")
                    fact["asset_sha256"] = assets[fact["asset_id"]].sha256
        expression = {"contract_version": "seedance-preserved-source/2", "parts": parts, "implicit_references": implicit,
            "source_sha256": source_parts_sha256(parts, implicit), **grounding}
        expression["image_aliases"] = []
        for alias in aliases.get(unit["occurrence_id"], []):
            if set(alias) != {"label", "slot_id"} or alias["slot_id"] not in references:
                raise _source_error(unit, "reference_aliases", "Reference alias must name an original tray slot")
            expression["image_aliases"].append({"label": alias["label"],
                "asset_ids": [m["asset_id"] for m in materials(references[alias["slot_id"]])]})
        try:
            prompt = adapted_canvas_prompt(expression)
        except ValueError as error:
            raise _source_error(unit, "shot.preserved_source_expression",
                "Original parts, material roles or reference aliases conflict") from error
        for field in ("dialogue", "narration"):
            spoken = row["shot"].get(field, "")
            if spoken and (not isinstance(spoken, str) or spoken not in unit["source_text"]):
                raise _source_error(unit, f"shot.{field}", "Reproduction speech must be quoted from the original canvas text")
        authored = row["shot"].get("intent")
        if authored is not None and authored != prompt:
            raise _source_error(unit, "shot.intent", "Director intent differs from the original mechanically adapted canvas prompt")
        row["shot"].update(intent=prompt, preserved_source_expression=expression)
        row.setdefault("adaptation_reason", "Mechanical reference indexing; original text retained verbatim")
        if generation:
            action = generation.setdefault("generation_intent", {}).setdefault("subject_action", {})
            if action.get("progression", prompt) != prompt:
                raise _source_error(unit, "generation.generation_intent.subject_action.progression",
                    "Reproduction progression expands the canvas source")
            action["progression"] = prompt
    return packet, direction, registry, artifacts


def open_canvas_project(*, inspection, definition, data_root, committer, resume=True,
                        ffprobe_executable=None, **runtime):
    project_path = committer.project_root / "project.yaml"
    if resume and project_path.exists():
        from ai_video.production.project import load_production_project
        loaded = load_production_project(project_path)
        packet = CanvasProductionService.from_inspection(inspection=inspection,
            committer=committer, direction=definition["direction"]).packet
        source = next(s for s in loaded.project.source_provenance if s.reference == "canvas-director-data")
        from ai_video.production.authoring_input import PREFIX, reopen_authoring_input
        reference = next(s for s in loaded.project.source_provenance if s.reference.startswith(PREFIX)
            and s.content_hash == source.content_hash)
        stored = reopen_authoring_input(loaded.root, reference)
        if (input_hash(stored) != source.content_hash or stored["packet"] != packet
                or definition["direction"]["project_id"] != loaded.project.project_id):
            raise ValueError("resumed canvas project differs from the inspected source selection")
        direction = stored["direction"]
        registry, artifacts = loaded.registry, ()
    else:
        packet, direction, registry, artifacts = prepare_canvas_project_data(
            inspection=inspection, definition=definition, data_root=data_root,
            ffprobe_executable=ffprobe_executable)
    service = CanvasProductionService(committer=committer, packet=packet, direction=direction, **runtime)
    return service, registry, artifacts
