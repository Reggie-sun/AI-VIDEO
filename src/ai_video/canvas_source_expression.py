"""Bind preserved creative source parts to the inspected canvas and Registry."""

from ai_video.canvas_subject import subject_material_references
from ai_video.production.seedance_source_expression import PreservedSourceExpression


def require_canvas_source_expression(*, packet, unit, row, registry):
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
            if (asset is None or asset.sha256 != material.asset_sha256
                    or asset.creation_receipt_id != receipt):
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
        if len(remaining) != 1 or remaining[0].get("canvas_role") != "firstFrame":
            raise ValueError("implicit source material requires the single original first frame")
        require_materials(remaining[0], expression.implicit_references)
    if used != set(refs):
        raise ValueError("preserved source must retain every original reference")
