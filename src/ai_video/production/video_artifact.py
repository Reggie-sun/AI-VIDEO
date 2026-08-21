"""Measured generated-video artifact validation and activation records."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
from typing import Callable, Literal

from pydantic import (
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image import MeasuredPng, measure_png_bytes
from ai_video.production.local_video import (
    LocalVideoFetchReceipt,
    LocalVideoTaskObservation,
)
from ai_video.production.models import (
    AssetRecord,
    AssetSourceKind,
    AssetType,
    EgressMetadata,
    QaVerdict,
    RegistrySnapshotPointer,
    StrictModel,
    ToolIdentity,
    VideoAssetMetadata,
)
from ai_video.production.review import (
    GeneratedShotContinuityEvidence,
    TrackedGeneratedShotContinuityMeasurements,
    adjudicate_generated_shot_continuity,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    TerminalFrameEvidence,
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


@dataclass(frozen=True)
class TerminalFrameExtractionResult:
    png_bytes: bytes
    extractor_name: str
    extractor_version: str


class TerminalFrameExtractionReceipt(_VideoArtifactStrictModel):
    source_shot_id: str = Field(pattern=_SAFE_ID.pattern)
    source_shot_revision: int = Field(strict=True, ge=1)
    source_shot_content_hash: str = Field(pattern=_SHA256)
    source_video_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    source_video_sha256: str = Field(pattern=_SHA256)
    source_generation_id: str = Field(pattern=_SAFE_ID.pattern)
    source_request_input_hash: str = Field(pattern=_SHA256)
    source_resolved_generation_hash: str = Field(pattern=_SHA256)
    source_provenance_receipt_id: str = Field(pattern=_SAFE_ID.pattern)
    source_container_name: Literal["mp4"]
    source_codec_name: str = Field(min_length=1)
    source_width: int = Field(strict=True, gt=0)
    source_height: int = Field(strict=True, gt=0)
    source_fps_numerator: int = Field(strict=True, gt=0)
    source_fps_denominator: int = Field(strict=True, gt=0)
    source_duration_milliseconds: int = Field(strict=True, gt=0)
    source_frame_count: int = Field(strict=True, gt=0)
    frame_index: int = Field(strict=True, ge=0)
    timestamp_numerator: int = Field(strict=True, ge=0)
    timestamp_denominator: int = Field(strict=True, gt=0)
    selection_rule: Literal["generated_candidate_terminal"]
    extraction_contract_version: Literal["terminal-frame-v1"]
    extractor_name: str = Field(pattern=_SAFE_ID.pattern)
    extractor_version: str = Field(pattern=_SAFE_ID.pattern)
    extracted_asset_id: str = Field(pattern=_SAFE_ID.pattern)
    extracted_sha256: str = Field(pattern=_SHA256)
    extracted_mime_type: Literal["image/png"]
    extracted_size_bytes: int = Field(strict=True, gt=0)
    extracted_width: int = Field(strict=True, gt=0)
    extracted_height: int = Field(strict=True, gt=0)
    extracted_color_space: Literal["unmeasured"]
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "TerminalFrameExtractionReceipt":
        if self.frame_index != self.source_frame_count - 1:
            raise ValueError("terminal extraction must select the last source frame")
        expected = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-extraction/1",
                **self.model_dump(mode="json", exclude={"content_hash"}),
            }
        )
        if self.content_hash != expected:
            raise ValueError("terminal extraction receipt content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "TerminalFrameExtractionReceipt":
        data = dict(values)
        candidate = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            {
                "schema": "ai-video-terminal-frame-extraction/1",
                **candidate.model_dump(
                    mode="json", exclude={"content_hash"}, warnings=False
                ),
            }
        )
        return cls.model_validate(data)


TerminalFrameExtractor = Callable[[bytes, int], TerminalFrameExtractionResult]


def _default_terminal_frame_extractor(
    source_bytes: bytes, frame_index: int
) -> TerminalFrameExtractionResult:
    from ai_video.ffmpeg_tools import run_command

    with tempfile.TemporaryDirectory(prefix="ai-video-terminal-frame-") as scratch:
        source = Path(scratch) / "source.mp4"
        target = Path(scratch) / "terminal.png"
        source.write_bytes(source_bytes)
        run_command(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-vf",
                f"select=eq(n\\,{frame_index})",
                "-frames:v",
                "1",
                str(target),
            ]
        )
        try:
            version_line = subprocess.run(
                ["ffmpeg", "-version"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()[0]
            version = version_line.split()[2]
            payload = target.read_bytes()
        except (IndexError, OSError, subprocess.SubprocessError) as exc:
            raise _video_artifact_error(
                "Terminal frame extractor identity or output is unreadable."
            ) from exc
    return TerminalFrameExtractionResult(
        png_bytes=payload,
        extractor_name="ffmpeg",
        extractor_version=version,
    )


def extract_terminal_frame_candidate(
    held_fd: int,
    *,
    request: ResolvedVideoGenerationRequest,
    measured_video: MeasuredVideoMetadata,
    source_provenance_receipt_id: str,
    extracted_asset_id: str,
    extractor: TerminalFrameExtractor | None = None,
) -> tuple[bytes, MeasuredPng, TerminalFrameExtractionReceipt]:
    """Extract and seal the exact final decoded frame from held source bytes."""

    scope = request.activation_scope
    if scope is None or not scope.request.seal_terminal_frame:
        raise _video_artifact_error(
            "Terminal frame extraction requires an explicitly sealed request."
        )
    opened = os.fstat(held_fd)
    position = os.lseek(held_fd, 0, os.SEEK_CUR)
    os.lseek(held_fd, 0, os.SEEK_SET)
    source_bytes = b""
    while chunk := os.read(held_fd, 1024 * 1024):
        source_bytes += chunk
    os.lseek(held_fd, position, os.SEEK_SET)
    if (
        opened.st_nlink != 1
        or len(source_bytes) != measured_video.size_bytes
        or hashlib.sha256(source_bytes).hexdigest()
        != measured_video.artifact_sha256
    ):
        raise _video_artifact_error(
            "Terminal frame extraction requires the exact measured source bytes."
        )
    frame_index = measured_video.frame_count - 1
    result = (extractor or _default_terminal_frame_extractor)(
        source_bytes, frame_index
    )
    measured_png = measure_png_bytes(result.png_bytes)
    if (
        measured_png.width != measured_video.width
        or measured_png.height != measured_video.height
    ):
        raise _video_artifact_error(
            "Terminal frame dimensions do not match the source video."
        )
    original = scope.request
    receipt = TerminalFrameExtractionReceipt.create(
        source_shot_id=original.target_shot_id,
        source_shot_revision=original.target_shot_revision,
        source_shot_content_hash=original.target_shot_content_hash,
        source_video_asset_id=request.output_asset_id,
        source_video_sha256=measured_video.artifact_sha256,
        source_generation_id=request.generation_id,
        source_request_input_hash=request.request_input_hash,
        source_resolved_generation_hash=request.resolved_generation_hash,
        source_provenance_receipt_id=source_provenance_receipt_id,
        source_container_name=measured_video.container_name,
        source_codec_name=measured_video.codec_name,
        source_width=measured_video.width,
        source_height=measured_video.height,
        source_fps_numerator=measured_video.fps_numerator,
        source_fps_denominator=measured_video.fps_denominator,
        source_duration_milliseconds=measured_video.duration_milliseconds,
        source_frame_count=measured_video.frame_count,
        frame_index=frame_index,
        timestamp_numerator=frame_index * measured_video.fps_denominator,
        timestamp_denominator=measured_video.fps_numerator,
        selection_rule="generated_candidate_terminal",
        extraction_contract_version="terminal-frame-v1",
        extractor_name=result.extractor_name,
        extractor_version=result.extractor_version,
        extracted_asset_id=extracted_asset_id,
        extracted_sha256=measured_png.sha256,
        extracted_mime_type="image/png",
        extracted_size_bytes=measured_png.size_bytes,
        extracted_width=measured_png.width,
        extracted_height=measured_png.height,
        extracted_color_space="unmeasured",
    )
    return result.png_bytes, measured_png, receipt


def bind_terminal_frame_evidence(
    extraction: TerminalFrameExtractionReceipt,
    *,
    source_registry: RegistrySnapshotPointer,
) -> TerminalFrameEvidence:
    data = extraction.model_dump(mode="python", exclude={"content_hash"})
    return TerminalFrameEvidence.create(
        **data,
        source_registry=source_registry,
        extraction_receipt_id=extraction.content_hash,
    )


def build_terminal_frame_asset_record(
    *,
    request: ResolvedVideoGenerationRequest,
    extraction: TerminalFrameExtractionReceipt,
) -> AssetRecord:
    scope = request.activation_scope
    if scope is None:
        raise _video_artifact_error(
            "Terminal frame asset requires durable authoring scope."
        )
    return AssetRecord(
        asset_id=extraction.extracted_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=Path(f"assets/files/{extraction.extracted_sha256}.png"),
        sha256=extraction.extracted_sha256,
        size_bytes=extraction.extracted_size_bytes,
        mime_type="image/png",
        width=extraction.extracted_width,
        height=extraction.extracted_height,
        source_kind=AssetSourceKind.DERIVED,
        tool=ToolIdentity(
            name=extraction.extractor_name,
            version=extraction.extractor_version,
        ),
        input_artifact_ids=(request.output_asset_id,),
        input_fingerprint=extraction.content_hash,
        creation_receipt_id=extraction.content_hash,
        usage_license=scope.usage_license,
    )


class VideoProbeReceipt(_VideoArtifactStrictModel):
    request_receipt_fingerprint: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    measured: MeasuredVideoMetadata
    continuity_evidence: GeneratedShotContinuityEvidence | None = None
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoProbeReceipt":
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("video probe receipt content hash is invalid")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_variant(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.continuity_evidence is None:
            data.pop("continuity_evidence", None)
        return data

    @classmethod
    def create(
        cls,
        *,
        request: ResolvedVideoGenerationRequest,
        fetch_receipt: VideoFetchReceipt | LocalVideoFetchReceipt,
        measured: MeasuredVideoMetadata,
        continuity_evidence: GeneratedShotContinuityEvidence | None = None,
    ) -> "VideoProbeReceipt":
        data = {
            "request_receipt_fingerprint": request.desired_generation_fingerprint,
            "resolved_generation_hash": request.resolved_generation_hash,
            "fetch_fingerprint": fetch_receipt.fetch_fingerprint,
            "measured": measured,
            "continuity_evidence": continuity_evidence,
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


GeneratedShotContinuityReviewer = Callable[
    [int, ResolvedVideoGenerationRequest, MeasuredVideoMetadata, str],
    GeneratedShotContinuityEvidence,
]


def _review_generated_shot_continuity(
    held_fd: int,
    request: ResolvedVideoGenerationRequest,
    measured: MeasuredVideoMetadata,
    reviewer: GeneratedShotContinuityReviewer | None,
    policy_content_hash: str | None,
    authorities: tuple[ToolIdentity, ...],
) -> GeneratedShotContinuityEvidence | None:
    binding = request.continuity_binding
    if binding is None:
        return None
    if reviewer is None or policy_content_hash is None or not authorities:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message=(
                "Continuity-bound generated Shot requires explicit per-Shot review evidence."
            ),
            retryable=False,
        )
    position = os.lseek(held_fd, 0, os.SEEK_CUR)
    review_fd = os.dup(held_fd)
    try:
        os.lseek(review_fd, 0, os.SEEK_SET)
        evidence = reviewer(review_fd, request, measured, policy_content_hash)
    except AiVideoError:
        raise
    except Exception as exc:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message="Generated Shot continuity evaluator failed.",
            technical_detail=str(exc),
            retryable=False,
            cause=exc,
        ) from exc
    finally:
        try:
            os.close(review_fd)
        except OSError:
            pass
        os.lseek(held_fd, position, os.SEEK_SET)
    return validate_generated_shot_continuity_evidence(
        evidence,
        request=request,
        measured=measured,
        policy_content_hash=policy_content_hash,
        authorities=authorities,
        require_pass=True,
    )


def validate_generated_shot_continuity_evidence(
    evidence: GeneratedShotContinuityEvidence,
    *,
    request: ResolvedVideoGenerationRequest,
    measured: MeasuredVideoMetadata,
    policy_content_hash: str,
    authorities: tuple[ToolIdentity, ...],
    require_pass: bool,
) -> GeneratedShotContinuityEvidence:
    binding = request.continuity_binding
    original = request.activation_scope.request if request.activation_scope else None
    measurements = (
        evidence.raw_measurements
        if isinstance(evidence, GeneratedShotContinuityEvidence)
        else None
    )
    fallback_is_authorized = not (
        isinstance(measurements, TrackedGeneratedShotContinuityMeasurements)
        and measurements.fallback_evidence is not None
        and measurements.fallback_evidence.evaluator not in authorities
    )
    if (
        binding is None
        or not isinstance(evidence, GeneratedShotContinuityEvidence)
        or original is None
        or evidence.source_shot_id != binding.terminal_frame.source_shot_id
        or evidence.target_shot_id != original.target_shot_id
        or evidence.target_shot_content_hash != original.target_shot_content_hash
        or evidence.resolved_generation_hash != request.resolved_generation_hash
        or evidence.artifact_sha256 != measured.artifact_sha256
        or evidence.continuity_constraints_hash != binding.constraints.content_hash
        or evidence.qa_policy_content_hash != policy_content_hash
        or evidence.evaluator not in authorities
        or not fallback_is_authorized
    ):
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message=(
                "Generated Shot continuity evidence does not bind the exact request and MP4."
            ),
            retryable=False,
        )
    verdict = adjudicate_generated_shot_continuity(evidence)
    if require_pass and verdict is not QaVerdict.PASS:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message=(
                "Generated Shot continuity review did not produce a complete passing verdict."
            ),
            technical_detail=f"verdict={verdict.value}",
            retryable=False,
        )
    return evidence


def invoke_generated_shot_continuity_reviewer(
    held_fd: int,
    request: ResolvedVideoGenerationRequest,
    measured: MeasuredVideoMetadata,
    reviewer: GeneratedShotContinuityReviewer,
    policy_content_hash: str,
    authorities: tuple[ToolIdentity, ...],
) -> GeneratedShotContinuityEvidence:
    position = os.lseek(held_fd, 0, os.SEEK_CUR)
    review_fd = os.dup(held_fd)
    try:
        os.lseek(review_fd, 0, os.SEEK_SET)
        evidence = reviewer(review_fd, request, measured, policy_content_hash)
    except AiVideoError:
        raise
    except Exception as exc:
        raise AiVideoError(
            code=ErrorCode.REVIEW_EVIDENCE_INVALID,
            user_message="Generated Shot continuity evaluator failed.",
            technical_detail=str(exc),
            retryable=False,
            cause=exc,
        ) from exc
    finally:
        try:
            os.close(review_fd)
        except OSError:
            pass
        os.lseek(held_fd, position, os.SEEK_SET)
    return validate_generated_shot_continuity_evidence(
        evidence,
        request=request,
        measured=measured,
        policy_content_hash=policy_content_hash,
        authorities=authorities,
        require_pass=False,
    )


class VideoProvenanceReceipt(_VideoArtifactStrictModel):
    generation_id: str = Field(pattern=_SAFE_ID.pattern)
    request_receipt_fingerprint: str = Field(pattern=_SHA256)
    resolved_generation_hash: str = Field(pattern=_SHA256)
    provider_kind: str = Field(pattern=_SAFE_ID.pattern)
    model_id: str = Field(pattern=_SAFE_ID.pattern)
    profile_sha256: str = Field(pattern=_SHA256)
    paid_submit_receipt_fingerprint: str | None = Field(default=None, pattern=_SHA256)
    local_submit_result_fingerprint: str | None = Field(default=None, pattern=_SHA256)
    observation_fingerprint: str = Field(pattern=_SHA256)
    fetch_fingerprint: str = Field(pattern=_SHA256)
    provider_file_id: str = Field(pattern=_SAFE_ID.pattern)
    artifact_sha256: str = Field(pattern=_SHA256)
    probe_receipt_id: str = Field(pattern=_SHA256)
    usage_license: str = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_seal(self) -> "VideoProvenanceReceipt":
        if (self.paid_submit_receipt_fingerprint is None) == (
            self.local_submit_result_fingerprint is None
        ):
            raise ValueError("video provenance requires exactly one submit identity")
        if self.content_hash != canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        ):
            raise ValueError("video provenance receipt content hash is invalid")
        return self

    @model_serializer(mode="wrap")
    def _serialize_compatible_variant(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        data = handler(self)
        if self.local_submit_result_fingerprint is None:
            data.pop("local_submit_result_fingerprint", None)
        if self.paid_submit_receipt_fingerprint is None:
            data.pop("paid_submit_receipt_fingerprint", None)
        return data

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

    @classmethod
    def create_local(
        cls,
        *,
        request: ResolvedVideoGenerationRequest,
        observation: LocalVideoTaskObservation,
        fetch_receipt: LocalVideoFetchReceipt,
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
            "local_submit_result_fingerprint": fetch_receipt.submit_result_fingerprint,
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


def _probe_generated_video_candidate(
    held_fd: int,
    expected_request: ResolvedVideoGenerationRequest,
    fetch_receipt: VideoFetchReceipt | LocalVideoFetchReceipt,
    *,
    probe: Callable[[int], dict] | None = None,
    continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
    continuity_policy_content_hash: str | None = None,
    continuity_authorities: tuple[ToolIdentity, ...] = (),
    defer_continuity_review: bool,
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
    continuity_evidence = (
        None
        if defer_continuity_review
        else _review_generated_shot_continuity(
            held_fd,
            expected_request,
            measured,
            continuity_reviewer,
            continuity_policy_content_hash,
            continuity_authorities,
        )
    )
    receipt = VideoProbeReceipt.create(
        request=expected_request,
        fetch_receipt=fetch_receipt,
        measured=measured,
        continuity_evidence=continuity_evidence,
    )
    return b"".join(chunks), measured, receipt


def probe_generated_video_candidate(
    held_fd: int,
    expected_request: ResolvedVideoGenerationRequest,
    fetch_receipt: VideoFetchReceipt | LocalVideoFetchReceipt,
    *,
    probe: Callable[[int], dict] | None = None,
    continuity_reviewer: GeneratedShotContinuityReviewer | None = None,
    continuity_policy_content_hash: str | None = None,
    continuity_authorities: tuple[ToolIdentity, ...] = (),
    max_size_bytes: int = 2_147_483_648,
) -> tuple[bytes, MeasuredVideoMetadata, VideoProbeReceipt]:
    """Measure one held MP4 and enforce continuity evidence when required."""

    return _probe_generated_video_candidate(
        held_fd,
        expected_request,
        fetch_receipt,
        probe=probe,
        continuity_reviewer=continuity_reviewer,
        continuity_policy_content_hash=continuity_policy_content_hash,
        continuity_authorities=continuity_authorities,
        defer_continuity_review=False,
        max_size_bytes=max_size_bytes,
    )


def _measure_generated_video_candidate_for_committer(
    held_fd: int,
    expected_request: ResolvedVideoGenerationRequest,
    fetch_receipt: VideoFetchReceipt | LocalVideoFetchReceipt,
    *,
    probe: Callable[[int], dict] | None = None,
    max_size_bytes: int = 2_147_483_648,
) -> tuple[bytes, MeasuredVideoMetadata, VideoProbeReceipt]:
    """Private measurement seam used before the committer checkpoints evidence."""

    return _probe_generated_video_candidate(
        held_fd,
        expected_request,
        fetch_receipt,
        probe=probe,
        defer_continuity_review=True,
        max_size_bytes=max_size_bytes,
    )


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
    "GeneratedShotContinuityReviewer",
    "TerminalFrameExtractionReceipt",
    "TerminalFrameExtractionResult",
    "VideoProbeReceipt",
    "VideoProvenanceReceipt",
    "bind_terminal_frame_evidence",
    "build_generated_video_asset_record",
    "build_terminal_frame_asset_record",
    "extract_terminal_frame_candidate",
    "probe_generated_video_candidate",
]
