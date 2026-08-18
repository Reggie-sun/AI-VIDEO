"""Measured generated-video artifact validation and activation records."""

from __future__ import annotations

import hashlib
import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from typing import Callable, Literal

from pydantic import ConfigDict, Field, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    EgressMetadata,
    StrictModel,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFetchReceipt,
    VideoTaskObservation,
)


_SAFE_ID = re.compile(r"^[A-Za-z0-9._:/-]{1,256}$")
_SHA256 = r"^[0-9a-f]{64}$"


class _VideoArtifactStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def _video_artifact_error(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_ARTIFACT_INVALID,
        user_message=message,
        retryable=False,
    )


class MeasuredVideoMetadata(_VideoArtifactStrictModel):
    container_name: Literal["mp4"]
    codec_name: str = Field(min_length=1)
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    fps_numerator: int = Field(strict=True, gt=0)
    fps_denominator: int = Field(strict=True, gt=0)
    duration_milliseconds: int = Field(strict=True, gt=0)
    frame_count: int = Field(strict=True, gt=0)
    audio_stream_count: int = Field(strict=True, ge=0)
    size_bytes: int = Field(strict=True, gt=0)
    artifact_sha256: str = Field(pattern=_SHA256)


class VideoProbeReceipt(_VideoArtifactStrictModel):
    request_receipt_fingerprint: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    measured: MeasuredVideoMetadata
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoProbeReceipt":
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("video probe receipt content hash is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: ResolvedVideoGenerationRequest,
        fetch_receipt: VideoFetchReceipt,
        measured: MeasuredVideoMetadata,
    ) -> "VideoProbeReceipt":
        data = {
            "request_receipt_fingerprint": request.desired_generation_fingerprint,
            "resolved_generation_hash": request.resolved_generation_hash,
            "fetch_fingerprint": fetch_receipt.fetch_fingerprint,
            "measured": measured,
        }
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        return cls.model_validate(
            {
                **data,
                "content_hash": canonical_sha256(
                    candidate.model_dump(mode="json", exclude={"content_hash"})
                ),
            }
        )


