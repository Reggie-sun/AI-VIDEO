"""Strict raw-video-frame provenance for automated imported image references."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Literal

from PIL import Image
from pydantic import ConfigDict, Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image import measure_png_bytes
from ai_video.production.models import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        ErrorCode.IMAGE_ASSET_INVALID,
        message,
        detail,
        retryable=False,
    )


class VideoFrameImageImportReferenceBinding(StrictModel):
    """A persisted, non-creative input frame used by automated image import."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    role: Literal["video_frame"]
    source_video_path: Path
    source_video_sha256: str = Field(pattern=_SHA256)
    source_video_size_bytes: int = Field(strict=True, gt=0)
    extracted_frame_path: Path
    extracted_frame_sha256: str = Field(pattern=_SHA256)
    extracted_frame_size_bytes: int = Field(strict=True, gt=0)
    extracted_frame_width: int = Field(strict=True, gt=0)
    extracted_frame_height: int = Field(strict=True, gt=0)
    frame_index: int = Field(strict=True, ge=0)
    extraction_contract_version: str = Field(pattern=r"^video-frame-import-v1$")
    extractor_name: str = Field(pattern=r"^ffmpeg$")
    extractor_version: str = Field(min_length=1, max_length=128)

    @field_validator("source_video_path", "extracted_frame_path")
    @classmethod
    def _require_safe_relative_path(cls, value: Path) -> Path:
        if value.is_absolute() or any(part in {"", ".", ".."} for part in value.parts):
            raise ValueError("video frame import evidence path must be safe and relative")
        return value

    @field_validator("extracted_frame_path")
    @classmethod
    def _require_png_path(cls, value: Path) -> Path:
        if value.suffix.lower() != ".png":
            raise ValueError("video frame import evidence must persist the extracted PNG")
        return value

    @field_validator("source_video_path")
    @classmethod
    def _require_mp4_path(cls, value: Path) -> Path:
        if value.suffix.lower() != ".mp4":
            raise ValueError("video frame import evidence must persist an MP4 source")
        return value

    @model_validator(mode="after")
    def _require_content_addressed_evidence_paths(
        self,
    ) -> "VideoFrameImageImportReferenceBinding":
        evidence_root = Path("evidence/video-frame-import")
        if self.source_video_path != evidence_root / f"{self.source_video_sha256}.mp4":
            raise ValueError("source video path must be its canonical evidence path")
        if (
            self.extracted_frame_path
            != evidence_root / f"{self.extracted_frame_sha256}.png"
        ):
            raise ValueError("extracted frame path must be its canonical evidence path")
        return self


def validate_video_frame_reference_bytes(
    reference: VideoFrameImageImportReferenceBinding,
    *,
    source_video_bytes: bytes,
    extracted_frame_bytes: bytes,
    verify_derivation: bool,
) -> None:
    """Verify immutable bytes, and at admission confirm the selected decoded frame."""

    if (
        len(source_video_bytes) != reference.source_video_size_bytes
        or hashlib.sha256(source_video_bytes).hexdigest()
        != reference.source_video_sha256
    ):
        raise _invalid("Video frame import source video bytes do not match the receipt.")
    if (
        len(extracted_frame_bytes) != reference.extracted_frame_size_bytes
        or hashlib.sha256(extracted_frame_bytes).hexdigest()
        != reference.extracted_frame_sha256
    ):
        raise _invalid("Video frame import extracted frame bytes do not match the receipt.")
    _validate_self_contained_mp4(source_video_bytes)
    measure_png_bytes(extracted_frame_bytes)
    try:
        with Image.open(BytesIO(extracted_frame_bytes)) as image:
            if image.format != "PNG":
                raise ValueError("not a PNG")
            rgba = image.convert("RGBA")
            width, height = rgba.size
            if rgba.getchannel("A").getextrema() != (255, 255):
                raise ValueError("transparent PNG")
            extracted_rgb = rgba.convert("RGB").tobytes()
    except (OSError, ValueError) as exc:
        raise _invalid("Video frame import extracted frame is not a readable PNG.") from exc
    if (
        width != reference.extracted_frame_width
        or height != reference.extracted_frame_height
    ):
        raise _invalid("Video frame import PNG dimensions do not match the receipt.")
    if verify_derivation:
        _validate_declared_ffmpeg_identity(reference)
        decoded_width, decoded_height, decoded_rgb = _decode_selected_frame_rgb(
            source_video_bytes, reference.frame_index
        )
        if (
            decoded_width != width
            or decoded_height != height
            or decoded_rgb != extracted_rgb
        ):
            raise _invalid(
                "Video frame import PNG is not the declared source video frame."
            )


