"""Single exact PNG preparation; no provider effects or reflection verdicts."""
from ai_video.production.image_bytes import measure_png_bytes


SEEDREAM_REFERENCE_VERSION = "seedream-single-reference-png/1"
SEEDREAM_ORIGINAL_VERSION = "seedream-original-png/1"
MAX_REFERENCE_BYTES = 10 * 1024 * 1024
MAX_REFERENCE_PIXELS = 36_000_000


def seedream_adapter_version(references):
    return SEEDREAM_REFERENCE_VERSION if references else SEEDREAM_ORIGINAL_VERSION


def validate_seedream_references(references):
    if len(references) > 1 or any(r.role != "scene" for r in references):
        raise ValueError("Seedream supports only one exact scene PNG reference")


def resolve_seedream_reference(references, resolver):
    validate_seedream_references(references)
    if not references:
        return None
    if resolver is None:
        raise ValueError("Seedream single PNG reference needs an injected byte resolver")
    raw = resolver(references[0])
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_REFERENCE_BYTES:
        raise ValueError("Seedream PNG reference exceeds its byte contract")
    measured = measure_png_bytes(raw)
    if (measured.sha256 != references[0].asset_sha256
            or min(measured.width, measured.height) <= 14
            or measured.width * measured.height > MAX_REFERENCE_PIXELS
            or not 1 / 16 <= measured.width / measured.height <= 16):
        raise ValueError("Seedream PNG reference identity or geometry differs")
    return raw


def validate_seedream_preview_references(preview):
    items = [i for i in preview.remote_call.egress_items if i.purpose == "reference"]
    if (len(preview.reference_asset_ids) > 1 or len(items) != len(preview.reference_asset_ids)
            or preview.reference_total_bytes != sum(i.size_bytes for i in items)
            or any(i.mime_type != "image/png" or i.item_id != "reference-1-scene" for i in items)):
        raise ValueError("Seedream preview must bind exact single PNG reference accounting")
