from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.image_edit_mask import (
    validate_edit_mask_inputs,
    validate_edit_mask_output,
    validate_edit_mask_request,
)


@dataclass(frozen=True)
class Reference:
    role: str
    creative_artifact_id: str
    creative_revision: int
    creative_content_hash: str
    asset_id: str
    asset_sha256: str


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    options = {"exif": image.info["exif"]} if "exif" in image.info else {}
    image.save(output, format="PNG", **options)
    return output.getvalue()


def _base_images() -> tuple[bytes, bytes]:
    source = Image.new("RGB", (16, 8), (20, 40, 60))
    mask = Image.new("L", (16, 8), 0)
    for y in range(8):
        for x in range(8):
            mask.putpixel((x, y), 255)
    return _png(source), _png(mask)


def _request(
    source: bytes | None = None,
    mask: bytes | None = None,
    *,
    provider_kind: str = "comfyui_local",
    roles: tuple[str, ...] = ("character", "scene", "edit_mask"),
    width: int | None = 16,
    height: int | None = 8,
) -> SimpleNamespace:
    source, mask = _base_images() if source is None or mask is None else (source, mask)
    refs = []
    for role in roles:
        if role == "character":
            refs.append(
                Reference(role, "character-1", 1, "a" * 64, "character-asset", "b" * 64)
            )
        elif role == "scene":
            refs.append(
                Reference(
                    role,
                    "scene-1",
                    2,
                    "c" * 64,
                    "scene-asset",
                    sha256(source).hexdigest(),
                )
            )
        elif role == "edit_mask":
            refs.append(
                Reference(
                    role,
                    "scene-1",
                    2,
                    "c" * 64,
                    "mask-asset",
                    sha256(mask).hexdigest(),
                )
            )
        else:
            refs.append(Reference(role, "other-1", 1, "d" * 64, f"{role}-asset", "e" * 64))
    return SimpleNamespace(
        provider_kind=provider_kind,
        references=tuple(refs),
        parameters=SimpleNamespace(width=width, height=height),
    )


def _assert_invalid_asset(callable_) -> None:
    with pytest.raises(AiVideoError) as error:
        callable_()
    assert error.value.code is ErrorCode.IMAGE_ASSET_INVALID
    assert error.value.retryable is False


def test_edit_mask_request_requires_exact_local_roles_and_shared_scene_owner():
    source, mask = _base_images()
    valid = _request(source, mask)
    assert validate_edit_mask_request(valid) is None

    with pytest.raises(ValueError, match="provider"):
        validate_edit_mask_request(_request(source, mask, provider_kind="seedream"))
    for rejected_roles in (
        ("character", "scene", "style", "edit_mask"),
        ("character", "scene", "continuity_terminal", "edit_mask"),
    ):
        with pytest.raises(ValueError, match="character, scene, edit_mask"):
            validate_edit_mask_request(_request(source, mask, roles=rejected_roles))
    with pytest.raises(ValueError, match="same creative owner"):
        changed_owner = _request(source, mask)
        refs = list(changed_owner.references)
        refs[2] = Reference(
            "edit_mask",
            "different-scene",
            2,
            "c" * 64,
            "mask-asset",
            sha256(mask).hexdigest(),
        )
        changed_owner.references = tuple(refs)
        validate_edit_mask_request(changed_owner)
    with pytest.raises(ValueError, match="different asset"):
        same_asset = _request(source, mask)
        refs = list(same_asset.references)
        refs[2] = Reference(
            "edit_mask", "scene-1", 2, "c" * 64, "scene-asset", sha256(mask).hexdigest()
        )
        same_asset.references = tuple(refs)
        validate_edit_mask_request(same_asset)
    with pytest.raises(ValueError, match="multiples of 8"):
        validate_edit_mask_request(_request(source, mask, width=18))


