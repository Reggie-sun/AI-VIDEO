from __future__ import annotations

import hashlib

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from ai_video.production.video_cleanup_contracts import (
    CleanPlateFrame,
    CleanPlatePatch,
    VideoCleanupPlan,
)
from ai_video.production.video_cleanup_pixels import apply_clean_plate_frame


_SHA = "a" * 64


def _patch(
    plate_frame: int,
    polygon: tuple[tuple[int, int], ...] = ((2, 2), (5, 2), (5, 5), (2, 5)),
    *,
    affine: tuple[float, float, float, float, float, float] = (1, 0, 0, 0, 1, 0),
    feather_px: int = 0,
) -> CleanPlatePatch:
    return CleanPlatePatch(
        plate_frame=plate_frame,
        polygons=(polygon,),
        plate_to_output_affine=affine,
        feather_px=feather_px,
    )


def _frame(*patches: CleanPlatePatch, protected=()) -> CleanPlateFrame:
    return CleanPlateFrame(
        frame_index=0,
        patches=tuple(patches),
        protected_polygons=tuple(protected),
    )


def _solid(size: tuple[int, int], color: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", size, color)


def test_plan_models_are_strict_ordered_and_bounded():
    plan = VideoCleanupPlan(
        contract_version="video-clean-plate/1",
        source_sha256=_SHA,
        frames=(CleanPlateFrame(frame_index=0, patches=(_patch(4),)),),
    )
    assert plan.frames[0].patches[0].plate_to_output_affine == (1, 0, 0, 0, 1, 0)

    with pytest.raises(ValidationError):
        CleanPlateFrame(frame_index=True, patches=(_patch(0),))
    with pytest.raises(ValidationError):
        CleanPlatePatch(plate_frame=0, polygons=(), feather_px=0)
    with pytest.raises(ValidationError):
        CleanPlatePatch(
            plate_frame=0,
            polygons=(((True, 1), (3, 1), (3, 3)),),
        )
    with pytest.raises(ValidationError):
        _patch(0, affine=(1, 0, 0, 0, float("nan"), 0))
    with pytest.raises(ValidationError):
        _patch(0, affine=(1, 0, 0, 0, 1, True))
    with pytest.raises(ValidationError):
        _patch(0, affine=(10**400, 0, 0, 0, 1, 0))
    with pytest.raises(ValidationError):
        VideoCleanupPlan(
            contract_version="video-clean-plate/1",
            source_sha256=_SHA,
            frames=(
                CleanPlateFrame(frame_index=1, patches=(_patch(0),)),
                CleanPlateFrame(frame_index=0, patches=(_patch(1),)),
            ),
        )
    with pytest.raises(ValidationError):
        VideoCleanupPlan(
            contract_version="video-clean-plate/1",
            source_sha256=_SHA,
            frames=tuple(
                CleanPlateFrame(frame_index=i, patches=(_patch(i),))
                for i in range(601)
            ),
        )


@pytest.mark.parametrize(
    ("size", "source_color", "plate_color"),
    [
        ((12, 10), (12, 40, 90), (220, 30, 15)),
        ((19, 13), (80, 20, 170), (10, 200, 55)),
        ((8, 9), (110, 110, 110), (230, 210, 20)),
    ],
)
def test_identity_patch_changes_only_the_explicit_area(size, source_color, plate_color):
    source = _solid(size, source_color)
    plate = _solid(size, plate_color)
    polygon = ((2, 2), (5, 2), (5, 5), (2, 5))

    output, proof = apply_clean_plate_frame(source, {7: plate}, _frame(_patch(7, polygon)))

    assert output.mode == "RGB"
    assert output.size == size
    assert output.getpixel((3, 3)) == plate_color
    assert output.getpixel((1, 3)) == source_color
    assert output.getpixel((6, 3)) == source_color
    assert proof.input_rgb_sha256 == hashlib.sha256(source.tobytes()).hexdigest()
    assert proof.output_rgb_sha256 == hashlib.sha256(output.tobytes()).hexdigest()
    assert proof.changed_pixel_count > 0
    assert proof.protected_pixel_changes == 0


def test_affine_translation_places_clean_plate_patch_at_output_location():
    source = _solid((12, 10), (20, 30, 40))
    plate = _solid((12, 10), (210, 120, 30))
    patch = _patch(
        4,
        ((1, 1), (2, 1), (2, 2), (1, 2)),
        affine=(1, 0, 4, 0, 1, 3),
    )

    output, proof = apply_clean_plate_frame(source, {4: plate}, _frame(patch))

    assert output.getpixel((5, 4)) == (210, 120, 30)
    assert output.getpixel((2, 2)) == (20, 30, 40)
    assert proof.changed_pixel_count > 0


def test_affine_scale_tracks_plate_coordinates_into_output_coordinates():
    source = _solid((12, 10), (20, 30, 40))
    plate = _solid((12, 10), (210, 120, 30))
    patch = _patch(
        4,
        ((1, 1), (2, 1), (2, 2), (1, 2)),
        affine=(2, 0, 1, 0, 1, 1),
    )

    output, _ = apply_clean_plate_frame(source, {4: plate}, _frame(patch))

    assert output.getpixel((4, 2)) == (210, 120, 30)
    assert output.getpixel((1, 2)) == (20, 30, 40)


def test_affine_shear_uses_the_forward_plate_to_output_mapping():
    source = _solid((12, 10), (20, 30, 40))
    plate = _solid((12, 10), (210, 120, 30))
    patch = _patch(
        4,
        ((2, 1), (3, 1), (3, 2), (2, 2)),
        affine=(1, 0.5, 1, 0.25, 1, 1),
    )

    output, _ = apply_clean_plate_frame(source, {4: plate}, _frame(patch))

    assert output.getpixel((4, 3)) == (210, 120, 30)
    assert output.getpixel((1, 1)) == (20, 30, 40)


def test_protected_foreground_stays_bit_identical_across_overlapping_patches():
    source = Image.new("RGB", (12, 10))
    pixels = source.load()
    for y in range(source.height):
        for x in range(source.width):
            pixels[x, y] = (x * 7, y * 9, (x + y) * 5)
    source_bytes = source.tobytes()
    plates = {
        2: _solid(source.size, (240, 15, 20)),
        8: _solid(source.size, (10, 220, 40)),
    }
    protected = ((4, 3), (7, 3), (7, 6), (4, 6))

    output, proof = apply_clean_plate_frame(
        source,
        plates,
        _frame(
            _patch(2, ((2, 2), (8, 2), (8, 7), (2, 7))),
            _patch(8, ((3, 1), (9, 1), (9, 8), (3, 8))),
            protected=(protected,),
        ),
    )

    before = np.asarray(Image.frombytes("RGB", source.size, source_bytes))
    after = np.asarray(output)
    protected_pixels = np.zeros((source.height, source.width), dtype=bool)
    protected_pixels[3:7, 4:8] = True
    assert np.array_equal(before[protected_pixels], after[protected_pixels])
    assert output.getpixel((3, 4)) != source.getpixel((3, 4))
    assert proof.protected_pixel_changes == 0
    assert proof.protected_rgb_sha256 == hashlib.sha256(
        before[protected_pixels].tobytes() + after[protected_pixels].tobytes()
    ).hexdigest()


def test_feather_is_local_and_has_interpolated_edge_pixels():
    source = _solid((16, 12), (0, 0, 0))
    plate = _solid(source.size, (255, 255, 255))
    patch = _patch(
        1,
        ((5, 3), (9, 3), (9, 8), (5, 8)),
        feather_px=2,
    )

    output, proof = apply_clean_plate_frame(source, {1: plate}, _frame(patch))

    assert output.getpixel((7, 5)) == (255, 255, 255)
    assert 0 < output.getpixel((4, 5))[0] < 255
    assert output.getpixel((2, 5)) == (0, 0, 0)
    assert proof.changed_pixel_count < source.width * source.height


def test_multiple_disjoint_plate_frames_form_one_effective_edit_region():
    source = _solid((14, 10), (30, 60, 90))
    red = _solid(source.size, (200, 0, 0))
    green = _solid(source.size, (0, 200, 0))

    output, proof = apply_clean_plate_frame(
        source,
        {3: red, 9: green},
        _frame(
            _patch(3, ((1, 2), (3, 2), (3, 4), (1, 4))),
            _patch(9, ((8, 2), (10, 2), (10, 4), (8, 4))),
        ),
    )

    assert output.getpixel((2, 3)) == (200, 0, 0)
    assert output.getpixel((9, 3)) == (0, 200, 0)
    assert output.getpixel((6, 3)) == (30, 60, 90)
    assert proof.changed_pixel_count > 0
    assert proof.effective_mask_sha256 != hashlib.sha256(bytes(source.width * source.height)).hexdigest()


@pytest.mark.parametrize(
    "polygon",
    [
        ((1, 1), (1, 1), (3, 3)),
        ((1, 1), (5, 5), (1, 5), (5, 1)),
        ((-1, 1), (3, 1), (3, 4), (1, 4)),
        ((1, 1), (9, 1), (9, 4), (1, 4)),
    ],
)
def test_invalid_polygon_geometry_is_rejected(polygon):
    with pytest.raises(ValueError):
        apply_clean_plate_frame(
            _solid((8, 8), (1, 2, 3)),
            {0: _solid((8, 8), (4, 5, 6))},
            _frame(_patch(0, polygon)),
        )


@pytest.mark.parametrize(
    "affine",
    [
        (1, 2, 0, 2, 4, 0),
        (float("inf"), 0, 0, 0, 1, 0),
    ],
)
def test_singular_or_nonfinite_transform_is_rejected(affine):
    with pytest.raises((ValueError, ValidationError)):
        patch = _patch(0, affine=affine)
        apply_clean_plate_frame(
            _solid((8, 8), (1, 2, 3)),
            {0: _solid((8, 8), (4, 5, 6))},
            _frame(patch),
        )


def test_missing_plate_incompatible_image_modes_and_sizes_are_rejected():
    source = _solid((8, 8), (1, 2, 3))
    patch = _patch(0)
    with pytest.raises(ValueError, match="missing"):
        apply_clean_plate_frame(source, {}, _frame(patch))
    with pytest.raises(ValueError, match="mapping keys"):
        apply_clean_plate_frame(source, {True: _solid(source.size, (4, 5, 6))}, _frame(patch))
    with pytest.raises(ValueError, match="geometry"):
        apply_clean_plate_frame(source, {0: _solid((7, 8), (4, 5, 6))}, _frame(patch))
    with pytest.raises(ValueError, match="RGB"):
        apply_clean_plate_frame(
            Image.new("L", source.size, 10),
            {0: _solid(source.size, (4, 5, 6))},
            _frame(patch),
        )
    with pytest.raises(ValueError, match="RGB"):
        apply_clean_plate_frame(
            source,
            {0: Image.new("RGBA", source.size, (4, 5, 6, 255))},
            _frame(patch),
        )


def test_positive_alpha_with_out_of_plate_sampling_is_rejected():
    source = _solid((8, 8), (1, 2, 3))
    plate = _solid(source.size, (4, 5, 6))
    patch = _patch(
        0,
        ((0, 1), (2, 1), (2, 4), (0, 4)),
        affine=(1, 0, 0.3, 0, 1, 0),
    )

    with pytest.raises(ValueError, match="outside plate geometry"):
        apply_clean_plate_frame(source, {0: plate}, _frame(patch))

