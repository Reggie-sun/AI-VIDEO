"""Deterministic, local pixel preparation for explicitly selected Registry images."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from typing import Literal, Sequence

from PIL import Image, ImageDraw
from pydantic import ConfigDict, Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256
from ai_video.production.image_bytes import MeasuredPng, measure_png_bytes
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    LoadedProductionProject,
    ToolIdentity,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_image_asset_path,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact


_TOOL = ToolIdentity(name="canvas-local-image-preparation", version="1")
_RECEIPT_PREFIX = "canvas-image-preparation:"
_RECEIPT_DIRECTORY = Path("evidence/canvas-image-preparation")


class CanvasImagePreparationOperation(StrictModel):
    """One explicit no-resize pixel operation over a current Registry image."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["pad", "crop", "binary_mask"]
    source_asset_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    new_asset_id: str = Field(min_length=1)
    usage_license: str = Field(min_length=1)
    fill_rgb: tuple[int, int, int] | None = None
    crop_box: tuple[int, int, int, int] | None = None
    canvas_size: tuple[int, int] | None = None
    rectangles: tuple[tuple[int, int, int, int], ...] = ()
    polygons: tuple[tuple[tuple[int, int], ...], ...] = ()

    @model_validator(mode="after")
    def _require_kind_parameters(self) -> "CanvasImagePreparationOperation":
        if self.kind == "pad":
            if self.fill_rgb is None or self.crop_box is not None or self.canvas_size is not None:
                raise ValueError("pad requires fill_rgb and accepts no crop or mask geometry")
            if self.rectangles or self.polygons:
                raise ValueError("pad does not accept mask geometry")
            if any(value < 0 or value > 255 for value in self.fill_rgb):
                raise ValueError("pad fill_rgb values must be bytes")
        elif self.kind == "crop":
            if self.crop_box is None or self.fill_rgb is not None or self.canvas_size is not None:
                raise ValueError("crop requires crop_box and accepts no pad or mask geometry")
            if self.rectangles or self.polygons:
                raise ValueError("crop does not accept mask geometry")
        else:
            if self.canvas_size is None or self.fill_rgb is not None or self.crop_box is not None:
                raise ValueError("binary_mask requires canvas_size and accepts no pad or crop geometry")
            if not self.rectangles and not self.polygons:
                raise ValueError("binary_mask requires at least one rectangle or polygon")
        return self


