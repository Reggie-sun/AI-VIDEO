from __future__ import annotations

from pathlib import Path

from ai_video import provider_console_media_index
from ai_video.provider_console_media_index import (
    project_runs_media_index,
    project_unresolved_workspace_media,
)


def test_runs_media_index_projects_only_exact_output_bindings() -> None:
    exact_sha = "a" * 64
    catalog = {
        "workspaces": [
            {"workspace": "run-a/project.yaml"},
            {"workspace": "run-b/project.yaml"},
        ]
    }
    details = {
        "run-a/project.yaml": {
            "attempts": [
                {
                    "attempt_id": "attempt-a",
                    "target_shot_id": "shot-1",
                    "target_shot_revision": 3,
                    "target_shot_content_hash": "b" * 64,
                    "generation_type": "I2V",
                    "prompt_text": "Exact submitted prompt.",
                    "shot_snapshot_status": "verified",
                    "shot_snapshot": {
                        "shot_id": "shot-1",
                        "intent": "Open on the product.",
                        "visual_strategy": "generated_video",
                        "revision": 3,
                        "content_hash": "b" * 64,
                    },
                    "candidate_media": None,
                    "fetched_media": {
                        "sha256": exact_sha,
                        "bytes": 1234,
                        "source_kind": "fetched_evidence",
                    },
                },
                {
                    "attempt_id": "invalid-output",
                    "fetched_media": {"sha256": "not-a-sha", "bytes": 50},
                },
            ]
        },
        "run-b/project.yaml": {"attempts": []},
    }

    result = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: catalog,
        detail_loader=lambda _root, workspace: details[workspace],
    )

    assert result == {
        "boundary": {
            "read_only": True,
            "association": "exact_sha256_and_bytes",
            "lifecycle_projection": False,
            "complete": True,
            "identity_coverage_complete": True,
        },
        "bindings": [
            {
                "sha256": exact_sha,
                "bytes": 1234,
                "workspace": "run-a/project.yaml",
                "attempt_id": "attempt-a",
                "target_shot_id": "shot-1",
                "target_shot_revision": 3,
                "target_shot_content_hash": "b" * 64,
                "generation_type": "I2V",
                "prompt_text": "Exact submitted prompt.",
                "shot_snapshot_status": "verified",
                "shot_snapshot": {
                    "shot_id": "shot-1",
                    "intent": "Open on the product.",
                    "visual_strategy": "generated_video",
                    "revision": 3,
                    "content_hash": "b" * 64,
                },
                "media_roles": ["fetched_media"],
            }
        ],
        "unresolved_media": [],
        "summary": {
            "workspace_count": 2,
            "projected_workspace_count": 2,
            "failed_workspace_count": 0,
            "recovered_workspace_count": 0,
            "catalog_truncated": False,
            "binding_count": 1,
            "unresolved_media_count": 0,
        },
    }


def test_runs_media_index_keeps_unavailable_snapshot_explicit() -> None:
    exact_sha = "c" * 64
    result = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: {"workspaces": [{"workspace": "run-a/project.yaml"}]},
        detail_loader=lambda _root, _workspace: {
            "attempts": [{
                "attempt_id": "attempt-a",
                "target_shot_id": "shot-current-unavailable",
                "generation_type": "T2V",
                "prompt_text": "Exact prompt remains available.",
                "shot_snapshot_status": "unavailable",
                "shot_snapshot": {"shot_id": "must-not-leak-current-shot"},
                "fetched_media": {"sha256": exact_sha, "bytes": 987},
            }]
        },
    )

    binding = result["bindings"][0]
    assert binding["shot_snapshot_status"] == "unavailable"
    assert binding["shot_snapshot"] is None
    assert binding["prompt_text"] == "Exact prompt remains available."


def test_runs_media_index_marks_truncated_or_failed_projection_incomplete() -> None:
    failed = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: {
            "workspaces": [{"workspace": "broken/project.yaml"}],
            "truncated": False,
        },
        detail_loader=lambda _root, _workspace: (_ for _ in ()).throw(ValueError("invalid")),
    )
    truncated = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: {"workspaces": [], "truncated": True},
    )
    invalid = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: {
            "workspaces": [{"workspace": "invalid/project.yaml"}],
            "truncated": False,
        },
        detail_loader=lambda _root, _workspace: {
            "kind": "production",
            "status": "invalid",
            "attempts": [],
        },
    )

    assert failed["boundary"]["complete"] is False
    assert failed["summary"]["failed_workspace_count"] == 1
    assert truncated["boundary"]["complete"] is False
    assert truncated["summary"]["catalog_truncated"] is True
    assert invalid["boundary"]["complete"] is False
    assert invalid["summary"]["failed_workspace_count"] == 1


