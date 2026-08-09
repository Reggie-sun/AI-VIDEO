from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterator, Literal, Protocol, cast
from urllib.parse import urlsplit

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import (
    _validated_raster_suffix,
    timeline_fingerprint,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    FixedTransform,
    MeasuredRenderMetadata,
    RendererAssetBinding,
    RendererCheckReceipt,
    RendererKind,
    RendererSelectionReceipt,
    ResolvedTimeline,
    ResolvedVisualSpan,
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
)


_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
_IMPORT_PATTERN = re.compile(
    r"@import\s+(?:url\(\s*)?(['\"]?)([^'\"\s;)]+)\1", re.IGNORECASE
)
_FORBIDDEN_TEXT = (
    "http://",
    "https://",
    "//cdn.",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket(",
    "Math.random(",
    "Date.now(",
    "new Date(",
    "performance.now(",
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
        forbidden_text=any(token.lower() in lowered for token in _FORBIDDEN_TEXT),
    )


def _seconds(frame_count: int, fps: int) -> str:
    value = Decimal(frame_count) / Decimal(fps)
    rendered = format(value.quantize(Decimal("0.000000001")), "f")
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


def _css_transform(transform: FixedTransform) -> str:
    return (
        f"translate({transform.translate_x_px}px,{transform.translate_y_px}px) "
        f"scale({_decimal_milli(transform.scale_x_milli)},"
        f"{_decimal_milli(transform.scale_y_milli)}) "
        f"rotate({_decimal_milli(transform.rotation_millidegrees)}deg)"
    )


def _render_source(timeline: ResolvedTimeline) -> str:
    fps = timeline.delivery_profile.fps
    duration = _seconds(timeline.total_frames, fps)
    clips: list[str] = []
    animations: list[str] = []
    keyframes: list[str] = []
    for span in timeline.visual_spans:
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
                    (
                        f'  <img src="{span.materialized_path.as_posix()}"'
                        f' style="transform:{escape(_css_transform(span.transform))};'
                        'transform-origin:0 0" alt="" />'
                    ),
                    "</div>",
                ]
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
            "    .clip img{width:100%;height:100%;object-fit:cover}",
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


def _source_bundle_sha256(
    index_path: Path,
    bindings: tuple[RendererAssetBinding, ...],
    *,
    expected_index_sha256: str,
) -> str:
    root = index_path.parent
    paths = {Path("index.html"), *(item.materialized_path for item in bindings)}
    if _list_regular_files_nofollow(root) != paths:
        raise _source_invalid("HyperFrames bundle file set changed after audit.")
    expected_hashes = {Path("index.html"): expected_index_sha256}
    for binding in bindings:
        previous = expected_hashes.get(binding.materialized_path)
        if previous is not None and previous != binding.asset_sha256:
            raise _source_invalid("HyperFrames bundle has conflicting asset hashes.")
        expected_hashes[binding.materialized_path] = binding.asset_sha256
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


