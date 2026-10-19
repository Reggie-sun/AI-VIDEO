"""Cleaned development sources retain their original failed-media capture."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Literal

from pydantic import model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetRecord, AssetRegistrySnapshot, AssetSourceKind, AssetType, ToolIdentity, VideoAssetMetadata
from ai_video.production.paths import _read_regular_file_nofollow, canonical_video_asset_path
from ai_video.production.repair_input_admission import (
    REPAIR_INPUT_TOOL, RepairPreviewInputAdmissionReceipt, repair_input_receipt_path,
)
from ai_video.production.video_cleanup_media import VideoCleanupReceipt, prepare_video_cleanup


CLEANED_REPAIR_INPUT_TOOL = ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="4")


class CleanedRepairInputAdmissionReceipt(RepairPreviewInputAdmissionReceipt):
    """Base artifact/probe remain original Provider bytes; cleanup.output is local."""

    contract_version: Literal["development-repair-input/4"] = "development-repair-input/4"
    source_asset: AssetRecord
    cleanup: VideoCleanupReceipt

    @model_validator(mode="after")
    def _derived_identity(self):
        source = self.source_asset
        if (source.tool.name != REPAIR_INPUT_TOOL.name or source.tool.version not in {"2", "3"}
                or source.source_kind is not AssetSourceKind.IMPORTED
                or source.sha256 != self.artifact_sha256 or source.size_bytes != self.size_bytes
                or source.asset_id == self.asset_id or source.usage_license != self.usage_license
                or self.cleanup.source != self.preview_probe.measured
                or self.cleanup.output.artifact_sha256 == self.artifact_sha256):
            raise ValueError("Cleaned repair input lost its exact original source binding")
        return self


def cleaned_repair_asset(receipt: CleanedRepairInputAdmissionReceipt) -> AssetRecord:
    measured = receipt.cleanup.output
    original_probe = receipt.preview_probe
    metadata = VideoAssetMetadata(container_name=measured.container_name, codec_name=measured.codec_name,
        width=measured.width, height=measured.height, fps_numerator=measured.fps_numerator,
        fps_denominator=measured.fps_denominator, duration_milliseconds=measured.duration_milliseconds,
        frame_count=measured.frame_count, probe_receipt_id=receipt.cleanup.content_hash,
        request_receipt_fingerprint=original_probe.request_receipt_fingerprint,
        resolved_generation_hash=original_probe.resolved_generation_hash,
        provenance_receipt_id=receipt.content_hash)
    return AssetRecord(asset_id=receipt.asset_id, asset_type=AssetType.VIDEO,
        artifact_path=canonical_video_asset_path(measured.artifact_sha256),
        sha256=measured.artifact_sha256, size_bytes=measured.size_bytes, mime_type="video/mp4",
        width=measured.width, height=measured.height, duration_seconds=measured.duration_milliseconds / 1000,
        source_kind=AssetSourceKind.DERIVED, tool=CLEANED_REPAIR_INPUT_TOOL,
        input_artifact_ids=(receipt.source_asset.asset_id,), input_fingerprint=receipt.content_hash,
        creation_receipt_id=receipt.content_hash, usage_license=receipt.usage_license,
        video_metadata=metadata)


def prepare_cleaned_repair_input(*, cleanup_plan, cleanup_tools, viewing_proxy=False, **arguments):
    """Capture original then derive; canonical bootstrap remains the only writer."""
    from ai_video.production.repair_input_admission import prepare_repair_input
    from ai_video.production.registry import registry_semantic_sha256
    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production._state_commit_contracts import PreparedArtifact

    output_id = arguments["asset_id"]
    if any(record.asset_id == output_id for record in arguments["registry"].assets):
        raise ValueError("Cleanup output asset id already exists")
    if viewing_proxy and any(record.asset_id == output_id + "-viewing" for record in arguments["registry"].assets):
        raise ValueError("Cleanup viewing asset id already exists")
    original_args = {**arguments, "asset_id": output_id + "-source"}
    if arguments.get("preview_use") is None or arguments.get("preview_probe") is None:
        raise ValueError("Cleanup requires an exact sealed preview use and original probe")
    registry, captured = prepare_repair_input(**original_args)
    source = next(record for record in registry.assets if record.asset_id == original_args["asset_id"])
    source_bytes = next(item.payload for item in captured if item.relative_path == source.artifact_path)
    source_receipt_bytes = next(item.payload for item in captured
        if item.relative_path == repair_input_receipt_path(source.creation_receipt_id))
    import json
    values = json.loads(source_receipt_bytes)
    result = prepare_video_cleanup(source_bytes=source_bytes, plan=cleanup_plan, tools=cleanup_tools)
    values.update(contract_version="development-repair-input/4", asset_id=output_id,
                  source_asset=source.model_dump(mode="json"), cleanup=result.receipt.model_dump(mode="json"))
    values["content_hash"] = canonical_sha256(values)
    receipt = CleanedRepairInputAdmissionReceipt.model_validate(values)
    asset = cleaned_repair_asset(receipt)
    extra_assets, extra_artifacts = (), ()
    if viewing_proxy:
        from ai_video.production.video_cleanup_viewing_admission import prepare_viewing_repair_input
        viewing, extra_artifacts = prepare_viewing_repair_input(master_asset=asset,
            master_receipt=receipt, source_bytes=result.media_bytes, tools=cleanup_tools)
        extra_assets = (viewing,)
    merged = registry.model_copy(update={"assets": (*registry.assets, asset, *extra_assets)})
    digest = registry_semantic_sha256(merged)
    merged = AssetRegistrySnapshot.model_validate({**merged.model_dump(mode="python"),
        "revision_id": digest, "content_hash": digest})
    payload = _canonical_json_bytes(receipt)
    source_root = Path(arguments["source_root"]).resolve(strict=True)
    if (_read_regular_file_nofollow(source_root / "state/manifest.json", contained_by=source_root / "state").data
            != receipt.source_manifest_json.encode("utf-8")):
        raise ValueError("Original source changed during cleanup preparation")
    return merged, (*captured,
        PreparedArtifact(asset.artifact_path, result.media_bytes, asset.sha256),
        PreparedArtifact(repair_input_receipt_path(receipt.content_hash), payload, sha256(payload).hexdigest()),
        *extra_artifacts)


def verify_cleaned_repair_input(record, root, payload):
    from ai_video.production.repair_input_admission import verify_repair_input

    receipt = CleanedRepairInputAdmissionReceipt.model_validate_json(payload)
    if record != cleaned_repair_asset(receipt):
        raise ValueError("Cleaned repair asset differs from its exact derivation")
    original = verify_repair_input(receipt.source_asset, root)
    values = receipt.model_dump(mode="json")
    for key, value in original.model_dump(mode="json").items():
        if key not in {"contract_version", "content_hash", "asset_id"} and values[key] != value:
            raise ValueError("Cleanup capture differs from its preserved original receipt")
    raw = _read_regular_file_nofollow(root / receipt.source_asset.artifact_path, contained_by=root / "assets")
    if raw.file_sha256 != receipt.artifact_sha256 or raw.size_bytes != receipt.size_bytes:
        raise ValueError("Cleaned repair source bytes changed")
    return receipt
