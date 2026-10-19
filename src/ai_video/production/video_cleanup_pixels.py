from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ai_video.production.video_cleanup_contracts import CleanPlateFrame, CleanPlatePatch, CleanupPolygon


@dataclass(frozen=True, slots=True)
class CleanupPixelProof:
    input_rgb_sha256: str
    output_rgb_sha256: str
    effective_mask_sha256: str
    protected_rgb_sha256: str
    changed_pixel_count: int
    protected_pixel_changes: int = 0


def apply_clean_plate_frame(
    source: Image.Image,
    plates: Mapping[int, Image.Image],
    frame: CleanPlateFrame,
) -> tuple[Image.Image, CleanupPixelProof]:
    """Apply explicit same-size clean-plate patches to one RGB frame.

    Polygon coordinates are integer pixel coordinates. Affines map plate
    coordinates forward to output coordinates; Pillow receives their inverse.
    The returned image is new and the source and supplied plates are untouched.
    """
    _require_rgb(source, "source")
    width, height = source.size
    if width <= 0 or height <= 0:
        raise ValueError("source geometry must be non-empty")
    if not isinstance(frame, CleanPlateFrame):
        raise ValueError("frame must be a CleanPlateFrame")
    if not frame.patches:
        raise ValueError("frame must contain at least one clean-plate patch")
    if not isinstance(plates, Mapping):
        raise ValueError("plates must map plate frame indices to RGB images")
    if any(type(index) is not int or index < 0 for index in plates):
        raise ValueError("plate mapping keys must be non-negative integer frame indices")

    protected = Image.new("L", source.size, 0)
    protected_draw = ImageDraw.Draw(protected)
    for polygon in frame.protected_polygons:
        _validate_polygon(polygon, width, height, "protected polygon")
        protected_draw.polygon(polygon, fill=255)
    protected_array = np.asarray(protected, dtype=np.uint8) > 0

    source_array = np.asarray(source, dtype=np.uint8)
    output_array = source_array.copy()
    effective_union = np.zeros((height, width), dtype=np.uint8)

    for patch in frame.patches:
        if not isinstance(patch, CleanPlatePatch):
            raise ValueError("patches must contain CleanPlatePatch values")
        plate_index = patch.plate_frame
        if isinstance(plate_index, bool) or not isinstance(plate_index, int) or plate_index < 0:
            raise ValueError("plate_frame must be a non-negative integer")
        plate = plates.get(plate_index)
        if plate is None:
            raise ValueError(f"missing clean plate for frame {plate_index}")
        _require_rgb(plate, f"clean plate {plate_index}")
        if plate.size != source.size:
            raise ValueError("source and clean plate geometry must match")

        affine, inverse = _affines(patch)
        mask = _plate_mask(source.size, patch, width, height)
        output_mask = mask.transform(
            source.size,
            Image.Transform.AFFINE,
            inverse,
            resample=Image.Resampling.BILINEAR,
            fillcolor=0,
        )
        alpha = np.asarray(output_mask, dtype=np.uint8).copy()
        alpha[protected_array] = 0
        active = alpha > 0
        if not np.any(active):
            continue

        _validate_active_samples(active, inverse, width, height)
        sampled_plate = plate.transform(
            source.size,
            Image.Transform.AFFINE,
            inverse,
            resample=Image.Resampling.BILINEAR,
            fillcolor=(0, 0, 0),
        )
        plate_array = np.asarray(sampled_plate, dtype=np.uint8)
        alpha32 = alpha.astype(np.uint32)[..., None]
        blended = (
            plate_array.astype(np.uint32) * alpha32
            + output_array.astype(np.uint32) * (255 - alpha32)
            + 127
        ) // 255
        output_array[active] = blended.astype(np.uint8)[active]
        effective_union[active] = 255

    changed_pixels = np.any(source_array != output_array, axis=2)
    protected_pixel_changes = int(np.count_nonzero(changed_pixels & protected_array))
    if protected_pixel_changes != 0:
        raise ValueError("clean-plate composition changed an explicitly protected pixel")

    output = Image.frombytes("RGB", source.size, output_array.tobytes())
    protected_bytes = source_array[protected_array].tobytes() + output_array[protected_array].tobytes()
    proof = CleanupPixelProof(
        input_rgb_sha256=_sha256(source.tobytes()),
        output_rgb_sha256=_sha256(output.tobytes()),
        effective_mask_sha256=_sha256(effective_union.tobytes()),
        protected_rgb_sha256=_sha256(protected_bytes),
        changed_pixel_count=int(np.count_nonzero(changed_pixels)),
        protected_pixel_changes=protected_pixel_changes,
    )
    return output, proof


def _require_rgb(image: Image.Image, label: str) -> None:
    if not isinstance(image, Image.Image) or image.mode != "RGB":
        raise ValueError(f"{label} must be a PIL RGB image")


