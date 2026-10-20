"""Deterministic ASS authoring and local libass glyph rasterization.

The caller owns subtitle timing and the returned state-to-frame windows. This
module only turns a cue design into a transparent, full-frame PNG image.
"""
from __future__ import annotations

import base64
import binascii
import ctypes
import ctypes.util
import importlib.metadata
import struct
import unicodedata
import zlib
from collections.abc import Mapping
from functools import lru_cache
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_video.production.text_fonts import EmbeddedFont as EmbeddedSubtitleFont


_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?$"
_MAX_TEXT_CHARS = 16_384
_MAX_LINES = 16
_MAX_WORD_STATES = 256
_MAX_RENDER_SIDE = 8_192
_MAX_RENDER_PIXELS = 12_000_000
_MAX_FONT_BYTES_TOTAL = 64 * 1024 * 1024
_MAX_PNG_BYTES = 64 * 1024 * 1024
_SYNTHETIC_EVENT_END_MS = 10


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, revalidate_instances="always")


class SubtitleLineStyle(_StrictFrozenModel):
    """Optional typography overrides for one explicitly authored text line."""

    line_index: int = Field(strict=True, ge=0, lt=_MAX_LINES)
    font_family: str | None = Field(default=None, min_length=1, max_length=100)
    font_size_px: int | None = Field(default=None, strict=True, ge=1, le=1_024)
    primary_color: str | None = Field(default=None, pattern=_COLOR_PATTERN)
    outline_color: str | None = Field(default=None, pattern=_COLOR_PATTERN)
    outline_px: float | None = Field(default=None, strict=True, ge=0, le=64)
    shadow_color: str | None = Field(default=None, pattern=_COLOR_PATTERN)
    shadow_px: float | None = Field(default=None, strict=True, ge=0, le=64)
    bold: bool | None = None
    italic: bool | None = None
    letter_spacing_px: float | None = Field(default=None, strict=True, ge=-32, le=64)
    # Retain null fields in early v2 artifacts, but reject ignored per-line
    # layout instructions. Alignment/margins/wrapping belong to the cue.
    alignment: None = None
    margin_left_px: None = None
    margin_right_px: None = None
    margin_vertical_px: None = None
    wrap_width_px: None = None


class SubtitleDesign(_StrictFrozenModel):
    """An open-ended text treatment expressed as renderer-independent intent.

    Colors use CSS-style ``#RRGGBB`` or ``#RRGGBBAA``. Dimensions are in
    PlayRes pixels, and ``alignment`` uses ASS's 1-through-9 keypad positions.
    """

    schema_version: Literal["2"] = "2"
    engine: Literal["libass"] = "libass"
    libass_version: int = Field(strict=True, gt=0)
    fonts: tuple[EmbeddedSubtitleFont, ...] = Field(min_length=1, max_length=8)
    font_family: str = Field(min_length=1, max_length=100)
    font_size_px: int = Field(default=48, strict=True, ge=1, le=1_024)
    primary_color: str = Field(default="#FFFFFF", pattern=_COLOR_PATTERN)
    outline_color: str = Field(default="#090B12", pattern=_COLOR_PATTERN)
    outline_px: float = Field(default=2.0, strict=True, ge=0, le=64)
    shadow_color: str = Field(default="#000000A0", pattern=_COLOR_PATTERN)
    shadow_px: float = Field(default=0.75, strict=True, ge=0, le=64)
    bold: bool = False
    italic: bool = False
    letter_spacing_px: float = Field(default=0.0, strict=True, ge=-32, le=64)
    alignment: int = Field(default=2, strict=True, ge=1, le=9)
    margin_left_px: int = Field(default=64, strict=True, ge=0, le=8_192)
    margin_right_px: int = Field(default=64, strict=True, ge=0, le=8_192)
    margin_vertical_px: int = Field(default=62, strict=True, ge=0, le=8_192)
    wrap_style: int = Field(default=0, strict=True, ge=0, le=3)
    wrap_width_px: int | None = Field(default=None, strict=True, ge=1, le=8_192)
    highlight_color: str = Field(default="#FFE28A", pattern=_COLOR_PATTERN)
    word_highlight: bool = False
    intent: str | None = Field(default=None, min_length=1, max_length=500)
    line_styles: tuple[SubtitleLineStyle, ...] = Field(default=(), max_length=_MAX_LINES)

    @model_validator(mode="after")
    def _validate_font_families_and_lines(self) -> "SubtitleDesign":
        available = {font.family for font in self.fonts}
        if len(available) != len(self.fonts):
            raise ValueError("Subtitle embedded font families must be unique.")
        if self.font_family not in available:
            raise ValueError("Subtitle font_family must name an embedded font.")
        line_indices: set[int] = set()
        for line_style in self.line_styles:
            if line_style.line_index in line_indices:
                raise ValueError("Subtitle line_styles must have unique line_index values.")
            line_indices.add(line_style.line_index)
            if (
                line_style.font_family is not None
                and line_style.font_family not in available
            ):
                raise ValueError("Subtitle line font_family must name an embedded font.")
        if self.intent is not None and not self.intent.strip():
            raise ValueError("Subtitle intent must be non-empty when supplied.")
        return self


