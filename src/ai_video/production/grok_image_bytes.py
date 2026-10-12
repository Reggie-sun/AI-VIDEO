"""Bounded, deterministic image decoding shared by adapter and offline reader."""

from io import BytesIO
import warnings

from PIL import Image

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


def decode_grok_image(wire: bytes) -> tuple[bytes, str, str]:
    if not wire or len(wire) > MAX_IMAGE_BYTES:
        raise ValueError("Grok image wire size is outside the accepted bound")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(BytesIO(wire)) as source:
                mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}.get(source.format)
                if (mime is None or source.width * source.height > MAX_IMAGE_PIXELS
                        or getattr(source, "n_frames", 1) != 1):
                    raise ValueError("Grok image format or dimensions are unsupported")
                source.load()
                if mime == "image/png":
                    return wire, mime, "identity-png"
                out = BytesIO()
                source.convert("RGBA" if source.mode in {"RGBA", "LA", "P"} else "RGB").save(out, format="PNG")
                png = out.getvalue()
                if len(png) > MAX_IMAGE_BYTES:
                    raise ValueError("Grok decoded PNG exceeds the accepted bound")
                return png, mime, "pillow-lossless-png"
        except Exception:
            raise ValueError("Grok image bytes could not be decoded within accepted bounds") from None
