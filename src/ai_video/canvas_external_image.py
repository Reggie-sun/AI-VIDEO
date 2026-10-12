"""An exact external image handle in source inventory, never a canvas graph node."""
import json
import re

from ai_video.production.hashing import canonical_sha256


def external_image_asset(reference):
    if reference.get("type") != "image" or "nodeId" in reference:
        return None
    if (set(reference) != {"slotId", "role", "sourceInstanceId", "type", "uri"}
            or not isinstance(reference["uri"], str)
            or not re.fullmatch(r"tos-[A-Za-z0-9_-]+/[A-Za-z0-9/_-]+", reference["uri"])
            or not isinstance(reference["sourceInstanceId"], str)
            or not reference["sourceInstanceId"].startswith("history-material:")):
        raise ValueError("external image needs its exact URI and history material identity")
    instance = json.loads(reference["sourceInstanceId"].split(":", 1)[1])
    if (not isinstance(instance, list) or len(instance) != 2 or not isinstance(instance[0], str)
            or not instance[0] or type(instance[1]) is not int or instance[1] < 0):
        raise ValueError("invalid external image history material identity")
    identity = canonical_sha256({"type": "image", "uri": reference["uri"]})
    return {"id": f"external-image-{identity}", "type": "image",
        "source_binding_kind": "external_uri", "data": {"resourceId": reference["uri"]}}
