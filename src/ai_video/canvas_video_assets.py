"""Prepare explicitly selected local MP4 references for the existing Registry.

This module snapshots and measures local bytes only. It does not write project
state, contact a Provider, or claim that a video was generated or accepted.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from ai_video.canvas_authoring import _safe_id
from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRecord, AssetRegistrySnapshot, AssetSourceKind, AssetType, ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.paths import (
    _open_regular_file_nofollow, _read_regular_file_nofollow, canonical_video_asset_path,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact


_MAX_BYTES = 50 * 1024 * 1024
_MAX_DURATION_MS = 15_000
_MIN_DURATION_MS = 2_000
_PROBE_CONFIG = {
    "format": "mov",
    "protocol_whitelist": ["file"],
    "enable_drefs": 0,
    "use_absolute_path": 0,
    "show": ["streams", "format"],
}


def _sha256_fd(descriptor: int) -> str:
    digest = hashlib.sha256()
    offset = 0
    while chunk := os.pread(descriptor, 1024 * 1024, offset):
        digest.update(chunk)
        offset += len(chunk)
    return digest.hexdigest()


def _probe_canvas_mp4(payload: bytes, ffprobe_executable: str | Path) -> dict[str, object]:
    """Measure one byte snapshot with an explicitly configured, file-only ffprobe."""
    executable = Path(ffprobe_executable)
    if not executable.is_absolute() or executable.name != "ffprobe":
        raise ValueError("video import requires an explicit absolute ffprobe executable")
    parent = executable.parent.resolve(strict=True)
    with _open_regular_file_nofollow(executable, contained_by=parent) as (probe_fd, opened), \
            tempfile.TemporaryDirectory(prefix="ai-video-canvas-video-") as temporary:
        probe_sha = _sha256_fd(probe_fd)
        input_path = Path(temporary) / "selected.mp4"
        with input_path.open("xb") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
        if input_path.read_bytes() != payload:
            raise ValueError("local video probe snapshot differs from selected bytes")
        arguments = (
            f"/proc/self/fd/{probe_fd}", "-v", "error", "-protocol_whitelist", "file",
            "-f", "mov", "-enable_drefs", "0", "-use_absolute_path", "0",
            "-show_streams", "-show_format", "-of", "json", str(input_path),
        )
        try:
            completed = subprocess.run(arguments, check=True, capture_output=True,
                timeout=45, pass_fds=(probe_fd,))
            document = json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            raise ValueError("selected local MP4 could not be measured by ffprobe") from exc
        if (_sha256_fd(probe_fd) != probe_sha
                or os.fstat(probe_fd).st_size != opened.st_size
                or input_path.read_bytes() != payload):
            raise ValueError("ffprobe or local video bytes changed during measurement")

    if not isinstance(document, dict) or not isinstance(document.get("format"), dict):
        raise ValueError("ffprobe returned incomplete MP4 metadata")
    format_name = document["format"].get("format_name")
    streams = document.get("streams")
    videos = [item for item in streams if isinstance(item, dict)
        and item.get("codec_type") == "video"] if isinstance(streams, list) else []
    if (not isinstance(format_name, str) or "mp4" not in format_name.split(",")
            or len(videos) != 1):
        raise ValueError("selected source must contain exactly one MP4 video stream")
    stream = videos[0]
    try:
        width, height = int(stream["width"]), int(stream["height"])
        codec = stream["codec_name"]
        fps_text = stream["avg_frame_rate"]
        fps_match = re.fullmatch(r"([1-9][0-9]*)/([1-9][0-9]*)", fps_text)
        if fps_match is None:
            raise ValueError
        fps_numerator, fps_denominator = map(int, fps_match.groups())
        if fps_numerator % fps_denominator:
            raise ValueError
        fps_numerator, fps_denominator = fps_numerator // fps_denominator, 1
        frame_count = int(stream["nb_frames"])
        duration = Decimal(document["format"]["duration"])
        if not isinstance(codec, str) or not codec.strip() or not duration.is_finite():
            raise ValueError
        duration_ms = int((duration * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (KeyError, TypeError, ValueError, InvalidOperation, ArithmeticError) as exc:
        raise ValueError("ffprobe metadata lacks integer FPS, frame count or finite duration") from exc
    if (width <= 0 or height <= 0 or fps_numerator <= 0 or frame_count <= 0
            or not _MIN_DURATION_MS <= duration_ms <= _MAX_DURATION_MS):
        raise ValueError("local MP4 dimensions, duration, FPS or frame count are out of bounds")
    measured = {
        "container_name": "mp4", "codec_name": codec, "width": width, "height": height,
        "fps_numerator": fps_numerator, "fps_denominator": fps_denominator,
        "duration_milliseconds": duration_ms, "frame_count": frame_count,
    }
    probe_config_sha = canonical_sha256(_PROBE_CONFIG)
    measurement_sha = canonical_sha256({"kind": "canvas-local-video-measurement/1",
        "input_sha256": hashlib.sha256(payload).hexdigest(), "input_size_bytes": len(payload),
        "ffprobe_sha256": probe_sha, "probe_config_sha256": probe_config_sha,
        "measured": measured})
    return {**measured, "ffprobe_sha256": probe_sha,
        "probe_config_sha256": probe_config_sha, "measurement_sha256": measurement_sha}


def prepare_canvas_video_assets(*, packet, selections, allowed_asset_root, ffprobe_executable):
    """Build Registry records and immutable artifacts from exact local MP4 selections."""
    root = Path(allowed_asset_root).resolve(strict=True)
    source_assets = {item["id"]: item for item in packet["assets"]}
    snapshot = packet.get("source_snapshot_sha256")
    if not isinstance(snapshot, str) or not re.fullmatch(r"[0-9a-f]{64}", snapshot):
        raise ValueError("local video selection requires an exact source snapshot")
    records, artifacts = [], {}
    selected_nodes, selected_resources = set(), set()
    for selection in selections:
        required = {"asset_id", "node_id", "resource_id", "path", "usage_license", "tool"}
        optional = {"input_artifact_ids"}
        if not isinstance(selection, dict) or not required <= set(selection) or set(selection) - required - optional:
            raise ValueError("MP4 selection requires exact node/resource, path, license and tool identity")
        asset_id = _safe_id(selection["asset_id"])
        node_id, resource_id = selection["node_id"], selection["resource_id"]
        source = source_assets.get(node_id)
        if (source is None or source.get("type") != "video"
                or source.get("data", {}).get("resourceId") != resource_id
                or not isinstance(resource_id, str) or not resource_id):
            raise ValueError("selected MP4 pointer differs from the exact canvas video resource")
        if (node_id in selected_nodes or resource_id in selected_resources
                or Path(selection["path"]).suffix.lower() != ".mp4"):
            raise ValueError("local MP4 selections must be unique and use an .mp4 file")
        selected_nodes.add(node_id)
        selected_resources.add(resource_id)
        tool = ToolIdentity.model_validate(selection["tool"])
        input_artifact_ids = tuple(selection.get("input_artifact_ids", ()))
        if (any(not isinstance(value, str) or not value for value in input_artifact_ids)
                or len(set(input_artifact_ids)) != len(input_artifact_ids)):
            raise ValueError("local video input artifact identities must be unique strings")
        if not isinstance(selection["usage_license"], str) or not selection["usage_license"].strip():
            raise ValueError("local MP4 selection requires its declared usage license")
        raw = _read_regular_file_nofollow(Path(selection["path"]), contained_by=root)
        if not 0 < raw.size_bytes <= _MAX_BYTES:
            raise ValueError("selected local MP4 must be at most 50 MiB")
        measured = _probe_canvas_mp4(raw.data, ffprobe_executable)
        if (not _MIN_DURATION_MS <= measured["duration_milliseconds"] <= _MAX_DURATION_MS
                or measured["fps_denominator"] != 1 or measured["fps_numerator"] <= 0):
            raise ValueError("selected local MP4 requires bounded duration and integer FPS")
        measured_fields = {key: measured[key] for key in (
            "container_name", "codec_name", "width", "height", "fps_numerator",
            "fps_denominator", "duration_milliseconds", "frame_count")}
        request_fingerprint = canonical_sha256({"kind": "canvas-local-video-selection-request/1",
            "source_snapshot_sha256": snapshot, "node_id": node_id, "resource_id": resource_id,
            "asset_id": asset_id, "sha256": raw.file_sha256, "size_bytes": raw.size_bytes,
            "usage_license": selection["usage_license"], "tool": tool.model_dump(mode="json"),
            "input_artifact_ids": list(input_artifact_ids)})
        receipt_data = {"kind": "canvas-local-video-selection/1",
            "source_snapshot_sha256": snapshot, "node_id": node_id, "resource_id": resource_id,
            "asset_id": asset_id, "sha256": raw.file_sha256, "size_bytes": raw.size_bytes,
            "measured": measured_fields, "measurement": {
                "ffprobe_sha256": measured["ffprobe_sha256"],
                "probe_config_sha256": measured["probe_config_sha256"],
                "measurement_sha256": measured["measurement_sha256"]},
            "request_fingerprint": request_fingerprint,
            "usage_license": selection["usage_license"], "tool": tool.model_dump(mode="json"),
            "input_artifact_ids": list(input_artifact_ids),
            "source_binding": "director_declared_local_bytes",
            "provider_generation": "NOT_CLAIMED", "platform_adoption": "NOT_EVALUATED"}
        reference = authoring_input_reference(receipt_data)
        receipt_payload = authoring_input_payload(receipt_data)
        metadata = VideoAssetMetadata(container_name="mp4", codec_name=str(measured["codec_name"]),
            width=int(measured["width"]), height=int(measured["height"]),
            fps_numerator=int(measured["fps_numerator"]), fps_denominator=int(measured["fps_denominator"]),
            duration_milliseconds=int(measured["duration_milliseconds"]), frame_count=int(measured["frame_count"]),
            probe_receipt_id=f"canvas-local-video-measurement:{measured['measurement_sha256']}",
            request_receipt_fingerprint=request_fingerprint,
            resolved_generation_hash=str(measured["measurement_sha256"]),
            provenance_receipt_id=f"canvas-local-video-selection:{reference.content_hash}")
        asset = AssetRecord(asset_id=asset_id, asset_type=AssetType.VIDEO,
            artifact_path=canonical_video_asset_path(raw.file_sha256), sha256=raw.file_sha256,
            size_bytes=raw.size_bytes, mime_type="video/mp4",
            duration_seconds=metadata.duration_milliseconds / 1000,
            width=metadata.width, height=metadata.height, source_kind=AssetSourceKind.IMPORTED,
            tool=tool, input_artifact_ids=input_artifact_ids, input_fingerprint=reference.content_hash,
            creation_receipt_id=f"canvas-local-video-selection:{reference.content_hash}",
            usage_license=selection["usage_license"], video_metadata=metadata)
        media_path = asset.artifact_path
        artifacts[media_path] = PreparedArtifact(media_path, raw.data, raw.file_sha256)
        receipt_path = Path(reference.reference)
        artifacts[receipt_path] = PreparedArtifact(receipt_path, receipt_payload,
            hashlib.sha256(receipt_payload).hexdigest())
        records.append(asset)
    if len({asset.asset_id for asset in records}) != len(records):
        raise ValueError("selected MP4 asset labels must be unique")
    registry = AssetRegistrySnapshot(schema_version="2.2", revision_id="0" * 64, content_hash="0" * 64,
        assets=tuple(sorted(records, key=lambda asset: asset.asset_id)))
    identity = registry_semantic_sha256(registry)
    sealed = registry.model_copy(update={"revision_id": identity, "content_hash": identity})
    return sealed, tuple(artifacts[path] for path in sorted(artifacts))