class _ASSImage(ctypes.Structure):
    pass


_ASSImagePointer = ctypes.POINTER(_ASSImage)
_ASSImage._fields_ = [
    ("w", ctypes.c_int),
    ("h", ctypes.c_int),
    ("stride", ctypes.c_int),
    ("bitmap", ctypes.POINTER(ctypes.c_ubyte)),
    ("color", ctypes.c_uint32),
    ("dst_x", ctypes.c_int),
    ("dst_y", ctypes.c_int),
    ("next", _ASSImagePointer),
    ("type", ctypes.c_int),
]


_LibassMessageCallback = ctypes.CFUNCTYPE(
    None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p
)


@lru_cache(maxsize=1)
def _load_libass() -> ctypes.CDLL:
    discovered = ctypes.util.find_library("ass")
    candidates = (
        [discovered]
        if discovered
        else ["libass.so.9", "libass.so", "libass.dylib", "libass-9.dll"]
    )
    library: ctypes.CDLL | None = None
    load_error: OSError | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            library = ctypes.CDLL(candidate)
            break
        except OSError as exc:
            load_error = exc
            continue
    if library is None:
        raise ValueError(
            "The native libass runtime is unavailable or has unresolved native dependencies."
        ) from load_error

    library.ass_library_version.argtypes = []
    library.ass_library_version.restype = ctypes.c_int
    library.ass_library_init.argtypes = []
    library.ass_library_init.restype = ctypes.c_void_p
    library.ass_library_done.argtypes = [ctypes.c_void_p]
    library.ass_library_done.restype = None
    library.ass_set_message_cb.argtypes = [
        ctypes.c_void_p,
        _LibassMessageCallback,
        ctypes.c_void_p,
    ]
    library.ass_set_message_cb.restype = None
    library.ass_add_font.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    library.ass_add_font.restype = None
    library.ass_renderer_init.argtypes = [ctypes.c_void_p]
    library.ass_renderer_init.restype = ctypes.c_void_p
    library.ass_renderer_done.argtypes = [ctypes.c_void_p]
    library.ass_renderer_done.restype = None
    library.ass_set_storage_size.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    library.ass_set_storage_size.restype = None
    library.ass_set_frame_size.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    library.ass_set_frame_size.restype = None
    library.ass_set_fonts.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    library.ass_set_fonts.restype = None
    library.ass_free_track.argtypes = [ctypes.c_void_p]
    library.ass_free_track.restype = None
    library.ass_read_memory.argtypes = [
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_char_p,
    ]
    library.ass_read_memory.restype = ctypes.c_void_p
    library.ass_render_frame.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_longlong,
        ctypes.POINTER(ctypes.c_int),
    ]
    library.ass_render_frame.restype = _ASSImagePointer
    return library


