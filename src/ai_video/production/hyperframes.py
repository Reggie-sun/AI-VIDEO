from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import struct
import subprocess
import wave
from io import BytesIO
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import (
    Decimal,
    DecimalException,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    localcontext,
)
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterator, Literal, Protocol, cast
from urllib.parse import urlsplit

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import (
    _canonical_track_bytes,
    validate_caption_track_timeline_binding,
)
from ai_video.production.composition import (
    _validated_visual_suffix,
    timeline_fingerprint,
)
from ai_video.production.hashing import seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    AudioChannelLayout,
    CaptionTrack,
    MeasuredAudioRenderMetadata,
    MeasuredRenderMetadata,
    RendererAssetBinding,
    RendererAudioBinding,
    RendererCaptionBinding,
    RendererCheckReceipt,
    RendererKind,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderArtifactPointer,
    RenderOutputPointer,
    RenderReceipt,
    RenderSourceBundlePointer,
    RenderSourceFilePointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ProductionManifest,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
)
from ai_video.production.paths import (
    NoFollowFile,
    _copy_held_fd_to_regular_file_nofollow,
    _create_directory_nofollow,
    _create_regular_file_nofollow,
    _list_regular_files_nofollow,
    _open_regular_file_nofollow,
    _read_regular_file_nofollow,
    _validate_contained_target,
    _validate_directory_nofollow,
    _validate_new_contained_output,
    _validate_new_contained_root,
    canonical_render_output_path,
    canonical_render_attempt_root,
    canonical_render_receipt_path,
    canonical_render_source_asset_path,
    canonical_render_source_index_path,
    canonical_render_source_root,
    canonical_render_state_path,
    canonical_render_timeline_path,
    canonical_renderer_source_receipt_path,
)
from ai_video.production.state_commit import (
    ActivateRenderStateRequest,
    BeginRenderAttemptRequest,
    PreparedArtifact,
    ProductionStateCommitter,
    RecordRenderFailureRequest,
    RenderAttemptPaths,
)
from ai_video.production.visual_media import render_visual_element, visual_media_css

RenderDependencyTransitionPreparer = Callable[
    [ActivateRenderStateRequest], ActivateRenderStateRequest
]


_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
_IMPORT_PATTERN = re.compile(
    r"@import\s+(?:url\(\s*)?(['\"]?)([^'\"\s;)]+)\1", re.IGNORECASE
)
_CSS_EXECUTABLE_PATTERN = re.compile(
    r"(?i)(?:\bexpression\s*\(|(?:^|[;{])\s*behavior\s*:|"
    r"(?:^|[;{])\s*-moz-binding\s*:)"
)


@dataclass
class RendererAttemptError(AiVideoError):
    phase: Literal["source", "lint", "check", "render", "verify"] = "render"


def _source_invalid(message: str, detail: str | None = None) -> RendererAttemptError:
    return RendererAttemptError(
        code=ErrorCode.RENDERER_SOURCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
        phase="source",
    )


@dataclass(frozen=True)
class MaterializedHyperFramesSource:
    root: Path
    index_path: Path
    source_sha256: str
    bundle_sha256: str
    asset_bindings: tuple[RendererAssetBinding, ...]
    timeline: ResolvedTimeline
    audio_bindings: tuple[RendererAudioBinding, ...] = ()
    caption_bindings: tuple[RendererCaptionBinding, ...] = ()


@dataclass(frozen=True)
class _ParsedSourceDocument:
    stage_attributes: dict[str, str | None]
    clip_attributes: tuple[dict[str, str | None], ...]
    media_urls: frozenset[str]
    all_urls: frozenset[str]
    css_imports: tuple[str, ...]
    css_model: tuple[object, ...]
    document_model: tuple[object, ...]
    has_script: bool
    external_styles_or_fonts: bool
    has_event_handler: bool
    forbidden_text: bool


