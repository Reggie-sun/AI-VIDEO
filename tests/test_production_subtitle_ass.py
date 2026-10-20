from __future__ import annotations

import base64
import ctypes.util
import hashlib
import importlib.metadata
import struct
import zlib
from pathlib import Path

import pytest

from ai_video.production.subtitle_ass import (
    EmbeddedSubtitleFont,
    SubtitleDesign,
    SubtitleLineStyle,
    build_ass,
    libass_version,
    render_subtitle_states,
)


_FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
_LATIN_FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
)


def _font_from_path(path: Path) -> EmbeddedSubtitleFont:
    fonttools = pytest.importorskip("fontTools.ttLib")
    data = path.read_bytes()
    try:
        parsed = fonttools.TTFont(path, lazy=False)
        family = next(
            (
                name.toUnicode()
                for name in parsed["name"].names
                if name.nameID == 1
            ),
            None,
        )
        parsed.close()
    except Exception as exc:
        pytest.skip(f"Installed test font could not be inspected: {type(exc).__name__}.")
    if not family:
        pytest.skip("Installed test font has no family name.")
    return EmbeddedSubtitleFont(
        family=family,
        sha256=hashlib.sha256(data).hexdigest(),
        data_base64=base64.b64encode(data).decode("ascii"),
        license="Installed system font, embedded in this test only.",
    )


def _embedded_font() -> EmbeddedSubtitleFont:
    path = next((candidate for candidate in _FONT_CANDIDATES if candidate.is_file()), None)
    if path is None:
        pytest.skip("No standalone OTF/TTF test font is installed on this host.")
    font = _font_from_path(path)
    try:
        font.require_glyphs("字幕中文")
    except ValueError:
        pytest.skip("Installed standalone test font does not cover CJK.")
    return font


def _latin_font() -> EmbeddedSubtitleFont:
    path = next(
        (candidate for candidate in _LATIN_FONT_CANDIDATES if candidate.is_file()),
        None,
    )
    if path is None:
        pytest.skip("No standalone Latin test font is installed on this host.")
    font = _font_from_path(path)
    font.require_glyphs("Latin {\\pos(1,2)}")
    return font


def _design(font: EmbeddedSubtitleFont, **values: object) -> SubtitleDesign:
    try:
        native_version = libass_version()
    except ValueError as exc:
        pytest.skip(f"Optional native subtitle runtime unavailable: {exc}")
    fields: dict[str, object] = {
        "libass_version": native_version,
        "fonts": (font,),
        "font_family": font.family,
        "font_size_px": 36,
        "margin_left_px": 24,
        "margin_right_px": 24,
        "margin_vertical_px": 18,
    }
    fields.update(values)
    return SubtitleDesign(**fields)


def _require_pysubs2() -> None:
    try:
        version = importlib.metadata.version("pysubs2")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("Optional pysubs2 dependency is not installed.")
    if version != "1.8.0":
        pytest.skip("This test requires the project's pinned pysubs2 1.8.0.")


def _png_rgba(data_uri: str) -> tuple[int, int, bytes]:
    prefix = "data:image/png;base64,"
    assert data_uri.startswith(prefix)
    png = base64.b64decode(data_uri[len(prefix) :], validate=True)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    compressed = bytearray()
    width = height = 0
    while offset < len(png):
        size = struct.unpack_from(">I", png, offset)[0]
        kind = png[offset + 4 : offset + 8]
        chunk = png[offset + 8 : offset + 8 + size]
        if kind == b"IHDR":
            width, height = struct.unpack_from(">II", chunk)
        elif kind == b"IDAT":
            compressed.extend(chunk)
        offset += size + 12
        if kind == b"IEND":
            break
    raw = zlib.decompress(compressed)
    return width, height, raw


def test_font_digest_is_checked_before_ass_authoring() -> None:
    font = _embedded_font()
    with pytest.raises(ValueError, match="SHA-256"):
        EmbeddedSubtitleFont(
            family=font.family,
            sha256="0" * 64,
            data_base64=font.data_base64,
            license=font.license,
        )


def test_design_rejects_non_embedded_family_and_duplicate_line_override() -> None:
    font = _embedded_font()
    with pytest.raises(ValueError, match="embedded font"):
        _design(font, font_family="Unbundled Font")
    with pytest.raises(ValueError, match="extra_forbidden"):
        _design(font, unsupported_template="fixed")
    with pytest.raises(ValueError, match="unique line_index"):
        _design(
            font,
            line_styles=(
                SubtitleLineStyle(line_index=1, font_size_px=30),
                SubtitleLineStyle(line_index=1, primary_color="#FFEE00"),
            ),
        )


def test_missing_glyph_is_rejected_instead_of_using_a_system_fallback() -> None:
    font = _embedded_font()
    design = _design(font)
    with pytest.raises(ValueError, match="lacks required glyphs"):
        build_ass("\U0010ffff", design, 320, 180)


