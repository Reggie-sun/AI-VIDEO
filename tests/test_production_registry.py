from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_video.config import sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.captions import _canonical_track_bytes
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    AssetSourceKind,
    AssetType,
    CaptionTrack,
    ToolIdentity,
)
from ai_video.production.registry import load_asset_registry, registry_semantic_sha256
from production_project_factory import make_p4_composition_fixture

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


def write_snapshot(root: Path, snapshot: AssetRegistrySnapshot) -> Path:
    provisional = snapshot.model_copy(
        update={"revision_id": ZERO_HASH, "content_hash": ZERO_HASH}
    )
    digest = registry_semantic_sha256(provisional)
    sealed = provisional.model_copy(
        update={"revision_id": digest, "content_hash": digest}
    )
    path = root / f"assets/registry.{digest}.json"
    path.write_text(sealed.model_dump_json(indent=2), encoding="utf-8")
    return path


def test_registry_loads_verified_local_asset(tmp_path):
    path = write_registry(tmp_path)
    snapshot, asset_paths = load(path, tmp_path)
    assert snapshot.assets[0].asset_id == "image-hero-1"
    assert not snapshot.assets[0].artifact_path.is_absolute()
    assert asset_paths["image-hero-1"].is_absolute()
    assert asset_paths["image-hero-1"].is_relative_to(tmp_path.resolve())


def test_registry_21_verifies_audio_probe_against_typed_metadata(tmp_path):
    loaded, _ = make_p4_composition_fixture(tmp_path)
    audio = next(item for item in loaded.registry.assets if item.audio_metadata is not None)
    assert audio.audio_metadata is not None
    changed = audio.model_copy(
        update={
            "audio_metadata": audio.audio_metadata.model_copy(
                update={"duration_samples": audio.audio_metadata.duration_samples + 1}
            ),
            "duration_seconds": None,
        }
    )
    registry = loaded.registry.model_copy(
        update={
            "assets": tuple(
                changed if item.asset_id == changed.asset_id else item
                for item in loaded.registry.assets
            )
        }
    )
    path = write_snapshot(tmp_path, registry)

    with pytest.raises(AiVideoError, match="audio metadata"):
        load(path, tmp_path)


@pytest.mark.parametrize("mismatch", ["track", "style"])
def test_registry_21_verifies_caption_bytes_metadata_and_style(tmp_path, mismatch):
    loaded, _ = make_p4_composition_fixture(tmp_path)
    caption = next(item for item in loaded.registry.assets if item.caption_metadata is not None)
    assert caption.caption_metadata is not None
    if mismatch == "track":
        changed = caption.model_copy(
            update={
                "caption_metadata": caption.caption_metadata.model_copy(
                    update={"caption_track_id": "other-track"}
                )
            }
        )
        registry = loaded.registry.model_copy(
            update={
                "assets": tuple(
                    changed if item.asset_id == changed.asset_id else item
                    for item in loaded.registry.assets
                )
            }
        )
    else:
        style_path = (
            tmp_path
            / "assets/styles"
            / f"{caption.caption_metadata.style_content_hash}.json"
        )
        style_path.write_bytes(b'{"schema_version":"different"}')
        registry = loaded.registry
    path = write_snapshot(tmp_path, registry)

    with pytest.raises(AiVideoError, match="caption"):
        load(path, tmp_path)


def test_registry_21_recomputes_caption_timing_fingerprint(tmp_path):
    loaded, _ = make_p4_composition_fixture(tmp_path)
    caption = next(item for item in loaded.registry.assets if item.caption_metadata is not None)
    assert caption.caption_metadata is not None
    caption_path = tmp_path / caption.artifact_path
    track = CaptionTrack.model_validate_json(caption_path.read_bytes())
    forged = seal_artifact(
        track.model_copy(
            update={"content_hash": ZERO_HASH, "timing_fingerprint": ONE_HASH}
        )
    )
    payload = _canonical_track_bytes(forged)
    caption_path.write_bytes(payload)
    changed = caption.model_copy(
        update={
            "sha256": sha256_file(caption_path),
            "size_bytes": len(payload),
            "caption_metadata": caption.caption_metadata.model_copy(
                update={"timing_fingerprint": ONE_HASH}
            ),
        }
    )
    registry = loaded.registry.model_copy(
        update={
            "assets": tuple(
                changed if item.asset_id == changed.asset_id else item
                for item in loaded.registry.assets
            )
        }
    )
    path = write_snapshot(tmp_path, registry)

    with pytest.raises(AiVideoError, match="timing fingerprint"):
        load(path, tmp_path)


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


