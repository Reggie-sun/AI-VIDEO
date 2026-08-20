from __future__ import annotations

from pathlib import Path

import pytest

import ai_video.production._state_commit_bootstrap as bootstrap_module
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    canonical_project_snapshot_path,
    canonical_registry_snapshot_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import CommitPhase, ProductionStateCommitter
import production_project_factory as project_factory


class _RaiseAtPhase:
    def __init__(self, phase: CommitPhase) -> None:
        self.phase = phase

    def checkpoint(self, phase: CommitPhase) -> None:
        if phase is self.phase:
            raise OSError(f"injected failure at {phase.value}")


def _bootstrap_inputs(source: Path, writer: ProductionStateCommitter):
    project_factory.write_production_project(source)
    loaded = load_production_project(source / "project.yaml")
    referenced_paths = {
        loaded.project.artifacts.brief.path,
        loaded.project.artifacts.story.path,
        loaded.project.artifacts.storyboard.path,
        *(item.path for item in loaded.project.artifacts.characters),
        *(item.path for item in loaded.project.artifacts.scenes),
        *(item.path for item in loaded.project.artifacts.shots),
        *(item.artifact_path for item in loaded.registry.assets),
    }
    artifacts = tuple(
        writer.prepare_artifact(
            "bootstrap-initial",
            relative_path,
            (source / relative_path).read_bytes(),
        )
        for relative_path in sorted(referenced_paths, key=Path.as_posix)
    )
    return loaded.project, loaded.registry, artifacts


def test_bootstrap_initial_state_creates_strict_reopenable_canonical_snapshots(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)

    manifest = writer.bootstrap_initial_state(
        attempt_id="bootstrap-initial",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )

    expected_project_path = canonical_project_snapshot_path(
        project.revision, project.content_hash
    )
    expected_registry_path = canonical_registry_snapshot_path(registry.revision_id)
    assert manifest.schema_version == "2.0"
    assert manifest.manifest_revision == 1
    assert manifest.active_project.path == expected_project_path
    assert manifest.active_registry.path == expected_registry_path
    assert (target / "project.yaml").read_bytes() == (
        target / expected_project_path
    ).read_bytes()
    reopened = load_production_project(target / "project.yaml")
    assert reopened.project == project
    assert reopened.registry == registry


def test_bootstrap_initial_state_exact_replay_is_zero_write(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)
    committed = writer.bootstrap_initial_state(
        attempt_id="bootstrap-initial",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )
    before = {
        path.relative_to(target): (path.stat().st_mtime_ns, path.read_bytes())
        for path in target.rglob("*")
        if path.is_file()
    }

    replayed = writer.bootstrap_initial_state(
        attempt_id="bootstrap-replay",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )

    after = {
        path.relative_to(target): (path.stat().st_mtime_ns, path.read_bytes())
        for path in target.rglob("*")
        if path.is_file()
    }
    assert replayed == committed
    assert after == before


def test_bootstrap_initial_state_rejects_invalid_bundle_before_target_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)
    invalid = tuple(
        writer.prepare_artifact(
            "bootstrap-initial",
            artifact.relative_path,
            b"not: [valid yaml",
        )
        if artifact.relative_path == project.artifacts.story.path
        else artifact
        for artifact in artifacts
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.bootstrap_initial_state(
            attempt_id="bootstrap-initial",
            project=project,
            registry=registry,
            artifacts=invalid,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert tuple(target.iterdir()) == ()


def test_bootstrap_initial_state_rejects_unreferenced_extra_before_target_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)
    extra = writer.prepare_artifact(
        "bootstrap-initial",
        Path(".git/hooks/pre-commit"),
        b"#!/bin/sh\nexit 1\n",
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.bootstrap_initial_state(
            attempt_id="bootstrap-initial",
            project=project,
            registry=registry,
            artifacts=(*artifacts, extra),
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert tuple(target.iterdir()) == ()


def test_bootstrap_initial_state_rejects_missing_reference_before_target_mutation(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)

    with pytest.raises(AiVideoError) as exc_info:
        writer.bootstrap_initial_state(
            attempt_id="bootstrap-initial",
            project=project,
            registry=registry,
            artifacts=artifacts[:-1],
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert tuple(target.iterdir()) == ()


def test_bootstrap_initial_state_reports_unknown_when_post_commit_reopen_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    writer = ProductionStateCommitter(target)
    project, registry, artifacts = _bootstrap_inputs(source, writer)
    real_load = bootstrap_module.load_production_project

    def fail_target_reopen(entrypoint: Path):
        if entrypoint.parent == target:
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_INVALID,
                "injected post-commit reopen failure",
            )
        return real_load(entrypoint)

    monkeypatch.setattr(
        bootstrap_module,
        "load_production_project",
        fail_target_reopen,
    )

    with pytest.raises(AiVideoError) as exc_info:
        writer.bootstrap_initial_state(
            attempt_id="bootstrap-initial",
            project=project,
            registry=registry,
            artifacts=artifacts,
        )

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN
    assert (target / "state/manifest.json").exists()


@pytest.mark.parametrize(
    ("phase", "expected_code", "manifest_exists"),
    (
        (
            CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
            ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
            False,
        ),
        (
            CommitPhase.AFTER_MANIFEST_REPLACE,
            ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
            True,
        ),
    ),
)
def test_bootstrap_initial_state_crash_window_resumes_exact_input_without_rewrite(
    tmp_path: Path,
    phase: CommitPhase,
    expected_code: ErrorCode,
    manifest_exists: bool,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    crashing = ProductionStateCommitter(
        target,
        crash_injector=_RaiseAtPhase(phase),
    )
    project, registry, artifacts = _bootstrap_inputs(source, crashing)

    with pytest.raises(AiVideoError) as exc_info:
        crashing.bootstrap_initial_state(
            attempt_id="bootstrap-initial",
            project=project,
            registry=registry,
            artifacts=artifacts,
        )

    assert exc_info.value.code is expected_code
    assert (target / "state/manifest.json").exists() is manifest_exists
    resumed = ProductionStateCommitter(target).bootstrap_initial_state(
        attempt_id="bootstrap-initial",
        project=project,
        registry=registry,
        artifacts=artifacts,
    )
    assert load_production_project(target / "project.yaml").manifest == resumed
