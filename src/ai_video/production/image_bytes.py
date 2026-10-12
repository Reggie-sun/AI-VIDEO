"""Canonical exact PNG measurement shared by local and remote images."""

from __future__ import annotations

import hashlib
import struct
import zlib
from typing import Literal

from pydantic import ConfigDict, Field

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StrictModel


_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_BIT_DEPTHS = {
    0: {1, 2, 4, 8, 16},
    2: {8, 16},
    3: {1, 2, 4, 8},
    4: {8, 16},
    6: {8, 16},
}
def _image_bytes_invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.IMAGE_ASSET_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


class MeasuredPng(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(strict=True, gt=0)
    mime_type: Literal["image/png"]
    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    bit_depth: Literal[1, 2, 4, 8, 16]
    color_type: Literal[0, 2, 3, 4, 6]


def measure_png_bytes(payload: bytes) -> MeasuredPng:
    if not payload.startswith(_PNG_SIGNATURE):
        raise _image_bytes_invalid("Image provider output is not a PNG file.")

    cursor = len(_PNG_SIGNATURE)
    chunk_index = 0
    saw_idat = False
    saw_iend = False
    width = height = bit_depth = color_type = None
    while cursor < len(payload):
        if len(payload) - cursor < 12:
            raise _image_bytes_invalid("PNG output contains a truncated chunk.")
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        kind = payload[cursor + 4 : cursor + 8]
        chunk_end = cursor + 12 + length
        if chunk_end > len(payload):
            raise _image_bytes_invalid("PNG output contains a truncated chunk.")
        chunk_data = payload[cursor + 8 : cursor + 8 + length]
        expected_crc = struct.unpack(">I", payload[cursor + 8 + length : chunk_end])[0]
        measured_crc = zlib.crc32(kind + chunk_data) & 0xFFFFFFFF
        if expected_crc != measured_crc:
            raise _image_bytes_invalid("PNG output contains an invalid chunk checksum.")

        if chunk_index == 0:
            if kind != b"IHDR" or length != 13:
                raise _image_bytes_invalid("PNG output must start with a complete IHDR chunk.")
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", chunk_data)
            if width <= 0 or height <= 0:
                raise _image_bytes_invalid("PNG output has invalid dimensions.")
            if bit_depth not in _PNG_BIT_DEPTHS.get(color_type, set()):
                raise _image_bytes_invalid("PNG output has an invalid color type or bit depth.")
            if compression != 0 or filter_method != 0 or interlace not in {0, 1}:
                raise _image_bytes_invalid("PNG output has unsupported IHDR methods.")
        elif kind == b"IHDR":
            raise _image_bytes_invalid("PNG output contains more than one IHDR chunk.")

        if kind == b"IDAT":
            saw_idat = True
        if kind == b"IEND":
            if length != 0 or not saw_idat or chunk_end != len(payload):
                raise _image_bytes_invalid("PNG output has an invalid IEND boundary.")
            saw_iend = True
        cursor = chunk_end
        chunk_index += 1

    if not saw_iend or width is None or height is None:
        raise _image_bytes_invalid("PNG output is incomplete.")
    return MeasuredPng(
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        mime_type="image/png",
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
    )