def test_asset_symlink_loop_returns_typed_registry_error(tmp_path):
    path = write_registry(tmp_path)
    asset = tmp_path / "assets/files/hero.png"
    loop = asset.with_name("loop.png")
    asset.unlink()
    asset.symlink_to(loop.name)
    loop.symlink_to(asset.name)
    with pytest.raises(AiVideoError) as exc:
        load(path, tmp_path)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID


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


def make_generated_video_record(root: Path, *, artifact_path: Path | None = None):
    from ai_video.production.models import VideoAssetMetadata
    from ai_video.production.paths import canonical_video_asset_path

    payload = b"\x00\x00\x00\x18ftypmp42generated-video-bytes"
    digest = hashlib.sha256(payload).hexdigest()
    stored = artifact_path if artifact_path is not None else canonical_video_asset_path(digest)
    target = root / stored
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return AssetRecord(
        asset_id="video-output-001",
        asset_type=AssetType.VIDEO,
        artifact_path=stored,
        sha256=digest,
        size_bytes=len(payload),
        mime_type="video/mp4",
        duration_seconds=3.0,
        width=1280,
        height=720,
        source_kind=AssetSourceKind.GENERATED,
        tool=ToolIdentity(name="fixture", version="1"),
        input_fingerprint=ZERO_HASH,
        creation_receipt_id="receipt-video-output-001",
        usage_license="test-only",
        video_metadata=VideoAssetMetadata(
            container_name="mp4",
            codec_name="h264",
            width=1280,
            height=720,
            fps_numerator=24,
            fps_denominator=1,
            duration_milliseconds=3000,
            frame_count=72,
            probe_receipt_id="probe-video-output-001",
            request_receipt_fingerprint=ONE_HASH,
            resolved_generation_hash=ONE_HASH,
            provenance_receipt_id="provenance-video-output-001",
        ),
    )


def write_video_registry(root: Path, record) -> Path:
    return write_snapshot(
        root,
        AssetRegistrySnapshot(
            schema_version="2.2",
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            assets=(record,),
        ),
    )


def test_registry_22_reopens_generated_video_bytes_no_follow(tmp_path):
    record = make_generated_video_record(tmp_path)
    path = write_video_registry(tmp_path, record)
    snapshot, asset_paths = load(path, tmp_path)
    assert snapshot.schema_version == "2.2"
    assert snapshot.assets[0].video_metadata is not None
    assert asset_paths["video-output-001"] == (tmp_path / record.artifact_path).resolve()


def test_registry_22_rejects_symlinked_generated_video_asset(tmp_path):
    record = make_generated_video_record(tmp_path)
    path = write_video_registry(tmp_path, record)
    asset = tmp_path / record.artifact_path
    payload = asset.read_bytes()
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(payload)
    asset.unlink()
    asset.symlink_to(outside)
    with pytest.raises(AiVideoError) as exc:
        load(path, tmp_path)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID


def test_registry_22_requires_content_addressed_generated_video_path(tmp_path):
    record = make_generated_video_record(
        tmp_path, artifact_path=Path("assets/files/latest.mp4")
    )
    path = write_video_registry(tmp_path, record)
    with pytest.raises(AiVideoError, match="content-addressed"):
        load(path, tmp_path)


def test_project_root_symlink_loop_returns_typed_registry_error(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.symlink_to(second.name)
    second.symlink_to(first.name)
    with pytest.raises(AiVideoError) as exc:
        load_asset_registry("assets/registry.json", first, first / "assets/files")
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
