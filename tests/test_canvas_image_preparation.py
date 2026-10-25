from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from ai_video.production.image_preparation import (
    CanvasImagePreparationOperation,
    prepare_canvas_image_assets,
    verify_canvas_prepared_image_assets,
)
from ai_video.errors import AiVideoError
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    ToolIdentity,
)
from ai_video.production.registry import registry_semantic_sha256


def _png(size: tuple[int, int], color=(12, 34, 56), mode="RGB") -> bytes:
    image = Image.new(mode, size, color)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _palette_png() -> bytes:
    image = Image.new("P", (4, 4), 0)
    image.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _loaded(root: Path, payload: bytes | None = None):
    payload = payload or _png((9, 10))
    relative = Path("assets/files") / f"{sha256(payload).hexdigest()}.png"
    source = root / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(payload)
    measured = Image.open(BytesIO(payload))
    record = AssetRecord(
        asset_id="scene-original",
        asset_type=AssetType.IMAGE,
        artifact_path=relative,
        sha256=sha256(payload).hexdigest(),
        size_bytes=len(payload),
        mime_type="image/png",
        width=measured.width,
        height=measured.height,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture-local-import", version="1"),
        input_fingerprint="0" * 64,
        creation_receipt_id="fixture-receipt",
        usage_license="fixture-license",
    )
    registry = AssetRegistrySnapshot(
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=(record,),
    )
    registry_hash = registry_semantic_sha256(registry)
    registry = registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    loaded = SimpleNamespace(
        root=root,
        registry=registry,
        manifest=SimpleNamespace(
            active_registry=SimpleNamespace(
                revision_id=registry_hash, content_hash=registry_hash
            )
        ),
        asset_paths={record.asset_id: source},
    )
    return loaded, record, payload


def _persist_for_loader_verification(root: Path, loaded, bundle) -> None:
    for artifact in bundle.artifacts:
        destination = root / artifact.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(artifact.payload)
    loaded.registry = bundle.registry
    loaded.manifest.active_registry = SimpleNamespace(
        revision_id=bundle.registry.revision_id,
        content_hash=bundle.registry.content_hash,
    )
    loaded.asset_paths.update({
        record.asset_id: root / record.artifact_path for record in bundle.assets
    })


def test_pad_preserves_exact_source_pixels_and_verifiable_registry_lineage(tmp_path):
    loaded, source_record, source_bytes = _loaded(tmp_path)
    source_path = loaded.asset_paths[source_record.asset_id]
    before = source_path.read_bytes()
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=source_record.asset_id,
        source_sha256=source_record.sha256,
        new_asset_id="scene-padded",
        usage_license="licensed-for-this-test",
        fill_rgb=(255, 0, 255),
    )

    bundle = prepare_canvas_image_assets(loaded, [operation])

    assert source_path.read_bytes() == before == source_bytes
    assert len(bundle.registry.assets) == 2
    assert bundle.registry.assets[0] == source_record
    derived = bundle.assets[0]
    assert derived.asset_id == "scene-padded"
    assert derived.input_artifact_ids == (source_record.asset_id,)
    assert derived.usage_license == "licensed-for-this-test"
    assert derived.tool.name == "canvas-local-image-preparation"
    assert derived.source_kind == AssetSourceKind.DERIVED
    assert derived.width == 16 and derived.height == 16
    assert not (tmp_path / derived.artifact_path).exists()
    assert len(bundle.artifacts) == 2  # image bytes and content-addressed receipt

    output = next(a.payload for a in bundle.artifacts if a.relative_path == derived.artifact_path)
    image = Image.open(BytesIO(output))
    assert image.mode == "RGB"
    assert image.size == (16, 16)
    assert image.crop((0, 0, 9, 10)).tobytes() == Image.open(BytesIO(source_bytes)).tobytes()
    assert image.getpixel((15, 15)) == (255, 0, 255)
    receipt = bundle.receipts[0]
    assert receipt.source_sha256 == source_record.sha256
    assert receipt.operation.kind == "pad"
    assert receipt.output_sha256 == derived.sha256
    assert receipt.output_origin == "local_pixel_preparation"
    assert not (tmp_path / "evidence").exists()
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


def test_crop_is_pixel_exact_and_does_not_resize(tmp_path):
    loaded, record, source_bytes = _loaded(tmp_path)
    operation = CanvasImagePreparationOperation(
        kind="crop",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="scene-cropped",
        usage_license="explicit-license",
        crop_box=(2, 3, 8, 9),
    )

    bundle = prepare_canvas_image_assets(loaded, [operation])

    derived = bundle.assets[0]
    output = next(a.payload for a in bundle.artifacts if a.relative_path == derived.artifact_path)
    image = Image.open(BytesIO(output))
    source = Image.open(BytesIO(source_bytes))
    assert image.size == (6, 6)
    assert image.tobytes() == source.crop((2, 3, 8, 9)).tobytes()
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


