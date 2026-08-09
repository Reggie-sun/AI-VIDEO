from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition import (
    _validated_raster_suffix,
    timeline_fingerprint,
)
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    FixedTransform,
    RendererAssetBinding,
    ResolvedTimeline,
    ResolvedVisualSpan,
)
from ai_video.production.paths import (
    NoFollowFile,
    _create_directory_nofollow,
    _create_regular_file_nofollow,
    _list_regular_files_nofollow,
    _read_regular_file_nofollow,
    _validate_contained_target,
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


def _source_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.RENDERER_SOURCE_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
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
