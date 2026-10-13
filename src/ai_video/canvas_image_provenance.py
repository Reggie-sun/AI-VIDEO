"""Prepare evidence for an exact copy of an explicitly generated external PNG.

The supplied generation record is source evidence, not model qualification,
platform adoption, human identity attestation or media acceptance.
"""
import hashlib
import json
from pathlib import Path

from ai_video.production.models import AssetSourceKind, ToolIdentity, SourceReference
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.state_commit import PreparedArtifact
from ai_video.production.authoring_input import authoring_input_reference, authoring_input_payload


def prepare_generated_canvas_source(*, declared, measured, observation, root):
    if not isinstance(declared, dict) or set(declared) != {"record_path", "record_sha256", "tool"}:
        raise ValueError("generated source requires exact record path, hash and declared tool")
    record_path = Path(declared["record_path"])
    if record_path.is_absolute() or ".." in record_path.parts:
        raise ValueError("generated source record must be contained in the data root")
    tool = ToolIdentity.model_validate(declared["tool"])
    raw = _read_regular_file_nofollow(root / record_path, contained_by=root).data
    digest = hashlib.sha256(raw).hexdigest()
    if digest != declared["record_sha256"]:
        raise ValueError("generated source record bytes differ from the declared hash")
    record = json.loads(raw)
    facts = {"sha256": measured.sha256, "size_bytes": measured.size_bytes,
             "width": measured.width, "height": measured.height}
    if not isinstance(record, dict) or any(type(record.get(k)) is not type(v) or record[k] != v
                                          for k, v in facts.items()):
        raise ValueError("generated source record does not identify this exact measured PNG")
    source = {"kind": "canvas-generated-source-record/1", "record_sha256": digest,
              "record_utf8": raw.decode("utf-8")}
    source_reference = authoring_input_reference(source)
    source_payload = authoring_input_payload(source)
    receipt = {**observation, "kind": "canvas-generated-image-source/1",
        "derivation": "exact_external_generated_image_copy", "generated_source": {
            "record_path": source_reference.reference, "record_sha256": digest,
            "declared_tool": tool.model_dump(mode="json")}}
    reference = authoring_input_reference(receipt)
    identity = reference.content_hash
    payload = authoring_input_payload(receipt)
    return {"source_kind": AssetSourceKind.DERIVED,
        "tool": ToolIdentity(name="canvas-generated-image-source", version="1"),
        "input_fingerprint": identity, "creation_receipt_id": f"canvas-generated-image-source:{identity}"}, (
        PreparedArtifact(Path(source_reference.reference), source_payload, hashlib.sha256(source_payload).hexdigest()),
        PreparedArtifact(Path(reference.reference), payload, hashlib.sha256(payload).hexdigest()))


def require_generated_canvas_selection(*, asset, snapshot, node_id, resource_id,
                                       artifacts=(), previous=None):
    """Reopen the sealed copy evidence before preserving an original reference."""
    from ai_video.production.authoring_input import require_authoring_input, reopen_authoring_input, PREFIX
    if asset.source_kind is AssetSourceKind.GENERATED and asset.tool.name == "seedream":
        # The canvas resource explicitly names an existing canonical output.
        # Its paid/wire/request chain was checked by the standard project reader.
        from ai_video.production.project import load_production_project
        if previous is None or resource_id != asset.asset_id:
            raise ValueError("canonical generated selection must name its exact original output")
        reopened = load_production_project(previous.root / "project.yaml")
        if (reopened.manifest != previous.manifest or asset not in reopened.registry.assets
                or not asset.egress.remote or asset.cost_receipt_id is None):
            raise ValueError("canonical generated selection lacks current paid image provenance")
        return
    if (asset.source_kind is not AssetSourceKind.DERIVED
            or asset.tool != ToolIdentity(name="canvas-generated-image-source", version="1")
            or asset.creation_receipt_id != f"canvas-generated-image-source:{asset.input_fingerprint}"):
        raise ValueError("generated canvas selection lacks its exact copy identity")

    def reopen(reference):
        matches = [a for a in artifacts if a.relative_path.as_posix() == reference.reference]
        if len(matches) == 1:
            return require_authoring_input(reference, matches[0].payload)
        if not matches and previous is not None and reference in previous.project.source_provenance:
            return reopen_authoring_input(previous.root, reference)
        raise ValueError("generated canvas selection lacks sealed source evidence")

    receipt = reopen(SourceReference(kind="user_input", content_hash=asset.input_fingerprint,
        reference=f"{PREFIX}{asset.input_fingerprint}.json"))
    expected = {"kind": "canvas-generated-image-source/1", "derivation": "exact_external_generated_image_copy",
        "source_snapshot_sha256": snapshot, "node_id": node_id, "resource_id": resource_id,
        "asset_id": asset.asset_id, "sha256": asset.sha256, "size_bytes": asset.size_bytes,
        "width": asset.width, "height": asset.height, "usage_license": asset.usage_license,
        "source_binding": "director_declared", "platform_bytes_verified": False,
        "platform_adoption": "NOT_EVALUATED"}
    if any(type(receipt.get(k)) is not type(v) or receipt[k] != v for k, v in expected.items()):
        raise ValueError("generated copy differs from the original canvas resource")
    declared = receipt["generated_source"]
    path = declared["record_path"]
    source = reopen(SourceReference(kind="user_input", reference=path, content_hash=Path(path).stem))
    raw = source["record_utf8"].encode("utf-8")
    if (source["kind"] != "canvas-generated-source-record/1"
            or source["record_sha256"] != declared["record_sha256"]
            or hashlib.sha256(raw).hexdigest() != declared["record_sha256"]):
        raise ValueError("generated source record differs from the exact copy evidence")
    record = json.loads(raw)
    if any(type(record.get(k)) is not type(expected[k]) or record[k] != expected[k]
           for k in ("sha256", "size_bytes", "width", "height")):
        raise ValueError("generated source record differs from the selected image")
