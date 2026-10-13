"""Bind preserved creative source parts to the inspected canvas and Registry."""

from ai_video.canvas_subject import subject_material_references
from ai_video.production.seedance_source_expression import PreservedSourceExpression


def adapted_canvas_prompt(expression):
    """Use the compiler's per-media order and source grammar, without creative prose."""
    from ai_video.production.seedance_source_expression import _adapt_source_text, _source_materials
    from ai_video.production.video_compiler import _MEDIA_ROLE_ORDER, _ROLE_ORDER
    expression = PreservedSourceExpression.model_validate(expression)
    materials = _source_materials(expression)
    def order(material):
        if material.role == "video_reference":
            return (1, _MEDIA_ROLE_ORDER["reference_video"], material.asset_id)
        role = material.role if material.role in {"first_frame", "last_frame"} else "reference"
        return (0, _ROLE_ORDER[role], material.asset_id)
    image_materials = sorted((m for m in materials if m.role != "video_reference"),
        key=lambda m: order(m)[1:])
    video_materials = sorted((m for m in materials if m.role == "video_reference"),
        key=lambda m: order(m)[1:])
    indices = {(m.role, m.asset_id, m.asset_sha256): i
        for group in (image_materials, video_materials)
        for i, m in enumerate(group, 1)}
    return _adapt_source_text(expression, indices)


def require_canvas_source_expression(*, packet, unit, row, registry, previous=None, asset_artifacts=()):
    data = row["shot"].get("preserved_source_expression")
    if data is None:
        return
    expression = PreservedSourceExpression.model_validate(data)
    original = unit["prompt_source"].get("parts")
    if not isinstance(original, list) or len(original) != len(expression.parts):
        raise ValueError("preserved source requires exact original draft parts")
    refs = {r["slot_id"]: r for r in unit["references"]}
    assets = {a.asset_id: a for a in registry.assets} if registry is not None else {}
    source_assets = {a["id"]: a for a in packet["assets"]}
    used = set()

    def material_ids(ref):
        source = source_assets[ref["node_id"]]
        if source["type"] == "subject":
            members = subject_material_references(source)
            return [members["main"]["resource_id"], *(a["resource_id"] for a in members["auxiliaries"])]
        if source["type"] != "image":
            raise ValueError("preserved Seedance source only accepts image materials")
        return [source["data"]["resourceId"]]

    def require_materials(ref, materials):
        expected = material_ids(ref)
        if len(materials) != len(expected):
            raise ValueError("preserved source omitted a reference material")
        if source_assets[ref["node_id"]]["type"] == "subject" and any(
                material.role != "identity" for material in materials):
            raise ValueError("preserved subject materials must retain identity roles")
        for resource_id, material in zip(expected, materials, strict=True):
            asset = assets.get(material.asset_id)
            receipt = (f"canvas-local-selection:{packet['source_snapshot_sha256']}:"
                       f"{ref['node_id']}:{resource_id}")
            def require_original(asset):
                if asset is None:
                    raise ValueError("preserved source material is missing")
                if asset.creation_receipt_id != receipt:
                    from ai_video.canvas_image_provenance import require_generated_canvas_selection
                    require_generated_canvas_selection(asset=asset,
                        snapshot=packet["source_snapshot_sha256"], node_id=ref["node_id"],
                        resource_id=resource_id, artifacts=asset_artifacts, previous=previous)
            replacements = row.get("reference_replacements", {})
            replacement = replacements.get(material.asset_id)
            video_replacements = [(frame_id, value) for frame_id, value in replacements.items()
                if value.get("conditioning") == "source_video"
                and value.get("video_asset_id") == material.asset_id]
            if len(video_replacements) > 1:
                raise ValueError("source video reference has ambiguous accepted-state lineage")
            if video_replacements:
                if material.role != "video_reference" or replacement is not None:
                    raise ValueError("accepted source video must retain its explicit video reference role")
                frame_id, replacement = video_replacements[0]
                original = assets.get(replacement["original_asset_id"])
                require_original(original)
                if (asset is None or replacement.get("video_asset_sha256") != material.asset_sha256
                        or asset.sha256 != material.asset_sha256):
                    raise ValueError("source video replacement differs from its exact original reference")
                if previous is None:
                    raise ValueError("source video reference requires its accepted predecessor Registry")
                from ai_video.canvas_handoff import require_canvas_state_reference, require_canvas_video_reference
                frame = assets.get(frame_id)
                if frame is None:
                    raise ValueError("source video reference lost its separately approved state frame")
                state = require_canvas_state_reference(loaded=previous, asset=frame)
                video = require_canvas_video_reference(loaded=previous, asset=asset,
                    source_shot_id=replacement["source_shot_id"])
                if (state["source_shot_id"] != replacement["source_shot_id"]
                        or state["reference"]["frame_index"] != replacement["frame_index"]
                        or state["reference"]["source_video_sha256"] != asset.sha256
                        or video["request_input_hash"] != state["source_request_hash"]):
                    raise ValueError("source video and approved state frame do not share the exact accepted source")
                selected = [ref for ref in row.get("generation", {}).get("references", ())
                    if ref.get("asset_id") == asset.asset_id and ref.get("role") == "existing_video"]
                if len(selected) != 1:
                    raise ValueError("accepted source video is not the exact selected generation input")
            elif replacement is not None:
                original = assets.get(replacement["original_asset_id"])
                require_original(original)
                if (previous is None or asset is None or asset.sha256 != material.asset_sha256):
                    raise ValueError("state reference replacement lacks its original source binding")
                from ai_video.canvas_handoff import require_canvas_state_reference
                evidence = require_canvas_state_reference(loaded=previous, asset=asset)
                if (evidence["source_shot_id"] != replacement["source_shot_id"]
                        or evidence["reference"]["frame_index"] != replacement["frame_index"]):
                    raise ValueError("state reference replacement source or frame changed")
            else:
                require_original(asset)
                if asset.sha256 != material.asset_sha256:
                    raise ValueError("preserved source material differs from its exact imported canvas resource")
        used.add(ref["slot_id"])

    for raw, part in zip(original, expression.parts, strict=True):
        if raw.get("type") == "text":
            if part.type != "text" or part.text != raw.get("text"):
                raise ValueError("preserved source changed original text")
        elif raw.get("type") == "extension":
            if part.type != "reference" or part.slot_id != raw.get("object_id"):
                raise ValueError("preserved source changed original reference slot")
            require_materials(refs[part.slot_id], part.materials)
        else:
            raise ValueError("unsupported original source part")
    remaining = [ref for slot, ref in refs.items() if slot not in used]
    if expression.implicit_references:
        if expression.contract_version == "seedance-preserved-source/1":
            if len(remaining) != 1 or remaining[0].get("canvas_role") != "firstFrame":
                raise ValueError("implicit source material requires the single original first frame")
            require_materials(remaining[0], expression.implicit_references)
        else:
            offset = 0
            for ref in remaining:
                size = len(material_ids(ref))
                require_materials(ref, expression.implicit_references[offset:offset + size])
                offset += size
            if offset != len(expression.implicit_references):
                raise ValueError("implicit source materials differ from the original tray references")
    if used != set(refs):
        raise ValueError("preserved source must retain every original reference")