def libass_version() -> int:
    """Return the loaded libass ABI/build version, failing if it is unavailable."""

    try:
        version = int(_load_libass().ass_library_version())
    except ValueError:
        raise
    except (AttributeError, OSError) as exc:
        raise ValueError("The native libass runtime is unavailable.") from exc
    if version <= 0:
        raise ValueError("The native libass runtime returned an invalid version.")
    return version


def _require_pysubs2():
    try:
        import pysubs2
        version = importlib.metadata.version("pysubs2")
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        raise ValueError("ASS authoring requires the optional pysubs2 dependency.") from exc
    if version != "1.8.0":
        raise ValueError("ASS authoring requires pinned pysubs2 version 1.8.0.")
    return pysubs2


def _validate_frame(width: int, height: int) -> None:
    if (
        isinstance(width, bool)
        or not isinstance(width, int)
        or isinstance(height, bool)
        or not isinstance(height, int)
        or width < 1
        or height < 1
        or width > _MAX_RENDER_SIDE
        or height > _MAX_RENDER_SIDE
        or width * height > _MAX_RENDER_PIXELS
    ):
        raise ValueError("Subtitle frame dimensions are outside the bounded render size.")


def _coerce_design(style: Mapping[str, object] | SubtitleDesign) -> SubtitleDesign:
    if isinstance(style, SubtitleDesign):
        return SubtitleDesign.model_validate(style)
    if not isinstance(style, Mapping):
        raise ValueError("Subtitle style must be a SubtitleDesign or mapping.")
    values = dict(style)
    # This public renderer accepts JSON-like mappings while the model itself
    # remains strict for callers constructing a design directly.
    for key in ("fonts", "line_styles"):
        if isinstance(values.get(key), list):
            values[key] = tuple(values[key])
    try:
        return SubtitleDesign.model_validate(values)
    except (TypeError, ValueError) as exc:
        raise ValueError("Subtitle design is invalid.") from exc


def _validate_text(text: str, *, allow_whitespace_only: bool = False) -> str:
    if not isinstance(text, str):
        raise ValueError("Subtitle text must be a string.")
    if not text or len(text) > _MAX_TEXT_CHARS:
        raise ValueError("Subtitle text must be non-empty and within the text bound.")
    if "\r" in text:
        raise ValueError("Subtitle text must use LF line breaks without carriage returns.")
    if len(text.split("\n")) > _MAX_LINES:
        raise ValueError("Subtitle text exceeds the authored line bound.")
    if not allow_whitespace_only and not text.strip():
        raise ValueError("Subtitle text must contain visible characters.")
    for character in text:
        category = unicodedata.category(character)
        if (category == "Cc" and character != "\n") or category == "Cs":
            raise ValueError("Subtitle text contains an unsupported control character.")
    return text


def _validate_embedded_coverage(text: str, design: SubtitleDesign) -> None:
    fonts_by_family = {font.family: font for font in design.fonts}
    authored_lines = text.split("\n")
    if len(authored_lines) > _MAX_LINES:
        raise ValueError("Subtitle text exceeds the authored line bound.")
    line_styles = {item.line_index: item for item in design.line_styles}
    if any(index >= len(authored_lines) for index in line_styles):
        raise ValueError("Subtitle line_styles reference a line absent from the cue.")
    total_font_bytes = 0
    for font in design.fonts:
        data = font.font_bytes()
        total_font_bytes += len(data)
    if total_font_bytes > _MAX_FONT_BYTES_TOTAL:
        raise ValueError("Embedded subtitle fonts exceed the bounded total size.")
    for index, line_text in enumerate(authored_lines):
        line_style = line_styles.get(index)
        family = line_style.font_family if line_style and line_style.font_family else design.font_family
        font = fonts_by_family[family]
        # Formatting characters remain literal text; they do not require a glyph.
        glyph_text = "".join(
            character
            for character in line_text
            if unicodedata.category(character) not in {"Cc", "Cf", "Cs"}
        )
        font.require_glyphs(glyph_text)


