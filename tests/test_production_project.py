from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from ai_video.config import load_project
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import ProductionProject, Shot
from production_project_factory import write_production_project


def _select_project(project_path: Path, data: dict) -> ProductionProject:
    project = seal_artifact(ProductionProject.model_validate(data))
    project_path.write_text(
        yaml.safe_dump(
            project.model_dump(mode="json"),
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    manifest_path = project_path.parent / "state/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["active_project_revision"] = project.revision
    manifest["active_project_content_hash"] = project.content_hash
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return project


def _replace_shot(project_path: Path, **updates: object) -> None:
    root = project_path.parent
    shot_path = root / "creative/shots/shot-1.yaml"
    shot_data = yaml.safe_load(shot_path.read_text(encoding="utf-8"))
    shot = seal_artifact(Shot.model_validate({**shot_data, **updates}))
    shot_path.write_text(
        yaml.safe_dump(shot.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    ref = project_data["artifacts"]["shots"][0]
    ref.update(
        {
            "artifact_id": shot.artifact_id,
            "revision": shot.revision,
            "content_hash": shot.content_hash,
        }
    )
    _select_project(project_path, project_data)


def test_load_production_project_returns_verified_bundle(tmp_path):
    loaded = load_production_project(write_production_project(tmp_path))
    assert loaded.project.project_id == "comic-demo"
    assert loaded.shots[0].visual_strategy.value == "static_image"
    path = loaded.asset_paths["image-hero-1"]
    assert path.is_absolute()
    assert ".." not in str(path)
    assert path.is_relative_to(tmp_path.resolve())


def test_load_rejects_manifest_project_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["project_id"] = "other-project"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_load_rejects_same_revision_with_unselected_content_hash(tmp_path):
    project_path = write_production_project(tmp_path)
    data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    data["title"] = "A different sealed project"
    replacement = seal_artifact(ProductionProject.model_validate(data))
    project_path.write_text(
        yaml.safe_dump(replacement.model_dump(mode="json"), allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(AiVideoError, match="active project content hash"):
        load_production_project(project_path)


def test_load_rejects_active_project_revision_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["active_project_revision"] = 2
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AiVideoError, match="active project revision"):
        load_production_project(project_path)


def test_load_rejects_tampered_creative_hash(tmp_path):
    project_path = write_production_project(tmp_path)
    story_path = tmp_path / "creative/story.yaml"
    data = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    data["logline"] = "tampered"
    story_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert "content hash" in exc.value.user_message


def test_load_rejects_creative_reference_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["artifacts"]["story"]["content_hash"] = "1" * 64
    _select_project(project_path, project_data)
    with pytest.raises(AiVideoError, match="does not match its project reference"):
        load_production_project(project_path)


@pytest.mark.parametrize("stored", ["../story.yaml", "/tmp/story.yaml"])
def test_load_rejects_unsafe_creative_path_before_read(tmp_path, stored):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["artifacts"]["story"]["path"] = stored
    _select_project(project_path, project_data)
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "contained" in exc.value.user_message


def test_load_rejects_unsafe_asset_root(tmp_path):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["asset_root"] = "../outside"
    _select_project(project_path, project_data)
    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_creative_reference_must_remain_under_creative_root(tmp_path):
    project_path = write_production_project(tmp_path)
    original = tmp_path / "creative/story.yaml"
    relocated = tmp_path / "other/story.yaml"
    relocated.parent.mkdir()
    relocated.write_bytes(original.read_bytes())
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["artifacts"]["story"]["path"] = "other/story.yaml"
    _select_project(project_path, project_data)
    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_asset_root_must_remain_under_assets_root(tmp_path):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["asset_root"] = "creative"
    _select_project(project_path, project_data)
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "contained" in exc.value.user_message


def test_manifest_symlink_cannot_escape_state_root(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = tmp_path / "state/manifest.json"
    relocated = tmp_path / "creative/manifest.json"
    manifest.rename(relocated)
    manifest.symlink_to(relocated)
    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_manifest_symlink_loop_returns_typed_project_error(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = tmp_path / "state/manifest.json"
    loop = manifest.with_name("manifest-loop.json")
    manifest.unlink()
    manifest.symlink_to(loop.name)
    loop.symlink_to(manifest.name)
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_load_uses_only_active_registry_revision(tmp_path):
    project_path = write_production_project(tmp_path)
    decoy = tmp_path / f"assets/registry.{'1' * 64}.json"
    decoy.write_text("not json", encoding="utf-8")
    loaded = load_production_project(project_path)
    assert loaded.registry.revision_id == loaded.manifest.active_registry_revision


def test_registry_errors_remain_typed_as_registry_errors(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = json.loads((tmp_path / "state/manifest.json").read_text(encoding="utf-8"))
    registry_path = tmp_path / f"assets/registry.{manifest['active_registry_revision']}.json"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    data["assets"][0]["sha256"] = "1" * 64
    registry_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID


def test_load_rejects_unknown_creative_cross_reference(tmp_path):
    project_path = write_production_project(tmp_path)
    _replace_shot(project_path, character_ids=("missing",))
    with pytest.raises(AiVideoError, match="unknown character"):
        load_production_project(project_path)


def test_loader_creates_no_directories_and_preserves_input_mtimes(tmp_path):
    project_path = write_production_project(tmp_path)
    files_before = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_before = {
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()
    }
    load_production_project(project_path)
    files_after = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_after = {
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()
    }
    assert files_after == files_before
    assert directories_after == directories_before


def test_loader_requires_canonical_project_entrypoint_name(tmp_path):
    project_path = write_production_project(tmp_path)
    with pytest.raises(AiVideoError, match="must be named project.yaml"):
        load_production_project(project_path.with_name("other.yaml"))


def test_legacy_project_loader_remains_unchanged():
    project = load_project("configs/wan22_fast.project.yaml")
    assert project.project_name == "wan22-fast-demo"
