from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    ToolIdentity,
)
from ai_video.production.registry import load_asset_registry, registry_semantic_sha256

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def make_record(root: Path, artifact_path: str | Path = "assets/files/hero.png") -> AssetRecord:
    stored = Path(artifact_path)
    target = root / stored if not stored.is_absolute() and ".." not in stored.parts else None
    payload = b"hero-image"
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        size = target.stat().st_size
        digest = sha256_file(target)
    else:
        size = len(payload)
        digest = ZERO_HASH
    return AssetRecord(
        asset_id="image-hero-1",
        asset_type=AssetType.IMAGE,
        artifact_path=stored,
        sha256=digest,
        size_bytes=size,
        mime_type="image/png",
        width=1,
        height=1,
        source_kind=AssetSourceKind.IMPORTED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint=ZERO_HASH,
        creation_receipt_id="receipt-image-hero-1",
        usage_license="test-only",
    )


def write_registry(
    root: Path,
    *,
    artifact_path: str | Path = "assets/files/hero.png",
    records: tuple[AssetRecord, ...] | None = None,
    record_update: dict[str, object] | None = None,
    snapshot_update: dict[str, object] | None = None,
) -> Path:
    if records is None:
        record = make_record(root, artifact_path)
        if record_update:
            record = record.model_copy(update=record_update)
        records = (record,)
    snapshot = AssetRegistrySnapshot(
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=records,
    )
    digest = registry_semantic_sha256(snapshot)
    snapshot = snapshot.model_copy(update={"revision_id": digest, "content_hash": digest})
    if snapshot_update:
        snapshot = snapshot.model_copy(update=snapshot_update)
    path = root / f"assets/registry.{snapshot.revision_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
    return path


def load(path: Path, root: Path):
    return load_asset_registry(path.relative_to(root), root, root / "assets/files")


def test_registry_loads_verified_local_asset(tmp_path):
    path = write_registry(tmp_path)
    snapshot, asset_paths = load(path, tmp_path)
    assert snapshot.assets[0].asset_id == "image-hero-1"
    assert not snapshot.assets[0].artifact_path.is_absolute()
    assert asset_paths["image-hero-1"].is_absolute()
    assert asset_paths["image-hero-1"].is_relative_to(tmp_path.resolve())


@pytest.mark.parametrize("stored", ["/tmp/outside.png", "../outside.png"])
def test_registry_rejects_unsafe_asset_paths(tmp_path, stored):
    path = write_registry(tmp_path, artifact_path=stored)
    with pytest.raises(AiVideoError) as exc:
        load(path, tmp_path)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
    assert "unsafe" in exc.value.user_message


def test_registry_rejects_duplicate_asset_ids(tmp_path):
    record = make_record(tmp_path)
    path = write_registry(tmp_path, records=(record, record))
    with pytest.raises(AiVideoError, match="duplicate asset_id"):
        load(path, tmp_path)


def test_registry_rejects_filename_revision_mismatch(tmp_path):
    path = write_registry(tmp_path)
    wrong_path = path.with_name(f"registry.{ONE_HASH}.json")
    path.rename(wrong_path)
    with pytest.raises(AiVideoError, match="filename"):
        load(wrong_path, tmp_path)


def test_registry_rejects_semantic_hash_mismatch(tmp_path):
    path = write_registry(
        tmp_path,
        snapshot_update={"revision_id": ONE_HASH, "content_hash": ONE_HASH},
    )
    with pytest.raises(AiVideoError, match="content hash"):
        load(path, tmp_path)


def test_registry_rejects_revision_that_differs_from_content_hash(tmp_path):
    path = write_registry(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["revision_id"] = ONE_HASH
    wrong_path = path.with_name(f"registry.{ONE_HASH}.json")
    wrong_path.write_text(json.dumps(data), encoding="utf-8")
    path.unlink()
    with pytest.raises(AiVideoError, match="must equal"):
        load(wrong_path, tmp_path)


def test_registry_rejects_missing_asset_file(tmp_path):
    path = write_registry(tmp_path)
    (tmp_path / "assets/files/hero.png").unlink()
    with pytest.raises(AiVideoError, match="does not exist"):
        load(path, tmp_path)


@pytest.mark.parametrize(
    ("record_update", "message"),
    [({"size_bytes": 999}, "size mismatch"), ({"sha256": ONE_HASH}, "hash mismatch")],
)
def test_registry_rejects_wrong_file_evidence(tmp_path, record_update, message):
    path = write_registry(tmp_path, record_update=record_update)
    with pytest.raises(AiVideoError, match=message):
        load(path, tmp_path)


def test_registry_file_symlink_cannot_escape_project_root(tmp_path):
    root = tmp_path / "project"
    path = write_registry(root)
    outside = tmp_path / "outside-registry.json"
    path.rename(outside)
    path.symlink_to(outside)
    with pytest.raises(AiVideoError) as exc:
        load(path, root)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
    assert "unsafe" in exc.value.user_message


def test_asset_symlink_cannot_escape_asset_root(tmp_path):
    root = tmp_path / "project"
    path = write_registry(root)
    asset = root / "assets/files/hero.png"
    outside = tmp_path / "outside.png"
    asset.rename(outside)
    asset.symlink_to(outside)
    with pytest.raises(AiVideoError, match="unsafe"):
        load(path, root)


def test_internal_asset_symlink_resolves_inside_asset_root(tmp_path):
    target = tmp_path / "assets/files/target.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"inside")
    link = tmp_path / "assets/files/hero.png"
    link.symlink_to(target)
    record = make_record(tmp_path).model_copy(
        update={
            "artifact_path": Path("assets/files/hero.png"),
            "sha256": sha256_file(target),
            "size_bytes": target.stat().st_size,
        }
    )
    path = write_registry(tmp_path, records=(record,))
    _, asset_paths = load(path, tmp_path)
    assert asset_paths["image-hero-1"] == target.resolve()


def test_registry_rejects_asset_root_outside_project(tmp_path):
    root = tmp_path / "project"
    path = write_registry(root)
    with pytest.raises(AiVideoError) as exc:
        load_asset_registry(path.relative_to(root), root, tmp_path / "outside-assets")
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID


def test_registry_rejects_absolute_registry_path(tmp_path):
    path = write_registry(tmp_path)
    with pytest.raises(AiVideoError) as exc:
        load_asset_registry(path, tmp_path, tmp_path / "assets/files")
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