def test_edit_mask_input_requires_reference_hashes_and_selected_geometry():
    source, mask = _base_images()
    request = _request(source, mask)
    assert validate_edit_mask_inputs(request, source, mask) is None

    changed_source = Image.open(BytesIO(source)).convert("RGB")
    changed_source.putpixel((15, 7), (21, 40, 60))
    _assert_invalid_asset(
        lambda: validate_edit_mask_inputs(request, _png(changed_source), mask)
    )

    changed_mask_image = Image.open(BytesIO(mask)).convert("L")
    changed_mask_image.putpixel((8, 0), 255)
    _assert_invalid_asset(
        lambda: validate_edit_mask_inputs(request, source, _png(changed_mask_image))
    )

    mismatched_geometry = _png(Image.new("L", (8, 8), 255))
    mismatched_request = _request(source, mismatched_geometry)
    _assert_invalid_asset(
        lambda: validate_edit_mask_inputs(mismatched_request, source, mismatched_geometry)
    )


@pytest.mark.parametrize(
    "mask_image",
    [
        Image.new("L", (16, 8), 0),  # empty edit region
        Image.new("L", (16, 8), 255),  # no protected region
        Image.frombytes("L", (16, 8), bytes([128]) * 128),  # soft values
        Image.new("LA", (16, 8), (0, 255)),  # alpha channel
        Image.new("RGB", (16, 8), (255, 0, 0)),  # unequal color channels
    ],
)
def test_edit_mask_rejects_nonbinary_or_unsupported_mask_channels(mask_image: Image.Image):
    source, _ = _base_images()
    mask = _png(mask_image)
    request = _request(source, mask)
    _assert_invalid_asset(lambda: validate_edit_mask_inputs(request, source, mask))


def test_edit_mask_accepts_equal_rgb_binary_masks_and_opaque_rgba_source():
    source_image = Image.new("RGBA", (16, 8), (20, 40, 60, 255))
    source = _png(source_image)
    base_mask = Image.new("L", (16, 8), 0)
    for y in range(8):
        for x in range(8):
            base_mask.putpixel((x, y), 255)
    mask = _png(base_mask.convert("RGB"))
    assert validate_edit_mask_inputs(_request(source, mask), source, mask) is None


@pytest.mark.parametrize("source_mode", ["palette", "16bit", "transparent", "rotated"])
def test_edit_mask_rejects_non_rgb_source_encodings(source_mode: str):
    if source_mode == "palette":
        image = Image.new("P", (16, 8), 0)
    elif source_mode == "16bit":
        image = Image.new("I;16", (16, 8), 12)
    else:
        image = Image.new("RGBA", (16, 8), (20, 40, 60, 255))
        if source_mode == "transparent":
            image.putpixel((0, 0), (20, 40, 60, 254))
        else:
            exif = image.getexif()
            exif[274] = 6
            image.info["exif"] = exif.tobytes()
    source = _png(image)
    _, mask = _base_images()
    request = _request(source, mask)
    _assert_invalid_asset(lambda: validate_edit_mask_inputs(request, source, mask))


def test_edit_mask_allows_changes_inside_white_region_and_rejects_protected_changes():
    source, mask = _base_images()
    request = _request(source, mask)

    allowed = Image.open(BytesIO(source)).convert("RGBA")
    allowed.putpixel((3, 3), (240, 10, 20))
    assert validate_edit_mask_output(request, source, mask, _png(allowed)) is None

    changed_protected_pixel = Image.open(BytesIO(source)).convert("RGB")
    changed_protected_pixel.putpixel((15, 7), (21, 40, 60))
    _assert_invalid_asset(
        lambda: validate_edit_mask_output(request, source, mask, _png(changed_protected_pixel))
    )


def test_requests_without_edit_mask_are_noops():
    source, mask = _base_images()
    request = _request(source, mask, roles=())
    assert validate_edit_mask_request(request) is None
    assert validate_edit_mask_inputs(request, b"not a png", b"not a mask") is None
    assert validate_edit_mask_output(request, b"not a png", b"not a mask", b"not output") is None