def _validate_words(
    text: str,
    design: SubtitleDesign,
    word_texts: tuple[str, ...],
    highlight_index: int | None,
) -> None:
    if not isinstance(word_texts, tuple) or len(word_texts) > _MAX_WORD_STATES:
        raise ValueError("Subtitle word_texts must be a bounded tuple.")
    if word_texts:
        if not design.word_highlight:
            raise ValueError("Subtitle word states require word_highlight=true.")
        if any(not isinstance(word, str) or not word for word in word_texts):
            raise ValueError("Subtitle word_texts entries must be non-empty strings.")
        if "".join(word_texts) != text:
            raise ValueError("Subtitle word_texts must exactly concatenate to cue text.")
        for word in word_texts:
            _validate_text(word, allow_whitespace_only=True)
    elif highlight_index is not None:
        raise ValueError("A highlighted subtitle state requires word_texts.")
    if highlight_index is not None and (
        isinstance(highlight_index, bool)
        or not isinstance(highlight_index, int)
        or not 0 <= highlight_index < len(word_texts)
    ):
        raise ValueError("Subtitle highlight_index is outside word_texts.")


def _parse_color(color: str) -> tuple[int, int, int, int]:
    raw = color[1:]
    red, green, blue = (int(raw[index : index + 2], 16) for index in (0, 2, 4))
    alpha = int(raw[6:8], 16) if len(raw) == 8 else 255
    return red, green, blue, alpha


def _pysubs2_color(pysubs2, color: str):
    red, green, blue, alpha = _parse_color(color)
    # pysubs2.Color.a follows ASS's inverted alpha convention.
    return pysubs2.Color(red, green, blue, 255 - alpha)


def _ass_rgb_tag(color: str) -> str:
    red, green, blue, _ = _parse_color(color)
    return f"&H{blue:02X}{green:02X}{red:02X}&"


def _ass_alpha_tag(color: str) -> str:
    _, _, _, alpha = _parse_color(color)
    return f"&H{255 - alpha:02X}&"


def _escape_ass_literal(text: str) -> str:
    # libass does NOT treat \\\\ as one escaped backslash: the second one can
    # still start N/n/h. An invisible WORD JOINER separates the control prefix
    # without changing visible glyphs; braces use libass's explicit escapes.
    return text.replace("\\", "\\\u2060").replace("{", "\\{").replace("}", "\\}")


def _line_values(design: SubtitleDesign, index: int) -> dict[str, object]:
    values: dict[str, object] = {
        "font_family": design.font_family,
        "font_size_px": design.font_size_px,
        "primary_color": design.primary_color,
        "outline_color": design.outline_color,
        "outline_px": design.outline_px,
        "shadow_color": design.shadow_color,
        "shadow_px": design.shadow_px,
        "bold": design.bold,
        "italic": design.italic,
        "letter_spacing_px": design.letter_spacing_px,
        "alignment": design.alignment,
        "margin_left_px": design.margin_left_px,
        "margin_right_px": design.margin_right_px,
        "margin_vertical_px": design.margin_vertical_px,
        "wrap_width_px": design.wrap_width_px,
    }
    line_style = next((item for item in design.line_styles if item.line_index == index), None)
    if line_style is not None:
        values.update(line_style.model_dump(exclude={"line_index"}, exclude_none=True))
    return values


def _fit_line_margins(values: dict[str, object], width: int) -> tuple[int, int]:
    left = int(values["margin_left_px"])
    right = int(values["margin_right_px"])
    requested_width = values["wrap_width_px"]
    if requested_width is None:
        if left + right >= width:
            raise ValueError("Subtitle horizontal margins leave no wrapping width.")
        return left, right
    wrap_width = int(requested_width)
    if left + right >= width or wrap_width > width - left - right:
        raise ValueError("Subtitle wrap_width_px exceeds the available line width.")
    extra = width - left - right - wrap_width
    horizontal_alignment = int(values["alignment"]) % 3
    if horizontal_alignment == 1:
        right += extra
    elif horizontal_alignment == 0:
        left += extra
    else:
        left += extra // 2
        right += extra - extra // 2
    return left, right