class VideoProvenanceReceipt(_VideoArtifactStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    request_receipt_fingerprint: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_sha256: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str = Field(pattern=_SHA256)
    observation_fingerprint: str = Field(pattern=_SHA256)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    provider_file_id: str = Field(pattern=_SAFE_ID.pattern)
    artifact_sha256: str = Field(pattern=_SHA256)
    probe_receipt_id: str = Field(pattern=_SHA256)
    usage_license: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoProvenanceReceipt":
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("video provenance receipt content hash is invalid")
        return self

    @classmethod
    def create(
        cls,
        *,
        request: ResolvedVideoGenerationRequest,
        observation: VideoTaskObservation,
        fetch_receipt: VideoFetchReceipt,
        probe_receipt: VideoProbeReceipt,
    ) -> "VideoProvenanceReceipt":
        scope = request.activation_scope
        if scope is None:
            raise AiVideoError(
                code=ErrorCode.VIDEO_REQUEST_INVALID,
                user_message="Video activation requires durable authoring scope.",
                retryable=False,
            )
        data = {
            "generation_id": request.generation_id,
            "request_receipt_fingerprint": request.desired_generation_fingerprint,
            "resolved_generation_hash": request.resolved_generation_hash,
            "provider_kind": request.provider_kind,
            "model_id": request.model_id,
            "profile_sha256": request.provider_profile.profile_sha256,
            "paid_submit_receipt_fingerprint": fetch_receipt.paid_submit_receipt_fingerprint,
            "observation_fingerprint": observation.observation_fingerprint,
            "fetch_fingerprint": fetch_receipt.fetch_fingerprint,
            "provider_file_id": fetch_receipt.provider_file_id,
            "artifact_sha256": fetch_receipt.artifact_sha256,
            "probe_receipt_id": probe_receipt.content_hash,
            "usage_license": scope.usage_license,
        }
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        return cls.model_validate(
            {
                **data,
                "content_hash": canonical_sha256(
                    candidate.model_dump(mode="json", exclude={"content_hash"})
                ),
            }
        )


def _probe_fraction(value: object, label: str) -> Fraction:
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise _video_artifact_error(f"Measured video {label} is invalid.") from exc
    if result <= 0:
        raise _video_artifact_error(f"Measured video {label} must be positive.")
    return result


def probe_generated_video_candidate(
    held_fd: int,
    expected_request: ResolvedVideoGenerationRequest,
    fetch_receipt: VideoFetchReceipt,
    *,
    probe: Callable[[int], dict] | None = None,
    max_size_bytes: int = 2_147_483_648,
) -> tuple[bytes, MeasuredVideoMetadata, VideoProbeReceipt]:
    """Measure one held regular MP4 and reject Provider-claimed metadata."""

    opened = os.fstat(held_fd)
    if opened.st_size <= 0 or opened.st_size > max_size_bytes or opened.st_nlink != 1:
        raise _video_artifact_error("Generated video file identity is invalid.")
    position = os.lseek(held_fd, 0, os.SEEK_CUR)
    os.lseek(held_fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    total = 0
    chunks: list[bytes] = []
    while chunk := os.read(held_fd, 1024 * 1024):
        total += len(chunk)
        digest.update(chunk)
        chunks.append(chunk)
    os.lseek(held_fd, position, os.SEEK_SET)
    if (
        total != opened.st_size
        or total != fetch_receipt.size_bytes
        or digest.hexdigest() != fetch_receipt.artifact_sha256
    ):
        raise _video_artifact_error("Fetched video bytes do not match durable evidence.")
    if probe is None:
        from ai_video.production.hyperframes import probe_clip_fd

        probe = probe_clip_fd
    try:
        raw = probe(held_fd)
        streams = raw["streams"]
        format_info = raw["format"]
        video_streams = [item for item in streams if item.get("codec_type") == "video"]
        audio_streams = [item for item in streams if item.get("codec_type") == "audio"]
        if len(video_streams) != 1:
            raise ValueError("exactly one video stream is required")
        video_stream = video_streams[0]
        format_names = set(str(format_info["format_name"]).split(","))
        if not format_names.intersection({"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}):
            raise ValueError("container is not MP4")
        fps = _probe_fraction(video_stream.get("avg_frame_rate"), "FPS")
        duration = Decimal(str(video_stream.get("duration", format_info["duration"])))
        duration_milliseconds = int(
            (duration * 1000).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        frame_count = int(video_stream["nb_frames"])
        measured = MeasuredVideoMetadata(
            container_name="mp4",
            codec_name=str(video_stream["codec_name"]),
            width=video_stream["width"],
            height=video_stream["height"],
            fps_numerator=fps.numerator,
            fps_denominator=fps.denominator,
            duration_milliseconds=duration_milliseconds,
            frame_count=frame_count,
            audio_stream_count=len(audio_streams),
            size_bytes=total,
            artifact_sha256=fetch_receipt.artifact_sha256,
        )
    except (AiVideoError, InvalidOperation):
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise _video_artifact_error("Generated video probe evidence is invalid.") from exc

    output = expected_request.effective_output
    expected_duration = getattr(output, "duration_seconds", None)
    expected_frames = getattr(output, "frame_count", None)
    expected_width = getattr(output, "width", None)
    expected_height = getattr(output, "height", None)
    expected_fps = getattr(output, "fps", None)
    if (
        expected_frames is None
        and expected_duration is not None
        and expected_fps is not None
    ):
        derived_frames = Fraction(str(expected_duration)) * Fraction(str(expected_fps))
        if derived_frames.denominator == 1:
            expected_frames = derived_frames.numerator
    if (
        output.container != "mp4"
        or output.mime_type != "video/mp4"
        or expected_width is not None
        and measured.width != expected_width
        or expected_height is not None
        and measured.height != expected_height
        or expected_fps is not None
        and Fraction(measured.fps_numerator, measured.fps_denominator) != expected_fps
        or expected_duration is not None
        and measured.duration_milliseconds != expected_duration * 1000
        or expected_frames is not None
        and measured.frame_count != expected_frames
        or output.native_audio != (measured.audio_stream_count > 0)
    ):
        raise _video_artifact_error(
            "Measured video does not match the exact resolved output contract."
        )
    receipt = VideoProbeReceipt.create(
        request=expected_request,
        fetch_receipt=fetch_receipt,
        measured=measured,
    )
    return b"".join(chunks), measured, receipt


def build_generated_video_asset_record(
    *,
    request: ResolvedVideoGenerationRequest,
    measured: MeasuredVideoMetadata,
    probe_receipt: VideoProbeReceipt,
    provenance: VideoProvenanceReceipt,
    egress: EgressMetadata,
    cost_receipt_id: str | None,
) -> AssetRecord:
    scope = request.activation_scope
    if scope is None:
        raise AiVideoError(
            code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Video activation requires durable authoring scope.",
            retryable=False,
        )
    original = scope.request
    return AssetRecord(
        asset_id=request.output_asset_id,
        asset_type=AssetType.VIDEO,
        artifact_path=Path(f"assets/files/{measured.artifact_sha256}.mp4"),
        sha256=measured.artifact_sha256,
        size_bytes=measured.size_bytes,
        mime_type="video/mp4",
        duration_seconds=measured.duration_milliseconds / 1000,
        width=measured.width,
        height=measured.height,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(
            name=request.provider_kind,
            version=request.provider_profile.profile_version,
        ),
        input_artifact_ids=original.input_artifact_ids,
        input_fingerprint=request.resolved_generation_hash,
        creation_receipt_id=provenance.content_hash,
        usage_license=scope.usage_license,
        egress=egress,
        cost_receipt_id=cost_receipt_id,
        video_metadata=VideoAssetMetadata(
            container_name=measured.container_name,
            codec_name=measured.codec_name,
            width=measured.width,
            height=measured.height,
            fps_numerator=measured.fps_numerator,
            fps_denominator=measured.fps_denominator,
            duration_milliseconds=measured.duration_milliseconds,
            frame_count=measured.frame_count,
            probe_receipt_id=probe_receipt.content_hash,
            request_receipt_fingerprint=request.desired_generation_fingerprint,
            resolved_generation_hash=request.resolved_generation_hash,
            provenance_receipt_id=provenance.content_hash,
        ),
    )


__all__ = [
    "MeasuredVideoMetadata",
    "VideoProbeReceipt",
    "VideoProvenanceReceipt",
    "build_generated_video_asset_record",
    "probe_generated_video_candidate",
]