@pytest.mark.parametrize("mode,color", [("RGB", (12, 34, 56)), ("RGBA", (12, 34, 56, 255))])
def test_letterbox_centers_exact_pixels_and_reopens_lineage(tmp_path, mode, color):
    loaded, record, original = _loaded(tmp_path, _png((9, 10), color, mode))
    operation = CanvasImagePreparationOperation(kind="letterbox",
        source_asset_id=record.asset_id, source_sha256=record.sha256,
        new_asset_id="presentation-matte", usage_license="fixture",
        canvas_size=(16, 27), fill_rgb=(231, 213, 172))
    bundle = prepare_canvas_image_assets(loaded, [operation])
    image = Image.open(BytesIO(next(a.payload for a in bundle.artifacts
        if a.relative_path == bundle.assets[0].artifact_path)))
    assert image.size == (16, 27)
    assert image.crop((3, 8, 12, 18)).tobytes() == Image.open(BytesIO(original)).tobytes()
    assert image.getpixel((0, 0)) == ((231, 213, 172, 255) if mode == "RGBA" else (231, 213, 172))
    assert loaded.asset_paths[record.asset_id].read_bytes() == original
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


@pytest.mark.parametrize("size", [(8, 27), (16, 9), (0, 10), (100000, 100000)])
def test_letterbox_rejects_cropping_or_unbounded_canvas_before_writes(tmp_path, size):
    loaded, record, _ = _loaded(tmp_path)
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(loaded, [dict(kind="letterbox",
            source_asset_id=record.asset_id, source_sha256=record.sha256,
            new_asset_id="invalid-matte", usage_license="fixture",
            canvas_size=size, fill_rgb=(0, 0, 0))])
    assert len(list((tmp_path / "assets/files").iterdir())) == 1


def test_accepts_fully_opaque_rgba_source(tmp_path):
    loaded, record, _ = _loaded(tmp_path, _png((9, 10), (12, 34, 56, 255), "RGBA"))
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="opaque-rgba-pad",
        usage_license="explicit-license",
        fill_rgb=(0, 0, 0),
    )
    bundle = prepare_canvas_image_assets(loaded, [operation])
    output = Image.open(BytesIO(bundle.artifacts[0].payload))
    assert output.mode == "RGBA" and output.size == (16, 16)
    assert output.getpixel((0, 0)) == (12, 34, 56, 255)
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


def test_rejects_animated_png_source_instead_of_silently_taking_first_frame(tmp_path):
    stream = BytesIO()
    Image.new("RGB", (8, 8), (0, 0, 0)).save(stream, format="PNG", save_all=True,
        append_images=[Image.new("RGB", (8, 8), (255, 255, 255))], duration=100, loop=0)
    loaded, record, _ = _loaded(tmp_path, stream.getvalue())
    operation = CanvasImagePreparationOperation(kind="pad", source_asset_id=record.asset_id,
        source_sha256=record.sha256, new_asset_id="animated-derived", usage_license="fixture",
        fill_rgb=(0, 0, 0))
    with pytest.raises(ValueError, match="single-frame"):
        prepare_canvas_image_assets(loaded, [operation])


def test_binary_mask_is_binary_and_protects_unselected_pixels(tmp_path):
    loaded, record, _ = _loaded(tmp_path)
    operation = CanvasImagePreparationOperation(
        kind="binary_mask",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="edit-mask",
        usage_license="explicit-mask-license",
        canvas_size=(16, 16),
        rectangles=((2, 2, 7, 7),),
        polygons=(),
    )

    bundle = prepare_canvas_image_assets(loaded, [operation])

    derived = bundle.assets[0]
    output = next(a.payload for a in bundle.artifacts if a.relative_path == derived.artifact_path)
    mask = Image.open(BytesIO(output))
    assert mask.mode == "L" and mask.size == (16, 16)
    assert set(mask.tobytes()) == {0, 255}
    assert mask.getpixel((2, 2)) == 255
    assert mask.getpixel((7, 7)) == 0
    assert mask.getpixel((15, 15)) == 0
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


def test_binary_mask_supports_explicit_polygon_pixels(tmp_path):
    loaded, record, _ = _loaded(tmp_path)
    operation = CanvasImagePreparationOperation(
        kind="binary_mask",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="polygon-mask",
        usage_license="explicit-mask-license",
        canvas_size=(16, 16),
        rectangles=(),
        polygons=(((2, 2), (6, 2), (2, 6)),),
    )
    bundle = prepare_canvas_image_assets(loaded, [operation])
    mask = Image.open(BytesIO(bundle.artifacts[0].payload))
    assert mask.mode == "L" and mask.getpixel((3, 3)) == 255
    assert mask.getpixel((6, 6)) == 0
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    verify_canvas_prepared_image_assets(loaded)