def _style_for_line(pysubs2, design: SubtitleDesign, index: int, width: int):
    values = _line_values(design, index)
    left, right = _fit_line_margins(values, width)
    return pysubs2.SSAStyle(
        fontname=str(values["font_family"]),
        fontsize=float(values["font_size_px"]),
        primarycolor=_pysubs2_color(pysubs2, str(values["primary_color"])),
        secondarycolor=_pysubs2_color(pysubs2, design.highlight_color),
        tertiarycolor=_pysubs2_color(pysubs2, str(values["outline_color"])),
        outlinecolor=_pysubs2_color(pysubs2, str(values["outline_color"])),
        backcolor=_pysubs2_color(pysubs2, str(values["shadow_color"])),
        bold=bool(values["bold"]),
        italic=bool(values["italic"]),
        spacing=float(values["letter_spacing_px"]),
        borderstyle=1,
        outline=float(values["outline_px"]),
        shadow=float(values["shadow_px"]),
        alignment=pysubs2.Alignment(int(values["alignment"])),
        marginl=left,
        marginr=right,
        marginv=int(values["margin_vertical_px"]),
        encoding=1,
    )


def _line_style_name(index: int) -> str:
    return "Default" if index == 0 else f"Line{index}"


def _markup_text(
    text: str,
    design: SubtitleDesign,
    *,
    highlight_index: int | None,
    word_texts: tuple[str, ...],
) -> str:
    if not word_texts:
        rendered_lines: list[str] = []
        for index, line in enumerate(text.split("\n")):
            if index:
                rendered_lines.append(r"\N")
            rendered_lines.append("{\\r" + _line_style_name(index) + "}")
            rendered_lines.append(_escape_ass_literal(line))
        return "".join(rendered_lines)

    output = ["{\\rDefault}"]
    line_index = 0
    for word_index, word in enumerate(word_texts):
        fragments = word.split("\n")
        for fragment_index, fragment in enumerate(fragments):
            if fragment:
                if word_index == highlight_index:
                    output.append(
                        "{\\1c"
                        + _ass_rgb_tag(design.highlight_color)
                        + "\\1a"
                        + _ass_alpha_tag(design.highlight_color)
                        + "\\b1}"
                    )
                    output.append(_escape_ass_literal(fragment))
                    output.append("{\\r" + _line_style_name(line_index) + "}")
                else:
                    output.append(_escape_ass_literal(fragment))
            if fragment_index < len(fragments) - 1:
                output.append(r"\N")
                line_index += 1
                output.append("{\\r" + _line_style_name(line_index) + "}")
    return "".join(output)


def _build_ass(
    text: str,
    design: SubtitleDesign,
    width: int,
    height: int,
    *,
    highlight_index: int | None,
    word_texts: tuple[str, ...],
) -> str:
    _validate_frame(width, height)
    text = _validate_text(text)
    _validate_words(text, design, word_texts, highlight_index)
    _validate_embedded_coverage(text, design)
    pysubs2 = _require_pysubs2()

    line_count = len(text.split("\n"))
    subs = pysubs2.SSAFile()
    subs.info.update(
        {
            "ScriptType": "v4.00+",
            "PlayResX": str(width),
            "PlayResY": str(height),
            "WrapStyle": str(design.wrap_style),
            "ScaledBorderAndShadow": "yes",
        }
    )
    subs.styles.clear()
    for index in range(line_count):
        subs.styles[_line_style_name(index)] = _style_for_line(
            pysubs2, design, index, width
        )
    # ASS needs an event window even for a static glyph raster. This fixed
    # ten-millisecond sample interval is private to rasterization; production
    # cue timing is resolved by the parent compiler.
    subs.events.append(
        pysubs2.SSAEvent(
            start=0,
            end=_SYNTHETIC_EVENT_END_MS,
            text=_markup_text(
                text,
                design,
                highlight_index=highlight_index,
                word_texts=word_texts,
            ),
            style="Default",
        )
    )
    return subs.to_string("ass")


