"""A separate viewing proxy preserves its strict repair master lineage."""
from __future__ import annotations

from hashlib import sha256
from typing import Literal

from pydantic import model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import AssetRecord, AssetSourceKind, AssetType, ToolIdentity, VideoAssetMetadata
from ai_video.production.paths import _read_regular_file_nofollow, canonical_video_asset_path
from ai_video.production.repair_input_admission import REPAIR_INPUT_TOOL, repair_input_receipt_path
from ai_video.production.video_cleanup_admission import CleanedRepairInputAdmissionReceipt
from ai_video.production.video_cleanup_viewing import CleanupViewingProxyReceipt, prepare_cleanup_viewing_proxy


VIEWING_REPAIR_INPUT_TOOL = ToolIdentity(name=REPAIR_INPUT_TOOL.name, version="5")


class ViewingRepairInputAdmissionReceipt(CleanedRepairInputAdmissionReceipt):
    contract_version: Literal["development-repair-input/5"] = "development-repair-input/5"
    master_asset: AssetRecord
    viewing: CleanupViewingProxyReceipt

    @model_validator(mode="after")
    def _viewing_lineage(self):
        master = self.master_asset
        if (master.tool.name != REPAIR_INPUT_TOOL.name or master.tool.version != "4"
                or master.source_kind is not AssetSourceKind.DERIVED
                or master.sha256 != self.cleanup.output.artifact_sha256
                or master.size_bytes != self.cleanup.output.size_bytes
                or master.usage_license != self.usage_license
                or master.asset_id in {self.asset_id, self.source_asset.asset_id}
                or self.viewing.source != self.cleanup.output):
            raise ValueError("Viewing proxy lost its exact cleanup master binding")
        return self


def viewing_repair_asset(receipt: ViewingRepairInputAdmissionReceipt) -> AssetRecord:
    measured = receipt.viewing.output
    probe = receipt.preview_probe
    metadata = VideoAssetMetadata(container_name=measured.container_name, codec_name=measured.codec_name,
        width=measured.width, height=measured.height, fps_numerator=measured.fps_numerator,
        fps_denominator=measured.fps_denominator, duration_milliseconds=measured.duration_milliseconds,
        frame_count=measured.frame_count, probe_receipt_id=receipt.viewing.content_hash,
        request_receipt_fingerprint=probe.request_receipt_fingerprint,
        resolved_generation_hash=probe.resolved_generation_hash,
        provenance_receipt_id=receipt.content_hash)
    return AssetRecord(asset_id=receipt.asset_id, asset_type=AssetType.VIDEO,
        artifact_path=canonical_video_asset_path(measured.artifact_sha256),
        sha256=measured.artifact_sha256, size_bytes=measured.size_bytes, mime_type="video/mp4",
        width=measured.width, height=measured.height, duration_seconds=measured.duration_milliseconds / 1000,
        source_kind=AssetSourceKind.DERIVED, tool=VIEWING_REPAIR_INPUT_TOOL,
        input_artifact_ids=(receipt.master_asset.asset_id,), input_fingerprint=receipt.content_hash,
        creation_receipt_id=receipt.content_hash, usage_license=receipt.usage_license,
        video_metadata=metadata)


def prepare_viewing_repair_input(*, master_asset, master_receipt, source_bytes, tools):
    from ai_video.production._state_commit_common import _canonical_json_bytes
    from ai_video.production._state_commit_contracts import PreparedArtifact

    result = prepare_cleanup_viewing_proxy(source_bytes=source_bytes, tools=tools)
    values = master_receipt.model_dump(mode="json")
    values.update(contract_version="development-repair-input/5",
        asset_id=master_asset.asset_id + "-viewing", master_asset=master_asset.model_dump(mode="json"),
        viewing=result.receipt.model_dump(mode="json"))
    values["content_hash"] = canonical_sha256(values)
    receipt = ViewingRepairInputAdmissionReceipt.model_validate(values)
    asset = viewing_repair_asset(receipt)
    payload = _canonical_json_bytes(receipt)
    return asset, (
        PreparedArtifact(asset.artifact_path, result.media_bytes, asset.sha256),
        PreparedArtifact(repair_input_receipt_path(receipt.content_hash), payload, sha256(payload).hexdigest()),
    )


def verify_viewing_repair_input(record, root, payload):
    from ai_video.production.repair_input_admission import verify_repair_input

    receipt = ViewingRepairInputAdmissionReceipt.model_validate_json(payload)
    if record != viewing_repair_asset(receipt):
        raise ValueError("Viewing repair asset differs from its exact derivation")
    master = verify_repair_input(receipt.master_asset, root)
    if master.contract_version != "development-repair-input/4":
        raise ValueError("Viewing repair source is not a preserved cleanup master")
    values = receipt.model_dump(mode="json")
    for key, value in master.model_dump(mode="json").items():
        if key not in {"contract_version", "content_hash", "asset_id"} and values[key] != value:
            raise ValueError("Viewing proxy differs from its preserved master receipt")
    raw = _read_regular_file_nofollow(root / receipt.master_asset.artifact_path, contained_by=root / "assets")
    if raw.file_sha256 != receipt.viewing.source.artifact_sha256 or raw.size_bytes != receipt.viewing.source.size_bytes:
        raise ValueError("Viewing proxy master bytes changed")
    return receipt
