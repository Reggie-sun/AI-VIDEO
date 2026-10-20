"""Self-contained, content-addressed fonts; no system-font fallback authority."""
from __future__ import annotations

import base64
import hashlib
import io
import struct
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmbeddedFont(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, revalidate_instances="always")
    family: str = Field(min_length=1, max_length=100, pattern=r"^[\w .-]+$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_base64: str = Field(min_length=1, max_length=24_000_000)
    license: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def _verify(self) -> "EmbeddedFont":
        _font_info(self.family, self.sha256, self.data_base64)
        return self

    def font_bytes(self) -> bytes:
        return base64.b64decode(self.data_base64, validate=True)

    def require_glyphs(self, text: str) -> None:
        cmap, _ = _font_info(self.family, self.sha256, self.data_base64)
        missing = sorted({ord(c) for c in text if not c.isspace() and ord(c) not in cmap})
        if missing:
            raise ValueError("Embedded font lacks required glyphs: " + ",".join(f"U+{c:04X}" for c in missing[:16]))

    @property
    def mime(self) -> str:
        return _font_info(self.family, self.sha256, self.data_base64)[1]


@lru_cache(maxsize=8)
def _font_info(family: str, digest: str, encoded: str) -> tuple[frozenset[int], str]:
    try:
        from fontTools.ttLib import TTFont, TTLibError
    except ImportError as exc:
        raise ValueError("Embedded fonts require ai-video[text] (fonttools).") from exc
    try:
        data = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError("Embedded font base64 is invalid.") from exc
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Embedded font SHA-256 does not match bytes.")
    if data[:4] not in {b"OTTO", b"\x00\x01\x00\x00"}:
        raise ValueError("Embedded fonts must be standalone OpenType/TrueType.")
    try:
        with TTFont(io.BytesIO(data), lazy=False) as font:
            names = {n.toUnicode() for n in font["name"].names if n.nameID in {1, 16}}
            if family not in names:
                raise ValueError("Embedded font family does not match its name table.")
            cmap = frozenset(font.getBestCmap() or {})
    except (TTLibError, KeyError, OSError, struct.error, EOFError, IndexError) as exc:
        raise ValueError("Embedded font tables are invalid.") from exc
    return cmap, "font/otf" if data[:4] == b"OTTO" else "font/ttf"