@pytest.mark.parametrize(
    "overrides",
    [
        {"rectangles": (), "polygons": ()},
        {"rectangles": ((0, 0, 8, 8),), "polygons": ()},
        {"rectangles": ((-1, 0, 2, 3),), "polygons": ()},
        {"canvas_size": (24, 16)},
    ],
)
def test_rejects_empty_full_or_invalid_mask_geometry(tmp_path, overrides):
    loaded, record, _ = _loaded(tmp_path, _png((8, 8)))
    values = {
        "kind": "binary_mask",
        "source_asset_id": record.asset_id,
        "source_sha256": record.sha256,
        "new_asset_id": "bad-mask",
        "usage_license": "explicit-license",
        "canvas_size": (8, 8),
        "rectangles": ((2, 2, 7, 7),),
        "polygons": (),
    }
    values.update(overrides)
    with pytest.raises(ValueError):
        operation = CanvasImagePreparationOperation(**values)
        prepare_canvas_image_assets(loaded, [operation])


def test_rejects_stale_hash_unknown_id_and_registry_collision(tmp_path):
    loaded, record, _ = _loaded(tmp_path)
    base = {
        "kind": "pad",
        "source_asset_id": record.asset_id,
        "source_sha256": record.sha256,
        "new_asset_id": "derived",
        "usage_license": "explicit-license",
        "fill_rgb": (0, 0, 0),
    }
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(
            loaded,
            [CanvasImagePreparationOperation(**{**base, "source_sha256": "f" * 64})],
        )
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(
            loaded,
            [CanvasImagePreparationOperation(**{**base, "source_asset_id": "missing"})],
        )
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(
            loaded,
            [CanvasImagePreparationOperation(**{**base, "new_asset_id": record.asset_id})],
        )


@pytest.mark.parametrize(
    "payload",
    [
        _palette_png(),
        _png((4, 4), (1, 2, 3, 4), "RGBA"),
        _png((4, 4), 128, "I;16"),
    ],
)
def test_rejects_palette_transparent_or_sixteen_bit_source_png(tmp_path, payload):
    loaded, record, _ = _loaded(tmp_path, payload)
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="prepared",
        usage_license="explicit-license",
        fill_rgb=(0, 0, 0),
    )
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(loaded, [operation])


def test_rejects_crc_corruption_and_escaping_loaded_path(tmp_path):
    valid = _png((4, 4))
    corrupt = bytearray(valid)
    corrupt[-1] ^= 1
    loaded, record, _ = _loaded(tmp_path, bytes(corrupt))
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="prepared",
        usage_license="explicit-license",
        fill_rgb=(0, 0, 0),
    )
    with pytest.raises(AiVideoError):
        prepare_canvas_image_assets(loaded, [operation])

    escaped, escaped_record, _ = _loaded(tmp_path / "escaped", valid)
    escaped.asset_paths[escaped_record.asset_id] = tmp_path.parent / "outside.png"
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(escaped, [
            CanvasImagePreparationOperation(
                kind="pad",
                source_asset_id=escaped_record.asset_id,
                source_sha256=escaped_record.sha256,
                new_asset_id="prepared",
                usage_license="explicit-license",
                fill_rgb=(0, 0, 0),
            )
        ])


def test_rejects_symlinked_source_path(tmp_path):
    loaded, record, payload = _loaded(tmp_path)
    source_path = loaded.asset_paths[record.asset_id]
    source_path.unlink()
    elsewhere = tmp_path / "elsewhere.png"
    elsewhere.write_bytes(payload)
    source_path.symlink_to(elsewhere)
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="prepared",
        usage_license="explicit-license",
        fill_rgb=(0, 0, 0),
    )
    with pytest.raises(ValueError):
        prepare_canvas_image_assets(loaded, [operation])


@pytest.mark.parametrize("mutated", ["source", "output", "receipt"])
def test_verifier_detects_source_output_or_receipt_mutation(tmp_path, mutated):
    loaded, record, _ = _loaded(tmp_path)
    operation = CanvasImagePreparationOperation(
        kind="pad",
        source_asset_id=record.asset_id,
        source_sha256=record.sha256,
        new_asset_id="scene-padded",
        usage_license="explicit-license",
        fill_rgb=(0, 0, 0),
    )
    bundle = prepare_canvas_image_assets(loaded, [operation])
    _persist_for_loader_verification(tmp_path, loaded, bundle)
    output_record = bundle.assets[0]
    output_path = tmp_path / output_record.artifact_path
    verify_canvas_prepared_image_assets(loaded)

    if mutated == "source":
        loaded.asset_paths[record.asset_id].write_bytes(b"changed")
    elif mutated == "output":
        output_path.write_bytes(b"changed")
    else:
        receipt_path = tmp_path / f"evidence/canvas-image-preparation/{bundle.receipts[0].content_hash}.json"
        receipt_path.write_bytes(b"{}")
    with pytest.raises(ValueError):
        verify_canvas_prepared_image_assets(loaded)
