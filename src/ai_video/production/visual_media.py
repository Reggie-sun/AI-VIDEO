from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from html import escape

from ai_video.production.models import (
    AssetRecord,
    CompositionLayerSpec,
    DeliveryProfile,
    FixedTransform,
    ResolvedVisualSpan,
)


class VisualMediaValidationError(ValueError):
    """A visual asset cannot satisfy the deterministic render contract."""


def validated_visual_suffix(
    payload: bytes,
    *,
    suffix: str,
    mime_type: str,
) -> str:
    suffix = suffix.lower()
    head = payload[:16]
    if (
        mime_type == "image/png"
        and suffix == ".png"
        and head.startswith(b"\x89PNG\r\n\x1a\n")
    ):
        return ".png"
    if (
        mime_type == "image/jpeg"
        and suffix in {".jpg", ".jpeg"}
        and head.startswith(b"\xff\xd8\xff")
    ):
        return ".jpg"
    if (
        mime_type == "image/webp"
        and suffix == ".webp"
        and head[:4] == b"RIFF"
        and head[8:12] == b"WEBP"
    ):
        return ".webp"
    if mime_type != "video/mp4":
        raise VisualMediaValidationError(
            "P3 asset MIME, magic bytes and raster suffix do not agree."
        )
    if suffix != ".mp4":
        raise VisualMediaValidationError("MP4 asset MIME and suffix do not agree.")
    _validate_mp4_boxes(payload)
    return ".mp4"


def visual_payload_matches(payload: bytes, *, suffix: str, mime_type: str) -> bool:
    try:
        validated_visual_suffix(payload, suffix=suffix, mime_type=mime_type)
    except VisualMediaValidationError:
        return False
    return True


def resolved_video_trim_duration(
    asset: AssetRecord,
    layer: CompositionLayerSpec,
    *,
    duration_frames: int,
    delivery_profile: DeliveryProfile,
) -> int:
    metadata = asset.video_metadata
    if metadata is None:
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} has no P8 metadata."
        )
    if metadata.container_name != "mp4" or metadata.codec_name != "h264":
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} must be H.264 in MP4."
        )
    if (
        metadata.width != delivery_profile.width
        or metadata.height != delivery_profile.height
        or asset.width not in {None, metadata.width}
        or asset.height not in {None, metadata.height}
    ):
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} dimensions do not match delivery."
        )
    if metadata.fps_numerator != (
        delivery_profile.fps * metadata.fps_denominator
    ):
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} frame rate does not match delivery."
        )
    measured_duration_delta = abs(
        metadata.frame_count * 1000 * metadata.fps_denominator
        - metadata.duration_milliseconds * metadata.fps_numerator
    )
    if measured_duration_delta > 1000 * metadata.fps_denominator:
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} duration and frame count disagree."
        )
    trim_duration = layer.trim_duration_frames or duration_frames
    if trim_duration != duration_frames:
        raise VisualMediaValidationError(
            "Video trim duration must equal its resolved Shot duration."
        )
    if layer.trim_start_frame + trim_duration > metadata.frame_count:
        raise VisualMediaValidationError(
            f"Video asset {asset.asset_id} cannot cover its resolved Shot interval."
        )
    return trim_duration


def render_visual_element(
    span: ResolvedVisualSpan,
    *,
    video_id: str,
    start_seconds: str,
    duration_seconds: str,
    media_start_seconds: str,
    track_index: int,
) -> str:
    source_path = span.materialized_path.as_posix()
    style = f"transform:{escape(_css_transform(span.transform))};transform-origin:0 0"
    if span.asset_mime_type == "video/mp4":
        return (
            f'  <video id="{video_id}" src="{source_path}" muted playsinline '
            f'preload="auto" data-start="{start_seconds}" '
            f'data-duration="{duration_seconds}" '
            f'data-media-start="{media_start_seconds}" '
            f'data-track-index="{track_index}" style="{style}"></video>'
        )
    return f'  <img src="{source_path}" style="{style}" alt="" />'


def visual_media_css(spans: Iterable[ResolvedVisualSpan]) -> str:
    if any(span.asset_mime_type == "video/mp4" for span in spans):
        return "    .clip img,.clip video{width:100%;height:100%;object-fit:cover}"
    return "    .clip img{width:100%;height:100%;object-fit:cover}"


def _css_transform(transform: FixedTransform) -> str:
    return (
        f"translate({transform.translate_x_px}px,{transform.translate_y_px}px) "
        f"scale({_decimal_milli(transform.scale_x_milli)},"
        f"{_decimal_milli(transform.scale_y_milli)}) "
        f"rotate({_decimal_milli(transform.rotation_millidegrees)}deg)"
    )


def _decimal_milli(value: int) -> str:
    rendered = format(Decimal(value) / Decimal(1000), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _validate_mp4_boxes(payload: bytes) -> None:
    offset = 0
    box_types: list[bytes] = []
    while offset < len(payload):
        if len(payload) - offset < 8:
            raise VisualMediaValidationError(
                "MP4 asset contains a truncated top-level box."
            )
        size = int.from_bytes(payload[offset : offset + 4], "big")
        box_type = payload[offset + 4 : offset + 8]
        header_size = 8
        if size == 1:
            if len(payload) - offset < 16:
                raise VisualMediaValidationError(
                    "MP4 asset contains a truncated extended-size box."
                )
            size = int.from_bytes(payload[offset + 8 : offset + 16], "big")
            header_size = 16
        elif size == 0:
            size = len(payload) - offset
        if size < header_size or offset + size > len(payload):
            raise VisualMediaValidationError(
                "MP4 asset contains an invalid top-level box size."
            )
        box_types.append(box_type)
        offset += size
    if not box_types or box_types[0] != b"ftyp" or b"moov" not in box_types:
        raise VisualMediaValidationError(
            "MP4 asset requires top-level ftyp and moov boxes."
        )