def _decode_selected_frame_rgb(
    source_video_bytes: bytes, frame_index: int
) -> tuple[int, int, bytes]:
    """Decode one exact presentation-order frame without creating project media."""

    with tempfile.TemporaryDirectory(prefix="ai-video-image-import-frame-") as scratch:
        source = Path(scratch) / "source.mp4"
        source.write_bytes(source_video_bytes)
        try:
            completed = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-nostdin",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-f",
                    "mov",
                    "-enable_drefs",
                    "0",
                    "-use_absolute_path",
                    "0",
                    "-i",
                    str(source),
                    "-map",
                    "0:v:0",
                    "-vf",
                    f"select=eq(n\\,{frame_index}),format=rgb24",
                    "-frames:v",
                    "1",
                    "-f",
                    "image2pipe",
                    "-vcodec",
                    "png",
                    "-",
                ],
                check=False,
                capture_output=True,
                timeout=10,
            )
        except FileNotFoundError as exc:
            raise _invalid("Video frame import requires the declared ffmpeg extractor.") from exc
        except subprocess.TimeoutExpired as exc:
            raise _invalid("Video frame import frame decoding timed out.") from exc
    if completed.returncode != 0 or not completed.stdout:
        raise _invalid("Video frame import could not decode the declared source frame.")
    try:
        measure_png_bytes(completed.stdout)
        with Image.open(BytesIO(completed.stdout)) as image:
            rgb = image.convert("RGB")
            return rgb.width, rgb.height, rgb.tobytes()
    except (AiVideoError, OSError, ValueError) as exc:
        raise _invalid("Video frame import decoded frame is not a readable PNG.") from exc


def _validate_declared_ffmpeg_identity(
    reference: VideoFrameImageImportReferenceBinding,
) -> None:
    try:
        completed = subprocess.run(
            ["ffmpeg", "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except FileNotFoundError as exc:
        raise _invalid("Video frame import requires the declared ffmpeg extractor.") from exc
    except subprocess.TimeoutExpired as exc:
        raise _invalid("Video frame import extractor identity check timed out.") from exc
    try:
        version = completed.stdout.splitlines()[0].split()[2]
    except (IndexError, AttributeError) as exc:
        raise _invalid("Video frame import extractor identity is unreadable.") from exc
    if completed.returncode != 0 or version != reference.extractor_version:
        raise _invalid("Video frame import extractor identity does not match the receipt.")


def _validate_self_contained_mp4(source_video_bytes: bytes) -> None:
    try:
        boxes = tuple(_iso_boxes(source_video_bytes, 0, len(source_video_bytes)))
        if not boxes or boxes[0][0] != b"ftyp" or not any(
            kind == b"moov" for kind, _, _ in boxes
        ):
            raise ValueError("not an ISO BMFF MP4")
        _validate_dref_boxes(source_video_bytes, 0, len(source_video_bytes))
    except ValueError as exc:
        raise _invalid("Video frame import source is not a self-contained MP4.") from exc


def _validate_dref_boxes(
    payload: bytes, start: int, end: int, *, depth: int = 0
) -> None:
    if depth > 8:
        raise ValueError("ISO BMFF container nesting is too deep")
    for kind, data_start, data_end in _iso_boxes(payload, start, end):
        if kind == b"dref":
            _validate_self_contained_dref(payload, data_start, data_end)
        elif kind in {b"moov", b"trak", b"mdia", b"minf", b"dinf"}:
            _validate_dref_boxes(payload, data_start, data_end, depth=depth + 1)


def _validate_self_contained_dref(payload: bytes, start: int, end: int) -> None:
    if end - start < 8:
        raise ValueError("truncated dref")
    entry_count = int.from_bytes(payload[start + 4 : start + 8], "big")
    cursor = start + 8
    for _ in range(entry_count):
        entry_start = cursor
        entry_kind, entry_data_start, entry_end = _read_iso_box(payload, cursor, end)
        if entry_kind not in {b"url ", b"urn ", b"alis "} or entry_end <= entry_data_start + 3:
            raise ValueError("unsupported dref entry")
        flags = int.from_bytes(payload[entry_data_start : entry_data_start + 4], "big")
        if flags & 1 == 0:
            raise ValueError("external dref entry")
        cursor = entry_end
        if cursor <= entry_start:
            raise ValueError("invalid dref entry")
    if cursor != end:
        raise ValueError("dref entry boundary mismatch")


def _iso_boxes(payload: bytes, start: int, end: int):
    cursor = start
    while cursor < end:
        kind, data_start, box_end = _read_iso_box(payload, cursor, end)
        yield kind, data_start, box_end
        cursor = box_end


def _read_iso_box(payload: bytes, start: int, end: int) -> tuple[bytes, int, int]:
    if end - start < 8:
        raise ValueError("truncated ISO BMFF box")
    declared = int.from_bytes(payload[start : start + 4], "big")
    kind = payload[start + 4 : start + 8]
    header = 8
    if declared == 1:
        if end - start < 16:
            raise ValueError("truncated extended ISO BMFF box")
        declared = int.from_bytes(payload[start + 8 : start + 16], "big")
        header = 16
    elif declared == 0:
        declared = end - start
    if declared < header or start + declared > end:
        raise ValueError("invalid ISO BMFF box boundary")
    return kind, start + header, start + declared