class _SourceParser(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.stage_attributes: list[dict[str, str | None]] = []
        self.clip_attributes: list[dict[str, str | None]] = []
        self.media_urls: set[str] = set()
        self.all_urls: set[str] = set()
        self.styles: list[str] = []
        self.document: list[object] = []
        self.has_script = False
        self.external_styles_or_fonts = False
        self.has_event_handler = False
        self._in_style = False
        self._style_parts: list[str] = []

    def handle_decl(self, decl: str) -> None:
        self.document.append(("decl", decl.lower()))

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._handle_tag("start", tag, attrs)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._handle_tag("startend", tag, attrs)

    def _handle_tag(
        self, kind: str, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        lowered = tag.lower()
        if len({name.lower() for name, _ in attrs}) != len(attrs):
            raise _source_invalid("HyperFrames source contains duplicate attributes.")
        attributes = {name.lower(): value for name, value in attrs}
        self.document.append((kind, lowered, tuple(sorted(attributes.items()))))
        if lowered == "style":
            self._in_style = True
            self._style_parts = []
        if lowered == "script":
            self.has_script = True
        if lowered == "link":
            rel = (attributes.get("rel") or "").lower().split()
            if "stylesheet" in rel or "preload" in rel or "font" in rel:
                self.external_styles_or_fonts = True
        if attributes.get("id") == "stage":
            self.stage_attributes.append(attributes)
        classes = (attributes.get("class") or "").split()
        if "clip" in classes:
            self.clip_attributes.append(attributes)
        for name, value in attributes.items():
            if name.startswith("on"):
                self.has_event_handler = True
            if value is None:
                continue
            if name in {"src", "href", "poster"}:
                self.all_urls.add(value)
                if lowered in {"img", "video", "audio", "source"}:
                    self.media_urls.add(value)
            elif name == "srcset":
                for candidate in value.split(","):
                    url = candidate.strip().split(maxsplit=1)[0]
                    if url:
                        self.all_urls.add(url)
                        self.media_urls.add(url)
            elif name == "style":
                self.all_urls.update(match[1] for match in _URL_PATTERN.findall(value))

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        self.document.append(("end", lowered))
        if lowered == "style":
            self._in_style = False
            self.styles.append("".join(self._style_parts))

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_parts.append(data)
        elif data.strip():
            self.document.append(("data", data.strip()))


def _split_css_rules(css: str) -> tuple[tuple[str, str], ...]:
    rules: list[tuple[str, str]] = []
    cursor = 0
    length = len(css)
    while cursor < length:
        while cursor < length and css[cursor].isspace():
            cursor += 1
        if cursor == length:
            break
        opening = css.find("{", cursor)
        if opening < 0:
            raise _source_invalid("CSS contains an unterminated rule.")
        header = css[cursor:opening].strip()
        if not header:
            raise _source_invalid("CSS contains an empty rule header.")
        depth = 1
        end = opening + 1
        while end < length and depth:
            if css[end] == "{":
                depth += 1
            elif css[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise _source_invalid("CSS contains an unterminated rule body.")
        rules.append((header, css[opening + 1 : end - 1]))
        cursor = end
    return tuple(rules)


def _parse_declarations(body: str) -> tuple[tuple[str, str], ...]:
    declarations: list[tuple[str, str]] = []
    for item in body.split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise _source_invalid("CSS contains an invalid declaration.")
        name, value = item.split(":", 1)
        declarations.append((name.strip().lower(), value.strip()))
    if len({name for name, _ in declarations}) != len(declarations):
        raise _source_invalid("CSS contains a duplicate declaration.")
    return tuple(declarations)


def _parse_css_model(styles: list[str]) -> tuple[object, ...]:
    model: list[object] = []
    for css in styles:
        if re.search(r"(?i)(?<![-\w])@import\b", css):
            raise _source_invalid("CSS imports are not allowed in HyperFrames source.")
        for header, body in _split_css_rules(css):
            if header.lower().startswith("@keyframes "):
                name = header.split(maxsplit=1)[1]
                stops = tuple(
                    (stop_header.replace(" ", ""), _parse_declarations(stop_body))
                    for stop_header, stop_body in _split_css_rules(body)
                )
                model.append(("keyframes", name, stops))
            else:
                model.append(("rule", header.replace(" ", ""), _parse_declarations(body)))
    return tuple(model)


def _parse_source_document(source: str) -> _ParsedSourceDocument:
    parser = _SourceParser(source)
    try:
        parser.feed(source)
        parser.close()
    except AiVideoError:
        raise
    except (UnicodeError, ValueError) as exc:
        raise _source_invalid("HyperFrames source could not be parsed.", str(exc)) from exc
    if len(parser.stage_attributes) != 1:
        raise _source_invalid("HyperFrames source must contain exactly one stage root.")
    imports: list[str] = []
    for style in parser.styles:
        imports.extend(match[1] for match in _IMPORT_PATTERN.findall(style))
        parser.all_urls.update(match[1] for match in _URL_PATTERN.findall(style))
    lowered = source.lower()
    forbidden_runtime_context = any(
        bool(urlsplit(value.strip()).scheme)
        or bool(urlsplit(value.strip()).netloc)
        or value.strip().startswith("//")
        for value in parser.all_urls
    ) or any(_CSS_EXECUTABLE_PATTERN.search(style) for style in parser.styles)
    return _ParsedSourceDocument(
        stage_attributes=parser.stage_attributes[0],
        clip_attributes=tuple(parser.clip_attributes),
        media_urls=frozenset(parser.media_urls),
        all_urls=frozenset(parser.all_urls),
        css_imports=tuple(imports),
        css_model=_parse_css_model(parser.styles),
        document_model=tuple(parser.document),
        has_script=parser.has_script,
        external_styles_or_fonts=(
            parser.external_styles_or_fonts or "@font-face" in lowered
        ),
        has_event_handler=parser.has_event_handler,
        # Caption/data text is inert and remains part of the exact document model.
        # Only URL-bearing or executable CSS contexts are classified here; script
        # tags and event handlers are tracked independently by the parser.
        forbidden_text=forbidden_runtime_context,
    )


def _seconds(frame_count: int, fps: int) -> str:
    value = Decimal(frame_count) / Decimal(fps)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _clip_start_seconds(frame: int, fps: int) -> str:
    value = Decimal(frame) / Decimal(fps)
    rendered = format(
        value.quantize(Decimal("0.000000001"), rounding=ROUND_FLOOR), "f"
    )
    return rendered.rstrip("0").rstrip(".") or "0"


def _capture_safe_boundary_percent(
    frame: int,
    *,
    total_frames: int,
    fps: int,
    serialized_duration: str,
) -> str:
    if frame == 0:
        return "0%"
    if frame == total_frames:
        return "100%"
    if not 0 < frame < total_frames:
        raise _source_invalid("CSS boundary frame is outside the timeline.")
    duration_decimal = Decimal(serialized_duration)
    if not duration_decimal.is_finite() or duration_decimal <= 0:
        raise _source_invalid("Serialized CSS duration is not finite and positive.")
    previous_time = Decimal(frame - 1) / Decimal(fps)
    current_time = Decimal(frame) / Decimal(fps)
    target_time = (Decimal(frame) - Decimal("0.5")) / Decimal(fps)
    value = (target_time * Decimal(100) / duration_decimal).quantize(
        Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
    )
    rendered = format(value, "f").rstrip("0").rstrip(".")
    mapped_decimal = Decimal(rendered) * duration_decimal / Decimal(100)
    duration_f = float(serialized_duration)
    duration_ms_f = duration_f * 1000.0
    offset_progress_f = float(rendered) / 100.0
    previous_raw_seconds_f = (frame - 1) / fps
    current_raw_seconds_f = frame / fps
    previous_frame_position_f = previous_raw_seconds_f * fps + 1e-9
    current_frame_position_f = current_raw_seconds_f * fps + 1e-9
    values = (
        duration_f,
        duration_ms_f,
        offset_progress_f,
        previous_raw_seconds_f,
        current_raw_seconds_f,
        previous_frame_position_f,
        current_frame_position_f,
    )
    if duration_ms_f <= 0.0 or not all(math.isfinite(item) for item in values):
        raise _source_invalid("Serialized CSS millisecond seek values are invalid.")
    previous_quantized_seconds_f = math.floor(previous_frame_position_f) / fps
    current_quantized_seconds_f = math.floor(current_frame_position_f) / fps
    previous_ms_f = previous_quantized_seconds_f * 1000.0
    current_ms_f = current_quantized_seconds_f * 1000.0
    previous_progress_f = previous_ms_f / duration_ms_f
    current_progress_f = current_ms_f / duration_ms_f
    quantized_values = (
        previous_quantized_seconds_f,
        current_quantized_seconds_f,
        previous_ms_f,
        current_ms_f,
        previous_progress_f,
        current_progress_f,
    )
    if not (
        previous_time < mapped_decimal < current_time
        and all(math.isfinite(item) for item in quantized_values)
        and previous_progress_f < current_progress_f
        and previous_progress_f < offset_progress_f < current_progress_f
    ):
        raise _source_invalid("Serialized CSS boundary is not capture-frame safe.")
    return f"{rendered}%"


def _css_animation_name(layer_id: str) -> str:
    return f"p3-layer-{hashlib.sha256(layer_id.encode('utf-8')).hexdigest()}"


def _css_visibility_keyframes(
    name: str,
    *,
    start_frame: int,
    end_frame: int,
    total_frames: int,
    fps: int,
    serialized_duration: str,
    target_opacity: str,
) -> str:
    start = _capture_safe_boundary_percent(
        start_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    end = _capture_safe_boundary_percent(
        end_frame,
        total_frames=total_frames,
        fps=fps,
        serialized_duration=serialized_duration,
    )
    if start_frame == 0 and end_frame == total_frames:
        body = f"0%,100%{{opacity:{target_opacity}}}"
    elif start_frame == 0:
        body = f"0%,{end}{{opacity:{target_opacity}}}{end},100%{{opacity:0}}"
    elif end_frame == total_frames:
        body = f"0%,{start}{{opacity:0}}{start},100%{{opacity:{target_opacity}}}"
    else:
        body = (
            f"0%,{start}{{opacity:0}}"
            f"{start},{end}{{opacity:{target_opacity}}}"
            f"{end},100%{{opacity:0}}"
        )
    return f"@keyframes {name}{{{body}}}"


def _decimal_milli(value: int) -> str:
    rendered = format(Decimal(value) / Decimal(1000), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


def _sample_seconds(samples: int, sample_rate: int) -> str:
    value = Decimal(samples) / Decimal(sample_rate)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
    return rendered.rstrip("0").rstrip(".") or "0"


_MIX_SCALE = 1_000_000
_MIN_GAIN_MILLIDB = -96_000
_MAX_GAIN_MILLIDB = 24_000


def _fixed_gain(gain_millidb: int) -> int:
    """Convert the adapter-supported -96..+24 dB range to fixed-point gain."""

    if not _MIN_GAIN_MILLIDB <= gain_millidb <= _MAX_GAIN_MILLIDB:
        raise _source_invalid(
            "Audio gain is outside the P4 renderer adapter range.",
            f"supported gain_millidb range is {_MIN_GAIN_MILLIDB}..{_MAX_GAIN_MILLIDB}",
        )
    try:
        with localcontext() as context:
            context.prec = 50
            context.rounding = ROUND_HALF_EVEN
            exponent = Decimal(gain_millidb) / Decimal(20_000)
            scaled = (Decimal(10) ** exponent) * Decimal(_MIX_SCALE)
            return int(scaled.to_integral_value(rounding=ROUND_HALF_EVEN))
    except (DecimalException, OverflowError, ValueError) as exc:
        raise _source_invalid(
            "Audio gain could not be converted deterministically.",
            f"supported gain_millidb range is {_MIN_GAIN_MILLIDB}..{_MAX_GAIN_MILLIDB}",
        ) from exc


def _multiply_fixed(left: int, right: int) -> int:
    product = left * right
    return (product + _MIX_SCALE // 2) // _MIX_SCALE


def _scale_pcm(sample: int, scale: int) -> int:
    product = sample * scale
    if product >= 0:
        return (product + _MIX_SCALE // 2) // _MIX_SCALE
    return -((-product + _MIX_SCALE // 2) // _MIX_SCALE)


def _linear_scale(start: int, end: int, ordinal: int, length: int) -> int:
    if length <= 0:
        return end
    return start + ((end - start) * ordinal + length // 2) // length


def _ducking_scale(
    sample: int,
    *,
    intervals: tuple[tuple[int, int], ...],
    attenuation: int,
    attack: int,
    release: int,
) -> int:
    result = _MIX_SCALE
    for start, end in intervals:
        if start <= sample < end:
            if attack and sample - start < attack:
                candidate = _linear_scale(
                    _MIX_SCALE, attenuation, sample - start + 1, attack
                )
            else:
                candidate = attenuation
            result = min(result, candidate)
        elif release and end <= sample < end + release:
            candidate = _linear_scale(
                attenuation, _MIX_SCALE, sample - end + 1, release
            )
            result = min(result, candidate)
    return result


def _decoded_pcm16(snapshot: NoFollowFile) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    sample_rate, channels, frames = _validated_wav(snapshot)
    with wave.open(BytesIO(snapshot.data), "rb") as source:
        payload = source.readframes(frames)
    values = struct.unpack(f"<{frames * channels}h", payload)
    if channels == 1:
        stereo = tuple((value, value) for value in values)
    else:
        stereo = tuple(zip(values[0::2], values[1::2], strict=True))
    return sample_rate, frames, stereo


def _mix_resolved_audio(
    timeline: ResolvedTimeline,
    *,
    audio_snapshots: Mapping[str, NoFollowFile],
) -> bytes:
    decoded: dict[str, tuple[tuple[int, int], ...]] = {}
    for asset_id, snapshot in audio_snapshots.items():
        sample_rate, _, samples = _decoded_pcm16(snapshot)
        if sample_rate != timeline.sample_rate:
            raise _source_invalid("Audio source sample rate does not match timeline.")
        decoded[asset_id] = samples
    by_track = {item.track_id: item for item in timeline.audio_spans}
    output = [[0, 0] for _ in range(timeline.total_samples)]
    for span in timeline.audio_spans:
        source = decoded[span.asset_id]
        source_end = span.source_start_sample + span.source_duration_samples
        if source_end > len(source) or span.duration_samples != span.source_duration_samples:
            raise _source_invalid("P4 pre-mix requires exact source-duration placement.")
        gain = _fixed_gain(span.gain_millidb)
        duck_intervals: tuple[tuple[int, int], ...] = ()
        attenuation = _MIX_SCALE
        attack = release = 0
        if span.ducking is not None:
            duck_intervals = tuple(
                (
                    by_track[track_id].start_sample,
                    by_track[track_id].start_sample
                    + by_track[track_id].duration_samples,
                )
                for track_id in span.ducking.sidechain_track_ids
            )
            attenuation = _fixed_gain(span.ducking.attenuation_millidb)
            attack = span.ducking.attack_samples
            release = span.ducking.release_samples
        for offset in range(span.duration_samples):
            envelope = _MIX_SCALE
            if span.fade_in_samples and offset < span.fade_in_samples:
                envelope = min(
                    envelope,
                    _linear_scale(0, _MIX_SCALE, offset + 1, span.fade_in_samples),
                )
            remaining = span.duration_samples - offset
            if span.fade_out_samples and remaining <= span.fade_out_samples:
                envelope = min(
                    envelope,
                    _linear_scale(0, _MIX_SCALE, remaining, span.fade_out_samples),
                )
            if span.ducking is not None:
                envelope = _multiply_fixed(
                    envelope,
                    _ducking_scale(
                        span.start_sample + offset,
                        intervals=duck_intervals,
                        attenuation=attenuation,
                        attack=attack,
                        release=release,
                    ),
                )
            scale = _multiply_fixed(gain, envelope)
            left, right = source[span.source_start_sample + offset]
            target = output[span.start_sample + offset]
            target[0] += _scale_pcm(left, scale)
            target[1] += _scale_pcm(right, scale)
    pcm = bytearray()
    for left, right in output:
        pcm.extend(
            struct.pack(
                "<hh",
                max(-32768, min(32767, left)),
                max(-32768, min(32767, right)),
            )
        )
    buffer = BytesIO()
    with wave.open(buffer, "wb") as mixed:
        mixed.setnchannels(2)
        mixed.setsampwidth(2)
        mixed.setframerate(timeline.sample_rate)
        mixed.writeframes(bytes(pcm))
    return buffer.getvalue()


def _stable_dom_id(prefix: str, identity: str) -> str:
    return f"{prefix}-{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"


def _caption_style_css(style_hash: str, style: Mapping[str, object]) -> str:
    if style.get("schema_version") != "1":
        raise _source_invalid("Caption style schema version is unsupported.")

    def integer(name: str, default: int, minimum: int, maximum: int) -> int:
        value = style.get(name, default)
        if isinstance(value, bool) or not isinstance(value, int):
            raise _source_invalid(f"Caption style {name} must be an integer.")
        if not minimum <= value <= maximum:
            raise _source_invalid(f"Caption style {name} is out of range.")
        return value

    def color(name: str, default: str) -> str:
        value = style.get(name, default)
        if not isinstance(value, str) or re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is None:
            raise _source_invalid(f"Caption style {name} must be a six-digit hex color.")
        return value.upper()

    font_family = style.get("font_family", "sans-serif")
    if (
        not isinstance(font_family, str)
        or not 1 <= len(font_family) <= 100
        or any(ord(character) < 32 for character in font_family)
    ):
        raise _source_invalid("Caption style font_family is invalid.")
    font_size = integer("font_size_px", 24, 8, 200)
    bottom = integer("bottom_margin_px", 52, 0, 500)
    max_width = integer("max_width_milli", 900, 100, 1000)
    outline_width = integer("outline_width_px", 2, 0, 20)
    text_color = color("text_color", "#FFFFFF")
    outline_color = color("outline_color", "#101820")
    width_percent = format(Decimal(max_width) / Decimal(10), "f").rstrip("0").rstrip(".")
    quoted_family = json.dumps(font_family, ensure_ascii=True)
    shadow = "none"
    if outline_width:
        shadow = ",".join(
            (
                f"-{outline_width}px 0 {outline_color}",
                f"{outline_width}px 0 {outline_color}",
                f"0 -{outline_width}px {outline_color}",
                f"0 {outline_width}px {outline_color}",
            )
        )
    return (
        f"    .caption-style-{style_hash}{{left:50%;right:auto;"
        f"bottom:{bottom}px;width:{width_percent};transform:translateX(-50%);"
        f"padding:0;background:transparent;color:{text_color};text-align:center;"
        f"font-family:{quoted_family};font-size:{font_size}px;font-weight:700;"
        f"line-height:1.25;white-space:pre-wrap;text-shadow:{shadow}}}"
    )


def _render_source(
    timeline: ResolvedTimeline,
    mixed_audio: RendererAudioBinding | None = None,
    caption_styles: Mapping[str, Mapping[str, object]] | None = None,
    *,
    legacy_caption_style: bool = False,
    caption_top_auto: bool = True,
) -> str:
    caption_styles = caption_styles or {}
    expected_style_hashes = {
        cue.style_content_hash for cue in timeline.caption_cues if cue.style_content_hash
    }
    if not legacy_caption_style and set(caption_styles) != expected_style_hashes:
        raise _source_invalid("Caption style values do not match the resolved timeline.")
    if legacy_caption_style and caption_styles:
        raise _source_invalid("Legacy caption source cannot consume style values.")
    fps = timeline.delivery_profile.fps
    duration = _seconds(timeline.total_frames, fps)
    clips: list[str] = []
    audio_elements: list[str] = []
    caption_elements: list[str] = []
    animations: list[str] = []
    keyframes: list[str] = []
    for track_index, span in enumerate(timeline.visual_spans):
        name = _css_animation_name(span.layer_id)
        animations.append(
            f".{name}{{animation-name:{name};animation-duration:{duration}s;"
            "animation-fill-mode:both;animation-play-state:paused;"
            "animation-timing-function:step-end}"
        )
        keyframes.append(
            _css_visibility_keyframes(
                name,
                start_frame=span.start_frame,
                end_frame=span.start_frame + span.duration_frames,
                total_frames=timeline.total_frames,
                fps=fps,
                serialized_duration=duration,
                target_opacity=_decimal_milli(span.opacity_milli),
            )
        )
        media = render_visual_element(
            span,
            video_id=_stable_dom_id("p3-video", span.layer_id),
            start_seconds=_clip_start_seconds(span.start_frame, fps),
            duration_seconds=_seconds(span.duration_frames, fps),
            media_start_seconds=_clip_start_seconds(span.trim_start_frame, fps),
            track_index=track_index,
        )
        clips.append(
            "\n".join(
                [
                    (
                        f'<div class="clip {name}" data-layer-id="{escape(span.layer_id)}"'
                        f' data-animation-name="{name}" data-shot-id="{escape(span.shot_id)}"'
                        f' data-asset-id="{escape(span.asset_id)}"'
                        f' data-asset-role="{escape(span.asset_role)}"'
                        f' data-asset-sha256="{span.asset_sha256}"'
                        f' data-start-frame="{span.start_frame}"'
                        f' data-duration-frames="{span.duration_frames}"'
                        f' data-start-sample="{span.start_sample}"'
                        f' data-duration-samples="{span.duration_samples}"'
                        ' data-transition-kind="cut" data-transition-frames="0"'
                        f' style="z-index:{span.z_index}">'
                    ),
                    media,
                    "</div>",
                ]
            )
        )
    if mixed_audio is not None:
        audio_elements.append(
            (
                f'<audio id="{_stable_dom_id("p4-audio-mix", timeline.composition_fingerprint)}"'
                f' class="clip" src="{mixed_audio.materialized_path.as_posix()}"'
                f' data-mix-asset-id="{escape(mixed_audio.asset_id)}"'
                f' data-mix-sha256="{mixed_audio.asset_sha256}"'
                f' data-resolved-track-ids="{escape(",".join(mixed_audio.resolved_track_ids))}"'
                ' data-start="0"'
                f' data-duration="{_sample_seconds(timeline.total_samples, timeline.sample_rate)}"'
                ' data-media-start="0" data-track-index="10000" data-volume="1"></audio>'
            )
        )
    for track_index, cue in enumerate(timeline.caption_cues, start=20_000):
        if cue.style_content_hash is None:
            raise _source_invalid("Resolved caption cue is missing its style identity.")
        caption_class = "clip caption"
        if not legacy_caption_style:
            caption_class += f" caption-style-{cue.style_content_hash}"
        caption_elements.append(
            (
                f'<div id="{_stable_dom_id("p4-caption", cue.caption_track_id + ":" + cue.segment_id)}" class="{caption_class}" data-layout-allow-caption-zone'
                f' data-caption-track-id="{escape(cue.caption_track_id)}"'
                f' data-caption-asset-id="{escape(cue.caption_asset_id)}"'
                f' data-caption-asset-sha256="{cue.caption_asset_sha256}"'
                f' data-caption-timing-fingerprint="{cue.caption_timing_fingerprint}"'
                f' data-segment-id="{escape(cue.segment_id)}"'
                f' data-style-reference-id="{escape(cue.style_reference_id or "")}"'
                f' data-style-content-hash="{cue.style_content_hash or ""}"'
                f' data-start-sample="{cue.start_sample}" data-end-sample="{cue.end_sample}"'
                f' data-start-frame="{cue.start_frame}" data-end-frame-exclusive="{cue.end_frame_exclusive}"'
                f' data-start="{_clip_start_seconds(cue.start_frame, fps)}"'
                f' data-duration="{_seconds(cue.end_frame_exclusive - cue.start_frame, fps)}"'
                f' data-track-index="{track_index}">{escape(cue.text)}</div>'
            )
        )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8" />',
            "  <style>",
            "    html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000}",
            "    #stage{position:relative;overflow:hidden}",
            "    .clip{position:absolute;inset:0}",
            visual_media_css(timeline.visual_spans),
            *(
                (
                    (
                        "    .caption{position:absolute;left:5%;right:5%;bottom:8%;padding:10px;background:#00ffff;color:#000;text-align:center;font:700 24px/1.25 sans-serif}"
                        if legacy_caption_style
                        else (
                            "    .caption{position:absolute;top:auto}"
                            if caption_top_auto
                            else "    .caption{position:absolute}"
                        )
                    ),
                )
                if timeline.caption_cues
                else ()
            ),
            *(
                _caption_style_css(style_hash, caption_styles[style_hash])
                for style_hash in sorted(caption_styles)
            ),
            *(f"    {rule}" for rule in animations),
            *(f"    {rule}" for rule in keyframes),
            "  </style>",
            "</head>",
            "<body>",
            (
                f'<div id="stage" data-no-timeline data-composition-id="{escape(timeline.timeline_id)}"'
                f' data-timeline-fingerprint="{timeline.composition_fingerprint}"'
                f' data-renderer-version="{escape(timeline.renderer.version)}"'
                f' data-start="0" data-duration="{duration}"'
                f' data-width="{timeline.delivery_profile.width}"'
                f' data-height="{timeline.delivery_profile.height}" data-fps="{fps}">'
            ),
            *clips,
            *caption_elements,
            *audio_elements,
            "</div>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _validate_local_relative_url(url: str) -> None:
    if not url or "%" in url or "\x00" in url or "\\" in url:
        raise _source_invalid("HyperFrames source contains an invalid local URL.")
    parsed = urlsplit(url)
    path = Path(parsed.path)
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or url.startswith("//")
        or path.is_absolute()
        or ".." in path.parts
        or path == Path(".")
    ):
        raise _source_invalid(f"HyperFrames source URL is not contained: {url}")


def _validated_wav(snapshot: NoFollowFile) -> tuple[int, int, int]:
    try:
        with wave.open(BytesIO(snapshot.data), "rb") as source:
            if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                raise ValueError("only PCM16 WAV is accepted by the P4 renderer")
            channels = source.getnchannels()
            if channels not in {1, 2}:
                raise ValueError("P4 audio must be mono or stereo")
            return source.getframerate(), channels, source.getnframes()
    except (EOFError, wave.Error, ValueError) as exc:
        raise _source_invalid("Renderer audio source is not canonical PCM16 WAV.", str(exc)) from exc


def _all_materialized_bindings(
    visual: tuple[RendererAssetBinding, ...],
    audio: tuple[RendererAudioBinding, ...],
    captions: tuple[RendererCaptionBinding, ...],
) -> tuple[tuple[Path, str], ...]:
    values = [(item.materialized_path, item.asset_sha256) for item in visual]
    values.extend((item.materialized_path, item.asset_sha256) for item in audio)
    for item in captions:
        values.append((item.materialized_path, item.caption_asset_sha256))
        if item.style_materialized_path is not None:
            assert item.style_content_hash is not None
            values.append((item.style_materialized_path, item.style_content_hash))
    return tuple(values)


def _source_bundle_sha256(
    index_path: Path,
    bindings: tuple[RendererAssetBinding, ...],
    *,
    expected_index_sha256: str,
    audio_bindings: tuple[RendererAudioBinding, ...] = (),
    caption_bindings: tuple[RendererCaptionBinding, ...] = (),
) -> str:
    root = index_path.parent
    materialized = _all_materialized_bindings(
        bindings, audio_bindings, caption_bindings
    )
    paths = {Path("index.html"), *(path for path, _ in materialized)}
    if _list_regular_files_nofollow(root) != paths:
        raise _source_invalid("HyperFrames bundle file set changed after audit.")
    expected_hashes = {Path("index.html"): expected_index_sha256}
    for path, digest in materialized:
        previous = expected_hashes.get(path)
        if previous is not None and previous != digest:
            raise _source_invalid("HyperFrames bundle has conflicting asset hashes.")
        expected_hashes[path] = digest
    entries = []
    for relative in sorted(paths, key=lambda item: item.as_posix()):
        snapshot = _read_regular_file_nofollow(root / relative, contained_by=root)
        if snapshot.file_sha256 != expected_hashes[relative]:
            raise _source_invalid(
                f"HyperFrames bundle file changed after audit: {relative}."
            )
        entries.append((relative.as_posix(), snapshot.file_sha256))
    payload = json.dumps(entries, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate_timeline(timeline: ResolvedTimeline) -> None:
    if not verify_artifact_hash(timeline):
        raise _source_invalid("Resolved timeline content hash is invalid.")
    if timeline_fingerprint(timeline) != timeline.composition_fingerprint:
        raise _source_invalid("Resolved timeline fingerprint is invalid.")


def _load_materialized_caption_styles(
    source_root: Path,
    bindings: tuple[RendererCaptionBinding, ...],
) -> dict[str, Mapping[str, object]]:
    styles: dict[str, Mapping[str, object]] = {}
    for binding in bindings:
        if (
            binding.style_content_hash is None
            or binding.style_materialized_path is None
        ):
            raise _source_invalid("Renderer caption binding is missing its style source.")
        snapshot = _read_regular_file_nofollow(
            source_root / binding.style_materialized_path,
            contained_by=source_root,
        )
        if snapshot.file_sha256 != binding.style_content_hash:
            raise _source_invalid("Caption style source hash does not match its binding.")
        try:
            value = json.loads(snapshot.data)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise _source_invalid("Caption style JSON is invalid.", str(exc)) from exc
        if not isinstance(value, dict):
            raise _source_invalid("Caption style JSON must be an object.")
        previous = styles.get(binding.style_content_hash)
        if previous is not None and previous != value:
            raise _source_invalid("Caption style identity has conflicting values.")
        styles[binding.style_content_hash] = value
    return styles


def _audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
    expected_timeline: ResolvedTimeline,
    expected_audio: tuple[RendererAudioBinding, ...] = (),
    expected_captions: tuple[RendererCaptionBinding, ...] = (),
) -> None:
    _validate_timeline(expected_timeline)
    timeline_bindings: dict[str, RendererAssetBinding] = {}
    for span in expected_timeline.visual_spans:
        binding = RendererAssetBinding(
            asset_id=span.asset_id,
            asset_sha256=span.asset_sha256,
            asset_mime_type=span.asset_mime_type,
            materialized_path=span.materialized_path,
        )
        previous = timeline_bindings.get(span.asset_id)
        if previous is not None and previous != binding:
            raise _source_invalid("Timeline contains a conflicting asset binding.")
        timeline_bindings[span.asset_id] = binding
    if expected_assets != tuple(
        timeline_bindings[key] for key in sorted(timeline_bindings)
    ):
        raise _source_invalid("Declared bindings do not exactly match the timeline.")
    source_root = index_path.parent
    snapshot = _read_regular_file_nofollow(index_path, contained_by=source_root)
    source = snapshot.data.decode("utf-8", errors="strict")
    parsed = _parse_source_document(source)
    caption_styles = _load_materialized_caption_styles(
        source_root, expected_captions
    )
    expected_current = _parse_source_document(
        _render_source(
            expected_timeline,
            expected_audio[0] if expected_audio else None,
            caption_styles,
        )
    )
    expected_legacy = _parse_source_document(
        _render_source(
            expected_timeline,
            expected_audio[0] if expected_audio else None,
            legacy_caption_style=True,
        )
    )
    expected_pre_top_fix = _parse_source_document(
        _render_source(
            expected_timeline,
            expected_audio[0] if expected_audio else None,
            caption_styles,
            caption_top_auto=False,
        )
    )

    def structure_matches(expected: _ParsedSourceDocument) -> bool:
        return (
            parsed.document_model == expected.document_model
            and parsed.css_model == expected.css_model
            and parsed.stage_attributes == expected.stage_attributes
            and parsed.clip_attributes == expected.clip_attributes
        )

    if not any(
        structure_matches(expected)
        for expected in (expected_current, expected_pre_top_fix, expected_legacy)
    ):
        raise _source_invalid("HyperFrames source structure does not match the timeline.")
    if parsed.stage_attributes.get("data-no-timeline", "missing") is not None:
        raise _source_invalid("HyperFrames source requires boolean data-no-timeline.")
    if (
        parsed.has_script
        or parsed.external_styles_or_fonts
        or parsed.has_event_handler
        or parsed.css_imports
        or parsed.forbidden_text
    ):
        raise _source_invalid("HyperFrames source contains a runtime or external input.")
    expected_urls = {item.materialized_path.as_posix() for item in expected_assets}
    expected_urls.update(item.materialized_path.as_posix() for item in expected_audio)
    if parsed.media_urls != expected_urls or parsed.all_urls != expected_urls:
        raise _source_invalid("Source URLs do not exactly match declared media bindings.")
    for url in parsed.all_urls:
        _validate_local_relative_url(url)
    for binding in expected_assets:
        relative = binding.materialized_path
        target = _validate_contained_target(source_root, relative, before_creation=False)
        target_snapshot = _read_regular_file_nofollow(target, contained_by=source_root)
        if target_snapshot.file_sha256 != binding.asset_sha256:
            raise _source_invalid(f"Changed source asset: {binding.asset_id}.")
        _validated_visual_suffix(
            target_snapshot,
            suffix=target.suffix,
            mime_type=binding.asset_mime_type,
        )
    for binding in expected_audio:
        target = _validate_contained_target(
            source_root, binding.materialized_path, before_creation=False
        )
        target_snapshot = _read_regular_file_nofollow(target, contained_by=source_root)
        if target_snapshot.file_sha256 != binding.asset_sha256:
            raise _source_invalid(f"Changed audio source asset: {binding.asset_id}.")
        sample_rate, channels, duration = _validated_wav(target_snapshot)
        if (
            sample_rate != binding.sample_rate_hz
            or channels != binding.channels
            or duration != binding.duration_samples
        ):
            raise _source_invalid("Measured renderer audio binding changed.")
    for binding in expected_captions:
        caption_path = _validate_contained_target(
            source_root, binding.materialized_path, before_creation=False
        )
        caption_snapshot = _read_regular_file_nofollow(
            caption_path, contained_by=source_root
        )
        if caption_snapshot.file_sha256 != binding.caption_asset_sha256:
            raise _source_invalid("Changed structured caption asset.")
        try:
            track = CaptionTrack.model_validate_json(caption_snapshot.data)
        except ValueError as exc:
            raise _source_invalid("Structured caption asset is invalid.", str(exc)) from exc
        if caption_snapshot.data != _canonical_track_bytes(track):
            raise _source_invalid("Structured caption bytes are not canonical.")
        cues = tuple(
            cue
            for cue in expected_timeline.caption_cues
            if cue.caption_track_id == binding.caption_track_id
        )
        try:
            validate_caption_track_timeline_binding(
                track,
                caption_asset_sha256=binding.caption_asset_sha256,
                cues=cues,
                audio_spans=expected_timeline.audio_spans,
                sample_rate_hz=expected_timeline.sample_rate,
                fps=expected_timeline.delivery_profile.fps,
                style_reference_id=binding.style_reference_id,
                style_content_hash=binding.style_content_hash,
            )
        except ValueError as exc:
            raise _source_invalid(
                "Structured caption semantics changed.", str(exc)
            ) from exc
        if binding.style_materialized_path is not None:
            style_path = _validate_contained_target(
                source_root, binding.style_materialized_path, before_creation=False
            )
            style_snapshot = _read_regular_file_nofollow(
                style_path, contained_by=source_root
            )
            if style_snapshot.file_sha256 != binding.style_content_hash:
                raise _source_invalid("Caption style bytes changed.")
            try:
                style_value = json.loads(style_snapshot.data)
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise _source_invalid("Caption style JSON is invalid.", str(exc)) from exc
            if not isinstance(style_value, dict):
                raise _source_invalid("Caption style JSON must be an object.")
    materialized = _all_materialized_bindings(
        expected_assets, expected_audio, expected_captions
    )
    expected_files = {Path("index.html"), *(path for path, _ in materialized)}
    if _list_regular_files_nofollow(source_root) != expected_files:
        raise _source_invalid("HyperFrames staging contains an undeclared file.")


def audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
    expected_timeline: ResolvedTimeline,
    expected_audio: tuple[RendererAudioBinding, ...] = (),
    expected_captions: tuple[RendererCaptionBinding, ...] = (),
) -> None:
    try:
        _audit_hyperframes_source(
            index_path,
            expected_assets=expected_assets,
            expected_timeline=expected_timeline,
            expected_audio=expected_audio,
            expected_captions=expected_captions,
        )
    except AiVideoError as exc:
        if exc.code is ErrorCode.RENDERER_SOURCE_INVALID:
            raise
        raise _source_invalid("HyperFrames source is invalid.", str(exc)) from exc
    except (OSError, UnicodeError, ValueError) as exc:
        raise _source_invalid("HyperFrames source could not be audited safely.", str(exc)) from exc


def _materialize_hyperframes_source(
    timeline: ResolvedTimeline,
    *,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
    staging_root: Path,
    allowed_staging_parent: Path,
) -> MaterializedHyperFramesSource:
    _validate_timeline(timeline)
    visual_ids = {item.asset_id for item in timeline.visual_spans}
    audio_ids = {item.asset_id for item in timeline.audio_spans}
    caption_ids = {item.caption_asset_id for item in timeline.caption_cues}
    style_ids = {
        item.style_reference_id
        for item in timeline.caption_cues
        if item.style_reference_id is not None
    }
    expected_ids = visual_ids | audio_ids | caption_ids | style_ids
    if set(asset_sources) != expected_ids:
        raise _source_invalid("Asset sources must exactly match timeline asset IDs.")
    root = _validate_new_contained_root(
        staging_root, allowed_parent=allowed_staging_parent
    )
    index_path = _validate_contained_target(
        root, Path("index.html"), before_creation=True
    )
    bindings_by_id: dict[str, RendererAssetBinding] = {}
    targets_by_id: dict[str, Path] = {}
    for span in timeline.visual_spans:
        expected = RendererAssetBinding(
            asset_id=span.asset_id,
            asset_sha256=span.asset_sha256,
            asset_mime_type=span.asset_mime_type,
            materialized_path=span.materialized_path,
        )
        previous = bindings_by_id.get(span.asset_id)
        if previous is not None and previous != expected:
            raise _source_invalid(f"Asset binding changed within timeline: {span.asset_id}.")
        bindings_by_id[span.asset_id] = expected
        targets_by_id[span.asset_id] = _validate_contained_target(
            root, span.materialized_path, before_creation=True
        )
    bindings = tuple(bindings_by_id[key] for key in sorted(bindings_by_id))

    audio_snapshots: dict[str, NoFollowFile] = {}
    for asset_id in sorted(audio_ids):
        spans = tuple(item for item in timeline.audio_spans if item.asset_id == asset_id)
        digest = spans[0].asset_sha256
        if any(item.asset_sha256 != digest for item in spans):
            raise _source_invalid("Timeline contains conflicting audio asset hashes.")
        source = Path(asset_sources[asset_id])
        snapshot = _read_regular_file_nofollow(source, contained_by=allowed_asset_root)
        if source.suffix.lower() != ".wav" or snapshot.file_sha256 != digest:
            raise _source_invalid("Audio source type or hash does not match timeline.")
        sample_rate, channels, duration_samples = _validated_wav(snapshot)
        if sample_rate != timeline.sample_rate or any(
            item.source_start_sample + item.source_duration_samples > duration_samples
            for item in spans
        ):
            raise _source_invalid("Audio source measurements do not match timeline.")
        audio_snapshots[asset_id] = snapshot
    audio_bindings: tuple[RendererAudioBinding, ...] = ()
    mixed_audio_bytes: bytes | None = None
    mixed_audio_target: Path | None = None
    if timeline.audio_spans:
        mixed_audio_bytes = _mix_resolved_audio(
            timeline, audio_snapshots=audio_snapshots
        )
        mixed_audio_hash = hashlib.sha256(mixed_audio_bytes).hexdigest()
        mixed_relative = Path("assets") / f"{mixed_audio_hash}.wav"
        mixed_audio_target = _validate_contained_target(
            root, mixed_relative, before_creation=True
        )
        audio_bindings = (
            RendererAudioBinding(
                asset_id=f"p4-mix-{timeline.composition_fingerprint}",
                asset_sha256=mixed_audio_hash,
                asset_mime_type="audio/wav",
                materialized_path=mixed_relative,
                sample_rate_hz=timeline.sample_rate,
                channels=2,
                duration_samples=timeline.total_samples,
                resolved_track_ids=tuple(item.track_id for item in timeline.audio_spans),
            ),
        )

    caption_bindings_list: list[RendererCaptionBinding] = []
    caption_styles: dict[str, Mapping[str, object]] = {}
    for caption_id in sorted(caption_ids):
        cues = tuple(
            item for item in timeline.caption_cues if item.caption_asset_id == caption_id
        )
        digest = cues[0].caption_asset_sha256
        if any(item.caption_asset_sha256 != digest for item in cues):
            raise _source_invalid("Timeline contains conflicting caption hashes.")
        caption_source = Path(asset_sources[caption_id])
        caption_snapshot = _read_regular_file_nofollow(
            caption_source, contained_by=allowed_asset_root
        )
        if caption_source.suffix.lower() != ".json" or caption_snapshot.file_sha256 != digest:
            raise _source_invalid("Caption source type or hash does not match timeline.")
        try:
            track = CaptionTrack.model_validate_json(caption_snapshot.data)
        except ValueError as exc:
            raise _source_invalid("Structured caption source is invalid.", str(exc)) from exc
        if (
            caption_snapshot.data != _canonical_track_bytes(track)
            or not verify_artifact_hash(track)
        ):
            raise _source_invalid("Structured caption content hash is invalid.")
        caption_relative = Path("assets") / f"{digest}.json"
        targets_by_id[caption_id] = _validate_contained_target(
            root, caption_relative, before_creation=True
        )
        style_identity = {
            (item.style_reference_id, item.style_content_hash) for item in cues
        }
        if len(style_identity) != 1:
            raise _source_invalid("Caption cues contain conflicting style identity.")
        style_id, style_hash = next(iter(style_identity))
        if style_id is None or style_hash is None:
            raise _source_invalid("Bound captions require an exact style reference.")
        try:
            validate_caption_track_timeline_binding(
                track,
                caption_asset_sha256=digest,
                cues=cues,
                audio_spans=timeline.audio_spans,
                sample_rate_hz=timeline.sample_rate,
                fps=timeline.delivery_profile.fps,
                style_reference_id=style_id,
                style_content_hash=style_hash,
            )
        except ValueError as exc:
            raise _source_invalid(
                "Caption cues do not match structured caption truth.", str(exc)
            ) from exc
        style_source = Path(asset_sources[style_id])
        style_snapshot = _read_regular_file_nofollow(
            style_source, contained_by=allowed_asset_root
        )
        if style_source.suffix.lower() != ".json" or style_snapshot.file_sha256 != style_hash:
            raise _source_invalid("Caption style type or hash does not match timeline.")
        try:
            style_value = json.loads(style_snapshot.data)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise _source_invalid("Caption style JSON is invalid.", str(exc)) from exc
        if not isinstance(style_value, dict):
            raise _source_invalid("Caption style JSON must be an object.")
        previous_style = caption_styles.get(style_hash)
        if previous_style is not None and previous_style != style_value:
            raise _source_invalid("Caption style identity has conflicting values.")
        caption_styles[style_hash] = style_value
        style_relative = Path("assets") / f"{style_hash}.json"
        targets_by_id[style_id] = _validate_contained_target(
            root, style_relative, before_creation=True
        )
        caption_bindings_list.append(
            RendererCaptionBinding(
                caption_track_id=track.caption_track_id,
                caption_asset_sha256=digest,
                materialized_path=caption_relative,
                style_reference_id=style_id,
                style_content_hash=style_hash,
                style_materialized_path=style_relative,
                resolved_cue_ids=tuple(item.segment_id for item in cues),
            )
        )
    caption_bindings = tuple(caption_bindings_list)
    source_text = _render_source(
        timeline,
        audio_bindings[0] if audio_bindings else None,
        caption_styles,
    )
    parsed_source = _parse_source_document(source_text)
    for url in parsed_source.all_urls:
        _validate_local_relative_url(url)

    snapshots_by_id: dict[str, NoFollowFile] = {}
    unique_targets: dict[Path, bytes] = {}
    for span in timeline.visual_spans:
        if span.asset_id in snapshots_by_id:
            continue
        source = Path(asset_sources[span.asset_id])
        source_snapshot = _read_regular_file_nofollow(
            source, contained_by=allowed_asset_root
        )
        suffix = _validated_visual_suffix(
            source_snapshot,
            suffix=source.suffix,
            mime_type=span.asset_mime_type,
        )
        if source_snapshot.file_sha256 != span.asset_sha256:
            raise _source_invalid(f"Asset bytes do not match timeline: {span.asset_id}.")
        relative = Path("assets") / f"{span.asset_sha256}{suffix}"
        if relative != span.materialized_path:
            raise _source_invalid("Timeline materialized path is not canonical.")
        target = targets_by_id[span.asset_id]
        existing = unique_targets.get(target)
        if existing is not None and existing != source_snapshot.data:
            raise _source_invalid("Canonical asset target has conflicting bytes.")
        unique_targets[target] = source_snapshot.data
        snapshots_by_id[span.asset_id] = source_snapshot
        targets_by_id[span.asset_id] = target

    for source_id in sorted(expected_ids - visual_ids - audio_ids):
        source = Path(asset_sources[source_id])
        source_snapshot = _read_regular_file_nofollow(
            source, contained_by=allowed_asset_root
        )
        target = targets_by_id[source_id]
        existing = unique_targets.get(target)
        if existing is not None and existing != source_snapshot.data:
            raise _source_invalid("Canonical source target has conflicting bytes.")
        unique_targets[target] = source_snapshot.data
    if mixed_audio_target is not None and mixed_audio_bytes is not None:
        unique_targets[mixed_audio_target] = mixed_audio_bytes

    _create_directory_nofollow(root, contained_by=allowed_staging_parent)
    _create_directory_nofollow(root / "assets", contained_by=root)
    for target, payload in unique_targets.items():
        copied = _create_regular_file_nofollow(
            target, data=payload, contained_by=root
        )
        if copied.file_sha256 != target.stem:
            raise _source_invalid("Copied source hash does not match canonical path.")
    source = source_text.encode("utf-8")
    index_snapshot = _create_regular_file_nofollow(
        index_path, data=source, contained_by=root
    )
    audit_hyperframes_source(
        index_path,
        expected_assets=bindings,
        expected_timeline=timeline,
        expected_audio=audio_bindings,
        expected_captions=caption_bindings,
    )
    bundle_sha256 = _source_bundle_sha256(
        index_path,
        bindings,
        expected_index_sha256=index_snapshot.file_sha256,
        audio_bindings=audio_bindings,
        caption_bindings=caption_bindings,
    )
    return MaterializedHyperFramesSource(
        root=root,
        index_path=index_path,
        source_sha256=index_snapshot.file_sha256,
        bundle_sha256=bundle_sha256,
        asset_bindings=bindings,
        timeline=timeline,
        audio_bindings=audio_bindings,
        caption_bindings=caption_bindings,
    )


def materialize_hyperframes_source(
    timeline: ResolvedTimeline,
    *,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
    staging_root: Path,
    allowed_staging_parent: Path,
) -> MaterializedHyperFramesSource:
    try:
        return _materialize_hyperframes_source(
            timeline,
            asset_sources=asset_sources,
            allowed_asset_root=allowed_asset_root,
            staging_root=staging_root,
            allowed_staging_parent=allowed_staging_parent,
        )
    except AiVideoError as exc:
        if exc.code is ErrorCode.RENDERER_SOURCE_INVALID:
            raise
        raise _source_invalid("HyperFrames source inputs are invalid.", str(exc)) from exc
    except (OSError, UnicodeError, ValueError) as exc:
        raise _source_invalid(
            "HyperFrames source could not be materialized safely.", str(exc)
        ) from exc


@dataclass(frozen=True)
class RendererCommandResult:
    returncode: int
    stdout: str
    stderr: str


class RendererRunner(Protocol):
    def version(self, *, env: dict[str, str]) -> str: ...

    def doctor(self, *, env: dict[str, str]) -> RendererCommandResult: ...

    def run(
        self,
        command: str,
        args: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
    ) -> RendererCommandResult: ...


@dataclass(frozen=True)
class HyperFramesRenderAttempt:
    attempt_id: str
    selection: RendererSelectionReceipt
    timeline: ResolvedTimeline
    asset_sources: Mapping[str, Path]
    allowed_asset_root: Path
    staging_root: Path
    allowed_staging_parent: Path
    output_path: Path
    verification_snapshot_path: Path


@dataclass(frozen=True)
class VerifiedRenderOutput:
    untrusted_staged_path: Path
    verification_snapshot_path: Path
    verified_bytes: bytes
    output_sha256: str
    output_size_bytes: int
    measured: MeasuredRenderMetadata
    decoded_frame_fingerprint: str
    decoded_audio_fingerprint: str | None = None


@dataclass(frozen=True)
class HyperFramesRenderResult:
    materialized: MaterializedHyperFramesSource
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]
    output: VerifiedRenderOutput


@dataclass(frozen=True)
class DurableRenderArtifacts:
    artifacts: tuple[PreparedArtifact, ...]
    next_render_state: RenderStateSnapshotPointer
    state: RenderStateSnapshot


def _validate_render_attempt_paths(
    paths: RenderAttemptPaths,
    *,
    project_root: Path,
    attempt_id: str,
) -> None:
    expected_root = project_root / canonical_render_attempt_root(attempt_id)
    if paths != RenderAttemptPaths(
        attempt_root=expected_root,
        source_root=expected_root / "source",
        staged_output_path=expected_root / "output/render.mp4",
        verification_snapshot_path=expected_root / "verified.mp4",
    ):
        raise _source_invalid("Render attempt paths are not canonical.")


def _failure_phase(exc: BaseException) -> Literal[
    "source", "lint", "check", "render", "verify"
]:
    value = getattr(exc, "phase", "source")
    return value if value in {"source", "lint", "check", "render", "verify"} else "source"


def _render_with_hyperframes(
    *,
    committer: ProductionStateCommitter,
    begin_request: BeginRenderAttemptRequest,
    timeline: ResolvedTimeline,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
    runner_factory: Callable[[], RendererRunner],
    browser_path: Path,
    ip_path: Path,
    expected_version: str,
    dependency_transition_preparer: RenderDependencyTransitionPreparer | None = None,
    probe: Callable[[int], dict] | None = None,
    decoded_frames: Callable[[int], str] | None = None,
    decoded_audio: Callable[[int, int, int], tuple[int, str]] | None = None,
    audio_measurement_method: str = "held-fd ffprobe packets plus pcm_s16le decode",
) -> ProductionManifest:
    manifest, fresh = committer._begin_render_attempt_with_status(begin_request)
    if not fresh:
        return committer._replay_render_attempt(begin_request, manifest)
    try:
        if (
            manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8"}
            and dependency_transition_preparer is None
        ):
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_INVALID,
                "Graph-aware Manifest render requires a dependency transition preparer.",
                retryable=False,
            )
        selection = begin_request.renderer_selection
        paths = committer.render_attempt_paths(selection.attempt_id)
        _validate_render_attempt_paths(
            paths,
            project_root=committer.project_root,
            attempt_id=selection.attempt_id,
        )
        committer._ensure_render_attempt_namespace()
        _create_directory_nofollow(
            paths.attempt_root,
            contained_by=committer.project_root,
            mode=0o700,
        )
        adapter = HyperFramesAdapter(
            runner=runner_factory(),
            expected_version=expected_version,
            browser_path=browser_path,
            ip_path=ip_path,
            probe=probe or probe_clip_fd,
            decoded_frames=decoded_frames or decoded_frame_sha256_fd,
            decoded_audio=decoded_audio or decoded_audio_sha256_fd,
            audio_measurement_method=audio_measurement_method,
        )
        result = adapter.render(
            HyperFramesRenderAttempt(
                attempt_id=selection.attempt_id,
                selection=selection,
                timeline=timeline,
                asset_sources=asset_sources,
                allowed_asset_root=allowed_asset_root,
                staging_root=paths.source_root,
                allowed_staging_parent=paths.attempt_root,
                output_path=paths.staged_output_path,
                verification_snapshot_path=paths.verification_snapshot_path,
            )
        )
        durable = prepare_durable_render_artifacts(
            result,
            timeline=timeline,
            renderer_selection=selection,
            current_project=manifest.active_project,
            current_registry=manifest.active_registry,
        )
    except Exception as exc:
        code = exc.code.value if isinstance(exc, AiVideoError) else ErrorCode.RENDER_FAILED.value
        message = (
            exc.user_message
            if isinstance(exc, AiVideoError)
            else str(exc) or "Render attempt failed."
        )
        failure = RecordRenderFailureRequest(
            attempt_id=begin_request.renderer_selection.attempt_id,
            expected_manifest_revision=manifest.manifest_revision,
            current_project=manifest.active_project,
            current_registry=manifest.active_registry,
            base_render_state=begin_request.base_render_state,
            renderer_selection=begin_request.renderer_selection,
            phase=_failure_phase(exc),
            error_code=code,
            error_message=message,
        )
        try:
            committer.record_render_failure(failure)
        except Exception as state_exc:
            state_exc.add_note(f"Original render failure: {exc}")
            raise state_exc from exc
        raise
    activation = ActivateRenderStateRequest(
        attempt_id=begin_request.renderer_selection.attempt_id,
        expected_manifest_revision=manifest.manifest_revision,
        current_project=manifest.active_project,
        current_registry=manifest.active_registry,
        base_render_state=begin_request.base_render_state,
        renderer_selection=begin_request.renderer_selection,
        artifacts=durable.artifacts,
        next_render_state=durable.next_render_state,
    )
    if manifest.schema_version in {"2.3", "2.4", "2.5", "2.6", "2.7", "2.8"}:
        assert dependency_transition_preparer is not None
        try:
            prepared_activation = dependency_transition_preparer(activation)
            if (
                not isinstance(prepared_activation, ActivateRenderStateRequest)
                or prepared_activation.attempt_id != activation.attempt_id
                or prepared_activation.expected_manifest_revision
                != activation.expected_manifest_revision
                or prepared_activation.current_project != activation.current_project
                or prepared_activation.current_registry != activation.current_registry
                or prepared_activation.base_render_state != activation.base_render_state
                or prepared_activation.renderer_selection != activation.renderer_selection
                or prepared_activation.next_render_state != activation.next_render_state
                or prepared_activation.dependency_graph_transition is None
                or not set(activation.artifacts).issubset(
                    prepared_activation.artifacts
                )
            ):
                raise AiVideoError(
                    ErrorCode.PRODUCTION_STATE_INVALID,
                    "Render dependency transition preparer changed the owned candidate.",
                    retryable=False,
                )
            activation = prepared_activation
        except Exception as exc:
            failure = RecordRenderFailureRequest(
                attempt_id=activation.attempt_id,
                expected_manifest_revision=manifest.manifest_revision,
                current_project=manifest.active_project,
                current_registry=manifest.active_registry,
                base_render_state=activation.base_render_state,
                renderer_selection=activation.renderer_selection,
                phase="verify",
                error_code=(
                    exc.code.value
                    if isinstance(exc, AiVideoError)
                    else ErrorCode.PRODUCTION_STATE_INVALID.value
                ),
                error_message=(
                    exc.user_message if isinstance(exc, AiVideoError) else str(exc)
                ),
            )
            committer.record_render_failure(failure)
            raise
    return committer.activate_render_state(activation)


def _renderer_tool_root(binary_path: Path) -> Path:
    binary = Path(binary_path)
    if not binary.is_absolute() or ".." in binary.parts:
        raise _renderer_unavailable(
            "HyperFrames binary path must be absolute and canonical."
        )
    tool_root = binary.parent.parent.parent
    expected = tool_root / "node_modules/.bin/hyperframes"
    if tool_root == Path(binary.anchor) or binary != expected:
        raise _renderer_unavailable(
            "HyperFrames binary must use <tool-root>/node_modules/.bin/hyperframes."
        )
    return tool_root


def render_with_hyperframes(
    *,
    committer: ProductionStateCommitter,
    begin_request: BeginRenderAttemptRequest,
    timeline: ResolvedTimeline,
    asset_sources: Mapping[str, Path],
    allowed_asset_root: Path,
    binary_path: Path,
    browser_path: Path,
    unshare_path: Path,
    ip_path: Path,
    bash_path: Path,
    ffmpeg_path: Path | None = None,
    ffprobe_path: Path | None = None,
    expected_version: str = "0.7.103",
    dependency_transition_preparer: RenderDependencyTransitionPreparer | None = None,
) -> ProductionManifest:
    """Run the sole production HyperFrames path and durably activate its result."""
    probe = None
    decoded_audio = None
    measurement_method = "held-fd ffprobe packets plus pcm_s16le decode"
    if getattr(timeline, "audio_spans", ()):
        if ffmpeg_path is None or ffprobe_path is None:
            raise _renderer_unavailable(
                "P4 audio render requires explicit ffmpeg and ffprobe paths."
            )
        ffmpeg = _validated_executable(ffmpeg_path, "ffmpeg")
        ffprobe = _validated_executable(ffprobe_path, "ffprobe")
        probe = lambda fd: probe_clip_fd_with_executable(fd, ffprobe)
        decoded_audio = lambda fd, rate, channels: decoded_audio_sha256_fd_with_executable(
            fd, rate, channels, ffmpeg
        )
        measurement_method = (
            "held-fd ffprobe packets plus pcm_s16le decode;"
            f"ffprobe={ffprobe}:{hashlib.sha256(ffprobe.read_bytes()).hexdigest()};"
            f"ffmpeg={ffmpeg}:{hashlib.sha256(ffmpeg.read_bytes()).hexdigest()}"
        )
    return _render_with_hyperframes(
        committer=committer,
        begin_request=begin_request,
        timeline=timeline,
        asset_sources=asset_sources,
        allowed_asset_root=allowed_asset_root,
        runner_factory=lambda: _NetworkIsolatedHyperFramesRunner(
            project_root=_renderer_tool_root(binary_path),
            binary=binary_path,
            browser_path=browser_path,
            unshare_path=unshare_path,
            ip_path=ip_path,
            bash_path=bash_path,
        ),
        browser_path=browser_path,
        ip_path=ip_path,
        expected_version=expected_version,
        dependency_transition_preparer=dependency_transition_preparer,
        probe=probe,
        decoded_audio=decoded_audio,
        audio_measurement_method=measurement_method,
    )


def _sealed_json_bytes(model: object) -> bytes:
    payload = json.dumps(
        model.model_dump(mode="json"),  # type: ignore[attr-defined]
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _prepared(path: Path, payload: bytes) -> PreparedArtifact:
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def prepare_durable_render_artifacts(
    result: HyperFramesRenderResult,
    *,
    timeline: ResolvedTimeline,
    renderer_selection: RendererSelectionReceipt,
    current_project: ProjectSnapshotPointer,
    current_registry: RegistrySnapshotPointer,
) -> DurableRenderArtifacts:
    """Seal the exact render graph without writing durable state."""
    materialized = result.materialized
    if (
        materialized.timeline != timeline
        or renderer_selection.attempt_id == ""
        or renderer_selection.timeline_fingerprint != timeline.composition_fingerprint
        or renderer_selection.current_project != current_project
        or renderer_selection.current_registry != current_registry
    ):
        raise _source_invalid("Durable render provenance does not match the attempt.")

    index_snapshot = _read_regular_file_nofollow(
        materialized.index_path, contained_by=materialized.root
    )
    if index_snapshot.file_sha256 != materialized.source_sha256:
        raise _source_invalid("Durable source index changed after render.")
    source_root = canonical_render_source_root(materialized.bundle_sha256)
    index_path = canonical_render_source_index_path(materialized.bundle_sha256)
    index_pointer = RenderSourceFilePointer(
        path=index_path,
        file_sha256=index_snapshot.file_sha256,
        size_bytes=index_snapshot.size_bytes,
    )

    asset_payloads: dict[Path, bytes] = {}
    asset_pointers: dict[Path, RenderSourceFilePointer] = {}
    durable_bindings: list[RendererAssetBinding] = []
    durable_audio_bindings: list[RendererAudioBinding] = []
    durable_caption_bindings: list[RendererCaptionBinding] = []
    for binding in materialized.asset_bindings:
        snapshot = _read_regular_file_nofollow(
            materialized.root / binding.materialized_path,
            contained_by=materialized.root,
        )
        suffix = _validated_visual_suffix(
            snapshot,
            suffix=binding.materialized_path.suffix,
            mime_type=binding.asset_mime_type,
        )
        if snapshot.file_sha256 != binding.asset_sha256:
            raise _source_invalid("Durable source asset changed after render.")
        durable_path = canonical_render_source_asset_path(
            materialized.bundle_sha256, binding.asset_sha256, suffix
        )
        previous = asset_payloads.get(durable_path)
        if previous is not None and previous != snapshot.data:
            raise _source_invalid("Durable source asset path has conflicting bytes.")
        asset_payloads[durable_path] = snapshot.data
        asset_pointers[durable_path] = RenderSourceFilePointer(
            path=durable_path,
            file_sha256=snapshot.file_sha256,
            size_bytes=snapshot.size_bytes,
        )
        durable_bindings.append(
            binding.model_copy(update={"materialized_path": durable_path})
        )

    def add_nonvisual(path: Path, expected_hash: str) -> Path:
        snapshot = _read_regular_file_nofollow(
            materialized.root / path, contained_by=materialized.root
        )
        if snapshot.file_sha256 != expected_hash:
            raise _source_invalid("Durable P4 source asset changed after render.")
        durable_path = canonical_render_source_asset_path(
            materialized.bundle_sha256, expected_hash, path.suffix
        )
        previous = asset_payloads.get(durable_path)
        if previous is not None and previous != snapshot.data:
            raise _source_invalid("Durable P4 source path has conflicting bytes.")
        asset_payloads[durable_path] = snapshot.data
        asset_pointers[durable_path] = RenderSourceFilePointer(
            path=durable_path,
            file_sha256=snapshot.file_sha256,
            size_bytes=snapshot.size_bytes,
        )
        return durable_path

    for binding in materialized.audio_bindings:
        durable_path = add_nonvisual(
            binding.materialized_path, binding.asset_sha256
        )
        durable_audio_bindings.append(
            binding.model_copy(update={"materialized_path": durable_path})
        )
    for binding in materialized.caption_bindings:
        caption_path = add_nonvisual(
            binding.materialized_path, binding.caption_asset_sha256
        )
        update: dict[str, object] = {"materialized_path": caption_path}
        if binding.style_materialized_path is not None:
            assert binding.style_content_hash is not None
            update["style_materialized_path"] = add_nonvisual(
                binding.style_materialized_path, binding.style_content_hash
            )
        durable_caption_bindings.append(binding.model_copy(update=update))

    source_bundle = RenderSourceBundlePointer(
        root_path=source_root,
        bundle_sha256=materialized.bundle_sha256,
        index=index_pointer,
        assets=tuple(asset_pointers[path] for path in sorted(asset_pointers)),
    )
    provenance = (
        SourceReference(
            kind="derived",
            reference=f"render-attempt:{renderer_selection.attempt_id}",
        ),
    )
    renderer = timeline.renderer
    p4_source_fields: dict[str, object] = {}
    if materialized.audio_bindings or materialized.caption_bindings:
        p4_source_fields = {
            "schema_version": "2.1",
            "audio_bindings": tuple(durable_audio_bindings),
            "caption_bindings": tuple(durable_caption_bindings),
        }
    source_receipt = seal_artifact(
        RendererSourceReceipt(
            artifact_id=f"renderer-source-{renderer_selection.attempt_id}",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=renderer_selection.receipt_id,
            source_provenance=provenance,
            attempt_id=renderer_selection.attempt_id,
            renderer=renderer,
            timeline_fingerprint=timeline.composition_fingerprint,
            source_bundle=source_bundle,
            source_sha256=materialized.source_sha256,
            asset_bindings=tuple(durable_bindings),
            checks=result.checks,
            **p4_source_fields,
        )
    )
    output_path = canonical_render_output_path(result.output.output_sha256)
    p4_render_fields: dict[str, object] = {}
    if timeline.audio_spans:
        p4_render_fields = {
            "schema_version": "2.1",
            "decoded_audio_fingerprint": result.output.decoded_audio_fingerprint,
        }
    render_receipt = seal_artifact(
        RenderReceipt(
            artifact_id=f"render-receipt-{renderer_selection.attempt_id}",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=renderer_selection.receipt_id,
            source_provenance=provenance,
            attempt_id=renderer_selection.attempt_id,
            renderer=renderer,
            timeline_fingerprint=timeline.composition_fingerprint,
            source_sha256=materialized.source_sha256,
            source_bundle_sha256=materialized.bundle_sha256,
            asset_hashes=tuple(item.file_sha256 for item in source_bundle.assets),
            output_path=output_path,
            output_sha256=result.output.output_sha256,
            output_size_bytes=result.output.output_size_bytes,
            measured=result.output.measured,
            decoded_frame_fingerprint=result.output.decoded_frame_fingerprint,
            **p4_render_fields,
        )
    )

    timeline_payload = _sealed_json_bytes(timeline)
    source_payload = _sealed_json_bytes(source_receipt)
    render_payload = _sealed_json_bytes(render_receipt)
    timeline_pointer = RenderArtifactPointer(
        path=canonical_render_timeline_path(timeline.content_hash),
        revision=timeline.revision,
        content_hash=timeline.content_hash,
        file_sha256=hashlib.sha256(timeline_payload).hexdigest(),
    )
    source_pointer = RenderArtifactPointer(
        path=canonical_renderer_source_receipt_path(source_receipt.content_hash),
        revision=source_receipt.revision,
        content_hash=source_receipt.content_hash,
        file_sha256=hashlib.sha256(source_payload).hexdigest(),
    )
    render_pointer = RenderArtifactPointer(
        path=canonical_render_receipt_path(render_receipt.content_hash),
        revision=render_receipt.revision,
        content_hash=render_receipt.content_hash,
        file_sha256=hashlib.sha256(render_payload).hexdigest(),
    )
    state = seal_artifact(
        RenderStateSnapshot(
            artifact_id=f"render-state-{renderer_selection.attempt_id}",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=renderer_selection.receipt_id,
            source_provenance=provenance,
            attempt_id=renderer_selection.attempt_id,
            project=current_project,
            registry=current_registry,
            renderer_selection=renderer_selection,
            renderer=renderer,
            timeline_fingerprint=timeline.composition_fingerprint,
            source_sha256=materialized.source_sha256,
            source_bundle_sha256=materialized.bundle_sha256,
            asset_hashes=tuple(item.file_sha256 for item in source_bundle.assets),
            timeline=timeline_pointer,
            source_bundle=source_bundle,
            source_receipt=source_pointer,
            render_receipt=render_pointer,
            output=RenderOutputPointer(
                path=output_path,
                file_sha256=result.output.output_sha256,
                size_bytes=result.output.output_size_bytes,
            ),
        )
    )
    state_payload = _sealed_json_bytes(state)
    state_pointer = RenderStateSnapshotPointer(
        path=canonical_render_state_path(state.content_hash),
        revision=state.revision,
        content_hash=state.content_hash,
        file_sha256=hashlib.sha256(state_payload).hexdigest(),
    )
    artifacts = [
        _prepared(timeline_pointer.path, timeline_payload),
        _prepared(index_path, index_snapshot.data),
        *(_prepared(path, asset_payloads[path]) for path in sorted(asset_payloads)),
        _prepared(source_pointer.path, source_payload),
        _prepared(render_pointer.path, render_payload),
        _prepared(output_path, result.output.verified_bytes),
        _prepared(state_pointer.path, state_payload),
    ]
    if artifacts[-2].file_sha256 != result.output.output_sha256:
        raise _render_failed("Verified render bytes do not match their held-FD hash.")
    return DurableRenderArtifacts(
        artifacts=tuple(sorted(artifacts, key=lambda item: item.relative_path.as_posix())),
        next_render_state=state_pointer,
        state=state,
    )


OFFLINE_ENV = {
    "CI": "1",
    "HYPERFRAMES_NO_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
    "HYPERFRAMES_NO_UPDATE_CHECK": "1",
    "HYPERFRAMES_NO_AUTO_INSTALL": "1",
}

_HYPERFRAMES_VERSION = "0.7.103"
_HYPERFRAMES_INTEGRITY = (
    "sha512-+E+CXuBiHgd6Rae/BltrErJGr0PtC/AL5uHXm6ZN77ziERtIFJvqaJveWDmJ4PH6UEJ/"
    "lf3Cqxuv8GpATt4Ljw=="
)


def _renderer_unavailable(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.RENDERER_UNAVAILABLE,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _render_failed(message: str, detail: str | None = None) -> RendererAttemptError:
    return RendererAttemptError(
        code=ErrorCode.RENDER_FAILED,
        user_message=message,
        technical_detail=detail,
        retryable=False,
        phase="verify",
    )


def _validated_executable(path: Path, label: str) -> Path:
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise _renderer_unavailable(
            f"Pinned HyperFrames {label} path must be absolute."
        )
    try:
        before = os.lstat(path)
        if stat.S_ISLNK(before.st_mode):
            raise ValueError("symlink executable")
        with _open_regular_file_nofollow(path, contained_by=path.parent) as (
            _descriptor,
            opened,
        ):
            mode = opened.st_mode
    except (OSError, ValueError) as exc:
        raise _renderer_unavailable(
            f"Pinned HyperFrames {label} path is not a regular executable.", str(exc)
        ) from exc
    if mode & 0o111 == 0:
        raise _renderer_unavailable(
            f"Pinned HyperFrames {label} path is not executable."
        )
    return path


def _controlled_env(browser_path: Path, ip_path: Path) -> dict[str, str]:
    browser = _validated_executable(browser_path, "browser")
    ip_binary = _validated_executable(ip_path, "ip")
    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        **OFFLINE_ENV,
        "HYPERFRAMES_BROWSER_PATH": str(browser),
        "P3_IP_PATH": str(ip_binary),
    }


def _require_exact_controlled_env(
    supplied: dict[str, str], expected: dict[str, str]
) -> None:
    if supplied != expected:
        raise _renderer_unavailable("HyperFrames controlled environment was altered.")


def _redact(value: str) -> str:
    return re.sub(
        r"(?i)(authorization|api[_-]?key|token|secret)(\s*[:=]\s*)\S+",
        r"\1\2[REDACTED]",
        value,
    )[-8_192:]


def _bounded_redacted_result(
    completed: subprocess.CompletedProcess[str],
) -> RendererCommandResult:
    return RendererCommandResult(
        returncode=completed.returncode,
        stdout=_redact(completed.stdout or ""),
        stderr=_redact(completed.stderr or ""),
    )


class _NetworkIsolatedHyperFramesRunner:
    """Sole production HyperFrames subprocess boundary."""

    _WRAPPER = '"$P3_IP_PATH" link set lo up; exec "$@"'

    def __init__(
        self,
        *,
        project_root: Path,
        binary: Path,
        browser_path: Path,
        ip_path: Path,
        unshare_path: Path,
        bash_path: Path,
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._browser = _validated_executable(browser_path, "browser")
        self._ip = _validated_executable(ip_path, "ip")
        self._unshare = _validated_executable(unshare_path, "unshare")
        self._bash = _validated_executable(bash_path, "bash")
        self._binary = self._validate_lock_owned_binary(binary)
        self._env = _controlled_env(self._browser, self._ip)
        self._probe_namespace()

    def _validate_lock_owned_binary(self, binary: Path) -> Path:
        expected_link = self._project_root / "node_modules/.bin/hyperframes"
        if Path(binary) != expected_link:
            raise _renderer_unavailable(
                "HyperFrames binary is not the project-local lock binary."
            )
        try:
            link = os.lstat(expected_link)
            if not stat.S_ISLNK(link.st_mode):
                raise ValueError("package .bin entry is not a symlink")
            target = expected_link.resolve(strict=True)
            expected_target = (
                self._project_root / "node_modules/hyperframes/bin/hyperframes.mjs"
            )
            if target != expected_target:
                raise ValueError("package .bin target is not lock-owned")
            _validated_executable(target, "binary")
            package = json.loads(
                _read_regular_file_nofollow(
                    self._project_root / "node_modules/hyperframes/package.json",
                    contained_by=self._project_root,
                ).data
            )
            lock = json.loads(
                _read_regular_file_nofollow(
                    self._project_root / "package-lock.json",
                    contained_by=self._project_root,
                ).data
            )
            lock_package = lock["packages"]["node_modules/hyperframes"]
            if package["version"] != _HYPERFRAMES_VERSION:
                raise ValueError("package version mismatch")
            if lock_package["version"] != _HYPERFRAMES_VERSION:
                raise ValueError("lock version mismatch")
            if lock_package["integrity"] != _HYPERFRAMES_INTEGRITY:
                raise ValueError("lock integrity mismatch")
        except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise _renderer_unavailable(
                "HyperFrames package lock validation failed.", str(exc)
            ) from exc
        return expected_link

    def _namespace_argv(self, *renderer_argv: str) -> list[str]:
        if renderer_argv and renderer_argv[0] not in {"--version", "--help"}:
            if "--json" not in renderer_argv:
                raise ValueError(
                    "Every non-version/help HyperFrames command requires --json."
                )
        return [
            str(self._unshare),
            "--user",
            "--map-root-user",
            "--net",
            "--pid",
            "--fork",
            "--mount-proc",
            str(self._bash),
            "-ceu",
            self._WRAPPER,
            "p3-hyperframes",
            str(self._binary),
            *renderer_argv,
        ]

    def _probe_namespace(self) -> None:
        argv = [
            str(self._unshare),
            "--user",
            "--map-root-user",
            "--net",
            "--pid",
            "--fork",
            "--mount-proc",
            str(self._bash),
            "-ceu",
            '"$P3_IP_PATH" link set lo up',
            "p3-hyperframes-probe",
        ]
        try:
            completed = subprocess.run(
                argv,
                cwd=self._project_root,
                env=dict(self._env),
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                check=False,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise _renderer_unavailable(
                "HyperFrames user/network/PID namespace is unavailable.",
                _redact(str(exc)),
            ) from exc
        if completed.returncode != 0:
            raise _renderer_unavailable(
                "HyperFrames user/network/PID namespace is unavailable.",
                _redact(completed.stderr or completed.stdout),
            )

    def _invoke(
        self, *renderer_argv: str, timeout_seconds: int
    ) -> RendererCommandResult:
        try:
            completed = subprocess.run(
                self._namespace_argv(*renderer_argv),
                cwd=self._project_root,
                env=dict(self._env),
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                check=False,
                text=True,
                timeout=timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            command = renderer_argv[0] if renderer_argv else "renderer"
            if command in {"--version", "doctor"}:
                raise _renderer_unavailable(
                    "HyperFrames isolated runtime is unavailable.", _redact(str(exc))
                ) from exc
            phase = cast(Literal["lint", "check", "render"], command)
            raise RendererAttemptError(
                code=(
                    ErrorCode.RENDERER_SOURCE_INVALID
                    if phase in {"lint", "check"}
                    else ErrorCode.RENDER_FAILED
                ),
                user_message=f"HyperFrames {phase} timed out.",
                technical_detail=_redact(str(exc)),
                retryable=False,
                phase=phase,
            ) from exc
        return _bounded_redacted_result(completed)

    def version(self, *, env: dict[str, str]) -> str:
        _require_exact_controlled_env(env, self._env)
        result = self._invoke("--version", timeout_seconds=30)
        if result.returncode != 0:
            raise _renderer_unavailable(
                "HyperFrames version check failed.", result.stderr
            )
        match = re.fullmatch(r"(?:hyperframes\s+)?(\d+\.\d+\.\d+)\s*", result.stdout)
        if match is None:
            raise _renderer_unavailable("HyperFrames version output is malformed.")
        return match.group(1)

    def doctor(self, *, env: dict[str, str]) -> RendererCommandResult:
        _require_exact_controlled_env(env, self._env)
        return self._invoke("doctor", "--json", timeout_seconds=120)

    def run(
        self,
        command: str,
        args: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
    ) -> RendererCommandResult:
        if command not in {"lint", "check", "render"}:
            raise _renderer_unavailable("Unapproved HyperFrames command was requested.")
        _require_exact_controlled_env(env, self._env)
        expected_prefix = str(Path(cwd))
        if command in {"lint", "check"}:
            valid_args = args == (expected_prefix, "--json")
        else:
            valid_args = (
                len(args) == 4
                and args[0] == expected_prefix
                and args[1] == "-o"
                and Path(args[2]).is_absolute()
                and args[3] == "--json"
            )
        if not valid_args:
            raise _renderer_unavailable(
                "HyperFrames command arguments are not approved."
            )
        if Path(cwd) != Path(args[0]):
            raise _renderer_unavailable(
                "HyperFrames command cwd must equal its source root."
            )
        return self._invoke(command, *args, timeout_seconds=timeout_seconds)


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _phase_source_invalid(
    phase: Literal["lint", "check"], message: str, detail: str | None = None
) -> RendererAttemptError:
    return RendererAttemptError(
        code=ErrorCode.RENDERER_SOURCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
        phase=phase,
    )


def _render_error(
    phase: Literal["lint", "check", "render"], result: RendererCommandResult
) -> RendererAttemptError:
    return RendererAttemptError(
        code=(
            ErrorCode.RENDERER_SOURCE_INVALID
            if phase in {"lint", "check"}
            else ErrorCode.RENDER_FAILED
        ),
        user_message=f"HyperFrames {phase} failed.",
        technical_detail=_redact(result.stderr or result.stdout),
        retryable=False,
        phase=phase,
    )


def _verify_failed(exc: Exception) -> RendererAttemptError:
    return RendererAttemptError(
        code=ErrorCode.RENDER_FAILED,
        user_message="Rendered output could not be verified.",
        technical_detail=_redact(str(exc)),
        retryable=False,
        phase="verify",
    )


def _exact_json_count(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative JSON integer")
    return value


def _verify_materialized_unchanged(value: MaterializedHyperFramesSource) -> None:
    snapshot = _read_regular_file_nofollow(value.index_path, contained_by=value.root)
    if snapshot.file_sha256 != value.source_sha256:
        raise _source_invalid("HyperFrames source changed after hashing.")
    audit_hyperframes_source(
        value.index_path,
        expected_assets=value.asset_bindings,
        expected_timeline=value.timeline,
        expected_audio=value.audio_bindings,
        expected_captions=value.caption_bindings,
    )
    if (
        _source_bundle_sha256(
            value.index_path,
            value.asset_bindings,
            expected_index_sha256=value.source_sha256,
            audio_bindings=value.audio_bindings,
            caption_bindings=value.caption_bindings,
        )
        != value.bundle_sha256
    ):
        raise _source_invalid("HyperFrames source bundle changed after hashing.")


def _read_all_from_held_fd(held_fd: int) -> bytes:
    os.lseek(held_fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while chunk := os.read(held_fd, 1024 * 1024):
        chunks.append(chunk)
    os.lseek(held_fd, 0, os.SEEK_SET)
    return b"".join(chunks)


@contextmanager
def _dup_held_fd_at_start(held_fd: int) -> Iterator[int]:
    duplicate = os.dup(held_fd)
    try:
        os.lseek(duplicate, 0, os.SEEK_SET)
        yield duplicate
    finally:
        os.close(duplicate)


def _require_same_regular_file(before: os.stat_result, after: os.stat_result) -> None:
    if not stat.S_ISREG(before.st_mode) or not stat.S_ISREG(after.st_mode):
        raise _render_failed("Output evidence is not a regular file.")
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ):
        raise _render_failed("Output identity changed during verification.")


def probe_clip_fd(held_fd: int) -> dict:
    return probe_clip_fd_with_executable(held_fd, Path("ffprobe"))


def probe_clip_fd_with_executable(held_fd: int, executable: Path) -> dict:
    with _dup_held_fd_at_start(held_fd) as probe_fd:
        result = subprocess.run(
            [
                str(executable),
                "-v",
                "error",
                "-show_streams",
                "-show_packets",
                "-show_format",
                "-of",
                "json",
                f"/proc/self/fd/{probe_fd}",
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(probe_fd,),
            check=False,
            text=True,
            timeout=120,
        )
    if result.returncode != 0:
        raise _render_failed("ffprobe failed.", _redact(result.stderr))
    return json.loads(result.stdout)


def decoded_frame_sha256_fd(held_fd: int) -> str:
    with _dup_held_fd_at_start(held_fd) as frame_fd:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                f"/proc/self/fd/{frame_fd}",
                "-map",
                "0:v:0",
                "-f",
                "framemd5",
                "-",
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(frame_fd,),
            check=False,
            text=True,
            timeout=1800,
        )
    if result.returncode != 0:
        raise _render_failed("framemd5 failed.", _redact(result.stderr))
    rows = [
        line.strip()
        for line in result.stdout.replace("\r\n", "\n").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not rows:
        raise _render_failed("Could not derive decoded frame evidence.")
    return _text_sha256("\n".join(rows) + "\n")


def decoded_audio_sha256_fd(
    held_fd: int, sample_rate: int, channels: int
) -> tuple[int, str]:
    return decoded_audio_sha256_fd_with_executable(
        held_fd, sample_rate, channels, Path("ffmpeg")
    )


def decoded_audio_sha256_fd_with_executable(
    held_fd: int, sample_rate: int, channels: int, executable: Path
) -> tuple[int, str]:
    with _dup_held_fd_at_start(held_fd) as audio_fd:
        result = subprocess.run(
            [
                str(executable),
                "-v",
                "error",
                "-i",
                f"/proc/self/fd/{audio_fd}",
                "-map",
                "0:a:0",
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(sample_rate),
                "-ac",
                str(channels),
                "-f",
                "s16le",
                "-",
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(audio_fd,),
            check=False,
            timeout=1800,
        )
    if result.returncode != 0:
        raise _render_failed("PCM audio decode failed.", _redact(result.stderr.decode(errors="replace")))
    frame_size = channels * 2
    if not result.stdout or len(result.stdout) % frame_size:
        raise _render_failed("Decoded PCM audio has an invalid sample count.")
    return len(result.stdout) // frame_size, hashlib.sha256(result.stdout).hexdigest()


def _json_int(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    parsed = int(str(value))
    if parsed < 0:
        raise ValueError(f"{label} must be non-negative")
    return parsed


def _measured_metadata(
    probe: dict,
    *,
    decoded_audio_samples: int | None = None,
    audio_measurement_method: str = "held-fd ffprobe packets plus pcm_s16le decode",
) -> MeasuredRenderMetadata:
    try:
        all_streams = probe["streams"]
        if not isinstance(all_streams, list):
            raise TypeError("streams must be a list")
        video = [item for item in all_streams if item.get("codec_type") == "video"]
        audio = [item for item in all_streams if item.get("codec_type") == "audio"]
        if len(video) != 1 or len(audio) > 1:
            raise ValueError("render must contain one video and at most one audio stream")
        stream = video[0]
        fps_num_text, fps_den_text = str(stream["r_frame_rate"]).split("/", 1)
        measured_audio = None
        if audio:
            if decoded_audio_samples is None:
                raise ValueError("decoded audio evidence is required")
            audio_stream = audio[0]
            packets = probe.get("packets")
            if not isinstance(packets, list):
                raise TypeError("audio packets must be a list")
            audio_packets = [
                item
                for item in packets
                if _json_int(item.get("stream_index"), "stream_index")
                == _json_int(audio_stream["index"], "audio index")
            ]
            if not audio_packets:
                raise ValueError("audio packet evidence is required")
            side_data = audio_packets[0].get("side_data_list", ())
            if not isinstance(side_data, list):
                raise TypeError("audio side data must be a list")
            skip = [
                item
                for item in side_data
                if isinstance(item, dict)
                and item.get("side_data_type") == "Skip Samples"
            ]
            if len(skip) != 1:
                raise ValueError("exact AAC priming evidence is required")
            priming = _json_int(skip[0].get("skip_samples"), "skip_samples")
            last_duration = _json_int(audio_packets[-1]["duration"], "last duration")
            if last_duration > 1024:
                raise ValueError("AAC packet duration exceeds the locked frame size")
            padding = 1024 - last_duration
            measured_audio = MeasuredAudioRenderMetadata(
                stream_count=1,
                codec_name=str(audio_stream["codec_name"]),
                sample_rate_hz=_json_int(audio_stream["sample_rate"], "sample_rate"),
                channels=_json_int(audio_stream["channels"], "channels"),
                channel_layout=AudioChannelLayout(str(audio_stream["channel_layout"])),
                decoded_samples=decoded_audio_samples,
                encoder_priming_samples=priming,
                encoder_padding_samples=padding,
                measurement_method=audio_measurement_method,
            )
        return MeasuredRenderMetadata(
            width=_exact_json_count(stream["width"], "width"),
            height=_exact_json_count(stream["height"], "height"),
            fps_num=int(fps_num_text),
            fps_den=int(fps_den_text),
            duration_frames=int(stream["nb_frames"]),
            codec_name=str(stream["codec_name"]),
            audio=measured_audio,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise _render_failed(
            "Render metadata is incomplete or invalid.", str(exc)
        ) from exc


def _validate_measured_timeline(
    measured: MeasuredRenderMetadata, timeline: ResolvedTimeline
) -> None:
    profile = timeline.delivery_profile
    if (measured.width, measured.height) != (profile.width, profile.height):
        raise _render_failed("Render dimensions do not match ResolvedTimeline.")
    if measured.fps_num != profile.fps * measured.fps_den:
        raise _render_failed("Render FPS does not match ResolvedTimeline.")
    if measured.duration_frames != timeline.total_frames:
        raise _render_failed("Render frame count does not match ResolvedTimeline.")
    if not timeline.audio_spans:
        if measured.audio is not None:
            raise _render_failed("Silent ResolvedTimeline produced unexpected audio.")
        return
    audio = measured.audio
    if audio is None:
        raise _render_failed("Audio ResolvedTimeline produced no audio stream.")
    if (
        audio.codec_name != "aac"
        or audio.sample_rate_hz != timeline.sample_rate
        or audio.channels != 2
        or audio.channel_layout is not AudioChannelLayout.STEREO
        or audio.encoder_priming_samples != 1024
        or audio.decoded_samples != timeline.total_samples + audio.encoder_padding_samples
    ):
        raise _render_failed("Measured audio does not match ResolvedTimeline delivery contract.")


class HyperFramesAdapter:
    def __init__(
        self,
        runner: RendererRunner,
        expected_version: str,
        *,
        probe: Callable[[int], dict] = probe_clip_fd,
        decoded_frames: Callable[[int], str] = decoded_frame_sha256_fd,
        decoded_audio: Callable[
            [int, int, int], tuple[int, str]
        ] = decoded_audio_sha256_fd,
        audio_measurement_method: str = "held-fd ffprobe packets plus pcm_s16le decode",
        browser_path: Path,
        ip_path: Path,
    ) -> None:
        if expected_version != _HYPERFRAMES_VERSION:
            raise _renderer_unavailable(
                "HyperFrames adapter version must match the exact project pin."
            )
        self._runner = runner
        self._expected_version = expected_version
        self._probe = probe
        self._decoded_frames = decoded_frames
        self._decoded_audio = decoded_audio
        self._audio_measurement_method = audio_measurement_method
        self._env = _controlled_env(browser_path, ip_path)

    def _check(
        self, command: Literal["lint", "check"], root: Path
    ) -> RendererCheckReceipt:
        result = self._runner.run(
            command,
            (str(root), "--json"),
            cwd=root,
            env=dict(self._env),
            timeout_seconds=120,
        )
        if result.returncode != 0:
            raise _render_error(command, result)
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, dict):
                raise TypeError("root must be an object")
            if command == "lint":
                error_count = _exact_json_count(payload["errorCount"], "errorCount")
                warning_count = _exact_json_count(
                    payload["warningCount"], "warningCount"
                )
            else:
                if payload.get("ok") is not True:
                    raise ValueError("HyperFrames check did not report ok=true")
                sections = ("lint", "runtime", "layout", "motion", "contrast")
                error_count = sum(
                    _exact_json_count(payload[name]["errorCount"], "errorCount")
                    for name in sections
                )
                warning_count = sum(
                    _exact_json_count(payload[name]["warningCount"], "warningCount")
                    for name in sections
                )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise _phase_source_invalid(
                command, f"Malformed HyperFrames {command} JSON.", str(exc)
            ) from exc
        if error_count:
            raise _phase_source_invalid(
                command, f"HyperFrames {command} reported {error_count} error(s)."
            )
        return RendererCheckReceipt(
            command=command,
            tool_version=self._expected_version,
            exit_code=result.returncode,
            stdout_sha256=_text_sha256(result.stdout),
            stderr_sha256=_text_sha256(_redact(result.stderr)),
            error_count=error_count,
            warning_count=warning_count,
        )

    def _validate_attempt(self, attempt: HyperFramesRenderAttempt) -> tuple[Path, Path]:
        if attempt.selection.selected_kinds != (RendererKind.HYPERFRAMES,):
            raise _renderer_unavailable(
                "P3 render attempt must select only hyperframes."
            )
        if attempt.timeline.renderer.kind is not RendererKind.HYPERFRAMES:
            raise _renderer_unavailable("ResolvedTimeline does not select hyperframes.")
        if (
            attempt.attempt_id != attempt.selection.attempt_id
            or attempt.selection.renderer_version != self._expected_version
            or attempt.timeline.renderer.version != self._expected_version
            or attempt.selection.timeline_fingerprint
            != attempt.timeline.composition_fingerprint
        ):
            raise _renderer_unavailable(
                "HyperFrames render attempt identity is inconsistent."
            )
        _validate_directory_nofollow(
            attempt.allowed_staging_parent,
            contained_by=attempt.allowed_staging_parent.parent,
            expected_mode=0o700,
        )
        staged = _validate_new_contained_output(
            attempt.output_path,
            allowed_parent=attempt.allowed_staging_parent,
            suffix=".mp4",
        )
        verification = _validate_new_contained_output(
            attempt.verification_snapshot_path,
            allowed_parent=attempt.allowed_staging_parent,
            suffix=".mp4",
        )
        if verification.parent != attempt.allowed_staging_parent:
            raise ValueError(
                "Verification snapshot must be directly inside the attempt directory."
            )
        return staged, verification

    def render(self, attempt: HyperFramesRenderAttempt) -> HyperFramesRenderResult:
        try:
            staged_output, verification_snapshot = self._validate_attempt(attempt)
        except AiVideoError:
            raise
        except (OSError, ValueError) as exc:
            raise _verify_failed(exc) from exc
        if self._runner.version(env=dict(self._env)) != self._expected_version:
            raise _renderer_unavailable(
                "Installed HyperFrames version does not match the pin."
            )
        doctor = self._runner.doctor(env=dict(self._env))
        if doctor.returncode != 0:
            raise _renderer_unavailable(
                "HyperFrames doctor exited nonzero.", _redact(doctor.stderr)
            )
        try:
            payload = json.loads(doctor.stdout)
            checks = payload["checks"]
            if not isinstance(checks, list):
                raise TypeError("checks must be a list")
            for name in ("Node.js", "FFmpeg", "FFprobe", "Chrome"):
                matches = [
                    item
                    for item in checks
                    if isinstance(item, dict) and item.get("name") == name
                ]
                if len(matches) != 1 or matches[0].get("ok") is not True:
                    raise ValueError(f"required doctor check failed: {name}")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise _renderer_unavailable(
                "HyperFrames doctor JSON did not accept the pinned runtime.", str(exc)
            ) from exc
        materialized = materialize_hyperframes_source(
            attempt.timeline,
            asset_sources=attempt.asset_sources,
            allowed_asset_root=attempt.allowed_asset_root,
            staging_root=attempt.staging_root,
            allowed_staging_parent=attempt.allowed_staging_parent,
        )
        lint = self._check("lint", materialized.root)
        _verify_materialized_unchanged(materialized)
        check = self._check("check", materialized.root)
        _verify_materialized_unchanged(materialized)
        try:
            _create_directory_nofollow(
                staged_output.parent, contained_by=attempt.allowed_staging_parent
            )
        except (OSError, ValueError) as exc:
            raise _verify_failed(exc) from exc
        rendered = self._runner.run(
            "render",
            (str(materialized.root), "-o", str(staged_output), "--json"),
            cwd=materialized.root,
            env=dict(self._env),
            timeout_seconds=1800,
        )
        if rendered.returncode != 0:
            raise _render_error("render", rendered)
        try:
            with _open_regular_file_nofollow(
                staged_output, contained_by=attempt.allowed_staging_parent
            ) as (staged_fd, staged_before):
                if staged_before.st_size == 0:
                    raise _render_failed("HyperFrames output is missing or empty.")
                with _copy_held_fd_to_regular_file_nofollow(
                    staged_fd,
                    verification_snapshot,
                    contained_by=attempt.allowed_staging_parent,
                    mode=0o600,
                ) as verification:
                    _require_same_regular_file(staged_before, os.fstat(staged_fd))
                    _verify_materialized_unchanged(materialized)
                    fd = verification.fd
                    before = verification.created_stat
                    _require_same_regular_file(before, os.fstat(fd))
                    verified_bytes = _read_all_from_held_fd(fd)
                    if len(verified_bytes) != before.st_size:
                        raise _render_failed(
                            "Verification snapshot size does not match held bytes."
                        )
                    output_sha256 = hashlib.sha256(verified_bytes).hexdigest()
                    probe = self._probe(fd)
                    decoded_audio_fingerprint = None
                    decoded_audio_samples = None
                    streams = probe.get("streams") if isinstance(probe, dict) else None
                    if isinstance(streams, list) and any(
                        item.get("codec_type") == "audio"
                        for item in streams
                        if isinstance(item, dict)
                    ):
                        decoded_audio_samples, decoded_audio_fingerprint = (
                            self._decoded_audio(fd, attempt.timeline.sample_rate, 2)
                        )
                    measured = _measured_metadata(
                        probe,
                        decoded_audio_samples=decoded_audio_samples,
                        audio_measurement_method=self._audio_measurement_method,
                    )
                    _validate_measured_timeline(measured, attempt.timeline)
                    decoded = self._decoded_frames(fd)
                    durable_bytes = _read_all_from_held_fd(fd)
                    if durable_bytes != verified_bytes:
                        raise _render_failed(
                            "Verification snapshot bytes changed while held open."
                        )
                    _require_same_regular_file(before, os.fstat(fd))
                    return HyperFramesRenderResult(
                        materialized=materialized,
                        checks=(lint, check),
                        output=VerifiedRenderOutput(
                            untrusted_staged_path=staged_output,
                            verification_snapshot_path=verification_snapshot,
                            verified_bytes=durable_bytes,
                            output_sha256=output_sha256,
                            output_size_bytes=len(durable_bytes),
                            measured=measured,
                            decoded_frame_fingerprint=decoded,
                            decoded_audio_fingerprint=decoded_audio_fingerprint,
                        ),
                    )
        except Exception as exc:
            raise _verify_failed(exc) from exc