class CanvasImagePreparationReceipt(StrictModel):
    """Content-addressed evidence for one deterministic derived PNG."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: Literal["canvas-image-preparation/1"] = "canvas-image-preparation/1"
    source_asset_id: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_size_bytes: int = Field(gt=0)
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    source_artifact_path: Path
    source_asset_record_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    operation: CanvasImagePreparationOperation
    input_artifact_ids: tuple[str, ...]
    usage_license: str
    tool: ToolIdentity
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_asset_id: str
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_size_bytes: int = Field(gt=0)
    output_width: int = Field(gt=0)
    output_height: int = Field(gt=0)
    output_mime_type: Literal["image/png"] = "image/png"
    output_artifact_path: Path
    output_origin: Literal["local_pixel_preparation"] = "local_pixel_preparation"
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _sealed_identity(self) -> "CanvasImagePreparationReceipt":
        if self.tool != _TOOL:
            raise ValueError("preparation receipt tool identity is not supported")
        if self.input_artifact_ids != (self.source_asset_id,):
            raise ValueError("derived image must retain its source Registry asset identity")
        if self.operation.source_asset_id != self.source_asset_id:
            raise ValueError("receipt operation source differs from its source binding")
        if self.operation.source_sha256 != self.source_sha256:
            raise ValueError("receipt operation SHA differs from its source binding")
        if self.operation.new_asset_id != self.output_asset_id:
            raise ValueError("receipt operation asset id differs from output binding")
        if self.operation.usage_license != self.usage_license:
            raise ValueError("receipt license differs from operation license")
        if self.output_artifact_path != canonical_image_asset_path(self.output_sha256):
            raise ValueError("prepared image path must be canonical and content-addressed")
        if self.content_hash != canonical_sha256(self):
            raise ValueError("image preparation receipt content hash is invalid")
        return self


@dataclass(frozen=True)
class CanvasImagePreparationBundle:
    registry: AssetRegistrySnapshot
    assets: tuple[AssetRecord, ...]
    artifacts: tuple[PreparedArtifact, ...]
    receipts: tuple[CanvasImagePreparationReceipt, ...]


def _receipt_path(content_hash: str) -> Path:
    return _RECEIPT_DIRECTORY / f"{content_hash}.json"


def _canonical_json_bytes(value: StrictModel) -> bytes:
    return json.dumps(
        value.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _receipt_from_json(value: dict) -> CanvasImagePreparationReceipt:
    data = dict(value)
    data["source_artifact_path"] = Path(data["source_artifact_path"])
    data["output_artifact_path"] = Path(data["output_artifact_path"])
    data["input_artifact_ids"] = tuple(data["input_artifact_ids"])
    operation = dict(data["operation"])
    for key in ("fill_rgb", "crop_box", "canvas_size"):
        if operation.get(key) is not None:
            operation[key] = tuple(operation[key])
    operation["rectangles"] = tuple(tuple(item) for item in operation.get("rectangles", ()))
    operation["polygons"] = tuple(
        tuple(tuple(point) for point in polygon)
        for polygon in operation.get("polygons", ())
    )
    data["operation"] = CanvasImagePreparationOperation.model_validate(operation)
    return CanvasImagePreparationReceipt.model_validate(data)


def _source_path(loaded: LoadedProductionProject, record: AssetRecord, root: Path) -> Path:
    relative = record.artifact_path
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"source asset path is not contained: {record.asset_id}")
    expected = root / relative
    mapped = loaded.asset_paths.get(record.asset_id)
    if mapped is None:
        raise ValueError(f"source asset has no loaded path: {record.asset_id}")
    try:
        if Path(mapped).resolve(strict=True) != expected.resolve(strict=True):
            raise ValueError(f"loaded source path differs from Registry: {record.asset_id}")
    except OSError as exc:
        raise ValueError(f"source asset path is unavailable: {record.asset_id}") from exc
    return expected


def _read_png(payload: bytes, *, allow_gray: bool = False) -> tuple[Image.Image, MeasuredPng]:
    measured = measure_png_bytes(payload)
    allowed_types = {2, 6, 0} if allow_gray else {2, 6}
    if measured.bit_depth != 8 or measured.color_type not in allowed_types:
        raise ValueError("image preparation accepts only 8-bit RGB/RGBA PNG sources")
    try:
        with Image.open(BytesIO(payload)) as opened:
            if getattr(opened, "n_frames", 1) != 1:
                raise ValueError("image preparation requires single-frame PNG sources")
            if opened.format != "PNG" or opened.mode not in ({"RGB", "RGBA", "L"} if allow_gray else {"RGB", "RGBA"}):
                raise ValueError("image preparation rejects palette, grayscale source, and non-PNG images")
            if "transparency" in opened.info:
                raise ValueError("image preparation rejects PNG transparency metadata")
            if opened.size != (measured.width, measured.height):
                raise ValueError("PNG dimensions differ from measured IHDR")
            orientation = opened.getexif().get(274)
            if orientation not in (None, 1):
                raise ValueError("image preparation rejects EXIF-oriented PNGs")
            opened.load()
            image = opened.copy()
    except (OSError, Image.DecompressionBombError) as exc:
        raise ValueError("image preparation could not decode the PNG source") from exc
    if image.mode == "RGBA" and image.getchannel("A").getextrema() != (255, 255):
        raise ValueError("image preparation requires opaque RGBA pixels")
    return image, measured


def _minimal_padded_size(width: int, height: int) -> tuple[int, int]:
    return ((width + 7) // 8 * 8, (height + 7) // 8 * 8)


def _apply_operation(
    source: Image.Image,
    operation: CanvasImagePreparationOperation,
) -> Image.Image:
    width, height = source.size
    if operation.kind == "pad":
        output_size = _minimal_padded_size(width, height)
        fill = operation.fill_rgb
        assert fill is not None
        color = (*fill, 255) if source.mode == "RGBA" else fill
        output = Image.new(source.mode, output_size, color)
        output.paste(source, (0, 0))
        return output
    if operation.kind == "crop":
        box = operation.crop_box
        assert box is not None
        left, top, right, bottom = box
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("crop_box must be a non-empty half-open box inside the source")
        return source.crop(box)

    canvas_size = operation.canvas_size
    assert canvas_size is not None
    if canvas_size != _minimal_padded_size(width, height):
        raise ValueError("binary mask canvas must be the source size with only minimal right/bottom 8-pixel padding")
    mask = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(mask)
    for left, top, right, bottom in operation.rectangles:
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("mask rectangles must be non-empty half-open boxes inside the source")
        draw.rectangle((left, top, right - 1, bottom - 1), fill=255)
    for polygon in operation.polygons:
        if len(polygon) < 3 or any(not (0 <= x < width and 0 <= y < height) for x, y in polygon):
            raise ValueError("mask polygons require three or more source-bounded pixel vertices")
        area2 = sum(
            polygon[index][0] * polygon[(index + 1) % len(polygon)][1]
            - polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
            for index in range(len(polygon))
        )
        if area2 == 0:
            raise ValueError("mask polygons must enclose a non-zero area")
        draw.polygon(polygon, fill=255)
    if mask.getextrema() != (0, 255):
        raise ValueError("binary mask must contain both protected black and editable white pixels")
    return mask


def _encode_png(image: Image.Image) -> bytes:
    stream = BytesIO()
    image.save(stream, format="PNG", compress_level=9, optimize=False)
    return stream.getvalue()


def _asset_from_receipt(receipt: CanvasImagePreparationReceipt) -> AssetRecord:
    return AssetRecord(
        asset_id=receipt.output_asset_id,
        asset_type=AssetType.IMAGE,
        artifact_path=receipt.output_artifact_path,
        sha256=receipt.output_sha256,
        size_bytes=receipt.output_size_bytes,
        mime_type=receipt.output_mime_type,
        width=receipt.output_width,
        height=receipt.output_height,
        source_kind=AssetSourceKind.DERIVED,
        tool=receipt.tool,
        input_artifact_ids=receipt.input_artifact_ids,
        input_fingerprint=receipt.input_fingerprint,
        creation_receipt_id=f"{_RECEIPT_PREFIX}{receipt.content_hash}",
        usage_license=receipt.usage_license,
    )


def prepare_canvas_image_assets(
    loaded: LoadedProductionProject,
    operations: Sequence[CanvasImagePreparationOperation | dict[str, object]],
) -> CanvasImagePreparationBundle:
    """Prepare derived PNGs without writes; a canonical committer owns persistence."""
    if not operations:
        raise ValueError("at least one image preparation operation is required")
    registry = loaded.registry
    current_hash = registry_semantic_sha256(registry)
    active = loaded.manifest.active_registry
    if (
        registry.revision_id != current_hash
        or registry.content_hash != current_hash
        or active.revision_id != registry.revision_id
        or active.content_hash != registry.content_hash
    ):
        raise ValueError("preparation requires the current active sealed Registry revision")
    records = {record.asset_id: record for record in registry.assets}
    if len(records) != len(registry.assets):
        raise ValueError("current Registry contains duplicate asset ids")
    parsed = tuple(
        operation
        if isinstance(operation, CanvasImagePreparationOperation)
        else CanvasImagePreparationOperation.model_validate(operation)
        for operation in operations
    )
    new_ids = [operation.new_asset_id for operation in parsed]
    if len(set(new_ids)) != len(new_ids) or any(asset_id in records for asset_id in new_ids):
        raise ValueError("new image asset ids must be unique and absent from the current Registry")

    root = Path(loaded.root).resolve(strict=True)
    new_records: list[AssetRecord] = []
    receipts: list[CanvasImagePreparationReceipt] = []
    artifacts_by_path: dict[Path, PreparedArtifact] = {}
    for operation in parsed:
        source_record = records.get(operation.source_asset_id)
        if source_record is None or source_record.asset_type != AssetType.IMAGE:
            raise ValueError("source_asset_id must identify an existing Registry image")
        if source_record.sha256 != operation.source_sha256:
            raise ValueError("selected source SHA differs from its current Registry record")
        source_path = _source_path(loaded, source_record, root)
        raw = _read_regular_file_nofollow(source_path, contained_by=root)
        if raw.file_sha256 != source_record.sha256 or raw.size_bytes != source_record.size_bytes:
            raise ValueError("source PNG bytes differ from the selected Registry identity")
        source, measured = _read_png(raw.data)
        if (source.size != (source_record.width, source_record.height)
                or source_record.mime_type != "image/png"):
            raise ValueError("source PNG geometry or MIME differs from the Registry record")

        output = _apply_operation(source, operation)
        output_bytes = _encode_png(output)
        output_measured = measure_png_bytes(output_bytes)
        if (output_measured.width, output_measured.height) != output.size or output_measured.bit_depth != 8:
            raise ValueError("prepared PNG geometry or bit depth differs from the pixel operation")
        output_sha = output_measured.sha256
        output_path = canonical_image_asset_path(output_sha)
        source_record_hash = canonical_sha256(source_record)
        fingerprint = canonical_sha256({
            "kind": "canvas-image-preparation-input/1",
            "source_asset_record_sha256": source_record_hash,
            "operation": operation.model_dump(mode="json"),
            "tool": _TOOL.model_dump(mode="json"),
        })
        receipt_data = {
            "kind": "canvas-image-preparation/1",
            "source_asset_id": source_record.asset_id,
            "source_sha256": source_record.sha256,
            "source_size_bytes": measured.size_bytes,
            "source_width": measured.width,
            "source_height": measured.height,
            "source_artifact_path": source_record.artifact_path,
            "source_asset_record_sha256": source_record_hash,
            "operation": operation,
            "input_artifact_ids": (source_record.asset_id,),
            "usage_license": operation.usage_license,
            "tool": _TOOL,
            "input_fingerprint": fingerprint,
            "output_asset_id": operation.new_asset_id,
            "output_sha256": output_sha,
            "output_size_bytes": len(output_bytes),
            "output_width": output.width,
            "output_height": output.height,
            "output_mime_type": "image/png",
            "output_artifact_path": output_path,
            "output_origin": "local_pixel_preparation",
        }
        provisional_receipt = CanvasImagePreparationReceipt.model_construct(
            **receipt_data, content_hash="0" * 64
        )
        receipt_data["content_hash"] = canonical_sha256(provisional_receipt)
        receipt = CanvasImagePreparationReceipt.model_validate(receipt_data)
        new_records.append(_asset_from_receipt(receipt))
        receipts.append(receipt)
        image_artifact = PreparedArtifact(output_path, output_bytes, sha256(output_bytes).hexdigest())
        prior = artifacts_by_path.get(output_path)
        if prior is not None and prior.payload != output_bytes:
            raise ValueError("content-addressed image path collision has different bytes")
        artifacts_by_path[output_path] = image_artifact
        receipt_path = _receipt_path(receipt.content_hash)
        receipt_bytes = _canonical_json_bytes(receipt)
        artifacts_by_path[receipt_path] = PreparedArtifact(
            receipt_path, receipt_bytes, sha256(receipt_bytes).hexdigest()
        )

    merged = AssetRegistrySnapshot(
        schema_version=registry.schema_version,
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(sorted((*registry.assets, *new_records), key=lambda asset: asset.asset_id)),
    )
    merged_hash = registry_semantic_sha256(merged)
    merged = merged.model_copy(update={"revision_id": merged_hash, "content_hash": merged_hash})
    return CanvasImagePreparationBundle(
        registry=merged,
        assets=tuple(new_records),
        artifacts=tuple(artifacts_by_path[path] for path in sorted(artifacts_by_path)),
        receipts=tuple(receipts),
    )


def verify_canvas_prepared_image_assets(bundle: LoadedProductionProject) -> None:
    """Read-only verification of this tool's committed assets in a loaded project."""
    registry = bundle.registry
    registry_hash = registry_semantic_sha256(registry)
    active = bundle.manifest.active_registry
    if (registry_hash != registry.content_hash or registry_hash != registry.revision_id
            or active.content_hash != registry.content_hash
            or active.revision_id != registry.revision_id):
        raise ValueError("prepared image evidence is not in the current active Registry")
    records = {record.asset_id: record for record in registry.assets}
    if len(records) != len(registry.assets):
        raise ValueError("active Registry contains duplicate asset ids")
    root = Path(bundle.root).resolve(strict=True)
    for record in registry.assets:
        marked = record.tool.name == _TOOL.name or record.creation_receipt_id.startswith(_RECEIPT_PREFIX)
        if not marked:
            continue
        if record.tool != _TOOL or record.source_kind != AssetSourceKind.DERIVED:
            raise ValueError(f"prepared image tool identity is invalid: {record.asset_id}")
        if record.artifact_path != canonical_image_asset_path(record.sha256):
            raise ValueError(f"prepared image path is not canonical: {record.asset_id}")
        if not record.creation_receipt_id.startswith(_RECEIPT_PREFIX):
            raise ValueError(f"prepared image receipt pointer is missing: {record.asset_id}")
        receipt_path = _receipt_path_for_asset(record)
        receipt_raw = _read_regular_file_nofollow(root / receipt_path, contained_by=root)
        try:
            receipt_json = json.loads(receipt_raw.data)
            receipt = _receipt_from_json(receipt_json)
        except Exception as exc:
            raise ValueError(f"prepared image receipt is invalid: {record.asset_id}") from exc
        if _canonical_json_bytes(receipt) != receipt_raw.data:
            raise ValueError(f"prepared image receipt is not canonically serialized: {record.asset_id}")
        if receipt.content_hash != receipt_path.stem:
            raise ValueError(f"prepared image receipt path does not match its content hash: {record.asset_id}")
        reconstructed = _asset_from_receipt(receipt)
        if reconstructed != record:
            raise ValueError(f"prepared image AssetRecord differs from its receipt: {record.asset_id}")
        expected_fingerprint = canonical_sha256({
            "kind": "canvas-image-preparation-input/1",
            "source_asset_record_sha256": receipt.source_asset_record_sha256,
            "operation": receipt.operation.model_dump(mode="json"),
            "tool": _TOOL.model_dump(mode="json"),
        })
        if record.input_fingerprint != receipt.input_fingerprint or receipt.input_fingerprint != expected_fingerprint:
            raise ValueError(f"prepared image operation fingerprint differs: {record.asset_id}")

        source_record = records.get(receipt.source_asset_id)
        if source_record is None or canonical_sha256(source_record) != receipt.source_asset_record_sha256:
            raise ValueError(f"prepared image source Registry identity differs: {record.asset_id}")
        if (source_record.artifact_path != receipt.source_artifact_path
                or source_record.sha256 != receipt.source_sha256
                or source_record.size_bytes != receipt.source_size_bytes
                or source_record.width != receipt.source_width
                or source_record.height != receipt.source_height):
            raise ValueError(f"prepared image source AssetRecord differs from receipt: {record.asset_id}")
        source_path = _source_path(bundle, source_record, root)
        source_raw = _read_regular_file_nofollow(source_path, contained_by=root)
        if source_raw.file_sha256 != receipt.source_sha256 or source_raw.size_bytes != receipt.source_size_bytes:
            raise ValueError(f"prepared image source bytes differ from receipt: {record.asset_id}")
        source, source_measured = _read_png(source_raw.data)
        if (source_measured.width != receipt.source_width
                or source_measured.height != receipt.source_height
                or source_record.sha256 != receipt.source_sha256):
            raise ValueError(f"prepared image source geometry differs from receipt: {record.asset_id}")

        output_path = root / record.artifact_path
        output_raw = _read_regular_file_nofollow(output_path, contained_by=root)
        if output_raw.file_sha256 != record.sha256 or output_raw.size_bytes != record.size_bytes:
            raise ValueError(f"prepared image output bytes differ from Registry: {record.asset_id}")
        expected = _apply_operation(source, receipt.operation)
        actual, measured = _read_png(output_raw.data, allow_gray=receipt.operation.kind == "binary_mask")
        if (actual.size != expected.size or actual.mode != expected.mode
                or actual.tobytes() != expected.tobytes()
                or measured.width != record.width or measured.height != record.height):
            raise ValueError(f"prepared image pixels do not reproduce the sealed operation: {record.asset_id}")


def _receipt_path_for_asset(record: AssetRecord) -> Path:
    # The receipt hash is bound into the content-addressed path and checked after reading.
    prefix = record.creation_receipt_id
    if not prefix.startswith(_RECEIPT_PREFIX):
        raise ValueError(f"prepared image receipt pointer is malformed: {record.asset_id}")
    content_hash = prefix[len(_RECEIPT_PREFIX):]
    if len(content_hash) != 64 or any(char not in "0123456789abcdef" for char in content_hash):
        raise ValueError(f"prepared image receipt identity is malformed: {record.asset_id}")
    return _receipt_path(content_hash)
