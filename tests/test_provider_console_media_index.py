from __future__ import annotations

from pathlib import Path

from ai_video.provider_console_media_index import project_runs_media_index


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
        "summary": {
            "workspace_count": 2,
            "projected_workspace_count": 2,
            "failed_workspace_count": 0,
            "catalog_truncated": False,
            "binding_count": 1,
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