def build_ass(
    text: str,
    design: SubtitleDesign,
    width: int,
    height: int,
    *,
    highlight_index: int | None = None,
    word_texts: tuple[str, ...] = (),
) -> str:
    """Compile a validated cue and authored style to an ASS document."""

    if not isinstance(design, SubtitleDesign):
        raise ValueError("build_ass requires a validated SubtitleDesign.")
    design = SubtitleDesign.model_validate(design)
    return _build_ass(
        text,
        design,
        width,
        height,
        highlight_index=highlight_index,
        word_texts=word_texts,
    )


def _render_ass_document(
    library: ctypes.CDLL,
    library_handle: ctypes.c_void_p,
    renderer: ctypes.c_void_p,
    ass_document: str,
    width: int,
    height: int,
) -> bytes:
    encoded = ass_document.encode("utf-8")
    buffer = ctypes.create_string_buffer(encoded)
    track = library.ass_read_memory(
        library_handle, ctypes.cast(buffer, ctypes.c_char_p), len(encoded), None
    )
    if not track:
        raise ValueError("libass could not parse the generated ASS document.")
    try:
        changed = ctypes.c_int(0)
        images = library.ass_render_frame(renderer, track, 0, ctypes.byref(changed))
        frame = np.zeros((height, width, 4), dtype=np.uint8)
        current = images
        image_count = 0
        max_blend = 255 * 255
        rounding = max_blend // 2
        while current:
            image_count += 1
            if image_count > _MAX_TEXT_CHARS:
                raise ValueError("libass returned too many glyph bitmaps.")
            item = current.contents
            current = item.next
            if item.w <= 0 or item.h <= 0:
                continue
            if item.stride < item.w or not item.bitmap:
                raise ValueError("libass returned an invalid glyph bitmap.")
            x0 = max(0, item.dst_x)
            y0 = max(0, item.dst_y)
            x1 = min(width, item.dst_x + item.w)
            y1 = min(height, item.dst_y + item.h)
            if x0 >= x1 or y0 >= y1:
                continue
            raw_size = item.stride * (item.h - 1) + item.w
            raw_source = np.ctypeslib.as_array(item.bitmap, shape=(raw_size,))
            source = np.ndarray(
                shape=(item.h, item.w),
                dtype=np.uint8,
                buffer=raw_source,
                strides=(item.stride, 1),
            )
            source_rows = source[y0 - item.dst_y : y1 - item.dst_y, x0 - item.dst_x : x1 - item.dst_x]
            packed_color = int(item.color)
            red = (packed_color >> 24) & 0xFF
            green = (packed_color >> 16) & 0xFF
            blue = (packed_color >> 8) & 0xFF
            opacity = 255 - (packed_color & 0xFF)
            coverage = source_rows.astype(np.uint32) * opacity
            destination = frame[y0:y1, x0:x1].astype(np.uint32)
            inverse = max_blend - coverage
            for channel, color_channel in enumerate((red, green, blue)):
                destination[..., channel] = (
                    coverage * color_channel
                    + inverse * destination[..., channel]
                    + rounding
                ) // max_blend
            destination[..., 3] = (
                coverage * 255
                + inverse * destination[..., 3]
                + rounding
            ) // max_blend
            frame[y0:y1, x0:x1] = destination.astype(np.uint8)

        alpha = frame[..., 3].astype(np.uint32)
        visible = alpha > 0
        if not bool(np.any(visible)):
            raise ValueError("libass produced no visible glyph pixels for the cue.")
        rgb = frame[..., :3].astype(np.uint32)
        rgb[visible] = (
            rgb[visible] * 255 + alpha[visible, None] // 2
        ) // alpha[visible, None]
        frame[..., :3] = np.minimum(rgb, 255).astype(np.uint8)
        return _encode_png(frame)
    finally:
        library.ass_free_track(track)


