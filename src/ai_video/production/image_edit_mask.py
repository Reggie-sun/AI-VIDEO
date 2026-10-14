"""Strict validation for exact local image-edit masks."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageChops

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image_bytes import MeasuredPng, measure_png_bytes
from ai_video.production.models import AssetRegistrySnapshot, AssetType
from ai_video.production.paths import _read_regular_file_nofollow

if TYPE_CHECKING:
    from ai_video.production.image import ImageGenerationRequest


_EDIT_MASK_ROLE_ORDER = ("character", "scene", "edit_mask")


def _invalid_asset(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.IMAGE_ASSET_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _request_edit_mask(
    request: ImageGenerationRequest,
) -> object | None:
    try:
        references = tuple(request.references)
    except (AttributeError, TypeError) as exc:
        raise ValueError("image request references are invalid") from exc
    return next(
        (item for item in references if getattr(item, "role", None) == "edit_mask"),
        None,
    )


def validate_edit_mask_request(request: ImageGenerationRequest) -> None:
    """Enforce the exact ComfyUI source, mask, and creative-owner contract."""
    mask_reference = _request_edit_mask(request)
    if mask_reference is None:
        return

    if getattr(request, "provider_kind", None) != "comfyui_local":
        raise ValueError("edit masks require the comfyui_local provider")

    references = tuple(request.references)
    roles = tuple(getattr(item, "role", None) for item in references)
    if roles != _EDIT_MASK_ROLE_ORDER:
        raise ValueError(
            "edit mask requests require exactly character, scene, edit_mask references"
        )

    scene_reference = references[1]
    if (
        getattr(scene_reference, "creative_artifact_id", None)
        != getattr(mask_reference, "creative_artifact_id", None)
        or getattr(scene_reference, "creative_revision", None)
        != getattr(mask_reference, "creative_revision", None)
        or getattr(scene_reference, "creative_content_hash", None)
        != getattr(mask_reference, "creative_content_hash", None)
    ):
        raise ValueError("scene and edit mask must have the same creative owner")
    if getattr(scene_reference, "asset_id", None) == getattr(mask_reference, "asset_id", None):
        raise ValueError("scene and edit mask must use a different asset")

    parameters = getattr(request, "parameters", None)
    width = getattr(parameters, "width", None)
    height = getattr(parameters, "height", None)
    if (
        type(width) is not int
        or type(height) is not int
        or width <= 0
        or height <= 0
        or width % 8 != 0
        or height % 8 != 0
    ):
        raise ValueError("edit mask requests require explicit geometry in multiples of 8")


def _selected_geometry(request: ImageGenerationRequest) -> tuple[int, int]:
    parameters = request.parameters
    width = getattr(parameters, "width", None)
    height = getattr(parameters, "height", None)
    if type(width) is not int or type(height) is not int:
        raise ValueError("edit mask requests require explicit geometry")
    return width, height


def _read_exact_png(
    payload: bytes,
    *,
    role: str,
    expected_size: tuple[int, int],
    allowed_color_types: set[int],
) -> tuple[MeasuredPng, Image.Image]:
    if type(payload) is not bytes or not payload:
        raise _invalid_asset(f"{role} must be nonempty PNG bytes")

    measured = measure_png_bytes(payload)
    if (measured.width, measured.height) != expected_size:
        raise _invalid_asset(
            f"{role} PNG geometry differs from the selected image geometry",
            f"expected={expected_size[0]}x{expected_size[1]}, "
            f"measured={measured.width}x{measured.height}",
        )
    if measured.bit_depth != 8 or measured.color_type not in allowed_color_types:
        raise _invalid_asset(f"{role} PNG has an unsupported channel layout or bit depth")

    try:
        with Image.open(BytesIO(payload), formats=("PNG",)) as image:
            # Dimensions are checked from IHDR before Pillow decompresses image pixels.
            if image.size != expected_size:
                raise _invalid_asset(
                    f"{role} PNG geometry differs from the selected image geometry"
                )
            if image.getexif().get(274, 1) not in (None, 1):
                raise _invalid_asset(f"{role} PNG requires EXIF orientation correction")
            if "transparency" in image.info:
                raise _invalid_asset(f"{role} PNG has unsupported transparency metadata")
            expected_modes = {
                0: {"L"},
                2: {"RGB"},
                6: {"RGBA"},
            }
            if image.mode not in expected_modes.get(measured.color_type, set()):
                raise _invalid_asset(f"{role} PNG has an unsupported channel layout")
            if getattr(image, "n_frames", 1) != 1:
                raise _invalid_asset(f"{role} PNG must contain exactly one frame")
            image.load()
            decoded = image.copy()
    except AiVideoError:
        raise
    except Exception as exc:
        raise _invalid_asset(f"{role} PNG could not be decoded", str(exc)) from exc

    if decoded.mode == "RGBA" and decoded.getchannel("A").getextrema() != (255, 255):
        raise _invalid_asset(f"{role} PNG must be fully opaque")
    return measured, decoded


def _validated_edit_inputs(
    request: ImageGenerationRequest,
    source_bytes: bytes,
    mask_bytes: bytes,
) -> tuple[Image.Image, Image.Image] | None:
    validate_edit_mask_request(request)
    mask_reference = _request_edit_mask(request)
    if mask_reference is None:
        return None

    references = tuple(request.references)
    scene_reference = references[1]
    expected_size = _selected_geometry(request)
    scene_measured, source = _read_exact_png(
        source_bytes,
        role="scene source",
        expected_size=expected_size,
        allowed_color_types={2, 6},
    )
    mask_measured, mask = _read_exact_png(
        mask_bytes,
        role="edit mask",
        expected_size=expected_size,
        allowed_color_types={0, 2},
    )
    if scene_measured.sha256 != getattr(scene_reference, "asset_sha256", None):
        raise _invalid_asset("scene source bytes do not match the exact scene reference")
    if mask_measured.sha256 != getattr(mask_reference, "asset_sha256", None):
        raise _invalid_asset("edit mask bytes do not match the exact edit mask reference")

    if mask.mode == "RGB":
        red, green, blue = mask.split()
        if (
            ImageChops.difference(red, green).getbbox() is not None
            or ImageChops.difference(red, blue).getbbox() is not None
        ):
            raise _invalid_asset("RGB edit mask channels must contain equal values")
        mask = red

    histogram = mask.histogram()
    if mask.getextrema() != (0, 255) or sum(histogram[1:255]) != 0:
        raise _invalid_asset(
            "edit mask must contain both black protection and white edit pixels only"
        )

    return source.convert("RGB"), mask


def validate_edit_mask_inputs(
    request: ImageGenerationRequest,
    source_bytes: bytes,
    mask_bytes: bytes,
) -> None:
    """Validate reference identity and decode-safe source/mask image bytes."""
    _validated_edit_inputs(request, source_bytes, mask_bytes)


def validate_edit_mask_output(
    request: ImageGenerationRequest,
    source_bytes: bytes,
    mask_bytes: bytes,
    output_bytes: bytes,
) -> None:
    """Require opaque output pixels outside white mask regions to stay exact."""
    validated = _validated_edit_inputs(request, source_bytes, mask_bytes)
    if validated is None:
        return
    source, mask = validated
    _, output = _read_exact_png(
        output_bytes,
        role="edited output",
        expected_size=_selected_geometry(request),
        allowed_color_types={2, 6},
    )

    difference = ImageChops.difference(source, output.convert("RGB"))
    protected = ImageChops.invert(mask)
    if any(
        ImageChops.multiply(channel, protected).getbbox() is not None
        for channel in difference.split()
    ):
        raise _invalid_asset("edited output changed pixels protected by the edit mask")


def validate_registered_edit_mask(
    *, request: ImageGenerationRequest, root: Path,
    registry: AssetRegistrySnapshot, output_bytes: bytes | None = None,
) -> None:
    """Reopen the same Registry inputs before intent and when reading output."""
    if _request_edit_mask(request) is None:
        return
    validate_edit_mask_request(request)
    assets = {item.asset_id: item for item in registry.assets}
    payloads = []
    for reference in request.references[1:]:
        asset = assets.get(reference.asset_id)
        if (asset is None or asset.asset_type != AssetType.IMAGE
                or asset.mime_type != "image/png" or asset.sha256 != reference.asset_sha256
                or (asset.width, asset.height) != _selected_geometry(request)):
            raise _invalid_asset("edit input does not match its selected Registry image")
        snapshot = _read_regular_file_nofollow(root / asset.artifact_path, contained_by=root)
        if snapshot.file_sha256 != asset.sha256 or snapshot.size_bytes != asset.size_bytes:
            raise _invalid_asset("edit input bytes do not match their Registry identity")
        payloads.append(snapshot.data)
    if output_bytes is None:
        validate_edit_mask_inputs(request, *payloads)
    else:
        validate_edit_mask_output(request, *payloads, output_bytes)