def test_pysubs2_ass_escapes_user_control_sequences_and_keeps_line_style() -> None:
    _require_pysubs2()
    font = _embedded_font()
    latin_font = _latin_font()
    design = _design(
        font,
        fonts=(font, latin_font),
        line_styles=(
            SubtitleLineStyle(
                line_index=1,
                font_family=latin_font.family,
                font_size_px=28,
                primary_color="#FFD580",
            ),
        ),
    )
    document = build_ass("字幕\nLatin {\\pos(1,2)}", design, 640, 360)
    assert "PlayResX: 640" in document
    assert "PlayResY: 360" in document
    assert "Line1" in document
    assert r"{\pos(1,2)}" not in document
    assert "0:00:00.01" in document


@pytest.mark.parametrize("field", ["alignment", "margin_left_px", "margin_right_px", "margin_vertical_px", "wrap_width_px"])
def test_line_positioning_is_rejected_instead_of_ignored(field):
    with pytest.raises(ValueError):
        SubtitleLineStyle(line_index=1, **{field:8})


@pytest.mark.parametrize("literal,reference", [
    (r"\N", "N\\"), (r"\n", "n\\"), (r"\h", "h\\"),
    (r"\\", r"\\"), (r"{\pos(1,2)}", "\\{pos(1,2)\\}\\"),
])
def test_literal_controls_preserve_actual_glyphs(literal, reference):
    import numpy as np
    _require_pysubs2()
    import pysubs2
    from ai_video.production.subtitle_ass import _render_states

    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    if not path.exists():
        pytest.skip("monospace reference font unavailable")
    d = _design(_font_from_path(path), alignment=7, outline_px=0.0, shadow_px=0.0)
    actual = render_subtitle_states(literal,d,width=640,height=180)[0]
    # Independent raw ASS reference: same glyph multiset, reordered so the
    # backslash is last and cannot introduce an ASS text control. Monospace
    # avoids kerning; compare visible glyph ink and extent, not ASS strings.
    subs = pysubs2.SSAFile.from_string(build_ass("x",d,640,180),format_="ass")
    subs.events[0].text = r"{\rDefault}" + reference
    expected = _render_states(d,(subs.to_string("ass"),),640,180)[0]
    def metrics(uri):
        w,h,raw = _png_rgba(uri)
        rgba = np.frombuffer(raw,dtype=np.uint8).reshape(h,1+w*4)[:,1:].reshape(h,w,4)
        alpha = rgba[:,:,3]
        ys,xs = np.nonzero(alpha)
        return int(alpha.sum()), int(xs.max()-xs.min()+1), int(ys.max()-ys.min()+1)
    ink,width,height = metrics(actual)
    expected_ink,expected_width,expected_height = metrics(expected)
    assert ink == pytest.approx(expected_ink,rel=0.06)
    assert abs(width-expected_width) <= 5
    assert abs(height-expected_height) <= 2


def test_cue_alignment_changes_real_raster_position():
    import numpy as np
    font = _latin_font()
    centers = []
    for alignment in (7,2):
        uri = render_subtitle_states("Qingyan",_design(font,alignment=alignment),width=640,height=360)[0]
        w,h,raw = _png_rgba(uri)
        alpha = np.frombuffer(raw,dtype=np.uint8).reshape(h,1+w*4)[:,1:].reshape(h,w,4)[:,:,3]
        ys,xs = np.nonzero(alpha)
        centers.append((xs.mean(),ys.mean()))
    assert centers[0][0] < 180 and centers[0][1] < 100
    assert centers[1][0] > 250 and centers[1][1] > 260


def test_version_mismatch_and_inexact_word_partition_fail_before_render() -> None:
    font = _embedded_font()
    mismatch = _design(font, libass_version=libass_version() + 1)
    with pytest.raises(ValueError, match="does not match"):
        render_subtitle_states("Hello", mismatch, width=320, height=180)

    highlight = _design(font, word_highlight=True)
    with pytest.raises(ValueError, match="exactly concatenate"):
        render_subtitle_states(
            "Hello world",
            highlight,
            width=320,
            height=180,
            word_texts=("Hello", "world"),
        )


def test_libass_renders_transparent_cjk_latin_and_word_highlight_states() -> None:
    if not ctypes.util.find_library("ass"):
        pytest.skip("Native libass is not installed on this host.")
    _require_pysubs2()
    font = _embedded_font()
    latin_font = _latin_font()

    design = _design(
        font,
        fonts=(font, latin_font),
        word_highlight=True,
        wrap_width_px=280,
        line_styles=(SubtitleLineStyle(line_index=1, font_family=latin_font.family),),
    )
    states = render_subtitle_states(
        "字幕中文\nLatin",
        design,
        width=400,
        height=220,
        word_texts=("字幕", "中文\n", "Latin"),
    )
    assert len(states) == 4
    assert len(set(states)) == len(states)
    for state in states:
        width, height, raw = _png_rgba(state)
        assert (width, height) == (400, 220)
        # PNG uses filter 0 + RGBA per row; at least one glyph pixel is visible.
        row_stride = 1 + width * 4
        assert all(raw[row * row_stride] == 0 for row in range(height))
        assert any(
            raw[row * row_stride + 4 : row * row_stride + 1 + width * 4 : 4]
            for row in range(height)
        )
