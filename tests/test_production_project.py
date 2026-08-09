from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from ai_video.config import load_project, sha256_file
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import (
    ProductionStateCommitter,
    load_production_project,
    prepare_project_registry_commit,
)
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ProductionManifest,
    ProductionProject,
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from production_project_factory import (
    load_revision_two_models,
    write_production_project,
)


def _manifest(root: Path) -> ProductionManifest:
    return ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )


def _write_manifest(root: Path, manifest: ProductionManifest) -> None:
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )


def _commit_revision_two(root: Path, *, attempt_id: str = "loader-revision-two") -> ProductionProject:
    manifest = _manifest(root)
    project, registry = load_revision_two_models(root)
    ProductionStateCommitter(root).commit(
        prepare_project_registry_commit(
            manifest=manifest,
            project=project,
            registry=registry,
            attempt_id=attempt_id,
        )
    )
    return project


def _corrupt_active_project(root: Path, project_data: dict[str, object]) -> None:
    manifest = _manifest(root)
    replacement = seal_artifact(ProductionProject.model_validate(project_data))
    snapshot_path = root / manifest.active_project.path
    snapshot_path.write_text(
        yaml.safe_dump(
            replacement.model_dump(mode="json"),
            sort_keys=True,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    pointer = manifest.active_project.model_copy(
        update={
            "content_hash": replacement.content_hash,
            "file_sha256": sha256_file(snapshot_path),
        }
    )
    _write_manifest(root, manifest.model_copy(update={"active_project": pointer}))


def test_load_production_project_returns_verified_bundle(tmp_path):
    project_path = write_production_project(tmp_path)
    loaded = load_production_project(project_path)
    assert loaded.project.project_id == "comic-demo"
    assert loaded.project.revision == 1
    assert loaded.shots[0].visual_strategy.value == "static_image"
    assert loaded.asset_paths["image-hero-1"].is_relative_to(tmp_path.resolve())


def test_load_selects_committed_revision_two_not_root_project(tmp_path):
    project_path = write_production_project(tmp_path)
    root_project_bytes = project_path.read_bytes()
    revision_two = _commit_revision_two(tmp_path)

    loaded = load_production_project(project_path)

    assert loaded.project.revision == 2
    assert loaded.project.content_hash == revision_two.content_hash
    assert loaded.project.title == "Comic Demo Revision 2"
    assert project_path.read_bytes() == root_project_bytes
    assert loaded.manifest.active_project.path != Path("project.yaml")


def test_load_requires_existing_regular_project_entrypoint(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    project_path.unlink()

    with pytest.raises(AiVideoError, match="entry point"):
        load_production_project(project_path)


def test_load_rejects_directory_project_entrypoint(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    project_path.unlink()
    project_path.mkdir()

    with pytest.raises(AiVideoError, match="regular file"):
        load_production_project(project_path)


@pytest.mark.parametrize("outside", [False, True])
def test_load_rejects_symlink_project_entrypoint(tmp_path, outside):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    original = project_path.read_bytes()
    project_path.unlink()
    target = (
        tmp_path.parent / "outside-project.yaml"
        if outside
        else tmp_path / "creative/entrypoint.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(original)
    project_path.symlink_to(target)

    with pytest.raises(AiVideoError, match="symlink"):
        load_production_project(project_path)


def test_load_rejects_manifest_project_id_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path).model_copy(update={"project_id": "other-project"})
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="project_id"):
        load_production_project(project_path)


def test_load_uses_manifest_pointer_not_decoy_filename_or_mtime(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    decoy = tmp_path / "state/projects/project.999.decoy.yaml"
    decoy.write_text("not: a production project\n", encoding="utf-8")
    decoy.touch()
    registry_decoy = tmp_path / f"assets/registry.{'f' * 64}.json"
    registry_decoy.write_text("not json", encoding="utf-8")
    registry_decoy.touch()

    loaded = load_production_project(project_path)

    assert loaded.project.revision == 2
    assert loaded.manifest.active_project.path.name != decoy.name
    assert loaded.manifest.active_registry.path.name != registry_decoy.name


def test_load_rejects_active_project_file_hash_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path).model_copy(
        update={
            "active_project": _manifest(tmp_path).active_project.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="file hash"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("revision", 999, "project revision"),
        ("content_hash", "f" * 64, "project content hash"),
    ],
)
def test_load_rejects_active_project_pointer_identity_mismatch(
    tmp_path, field, value, message
):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path)
    active_project = manifest.active_project.model_copy(update={field: value})
    active_project = active_project.model_copy(
        update={
            "path": canonical_project_snapshot_path(
                active_project.revision, active_project.content_hash
            )
        }
    )
    target = tmp_path / active_project.path
    target.write_bytes((tmp_path / manifest.active_project.path).read_bytes())
    _write_manifest(
        tmp_path,
        manifest.model_copy(update={"active_project": active_project}),
    )

    with pytest.raises(AiVideoError, match=message):
        load_production_project(project_path)


def test_load_rejects_active_registry_file_hash_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path).model_copy(
        update={
            "active_registry": _manifest(tmp_path).active_registry.model_copy(
                update={"file_sha256": "f" * 64}
            )
        }
    )
    _write_manifest(tmp_path, manifest)

    with pytest.raises(AiVideoError, match="file hash"):
        load_production_project(project_path)


def test_load_rejects_active_registry_identity_mismatch_without_fallback(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path)
    active_registry = manifest.active_registry.model_copy(
        update={
            "path": canonical_registry_snapshot_path("f" * 64),
            "revision_id": "f" * 64,
            "content_hash": "f" * 64,
        }
    )
    (tmp_path / active_registry.path).write_bytes(
        (tmp_path / manifest.active_registry.path).read_bytes()
    )
    _write_manifest(
        tmp_path, manifest.model_copy(update={"active_registry": active_registry})
    )

    with pytest.raises(AiVideoError, match="filename does not match revision_id"):
        load_production_project(project_path)


def test_load_rejects_tampered_active_registry_without_root_fallback(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = _manifest(tmp_path)
    registry_path = tmp_path / manifest.active_registry.path
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    data["assets"][0]["sha256"] = "1" * 64
    registry_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


@pytest.mark.parametrize("stored", ["../story.yaml", "/tmp/story.yaml", "other/story.yaml"])
def test_load_rejects_unsafe_creative_reference_path(tmp_path, stored):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["artifacts"]["story"]["path"] = stored
    _corrupt_active_project(tmp_path, project_data)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


@pytest.mark.parametrize("asset_root", ["../outside", "creative"])
def test_load_rejects_unsafe_asset_root(tmp_path, asset_root):
    project_path = write_production_project(tmp_path)
    project_data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    project_data["asset_root"] = asset_root
    _corrupt_active_project(tmp_path, project_data)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    "path", [Path("../outside.yaml"), Path("/tmp/outside.yaml")]
)
def test_load_rejects_unsafe_active_project_pointer_before_read(tmp_path, path):
    project_path = write_production_project(tmp_path)
    manifest_data = json.loads((tmp_path / "state/manifest.json").read_text(encoding="utf-8"))
    manifest_data["active_project"]["path"] = str(path)
    (tmp_path / "state/manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(AiVideoError, match="Could not load production state"):
        load_production_project(project_path)


@pytest.mark.parametrize(
    ("pointer_name", "path"),
    [
        ("active_project", "state/projects/arbitrary.yaml"),
        ("active_registry", "assets/arbitrary.json"),
    ],
)
def test_load_rejects_noncanonical_manifest_snapshot_pointer(
    tmp_path, pointer_name, path
):
    project_path = write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = tmp_path / manifest_data[pointer_name]["path"]
    target_path = tmp_path / path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(source_path.read_bytes())
    manifest_data[pointer_name]["path"] = path
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(AiVideoError, match="Could not load production state"):
        load_production_project(project_path)


def test_load_rejects_active_project_symlink_escape(tmp_path):
    project_path = write_production_project(tmp_path)
    _commit_revision_two(tmp_path)
    manifest = _manifest(tmp_path)
    outside = tmp_path.parent / "outside-project.yaml"
    target = tmp_path / manifest.active_project.path
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_manifest_symlink_cannot_escape_state_root(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest = tmp_path / "state/manifest.json"
    relocated = tmp_path / "creative/manifest.json"
    manifest.rename(relocated)
    manifest.symlink_to(relocated)

    with pytest.raises(AiVideoError, match="contained"):
        load_production_project(project_path)


def test_project_root_symlink_loop_returns_typed_project_error(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.symlink_to(second.name)
    second.symlink_to(first.name)

    with pytest.raises(AiVideoError) as exc:
        load_production_project(first / "project.yaml")
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_load_runs_full_creative_validation_for_selected_snapshot(tmp_path):
    project_path = write_production_project(tmp_path)
    story_path = tmp_path / "creative/story.yaml"
    data = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    data["logline"] = "tampered"
    story_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(AiVideoError, match="content hash"):
        load_production_project(project_path)


def test_loader_creates_no_directories_preserves_inputs_and_does_not_recover(tmp_path):
    project_path = write_production_project(tmp_path)
    orphan = tmp_path / "state/projects/project.99.orphan.yaml"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("untracked", encoding="utf-8")
    files_before = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()}

    load_production_project(project_path)

    files_after = {
        path.relative_to(tmp_path): (path.stat().st_mtime_ns, path.read_bytes())
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    directories_after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_dir()}
    assert files_after == files_before
    assert directories_after == directories_before


def test_loader_requires_canonical_project_entrypoint_name(tmp_path):
    project_path = write_production_project(tmp_path)
    with pytest.raises(AiVideoError, match="must be named project.yaml"):
        load_production_project(project_path.with_name("other.yaml"))


def test_legacy_project_loader_remains_unchanged():
    project = load_project("configs/wan22_fast.project.yaml")
    assert project.project_name == "wan22-fast-demo"
