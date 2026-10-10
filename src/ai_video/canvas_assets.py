"""Prepare explicit local PNG selections for the existing Registry/bootstrap owner.

The source pointer is a director assertion. Measured bytes are a separate fact;
this helper never certifies that a file was served by the platform or adopted by
its user, and never downloads or changes an image.
"""
from pathlib import Path
import hashlib

from ai_video.canvas_authoring import input_hash, _safe_id
from ai_video.production.image import _measure_png
from ai_video.production.models import AssetRecord, AssetRegistrySnapshot, AssetSourceKind, AssetType, ToolIdentity
from ai_video.production.paths import canonical_image_asset_path
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact
from ai_video.production.paths import _read_regular_file_nofollow


def prepare_canvas_png_assets(*, packet, selections, allowed_asset_root):
    """Compute identities from ordinary node/resource/file selections, without writes."""
    root = Path(allowed_asset_root).resolve(strict=True)
    source_assets = {a["id"]: a for a in packet["assets"]}
    records, artifacts = [], {}
    for selection in selections:
        if set(selection) != {"asset_id", "node_id", "resource_id", "path", "usage_license"}:
            raise ValueError("PNG selection requires asset label, node/resource, path and license")
        aid = _safe_id(selection["asset_id"])
        source = source_assets[selection["node_id"]]
        if source["type"] != "image" or source["data"]["resourceId"] != selection["resource_id"]:
            raise ValueError("selected PNG pointer differs from the preserved canvas reference")
        raw = _read_regular_file_nofollow(Path(selection["path"]), contained_by=root)
        measured = _measure_png(raw.data)
        observation = {"kind": "canvas-local-png-selection/1", "source_binding": "director_declared",
            "platform_bytes_verified": False, "platform_adoption": "NOT_EVALUATED",
            "source_snapshot_sha256": packet["source_snapshot_sha256"],
            "node_id": selection["node_id"], "resource_id": selection["resource_id"],
            "asset_id": aid, "sha256": measured.sha256, "size_bytes": measured.size_bytes,
            "width": measured.width, "height": measured.height, "usage_license": selection["usage_license"]}
        identity = input_hash(observation)
        path = canonical_image_asset_path(measured.sha256)
        records.append(AssetRecord(asset_id=aid, asset_type=AssetType.IMAGE, artifact_path=path,
            sha256=measured.sha256, size_bytes=measured.size_bytes, mime_type="image/png",
            width=measured.width, height=measured.height, source_kind=AssetSourceKind.IMPORTED,
            tool=ToolIdentity(name="canvas-local-png-selection", version="1"),
            input_fingerprint=identity, creation_receipt_id=(f"canvas-local-selection:"
                f"{packet['source_snapshot_sha256']}:{selection['node_id']}:{selection['resource_id']}"),
            usage_license=selection["usage_license"]))
        artifacts[path] = PreparedArtifact(path, raw.data, hashlib.sha256(raw.data).hexdigest())
    if len({a.asset_id for a in records}) != len(records):
        raise ValueError("selected asset labels must be unique")
    registry = AssetRegistrySnapshot(revision_id="0" * 64, content_hash="0" * 64,
        assets=tuple(sorted(records, key=lambda a: a.asset_id)))
    identity = registry_semantic_sha256(registry)
    return registry.model_copy(update={"revision_id": identity, "content_hash": identity}), tuple(
        artifacts[p] for p in sorted(artifacts))