def test_runs_media_index_recovers_video_evidence_without_claiming_workspace_valid() -> None:
    exact_sha = "d" * 64
    catalog = {
        "workspaces": [{"workspace": "historical/project.yaml"}],
        "truncated": False,
    }
    strict_invalid = {
        "kind": "production",
        "status": "invalid",
        "attempts": [],
    }
    recovered = {
        "kind": "production",
        "status": "recovered_video_evidence",
        "attempts": [{
            "attempt_id": "attempt-recovered",
            "target_shot_id": "shot-13",
            "generation_type": "I2V",
            "prompt_text": "Exact historical prompt.",
            "shot_snapshot_status": "verified",
            "shot_snapshot": {"shot_id": "shot-13", "content_hash": "e" * 64},
            "fetched_media": {"sha256": exact_sha, "bytes": 321},
        }],
    }

    result = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: catalog,
        detail_loader=lambda _root, _workspace: strict_invalid,
        video_evidence_loader=lambda _root, _workspace: recovered,
        unresolved_media_loader=lambda _root, _workspace: {
            "complete": True,
            "identities": [],
        },
    )

    assert result["boundary"]["complete"] is False
    assert result["boundary"]["identity_coverage_complete"] is True
    assert result["summary"]["recovered_workspace_count"] == 1
    assert result["summary"]["failed_workspace_count"] == 0
    assert result["bindings"][0]["sha256"] == exact_sha
    assert result["bindings"][0]["prompt_text"] == "Exact historical prompt."


def test_runs_media_index_scopes_failed_workspace_uncertainty_to_exact_media() -> None:
    unresolved_sha = "f" * 64
    catalog = {
        "workspaces": [{"workspace": "broken/project.yaml"}],
        "truncated": False,
    }
    invalid = {"kind": "production", "status": "invalid", "attempts": []}

    result = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: catalog,
        detail_loader=lambda _root, _workspace: invalid,
        video_evidence_loader=lambda _root, _workspace: invalid,
        unresolved_media_loader=lambda _root, _workspace: {
            "complete": True,
            "identities": [{"sha256": unresolved_sha, "bytes": 456}],
        },
    )

    assert result["boundary"]["complete"] is False
    assert result["boundary"]["identity_coverage_complete"] is True
    assert result["summary"]["failed_workspace_count"] == 1
    assert result["summary"]["unresolved_media_count"] == 1
    assert result["unresolved_media"] == [{"sha256": unresolved_sha, "bytes": 456}]

    scan_failed = project_runs_media_index(
        Path("/unused/runs"),
        catalog_loader=lambda _root: catalog,
        detail_loader=lambda _root, _workspace: invalid,
        video_evidence_loader=lambda _root, _workspace: invalid,
        unresolved_media_loader=lambda _root, _workspace: {
            "complete": False,
            "identities": [],
        },
    )
    assert scan_failed["boundary"]["identity_coverage_complete"] is False


def test_unresolved_workspace_media_is_exact_bounded_and_does_not_follow_links(
    tmp_path: Path, monkeypatch
) -> None:
    runs = tmp_path / "runs"
    workspace = runs / "broken"
    (workspace / "state").mkdir(parents=True)
    (workspace / "project.yaml").write_text("project_id: broken\n", encoding="utf-8")
    (workspace / "state" / "manifest.json").write_text("{}", encoding="utf-8")
    video = workspace / "candidate.mp4"
    video.write_bytes(b"exact-video")
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"outside-video")
    (workspace / "linked.mp4").symlink_to(outside)

    result = project_unresolved_workspace_media(runs, "broken/project.yaml")

    assert result == {
        "complete": True,
        "identities": [{
            "sha256": "5512bdf8b6a6e465108fdbd6c4d5fce70c1624a6f37d58c81b9b7883da6576f8",
            "bytes": 11,
        }],
    }

    monkeypatch.setattr(provider_console_media_index, "_MAX_UNRESOLVED_ENTRIES", 1)
    limited = project_unresolved_workspace_media(runs, "broken/project.yaml")
    assert limited["complete"] is False
