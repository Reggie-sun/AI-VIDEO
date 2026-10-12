"""Validated Grok video operation inputs and wire payloads.

The adapter owns submission and lifecycle. This leaf module owns the exact
operation path, input-byte checks, and provider JSON projection.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Literal

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.grok_profile import (
    GROK_VIDEO_MODEL_CLASSIC,
    GROK_VIDEO_MODEL_FULL,
    GROK_VIDEO_MODEL_LITE,
    GROK_VIDEO_MODELS,
    GrokProviderProfile,
)
from ai_video.production.video import (
    ResolvedVideoGenerationRequest,
    VideoFlexibleOutputRequirement,
    VideoGenerationMode,
    VideoImageReferenceBinding,
    VideoMediaReferenceBinding,
    VideoProviderCapabilities,
    VideoCapabilityVariant,
)


GROK_VIDEO_ENDPOINTS = {
    VideoGenerationMode.TEXT_TO_VIDEO: "generations",
    VideoGenerationMode.IMAGE_TO_VIDEO: "generations",
    VideoGenerationMode.REFERENCE_TO_VIDEO: "generations",
    VideoGenerationMode.VIDEO_EDIT: "edits",
    VideoGenerationMode.VIDEO_EXTEND: "extensions",
}
MAX_GROK_IMAGE_BYTES = 20 * 1024 * 1024
MAX_GROK_SOURCE_VIDEO_BYTES = 128 * 1024 * 1024
MAX_GROK_POST_BODY_BYTES = 400 * 1024 * 1024


def _error(message: str, code: ErrorCode = ErrorCode.VIDEO_REQUEST_INVALID) -> AiVideoError:
    return AiVideoError(code=code, user_message=message, retryable=False)


@dataclass(frozen=True)
class GrokEgressInput:
    asset_id: str
    asset_sha256: str
    size_bytes: int
    mime_type: str


@dataclass(frozen=True)
class GrokVideoOperation:
    endpoint: Literal["generations", "edits", "extensions"]
    model_id: str
    egress_inputs: tuple[GrokEgressInput, ...]
    body: bytes = field(repr=False)


ImageResolver = Callable[[VideoImageReferenceBinding], bytes]
MediaResolver = Callable[[VideoMediaReferenceBinding], bytes]


def grok_endpoint_for_mode(mode: VideoGenerationMode) -> Literal[
    "generations", "edits", "extensions"
]:
    try:
        return GROK_VIDEO_ENDPOINTS[mode]
    except (KeyError, TypeError):
        raise _error(
            "Grok video mode is outside the documented operation inventory.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        ) from None


def grok_egress_inputs(
    request: ResolvedVideoGenerationRequest,
) -> tuple[GrokEgressInput, ...]:
    """Return unique, canonically ordered input bytes for the sealed preview."""
    inputs: list[GrokEgressInput] = []
    by_asset: dict[str, tuple[GrokEgressInput, tuple[object, ...]]] = {}
    for binding in (*request.image_bindings, *request.media_bindings):
        candidate = GrokEgressInput(
            asset_id=binding.asset_id,
            asset_sha256=binding.asset_sha256,
            size_bytes=binding.size_bytes,
            mime_type=binding.mime_type,
        )
        details = tuple(
            getattr(binding, field, None)
            for field in (
                "kind", "width", "height", "fps", "duration_millis"
            )
        )
        prior = by_asset.get(candidate.asset_id)
        if prior is not None:
            if prior != (candidate, details):
                raise _error(
                    "Grok input asset identity conflicts across media roles."
                )
            continue
        by_asset[candidate.asset_id] = (candidate, details)
        inputs.append(candidate)
    return tuple(inputs)


def select_grok_capability(
    request: ResolvedVideoGenerationRequest,
    capabilities: VideoProviderCapabilities,
) -> VideoCapabilityVariant:
    matches = tuple(
        item
        for item in capabilities.variants
        if item.capability_id == request.capability_id
        and item.model_id == request.model_id
        and item.mode is request.mode
        and item.profile_version == request.provider_profile.profile_version
    )
    if len(matches) != 1:
        raise _error(
            "Grok request does not identify one selected model and operation capability.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    return matches[0]


def validate_grok_video_request(
    request: ResolvedVideoGenerationRequest,
    *,
    profile: GrokProviderProfile,
    capabilities: VideoProviderCapabilities,
    variant: VideoCapabilityVariant | None = None,
) -> VideoCapabilityVariant:
    """Reject controls that the selected Grok model and operation cannot express."""
    operation = grok_endpoint_for_mode(request.mode)
    selected = variant or select_grok_capability(request, capabilities)
    if (
        request.provider_name != "grok"
        or request.provider_kind != "grok"
        or request.provider_profile != profile.pointer()
        or request.model_id not in GROK_VIDEO_MODELS
        or selected.model_id != request.model_id
        or selected.mode is not request.mode
        or (request.model_id == GROK_VIDEO_MODEL_LITE and request.mode not in {
            VideoGenerationMode.TEXT_TO_VIDEO,
            VideoGenerationMode.IMAGE_TO_VIDEO,
        })
        or (operation in {"edits", "extensions"} and request.model_id != GROK_VIDEO_MODEL_CLASSIC)
    ):
        raise _error(
            "Grok request does not match the selected model, profile, and operation.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    output = request.effective_output
    if (
        not isinstance(output, VideoFlexibleOutputRequirement)
        or request.effective_seed is not None
        or request.effective_negative_prompt_text
        or output.fps is not None
    ):
        raise _error(
            "Grok does not support the requested seed, negative prompt, FPS, or output form.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if selected.output_capability is None or not selected.output_capability.supports(output):
        raise _error(
            "Grok output constraints do not match the selected operation capability.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )

    keyframes = tuple(getattr(profile, "keyframes", ()))
    voices = tuple(getattr(profile, "reference_voices", ()))
    reference_images = tuple(item for item in request.image_bindings if item.role == "reference")
    if keyframes:
        duration_seconds = output.duration_seconds
        if (
            request.model_id != GROK_VIDEO_MODEL_FULL
            or request.mode not in {
                VideoGenerationMode.IMAGE_TO_VIDEO,
                VideoGenerationMode.REFERENCE_TO_VIDEO,
            }
            or duration_seconds is None
        ):
            raise _error(
                "Grok keyframes require a timed full Imagine Video 1.5 image/reference request.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        if len(keyframes) > 4:
            raise _error("Grok supports at most four interior keyframes.", ErrorCode.VIDEO_REQUEST_INVALID)
        previous_tick = 0
        bound_references = {item.asset_id: item for item in reference_images}
        for keyframe in keyframes:
            asset_id = getattr(keyframe, "asset_id", None)
            asset_sha256 = getattr(keyframe, "asset_sha256", None)
            ticks = getattr(keyframe, "timestamp_ticks", None)
            binding = bound_references.get(asset_id)
            if (
                binding is None
                or binding.asset_sha256 != asset_sha256
                or not isinstance(ticks, int)
                or isinstance(ticks, bool)
                or ticks <= previous_tick
                or ticks >= duration_seconds * 3
            ):
                raise _error(
                    "Grok keyframe must bind a sorted, exact reference image inside the output.",
                    ErrorCode.VIDEO_REQUEST_INVALID,
                )
            previous_tick = ticks
    if voices:
        if (
            request.model_id != GROK_VIDEO_MODEL_FULL
            or request.mode not in {
                VideoGenerationMode.TEXT_TO_VIDEO,
                VideoGenerationMode.IMAGE_TO_VIDEO,
                VideoGenerationMode.REFERENCE_TO_VIDEO,
            }
            or not output.native_audio
        ):
            raise _error(
                "Grok preset reference voices require full 1.5 reference audio with native audio enabled.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        if len(voices) > 3:
            raise _error("Grok supports at most three preset reference voices.", ErrorCode.VIDEO_REQUEST_INVALID)

    if request.c4_multi_anchor_binding is not None:
        tier = getattr(request.c4_multi_anchor_binding.tier, "value", None)
        if (
            tier != "static_boundary"
            or request.model_id != GROK_VIDEO_MODEL_FULL
            or request.mode is not VideoGenerationMode.IMAGE_TO_VIDEO
            or request.media_bindings
            or tuple(item.role for item in request.image_bindings)
            != ("first_frame", "last_frame", "reference")
        ):
            raise _error(
                "Grok can express only exact static C4 first/last/reference boundaries.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
    if request.mode in {VideoGenerationMode.VIDEO_EDIT, VideoGenerationMode.VIDEO_EXTEND} and (
        request.image_bindings
        or request.c4_multi_anchor_binding is not None
        or request.continuity_binding is not None
        or request.hard_cut_keyframe_binding is not None
        or request.seal_terminal_frame
        or keyframes
        or voices
    ):
        raise _error(
            "Grok edit and extension accept only the sealed source video and prompt.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if request.media_bindings and request.mode not in {
        VideoGenerationMode.VIDEO_EDIT,
        VideoGenerationMode.VIDEO_EXTEND,
    }:
        raise _error(
            "Grok generation does not accept unqualified source video or audio media.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if request.mode in {VideoGenerationMode.VIDEO_EDIT, VideoGenerationMode.VIDEO_EXTEND}:
        _validate_inherited_video_output(request)
    if request.mode is VideoGenerationMode.VIDEO_EXTEND:
        _extension_seconds(request)
    return selected


def _source_video(request: ResolvedVideoGenerationRequest) -> VideoMediaReferenceBinding:
    videos = tuple(item for item in request.media_bindings if item.kind == "video")
    if (
        len(videos) != 1
        or len(request.media_bindings) != 1
        or videos[0].role != "reference_video"
        or videos[0].mime_type != "video/mp4"
        or videos[0].width is None
        or videos[0].height is None
    ):
        raise _error(
            "Grok video operations require one exact MP4 source binding.",
            ErrorCode.VIDEO_REQUEST_INVALID,
        )
    source = videos[0]
    if source.size_bytes > MAX_GROK_SOURCE_VIDEO_BYTES:
        raise _error(
            "Grok source video exceeds the local exact-byte limit.",
            ErrorCode.VIDEO_REQUEST_INVALID,
        )
    if min(source.width, source.height) > 720:
        raise _error(
            "Grok editing and extension do not downscale source video above 720p.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    return source


def _ratio_matches(width: int, height: int, ratio: str) -> bool:
    if ratio == "adaptive":
        return True
    try:
        requested = Fraction(*(int(part) for part in ratio.split(":")))
    except (ValueError, ZeroDivisionError):
        return False
    return Fraction(width, height) == requested


def _validate_inherited_video_output(request: ResolvedVideoGenerationRequest) -> None:
    source = _source_video(request)
    output = request.effective_output
    if not isinstance(output, VideoFlexibleOutputRequirement):
        raise _error("Grok edit and extension require flexible output constraints.")
    if output.container != "mp4" or output.mime_type != "video/mp4":
        raise _error("Grok edit and extension inherit an MP4 output container.", ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED)
    if output.dimension_mode == "exact":
        if output.width != source.width or output.height != source.height:
            raise _error(
                "Grok edit and extension inherit source geometry and cannot resize.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
    if not _ratio_matches(source.width, source.height, output.ratio):
        raise _error(
            "Grok edit and extension inherit source aspect ratio.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if output.resolution_label not in {"480p", "720p", "source", "adaptive"}:
        raise _error(
            "Grok edit and extension cannot request a different source resolution.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    source_short_dimension = min(source.width, source.height)
    if output.resolution_label in {"480p", "720p"} and source_short_dimension != int(output.resolution_label[:-1]):
        raise _error(
            "Grok edit and extension output resolution must match the source video.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if not output.native_audio:
        raise _error(
            "Grok edit and extension inherit source audio and cannot disable it.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if output.timing_mode == "provider_selected":
        return
    source_duration = source.duration_millis
    if output.timing_mode not in {"exact_seconds", "nominal_seconds"} or output.duration_seconds is None:
        raise _error(
            "Grok edit and extension cannot express the requested output timing.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    if request.mode is VideoGenerationMode.VIDEO_EDIT:
        if output.duration_seconds * 1000 != source_duration:
            raise _error(
                "Grok editing inherits the source duration exactly.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )


def _extension_seconds(request: ResolvedVideoGenerationRequest) -> int:
    source = _source_video(request)
    output = request.effective_output
    if (
        not isinstance(output, VideoFlexibleOutputRequirement)
        or output.timing_mode not in {"exact_seconds", "nominal_seconds"}
        or output.duration_seconds is None
    ):
        raise _error(
            "Grok extension requires a total output duration that seals an integer added duration.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    difference_ms = output.duration_seconds * 1000 - source.duration_millis
    if difference_ms % 1000:
        raise _error(
            "Grok extension total duration does not express an exact integer addition.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    added_seconds = difference_ms // 1000
    if not 2 <= added_seconds <= 10 or not 2_000 <= source.duration_millis <= 15_000:
        raise _error(
            "Grok extension source and added duration are outside documented bounds.",
            ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
        )
    return added_seconds


def _image_data_uri(binding: VideoImageReferenceBinding, raw: bytes) -> str:
    if (
        not isinstance(raw, bytes)
        or binding.size_bytes is None
        or binding.size_bytes > MAX_GROK_IMAGE_BYTES
        or len(raw) != binding.size_bytes
        or hashlib.sha256(raw).hexdigest() != binding.asset_sha256
    ):
        raise _error("Grok image bytes do not match their sealed Registry binding.")
    return f"data:{binding.mime_type};base64," + base64.b64encode(raw).decode("ascii")


def _video_data_uri(binding: VideoMediaReferenceBinding, raw: bytes) -> str:
    if (
        not isinstance(raw, bytes)
        or binding.size_bytes > MAX_GROK_SOURCE_VIDEO_BYTES
        or len(raw) != binding.size_bytes
        or hashlib.sha256(raw).hexdigest() != binding.asset_sha256
        or binding.mime_type != "video/mp4"
        or len(raw) < 12
        or raw[4:8] != b"ftyp"
    ):
        raise _error("Grok MP4 source bytes do not match their sealed Registry binding.")
    return "data:video/mp4;base64," + base64.b64encode(raw).decode("ascii")


def build_grok_video_operation(
    request: ResolvedVideoGenerationRequest,
    *,
    profile: GrokProviderProfile,
    capabilities: VideoProviderCapabilities,
    image_resolver: ImageResolver | None,
    media_resolver: MediaResolver | None,
) -> GrokVideoOperation:
    validate_grok_video_request(
        request, profile=profile, capabilities=capabilities
    )
    output = request.effective_output
    assert isinstance(output, VideoFlexibleOutputRequirement)
    egress = grok_egress_inputs(request)
    projected_bytes = sum((input.size_bytes * 4 + 2) // 3 for input in egress)
    if projected_bytes > MAX_GROK_POST_BODY_BYTES:
        raise _error("Grok aggregate media body exceeds the local size limit.")

    image_by_asset = {item.asset_id: item for item in request.image_bindings}
    media_by_asset = {item.asset_id: item for item in request.media_bindings}
    raw_by_asset: dict[str, bytes] = {}
    for identity in egress:
        image = image_by_asset.get(identity.asset_id)
        if image is not None:
            if image_resolver is None:
                raise _error("Grok image byte resolver is unavailable.")
            try:
                raw = image_resolver(image)
            except Exception:
                raise _error("Grok image bytes are unavailable.") from None
            data_uri = _image_data_uri(image, raw)
        else:
            media = media_by_asset[identity.asset_id]
            if media_resolver is None:
                raise _error("Grok source video byte resolver is unavailable.")
            try:
                raw = media_resolver(media)
            except Exception:
                raise _error("Grok source video bytes are unavailable.") from None
            data_uri = _video_data_uri(media, raw)
        raw_by_asset[identity.asset_id] = data_uri.encode("ascii")

    if grok_endpoint_for_mode(request.mode) == "generations":
        if output.duration_seconds is None:
            raise _error(
                "Grok video generation requires an expressible duration.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        payload: dict[str, object] = {
            "model": request.model_id,
            "prompt": request.prompt_text,
            "duration": output.duration_seconds,
            "resolution": output.resolution_label,
            "generate_audio": output.native_audio,
        }
        if output.ratio != "adaptive":
            payload["aspect_ratio"] = output.ratio
        first = next((item for item in request.image_bindings if item.role == "first_frame"), None)
        last = next((item for item in request.image_bindings if item.role == "last_frame"), None)
        if first is not None:
            payload["image"] = {"url": raw_by_asset[first.asset_id].decode("ascii")}
        if last is not None:
            payload["last_frame"] = {"url": raw_by_asset[last.asset_id].decode("ascii")}
        profile_keyframes = tuple(getattr(profile, "keyframes", ()))
        keyed_ids = {getattr(item, "asset_id") for item in profile_keyframes}
        refs = tuple(
            item for item in request.image_bindings
            if item.role == "reference" and item.asset_id not in keyed_ids
        )
        api_reference_limit = 14 if request.model_id == GROK_VIDEO_MODEL_FULL else 7 if request.model_id == GROK_VIDEO_MODEL_CLASSIC else 0
        if len(refs) > api_reference_limit:
            raise _error(
                "Grok reference image count exceeds the selected model capability.",
                ErrorCode.VIDEO_CAPABILITY_UNSUPPORTED,
            )
        if refs:
            payload["reference_images"] = [
                {"url": raw_by_asset[item.asset_id].decode("ascii")}
                for item in refs
            ]
        if profile_keyframes:
            payload["keyframes"] = [
                {
                    "image": {"url": raw_by_asset[item.asset_id].decode("ascii")},
                    "timestamp_s": getattr(item, "timestamp_ticks") / 3,
                }
                for item in profile_keyframes
            ]
        voices = tuple(getattr(profile, "reference_voices", ()))
        if voices:
            payload["reference_audios"] = [{"voice_id": voice} for voice in voices]
    else:
        source = _source_video(request)
        payload = {
            "model": request.model_id,
            "prompt": request.prompt_text,
            "video": {"url": raw_by_asset[source.asset_id].decode("ascii")},
        }
        if request.mode is VideoGenerationMode.VIDEO_EXTEND:
            payload["duration"] = _extension_seconds(request)

    try:
        body = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise _error("Grok request payload is invalid.") from None
    if len(body) > MAX_GROK_POST_BODY_BYTES:
        raise _error("Grok request body exceeds the local size limit.")
    return GrokVideoOperation(
        endpoint=grok_endpoint_for_mode(request.mode),
        model_id=request.model_id,
        egress_inputs=egress,
        body=body,
    )


__all__ = [
    "GROK_VIDEO_ENDPOINTS",
    "MAX_GROK_IMAGE_BYTES",
    "MAX_GROK_POST_BODY_BYTES",
    "MAX_GROK_SOURCE_VIDEO_BYTES",
    "GrokEgressInput",
    "GrokVideoOperation",
    "build_grok_video_operation",
    "grok_endpoint_for_mode",
    "grok_egress_inputs",
    "select_grok_capability",
    "validate_grok_video_request",
]