def _plate_mask(
    size: tuple[int, int],
    patch: CleanPlatePatch,
    width: int,
    height: int,
) -> Image.Image:
    base = Image.new("L", size, 0)
    draw = ImageDraw.Draw(base)
    affine, _ = _affines(patch)
    a, b, c, d, e, f = affine
    for polygon in patch.polygons:
        _validate_polygon(polygon, width, height, "clean-plate polygon")
        mapped = tuple((a * x + b * y + c, d * x + e * y + f) for x, y in polygon)
        if any(
            not (0.0 <= x <= width - 1 and 0.0 <= y <= height - 1)
            for x, y in mapped
        ):
            raise ValueError("transformed clean-plate polygon lies outside output geometry")
        draw.polygon(polygon, fill=255)

    radius = patch.feather_px
    if radius == 0:
        return base
    dilated = base.filter(ImageFilter.MaxFilter(size=2 * radius + 1))
    blurred = base.filter(ImageFilter.GaussianBlur(radius=float(radius)))
    interior = base.filter(ImageFilter.MinFilter(size=2 * radius + 1))
    return Image.fromarray(
        np.maximum(
            np.asarray(interior, dtype=np.uint8),
            np.minimum(np.asarray(dilated, dtype=np.uint8), np.asarray(blurred, dtype=np.uint8)),
        ),
        mode="L",
    )


def _validate_polygon(
    polygon: CleanupPolygon,
    width: int,
    height: int,
    label: str,
) -> None:
    if not isinstance(polygon, (tuple, list)) or len(polygon) < 3:
        raise ValueError(f"{label} must contain at least three vertices")
    vertices: list[tuple[int, int]] = []
    for point in polygon:
        if (
            not isinstance(point, (tuple, list))
            or len(point) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in point)
        ):
            raise ValueError(f"{label} vertices must be integer coordinate pairs")
        x, y = point
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"{label} has a vertex outside image geometry")
        vertices.append((x, y))

    if len(set(vertices)) != len(vertices):
        raise ValueError(f"{label} must not repeat vertices")
    area_twice = sum(
        vertices[index][0] * vertices[(index + 1) % len(vertices)][1]
        - vertices[(index + 1) % len(vertices)][0] * vertices[index][1]
        for index in range(len(vertices))
    )
    if area_twice == 0:
        raise ValueError(f"{label} must have non-zero area")

    count = len(vertices)
    for first in range(count):
        a, b = vertices[first], vertices[(first + 1) % count]
        for second in range(first + 1, count):
            if second == first or second == first + 1 or (first == 0 and second == count - 1):
                continue
            c, d = vertices[second], vertices[(second + 1) % count]
            if _segments_intersect(a, b, c, d):
                raise ValueError(f"{label} must not self-intersect")


def _segments_intersect(
    a: tuple[int, int],
    b: tuple[int, int],
    c: tuple[int, int],
    d: tuple[int, int],
) -> bool:
    def orientation(p: tuple[int, int], q: tuple[int, int], r: tuple[int, int]) -> int:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    def on_segment(p: tuple[int, int], q: tuple[int, int], r: tuple[int, int]) -> bool:
        return (
            min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
        )

    abc, abd = orientation(a, b, c), orientation(a, b, d)
    cda, cdb = orientation(c, d, a), orientation(c, d, b)
    if abc == 0 and on_segment(a, c, b):
        return True
    if abd == 0 and on_segment(a, d, b):
        return True
    if cda == 0 and on_segment(c, a, d):
        return True
    if cdb == 0 and on_segment(c, b, d):
        return True
    return (abc > 0) != (abd > 0) and (cda > 0) != (cdb > 0)


def _affines(
    patch: CleanPlatePatch,
) -> tuple[tuple[float, float, float, float, float, float], tuple[float, float, float, float, float, float]]:
    values = patch.plate_to_output_affine
    if len(values) != 6 or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("plate_to_output_affine must contain six finite numbers")
    try:
        a, b, c, d, e, f = (float(value) for value in values)
    except (OverflowError, ValueError):
        raise ValueError("plate_to_output_affine must contain six finite numbers") from None
    if not all(math.isfinite(value) for value in (a, b, c, d, e, f)):
        raise ValueError("plate_to_output_affine must contain six finite numbers")
    determinant = a * e - b * d
    if not math.isfinite(determinant) or determinant == 0.0:
        raise ValueError("plate_to_output_affine must be invertible")
    inverse = (
        e / determinant,
        -b / determinant,
        (b * f - e * c) / determinant,
        -d / determinant,
        a / determinant,
        (d * c - a * f) / determinant,
    )
    if any(not math.isfinite(value) for value in inverse):
        raise ValueError("plate_to_output_affine inverse must be finite")
    return (a, b, c, d, e, f), inverse


def _validate_active_samples(
    active: np.ndarray,
    inverse: tuple[float, float, float, float, float, float],
    width: int,
    height: int,
) -> None:
    y, x = np.nonzero(active)
    a, b, c, d, e, f = inverse
    sample_x = a * x + b * y + c
    sample_y = d * x + e * y + f
    if (
        np.any(sample_x < 0.0)
        or np.any(sample_x > width - 1)
        or np.any(sample_y < 0.0)
        or np.any(sample_y > height - 1)
    ):
        raise ValueError("positive-alpha clean-plate sampling falls outside plate geometry")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