def _audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
    expected_timeline: ResolvedTimeline,
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
    expected = _parse_source_document(_render_source(expected_timeline))
    if (
        parsed.document_model != expected.document_model
        or parsed.css_model != expected.css_model
        or parsed.stage_attributes != expected.stage_attributes
        or parsed.clip_attributes != expected.clip_attributes
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
    if parsed.media_urls != expected_urls or parsed.all_urls != expected_urls:
        raise _source_invalid("Source URLs do not exactly match declared raster bindings.")
    for url in parsed.all_urls:
        _validate_local_relative_url(url)
    for binding in expected_assets:
        relative = binding.materialized_path
        target = _validate_contained_target(source_root, relative, before_creation=False)
        target_snapshot = _read_regular_file_nofollow(target, contained_by=source_root)
        if target_snapshot.file_sha256 != binding.asset_sha256:
            raise _source_invalid(f"Changed source asset: {binding.asset_id}.")
        _validated_raster_suffix(
            target_snapshot,
            suffix=target.suffix,
            mime_type=binding.asset_mime_type,
        )
    expected_files = {Path("index.html"), *(item.materialized_path for item in expected_assets)}
    if _list_regular_files_nofollow(source_root) != expected_files:
        raise _source_invalid("HyperFrames staging contains an undeclared file.")


def audit_hyperframes_source(
    index_path: Path,
    *,
    expected_assets: tuple[RendererAssetBinding, ...],
    expected_timeline: ResolvedTimeline,
) -> None:
    try:
        _audit_hyperframes_source(
            index_path,
            expected_assets=expected_assets,
            expected_timeline=expected_timeline,
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
    expected_ids = {item.asset_id for item in timeline.visual_spans}
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
    source_text = _render_source(timeline)
    parsed_source = _parse_source_document(source_text)
    for url in parsed_source.all_urls:
        _validate_local_relative_url(url)

    snapshots_by_id: dict[str, NoFollowFile] = {}
    unique_targets: dict[Path, tuple[ResolvedVisualSpan, NoFollowFile]] = {}
    for span in timeline.visual_spans:
        if span.asset_id in snapshots_by_id:
            continue
        source = Path(asset_sources[span.asset_id])
        source_snapshot = _read_regular_file_nofollow(
            source, contained_by=allowed_asset_root
        )
        suffix = _validated_raster_suffix(
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
        if existing is not None and existing[1].data != source_snapshot.data:
            raise _source_invalid("Canonical asset target has conflicting bytes.")
        unique_targets[target] = (span, source_snapshot)
        snapshots_by_id[span.asset_id] = source_snapshot
        targets_by_id[span.asset_id] = target

    _create_directory_nofollow(root, contained_by=allowed_staging_parent)
    _create_directory_nofollow(root / "assets", contained_by=root)
    for target, (span, source_snapshot) in unique_targets.items():
        copied = _create_regular_file_nofollow(
            target, data=source_snapshot.data, contained_by=root
        )
        suffix = _validated_raster_suffix(
            copied, suffix=target.suffix, mime_type=span.asset_mime_type
        )
        if suffix != target.suffix or copied.file_sha256 != span.asset_sha256:
            raise _source_invalid(f"Copied asset hash mismatch: {span.asset_id}.")
    source = source_text.encode("utf-8")
    index_snapshot = _create_regular_file_nofollow(
        index_path, data=source, contained_by=root
    )
    audit_hyperframes_source(
        index_path, expected_assets=bindings, expected_timeline=timeline
    )
    bundle_sha256 = _source_bundle_sha256(
        index_path,
        bindings,
        expected_index_sha256=index_snapshot.file_sha256,
    )
    return MaterializedHyperFramesSource(
        root=root,
        index_path=index_path,
        source_sha256=index_snapshot.file_sha256,
        bundle_sha256=bundle_sha256,
        asset_bindings=bindings,
        timeline=timeline,
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


@dataclass(frozen=True)
class HyperFramesRenderResult:
    materialized: MaterializedHyperFramesSource
    checks: tuple[RendererCheckReceipt, RendererCheckReceipt]
    output: VerifiedRenderOutput


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
    )
    if (
        _source_bundle_sha256(
            value.index_path,
            value.asset_bindings,
            expected_index_sha256=value.source_sha256,
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
    with _dup_held_fd_at_start(held_fd) as probe_fd:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
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


def _measured_metadata(probe: dict) -> MeasuredRenderMetadata:
    try:
        all_streams = probe["streams"]
        if not isinstance(all_streams, list):
            raise TypeError("streams must be a list")
        video = [item for item in all_streams if item.get("codec_type") == "video"]
        audio = [item for item in all_streams if item.get("codec_type") == "audio"]
        if len(video) != 1 or audio:
            raise ValueError(
                "render must contain exactly one video stream and no audio"
            )
        stream = video[0]
        fps_num_text, fps_den_text = str(stream["r_frame_rate"]).split("/", 1)
        return MeasuredRenderMetadata(
            width=_exact_json_count(stream["width"], "width"),
            height=_exact_json_count(stream["height"], "height"),
            fps_num=int(fps_num_text),
            fps_den=int(fps_den_text),
            duration_frames=int(stream["nb_frames"]),
            codec_name=str(stream["codec_name"]),
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


class HyperFramesAdapter:
    def __init__(
        self,
        runner: RendererRunner,
        expected_version: str,
        *,
        probe: Callable[[int], dict] = probe_clip_fd,
        decoded_frames: Callable[[int], str] = decoded_frame_sha256_fd,
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
                    measured = _measured_metadata(self._probe(fd))
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
                        ),
                    )
        except Exception as exc:
            raise _verify_failed(exc) from exc
