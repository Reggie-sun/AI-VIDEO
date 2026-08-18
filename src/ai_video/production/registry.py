from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
import wave

from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import _canonical_track_bytes, caption_timing_fingerprint
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    CaptionTrack,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_video_asset_path,
    resolve_contained_path,
)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.ASSET_REGISTRY_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def registry_semantic_sha256(registry: AssetRegistrySnapshot) -> str:
    payload = registry.model_dump(
        mode="json",
        exclude={"content_hash", "revision_id"},
    )
    return canonical_sha256(payload)


def _verify_asset(record: AssetRecord, root: Path, asset_root: Path) -> Path:
    sealed_asset = (
        record.audio_metadata is not None
        or record.caption_metadata is not None
        or record.video_metadata is not None
    )
    if record.video_metadata is not None:
        expected = canonical_video_asset_path(record.sha256)
        if record.artifact_path != expected:
            raise _invalid(
                "Generated video asset path must be content-addressed: "
                f"{record.asset_id}",
                str(record.artifact_path),
            )
    try:
        resolved = resolve_contained_path(
            root,
            record.artifact_path,
            allowed_root=root / "assets" if sealed_asset else asset_root,
        )
    except ValueError as exc:
        raise _invalid(f"Asset path is unsafe: {record.asset_id}", str(exc)) from exc
    if not resolved.is_file():
        raise _invalid(f"Asset file does not exist: {record.asset_id}", str(resolved))
    try:
        payload = (
            _read_regular_file_nofollow(resolved, contained_by=root / "assets").data
            if sealed_asset
            else resolved.read_bytes()
        )
    except (OSError, ValueError) as exc:
        raise _invalid(f"Could not verify asset file: {record.asset_id}", str(exc)) from exc
    if len(payload) != record.size_bytes:
        raise _invalid(f"Asset size mismatch: {record.asset_id}", str(resolved))
    if hashlib.sha256(payload).hexdigest() != record.sha256:
        raise _invalid(f"Asset hash mismatch: {record.asset_id}", str(resolved))
    if record.audio_metadata is not None:
        _verify_audio_asset(record, payload)
    if record.caption_metadata is not None:
        _verify_caption_asset(record, payload, root)
    return resolved


def _verify_audio_asset(record: AssetRecord, payload: bytes) -> None:
    metadata = record.audio_metadata
    assert metadata is not None
    if record.mime_type not in {"audio/wav", "audio/x-wav"}:
        raise _invalid(f"Asset audio metadata is invalid: {record.asset_id}")
    try:
        with wave.open(BytesIO(payload), "rb") as source:
            measured = (
                source.getcomptype(),
                source.getsampwidth(),
                source.getframerate(),
                source.getnchannels(),
                source.getnframes(),
            )
    except (OSError, EOFError, wave.Error) as exc:
        raise _invalid(
            f"Asset audio metadata could not be verified: {record.asset_id}",
            str(exc),
        ) from exc
    expected = (
        "NONE",
        2,
        metadata.sample_rate_hz,
        metadata.channels,
        metadata.duration_samples,
    )
    if metadata.codec_name != "pcm_s16le" or measured != expected:
        raise _invalid(f"Asset audio metadata does not match bytes: {record.asset_id}")


def _verify_caption_asset(record: AssetRecord, payload: bytes, root: Path) -> None:
    metadata = record.caption_metadata
    assert metadata is not None
    if record.mime_type != "application/json":
        raise _invalid(f"Asset caption metadata is invalid: {record.asset_id}")
    try:
        track = CaptionTrack.model_validate_json(payload)
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(
            f"Asset caption bytes are invalid: {record.asset_id}", str(exc)
        ) from exc
    expected_metadata = (
        track.caption_track_id,
        track.language,
        track.source_audio_asset_id,
        track.source_audio_sha256,
        track.script_hash,
        track.transcript_hash,
        len(track.segments),
        sum(len(segment.words or ()) for segment in track.segments),
        track.segmentation_policy.policy_id,
        track.segmentation_policy.policy_version,
        track.alignment_receipt_id,
        track.timing_fingerprint,
        track.style_reference_id,
    )
    actual_metadata = (
        metadata.caption_track_id,
        metadata.language,
        metadata.source_audio_asset_id,
        metadata.source_audio_sha256,
        metadata.script_hash,
        metadata.transcript_hash,
        metadata.segment_count,
        metadata.word_count,
        metadata.segmentation_policy_id,
        metadata.segmentation_policy_version,
        metadata.alignment_receipt_id,
        metadata.timing_fingerprint,
        metadata.style_reference_id,
    )
    if (
        payload != _canonical_track_bytes(track)
        or not verify_artifact_hash(track)
        or expected_metadata != actual_metadata
    ):
        raise _invalid(f"Asset caption metadata does not match bytes: {record.asset_id}")
    if track.timing_fingerprint != caption_timing_fingerprint(track):
        raise _invalid(f"Asset caption timing fingerprint is invalid: {record.asset_id}")
    if metadata.style_content_hash is None:
        return
    style_relative = Path(f"assets/styles/{metadata.style_content_hash}.json")
    try:
        style_path = resolve_contained_path(
            root, style_relative, allowed_root=root / "assets/styles"
        )
        style_bytes = _read_regular_file_nofollow(
            style_path, contained_by=root / "assets/styles"
        ).data
        style_payload = json.loads(style_bytes)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise _invalid(
            f"Asset caption style could not be verified: {record.asset_id}", str(exc)
        ) from exc
    if (
        not isinstance(style_payload, dict)
        or hashlib.sha256(style_bytes).hexdigest() != metadata.style_content_hash
    ):
        raise _invalid(f"Asset caption style identity is invalid: {record.asset_id}")


def load_asset_registry(
    path: str | Path,
    project_root: str | Path,
    asset_root: str | Path,
) -> tuple[AssetRegistrySnapshot, dict[str, Path]]:
    try:
        root = Path(project_root).resolve()
        registry_path = resolve_contained_path(
            root,
            Path(path),
            allowed_root=root / "assets",
        )
        resolved_asset_root = Path(asset_root).resolve()
        resolved_asset_root.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise _invalid("Asset registry path configuration is unsafe.", str(exc)) from exc
    try:
        registry = AssetRegistrySnapshot.model_validate_json(
            registry_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load asset registry: {registry_path}", str(exc)) from exc
    ids = [asset.asset_id for asset in registry.assets]
    if len(ids) != len(set(ids)):
        raise _invalid("Asset registry contains duplicate asset_id values.")
    if registry_semantic_sha256(registry) != registry.content_hash:
        raise _invalid("Asset registry content hash does not match.")
    if registry.revision_id != registry.content_hash:
        raise _invalid("Asset registry revision_id must equal content_hash.")
    if registry_path.name != f"registry.{registry.revision_id}.json":
        raise _invalid("Asset registry filename does not match revision_id.")
    asset_paths = {
        item.asset_id: _verify_asset(item, root, resolved_asset_root)
        for item in registry.assets
    }
    return registry, asset_paths
