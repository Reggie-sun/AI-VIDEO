"""Measure supported reference images without rewriting their bytes."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO

from ai_video.production.image import measure_png_bytes


@dataclass(frozen=True)
class _ImageMeasurement:
    sha256: str
    size_bytes: int
    mime_type: str
    width: int
    height: int


def measure_reference_image(payload: bytes, mime_type: str):
    if mime_type == "image/png":
        return measure_png_bytes(payload)
    if mime_type != "image/jpeg":
        raise ValueError("unsupported Seedance reference image MIME")
    from PIL import Image

    with Image.open(BytesIO(payload)) as image:
        if image.format != "JPEG":
            raise ValueError("Seedance JPEG reference has another format")
        image.load()
        width, height = image.size
    return _ImageMeasurement(hashlib.sha256(payload).hexdigest(), len(payload),
                             mime_type, width, height)