def _encode_png(frame: np.ndarray) -> bytes:
    height, width, channels = frame.shape
    if channels != 4:
        raise ValueError("Subtitle raster must use RGBA pixels.")
    raw = b"".join(b"\x00" + frame[row].tobytes() for row in range(height))
    compressed = zlib.compress(raw, level=6)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
    if len(png) > _MAX_PNG_BYTES:
        raise ValueError("Subtitle PNG exceeded the bounded output size.")
    return png


@lru_cache(maxsize=16)
def _render_states(
    design: SubtitleDesign,
    documents: tuple[str, ...],
    width: int,
    height: int,
) -> tuple[str, ...]:
    _validate_frame(width, height)
    if sum(len(font.font_bytes()) for font in design.fonts) > _MAX_FONT_BYTES_TOTAL:
        raise ValueError("Embedded subtitle fonts exceed the bounded total size.")
    native = _load_libass()
    if design.libass_version != libass_version():
        raise ValueError("SubtitleDesign libass_version does not match the loaded runtime.")

    library_handle = native.ass_library_init()
    if not library_handle:
        raise ValueError("libass could not initialize its library context.")
    renderer_handle = None
    callback = _LibassMessageCallback(lambda _level, _format, _args, _data: None)
    try:
        native.ass_set_message_cb(library_handle, callback, None)
        for index, font in enumerate(design.fonts):
            data = font.font_bytes()
            font_name = f"embedded-{index}-{font.sha256}.{'otf' if font.mime == 'font/otf' else 'ttf'}".encode("ascii")
            native.ass_add_font(
                library_handle,
                font_name,
                ctypes.c_char_p(data),
                len(data),
            )
        renderer_handle = native.ass_renderer_init(library_handle)
        if not renderer_handle:
            raise ValueError("libass could not initialize its renderer context.")
        native.ass_set_storage_size(renderer_handle, width, height)
        native.ass_set_frame_size(renderer_handle, width, height)
        default_family = design.font_family.encode("utf-8")
        native.ass_set_fonts(renderer_handle, None, default_family, 0, None, 0)

        results: list[str] = []
        total_output = 0
        for document in documents:
            png = _render_ass_document(
                native, library_handle, renderer_handle, document, width, height
            )
            encoded_png = base64.b64encode(png)
            total_output += len(encoded_png)
            if total_output > _MAX_PNG_BYTES:
                raise ValueError("Subtitle state PNGs exceeded the bounded output size.")
            results.append("data:image/png;base64," + encoded_png.decode("ascii"))
        return tuple(results)
    finally:
        if renderer_handle:
            native.ass_renderer_done(renderer_handle)
        native.ass_library_done(library_handle)


def render_subtitle_states(
    text: str,
    style: Mapping[str, object] | SubtitleDesign,
    *,
    width: int,
    height: int,
    word_texts: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Render one base PNG and one state for each exact cue-word segment."""

    text = _validate_text(text)
    design = _coerce_design(style)
    _validate_frame(width, height)
    _validate_words(text, design, word_texts, None)
    if word_texts and not design.word_highlight:
        raise ValueError("Subtitle word states require word_highlight=true.")
    if len(word_texts) > _MAX_WORD_STATES:
        raise ValueError("Subtitle word_texts exceed the bounded state count.")
    if design.libass_version != libass_version():
        raise ValueError("SubtitleDesign libass_version does not match the loaded runtime.")

    state_indices: tuple[int | None, ...] = (None,) + tuple(range(len(word_texts)))
    documents = tuple(
        _build_ass(
            text,
            design,
            width,
            height,
            highlight_index=highlight_index,
            word_texts=word_texts,
        )
        for highlight_index in state_indices
    )
    return _render_states(design, documents, width, height)
