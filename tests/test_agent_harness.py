from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from scripts import agent_harness
from scripts import harness_pytest_guard


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agent/harness/policy.yaml"


def _git(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )


def _committed_repository(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "harness@example.invalid")
    _git(tmp_path, "config", "user.name", "Harness Test")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-qm", "baseline")
    return tracked


def _minimal_policy() -> dict[str, object]:
    return {
        "version": 2,
        "runs_dir": ".agent/harness/runs",
        "default_timeout_seconds": 30,
        "always_check_ids": [],
        "fallback_check_ids": [],
        "ignored_patterns": [],
        "sensitive_patterns": [],
        "audit_patterns": [],
        "audit_exempt_patterns": [],
        "checks": {
            "unit": {
                "argv": [sys.executable, "-c", "print('ok')"],
                "cwd": ".",
                "description": "Example unit test.",
            }
        },
        "categories": {},
    }


def test_repository_policy_v2_loads_and_references_known_checks() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    assert policy["version"] == 2
    assert policy["runs_dir"] == ".agent/harness/runs"
    assert policy["always_check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
    ]
    assert policy["categories"]["documentation"]["check_ids"] == [
        "docs_contract_check"
    ]
    assert "full_tests" in policy["fallback_check_ids"]
    assert "task_architecture_gate" in policy["fallback_check_ids"]
    assert "repository_architecture_gate" in policy["checks"]
    referenced_test_files = {
        argument
        for check in policy["checks"].values()
        for argument in check["argv"]
        if argument.startswith("tests/") and argument.endswith(".py")
    }
    assert referenced_test_files
    assert not [path for path in referenced_test_files if not (ROOT / path).is_file()]


def test_tracked_harness_runs_contract_is_not_ignored() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([".agent/harness/runs/.gitignore"], policy)

    assert report["changed_paths"] == [".agent/harness/runs/.gitignore"]
    assert report["ignored_paths"] == []
    assert report["categories"] == ["harness_control"]
    assert "harness_tests" in report["check_ids"]


def test_github_workflow_routes_to_harness_control_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        [".github/workflows/mandatory-gate.yml"], policy
    )

    assert report["categories"] == ["harness_control"]
    assert report["fallback_paths"] == []
    assert report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "harness_tests",
    ]


def test_docs_only_change_routes_to_behavioral_contract_gate() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["docs/superpowers/specs/example.md"], policy
    )

    assert report["categories"] == ["documentation"]
    assert report["fallback_paths"] == []
    assert report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
    ]


def test_code_only_change_still_routes_to_docs_contract_gate() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["src/ai_video/planning/video_planner.py"], policy
    )

    assert report["changed_paths"] == [
        "src/ai_video/planning/video_planner.py"
    ]
    assert "docs_contract_check" in report["check_ids"]


def test_mandatory_gate_workflow_preserves_server_check_contract() -> None:
    workflow_path = ROOT / ".github/workflows/mandatory-gate.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    assert workflow["name"] == "mandatory-gate"
    assert workflow["on"] == {"pull_request": {"branches": ["main"]}}
    assert workflow["permissions"] == {"contents": "read"}
    verify_job = workflow["jobs"]["verify"]
    assert verify_job["name"] == "mandatory-gate / verify"
    assert verify_job["env"] == {
        "BASE_SHA": "${{ github.event.pull_request.base.sha }}",
        "HEAD_SHA": "${{ github.event.pull_request.head.sha }}",
        "HARNESS_RUN_ID": (
            "pr-${{ github.event.pull_request.number }}-"
            "${{ github.run_id }}-${{ github.run_attempt }}"
        ),
    }
    steps = {step["name"]: step for step in verify_job["steps"]}
    checkout = steps["Check out exact PR head"]
    assert checkout["uses"] == (
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    )
    assert checkout["with"]["ref"] == "${{ env.HEAD_SHA }}"
    assert checkout["with"]["fetch-depth"] == 0
    assert checkout["with"]["persist-credentials"] is False
    assert steps["Set up Python"]["uses"] == (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    )
    assert "make harness-audit" in steps["Audit Harness policy"]["run"]
    range_command = steps["Verify exact PR range"]["run"]
    assert 'BASE_REF="${BASE_SHA}"' in range_command
    assert 'HEAD_REF="${HEAD_SHA}"' in range_command
    assert 'RUN_ID="${HARNESS_RUN_ID}"' in range_command
    upload = steps["Upload Harness receipt, JUnit, and logs"]
    assert upload["if"] == "always()"
    assert upload["uses"] == (
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    )
    assert ".agent/harness/runs/${{ env.HARNESS_RUN_ID }}/" in upload["with"][
        "path"
    ]
    assert upload["with"]["include-hidden-files"] is True


def test_shared_production_contract_routes_to_cross_surface_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["src/ai_video/production/models.py"], policy
    )

    assert report["categories"] == ["production_shared_contracts"]
    assert report["fallback_paths"] == []
    assert report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "production_contract_tests",
        "cli_config_tests",
        "task_architecture_gate",
    ]


def test_shot_router_routes_to_exact_contract_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/_shot_router_contracts.py",
        "src/ai_video/production/_shot_visual_resolver.py",
        "src/ai_video/production/shot_router.py",
        "tests/test_production_shot_router.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["production_shot_router"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "production_shot_router_tests",
            "provider_neutral_video_requirement_tests",
            "task_architecture_gate",
        ]

    argv = policy["checks"]["production_shot_router_tests"]["argv"]
    for path in (
        "tests/test_production_shot_router.py",
        "tests/test_production_video.py",
        "tests/test_production_dependency.py",
        "tests/test_production_selective_rebuild.py",
    ):
        assert path in argv


def test_video_planner_routes_to_exact_contract_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/planning/video_planner.py",
        "tests/fixtures/planning_factory.py",
        "tests/test_planning_video_planner.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["video_planning"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "video_planner_tests",
            "provider_neutral_video_requirement_tests",
            "shot_readiness_gate_tests",
            "task_architecture_gate",
        ]

    argv = policy["checks"]["video_planner_tests"]["argv"]
    assert "tests/test_planning_video_planner.py" in argv
    assert "tests/test_errors.py" in argv


def test_shot_readiness_gate_routes_to_focused_contract_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/quality_gates/shot_readiness_gate.py",
        "tests/test_shot_readiness_gate.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["shot_readiness_gate"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "shot_readiness_gate_tests",
            "task_architecture_gate",
        ]

    helper_report = agent_harness.inspect_paths(
        ["src/ai_video/planning/_asset_readiness.py"], policy
    )
    assert helper_report["categories"] == [
        "video_planning",
        "shot_readiness_gate",
    ]
    assert helper_report["fallback_paths"] == []
    assert helper_report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "video_planner_tests",
        "provider_neutral_video_requirement_tests",
        "shot_readiness_gate_tests",
        "task_architecture_gate",
    ]

    argv = policy["checks"]["shot_readiness_gate_tests"]["argv"]
    for path in (
        "tests/test_shot_readiness_gate.py",
        "tests/test_planning_video_planner.py",
        "tests/test_production_video_requirement.py",
        "tests/test_errors.py",
    ):
        assert path in argv


def test_quality_intelligence_routes_to_passive_capture_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/quality_intelligence/_capture_contracts.py",
        "src/ai_video/quality_intelligence/_capture_human.py",
        "src/ai_video/quality_intelligence/_capture_p6.py",
        "src/ai_video/quality_intelligence/capture.py",
        "src/ai_video/quality_intelligence/models.py",
        "tests/test_quality_experience_capture.py",
        "tests/test_quality_experience_dataset.py",
        "tests/fixtures/quality_experience/v1/prospective_failure.json",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["quality_intelligence"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "quality_intelligence_tests",
            "task_architecture_gate",
        ]

    argv = policy["checks"]["quality_intelligence_tests"]["argv"]
    for path in (
        "tests/test_quality_experience_capture.py",
        "tests/test_quality_experience_models.py",
        "tests/test_quality_experience_store.py",
        "tests/test_quality_experience_dataset.py",
        "tests/test_quality_experience_rag_projection.py",
    ):
        assert path in argv
    assert "tests/test_agent_memory.py" in argv


def test_composition_strategy_shadow_routes_to_focused_dev_checks() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        ".agent/playbooks/composition/schema.json",
        ".agent/playbooks/composition/hard_cut_continuation.yaml",
        "scripts/composition_playbooks.py",
        "scripts/composition_shadow.py",
        "tests/test_composition_playbooks.py",
        "tests/test_composition_strategy_proposal.py",
        "tests/test_composition_architecture.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["composition_strategy_shadow"]
        assert report["fallback_paths"] == []
        assert report["check_ids"][0] == "scope_diff_check"
        assert {
            "composition_playbook_tests",
            "composition_strategy_proposal_tests",
            "composition_architecture_tests",
            "task_architecture_gate",
        }.issubset(report["check_ids"])

    assert policy["checks"]["composition_playbook_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_composition_playbooks.py",
        "-q",
    ]
    assert policy["checks"]["composition_strategy_proposal_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_composition_strategy_proposal.py",
        "-q",
    ]
    assert policy["checks"]["composition_architecture_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_composition_architecture.py",
        "-q",
    ]


def test_provider_console_routes_to_local_runs_observer_suites() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/provider_console.py",
        "src/ai_video/provider_console_continuity.py",
        "tests/test_provider_console.py",
        "provider-console/src/App.jsx",
        "provider-console/src/continuity-review.js",
        "provider-console/scripts/runs-api.mjs",
        "provider-console/tests/runs-api.test.mjs",
        "provider-console/tests/continuity-review-contract.test.mjs",
        "provider-console/tests/continuity-review.test.mjs",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["provider_console"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "provider_console_python_tests",
            "provider_console_node_tests",
            "task_architecture_gate",
        ]

    python_argv = policy["checks"]["provider_console_python_tests"]["argv"]
    assert "tests/test_provider_console.py" in python_argv
    node_argv = policy["checks"]["provider_console_node_tests"]["argv"]
    assert node_argv == [
        "node",
        "--test",
        "provider-console/tests/runs-api.test.mjs",
        "provider-console/tests/continuity-review-contract.test.mjs",
    ]


def test_hyperframes_source_routes_to_composition_audio_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["src/ai_video/production/_hyperframes_source.py"], policy
    )

    assert report["categories"] == ["production_composition_audio"]
    assert report["fallback_paths"] == []
    assert report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "production_composition_audio_tests",
        "task_architecture_gate",
    ]


def test_production_policy_commands_cover_repository_mandatory_contract_tests() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    dependency_argv = policy["checks"]["production_dependency_tests"]["argv"]
    image_argv = policy["checks"]["production_image_tests"]["argv"]
    composition_audio_argv = policy["checks"][
        "production_composition_audio_tests"
    ]["argv"]

    for path in (
        "tests/test_production_models.py",
        "tests/test_production_project.py",
    ):
        assert path in dependency_argv
    for path in (
        "tests/test_production_models.py",
        "tests/test_production_registry.py",
        "tests/test_production_validation.py",
        "tests/test_production_project.py",
        "tests/test_comfy_client.py",
        "tests/test_workflow_loader.py",
    ):
        assert path in image_argv
    assert "tests/test_production_minimax_speech.py" in composition_audio_argv


def test_minimax_speech_adapter_routes_to_composition_audio_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/minimax_speech.py",
        "tests/test_production_minimax_speech.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert "production_composition_audio" in report["categories"]
        assert "production_composition_audio_tests" in report["check_ids"]


def test_root_level_credential_filenames_are_sensitive() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["client_secret.json", "credentials.json", "Client_Secret.json"], policy
    )

    assert report["changed_paths"] == []
    assert report["sensitive_paths"] == [
        "Client_Secret.json",
        "client_secret.json",
        "credentials.json",
    ]
    assert "full_tests" in report["check_ids"]


def test_nested_globstar_cache_paths_are_ignored() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["src/ai_video/__pycache__", "src/ai_video/__pycache__/module.pyc"],
        policy,
    )

    assert report["changed_paths"] == []
    assert report["ignored_paths"] == [
        "src/ai_video/__pycache__",
        "src/ai_video/__pycache__/module.pyc",
    ]


def test_video_recovery_change_routes_to_video_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/_video_continuity.py",
        "src/ai_video/production/video_artifact.py",
        "src/ai_video/production/video_dependency.py",
        "src/ai_video/production/_state_commit_video_candidate.py",
        "src/ai_video/production/_state_commit_video_continuity.py",
        "src/ai_video/production/_state_commit_video_activation.py",
        "src/ai_video/production/_state_commit_video_recovery.py",
        "tests/test_production_video_state_recovery.py",
        "tests/test_production_generated_video_e2e.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert "production_video_provider" in report["categories"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]

    provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    assert "tests/test_production_generated_video_e2e.py" in provider_argv


def test_continuity_evaluator_routes_to_review_and_video_provider_suites() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/continuity_evaluator.py",
        "src/ai_video/production/local_continuity_reviewer.py",
        "src/ai_video/production/continuity_review_coordinator.py",
        "tests/test_production_continuity_evaluator.py",
        "tests/test_production_local_continuity_reviewer.py",
        "tests/test_production_continuity_review_coordinator.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert set(report["categories"]) == {
            "production_review",
            "production_video_provider",
        }
        assert "production_review_tests" in report["check_ids"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]

    for check_id in ("production_review_tests", "production_video_provider_tests"):
        argv = policy["checks"][check_id]["argv"]
        assert "tests/test_production_continuity_evaluator.py" in argv
        assert "tests/test_production_local_continuity_reviewer.py" in argv
        assert "tests/test_production_continuity_review_coordinator.py" in argv


def test_minimax_adapters_route_to_video_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/minimax_h3.py",
        "src/ai_video/production/minimax_hailuo.py",
        "tests/test_production_minimax_h3.py",
        "tests/test_production_minimax_hailuo.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert "production_video_provider" in report["categories"]
        assert "production_video_provider_tests" in report["check_ids"]
    provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    assert "tests/test_production_minimax_h3.py" in provider_argv
    assert "tests/test_production_minimax_hailuo.py" in provider_argv


def test_h3_workflow_artifacts_route_to_video_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "workflows/bindings/minimax_h3_fl2va.json",
        "workflows/profiles/minimax_h3_fl2va_quality.json",
        "workflows/templates/minimax_h3_fl2va_api.json",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert "workflow" in report["categories"]
        assert "production_video_provider" in report["categories"]
        assert "workflow_tests" in report["check_ids"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]


def test_t8_native_turbo_v2_code_workflows_and_tests_route_to_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/_video_capability_fingerprint.py",
        "src/ai_video/production/comfy_t8_native_turbo_profile.py",
        "src/ai_video/production/comfy_t8_native_turbo_video.py",
        "workflows/bindings/minimax_h3_t8_ref2va_turbo_native_v2_binding.yaml",
        "workflows/profiles/minimax_h3_t8_i2va_turbo_native_v2.json",
        "workflows/templates/minimax_h3_t8_fl2va_turbo_native_v2_api.json",
        "tests/test_production_comfy_t8_native_turbo_video.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert "production_video_provider" in report["categories"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]
    provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    assert "tests/test_production_comfy_t8_native_turbo_video.py" in provider_argv


def test_seedance_adapter_and_extended_contracts_route_to_video_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/seedance.py",
        "src/ai_video/production/seedance_asset.py",
        "src/ai_video/production/seedance_capabilities.py",
        "src/ai_video/production/seedance_profile.py",
        "src/ai_video/production/video_contracts.py",
        "tests/test_production_seedance.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["production_video_provider"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]
    provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    assert "tests/test_production_seedance.py" in provider_argv


def test_production_test_helpers_route_to_their_contract_owners() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    shared = agent_harness.inspect_paths(["tests/production_project_factory.py"], policy)
    state = agent_harness.inspect_paths(["tests/helpers/p2a_crash_worker.py"], policy)
    bootstrap = agent_harness.inspect_paths(["tests/test_production_bootstrap.py"], policy)
    video = agent_harness.inspect_paths(["tests/paid_provider_support.py"], policy)

    assert shared["categories"] == ["production_shared_contracts"]
    assert "production_contract_tests" in shared["check_ids"]
    assert state["categories"] == ["production_state"]
    assert "production_state_tests" in state["check_ids"]
    assert bootstrap["categories"] == ["production_state"]
    assert "production_state_tests" in bootstrap["check_ids"]
    assert video["categories"] == ["production_video_provider"]
    assert "production_video_provider_tests" in video["check_ids"]


def test_approved_repair_freshness_routes_to_state_and_review_suites() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["src/ai_video/production/_repair_freshness.py"], policy
    )

    assert set(report["categories"]) == {"production_state", "production_review"}
    assert "production_state_tests" in report["check_ids"]
    assert "production_review_tests" in report["check_ids"]
    assert "task_architecture_gate" in report["check_ids"]


def test_shared_committer_helpers_route_to_full_production_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/_state_commit_common.py",
        "src/ai_video/production/_state_commit_contracts.py",
        "src/ai_video/production/_state_commit_io.py",
        "src/ai_video/production/_state_commit_transaction.py",
        "src/ai_video/production/_state_commit_recovery.py",
        "src/ai_video/production/_state_commit_recovery_fs.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert "production_shared_contracts" in report["categories"]
        assert "production_contract_tests" in report["check_ids"]


@pytest.mark.parametrize(
    ("path", "category", "check_id"),
    [
        (
            "src/ai_video/production/_state_commit_dependency.py",
            "production_dependency",
            "production_dependency_tests",
        ),
        (
            "src/ai_video/production/_state_commit_review.py",
            "production_review",
            "production_review_tests",
        ),
        (
            "src/ai_video/production/_state_commit_repair.py",
            "production_review",
            "production_review_tests",
        ),
        (
            "src/ai_video/production/_state_commit_voice_activation.py",
            "production_composition_audio",
            "production_composition_audio_tests",
        ),
        (
            "src/ai_video/production/_state_commit_render_lifecycle.py",
            "production_composition_audio",
            "production_composition_audio_tests",
        ),
    ],
)
def test_domain_committer_helpers_route_to_their_domain_suite(
    path: str, category: str, check_id: str
) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert category in report["categories"]
    assert check_id in report["check_ids"]


@pytest.mark.parametrize(
    "path",
    [
        ".gitattributes",
        ".agents/skills/open-video/SKILL.md",
        "skills-lock.json",
    ],
)
def test_project_skill_installation_routes_to_control_plane_harness(path: str) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert "control_plane" in report["categories"]
    assert "harness_tests" in report["check_ids"]


@pytest.mark.parametrize(
    ("path", "expected_categories"),
    [
        (
            "src/ai_video/production/video_requirement.py",
            {"provider_neutral_video_requirement", "production_video_provider"},
        ),
        (
            "src/ai_video/production/_video_requirement_routing.py",
            {"provider_neutral_video_requirement", "production_video_provider"},
        ),
        (
            "src/ai_video/production/video_compiler.py",
            {"provider_neutral_video_requirement", "production_video_provider"},
        ),
        (
            "src/ai_video/planning/video_planner.py",
            {"video_planning"},
        ),
        (
            "src/ai_video/production/_shot_router_contracts.py",
            {"production_shot_router"},
        ),
        (
            "src/ai_video/production/_shot_visual_resolver.py",
            {"production_shot_router"},
        ),
        (
            "src/ai_video/production/shot_router.py",
            {"production_shot_router"},
        ),
    ],
)
def test_provider_neutral_generation_paths_route_focused_contract(
    path: str,
    expected_categories: set[str],
) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert expected_categories.issubset(report["categories"])
    assert "provider_neutral_video_requirement_tests" in report["check_ids"]


def test_inspection_falls_back_to_full_tests_and_task_architecture_gate() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(["src/ai_video/new_surface.py"], policy)

    assert report["categories"] == []
    assert report["fallback_paths"] == ["src/ai_video/new_surface.py"]
    assert report["check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "full_tests",
        "task_architecture_gate",
    ]


def test_name_status_parser_keeps_both_sides_of_rename() -> None:
    payload = b"R100\0docs/old name.md\0docs/new name.md\0M\0README.md\0"

    assert agent_harness.parse_name_status_z(payload) == [
        "docs/old name.md",
        "docs/new name.md",
        "README.md",
    ]


def test_staged_scope_discovers_both_sides_of_real_git_rename(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    renamed = tmp_path / "renamed file.txt"
    tracked.rename(renamed)
    _git(tmp_path, "add", "tracked.txt", "renamed file.txt")

    scope = agent_harness.discover_scope(tmp_path, staged=True)

    assert scope["mode"] == "staged"
    assert scope["changed_paths"] == ["tracked.txt", "renamed file.txt"]


def test_completion_verification_rejects_explicit_or_empty_scope() -> None:
    with pytest.raises(ValueError, match="completion scope"):
        agent_harness.validate_completion_scope(
            {"mode": "explicit", "changed_paths": ["README.md"]}
        )
    with pytest.raises(ValueError, match="empty"):
        agent_harness.validate_completion_scope(
            {"mode": "staged", "changed_paths": []}
        )


def test_commit_range_completion_rejects_non_current_head_ref(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    initial_branch = _git(tmp_path, "branch", "--show-current").stdout.strip()
    _git(tmp_path, "switch", "-qc", "feature")
    tracked.write_text("feature\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-qm", "feature")
    _git(tmp_path, "switch", "-q", initial_branch)

    scope = agent_harness.discover_scope(
        tmp_path,
        base_ref=initial_branch,
        head_ref="feature",
    )

    assert scope["changed_paths"] == ["tracked.txt"]
    assert scope["closure_eligible"] is False
    with pytest.raises(ValueError, match="not closure eligible"):
        agent_harness.validate_completion_scope(scope)


def test_staged_snapshot_detects_index_drift(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    tracked.write_text("first\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")

    before = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")
    tracked.write_text("second\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    after = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")

    assert before["git_head"] == after["git_head"]
    assert before["changed_paths"] == ["tracked.txt"]
    assert before["index_tree"] != after["index_tree"]
    assert before["scope_sha256"] != after["scope_sha256"]


def test_git_scope_ignores_repository_redirect_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracked = _committed_repository(tmp_path)
    tracked.write_text("staged task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    expected = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "attacker.index"))
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "attacker.git"))

    actual = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")

    assert actual == expected
    scope = agent_harness.discover_scope(tmp_path, staged=True)
    with agent_harness.isolated_verification_workspace(tmp_path, scope) as checkout:
        assert (checkout / "tracked.txt").read_text(encoding="utf-8") == "staged task\n"


def test_scope_snapshot_rejects_discovery_drift() -> None:
    with pytest.raises(ValueError, match="scope changed before verification"):
        agent_harness.validate_scope_snapshot(
            {"changed_paths": ["one.py"]},
            {"changed_paths": ["one.py", "two.py"]},
        )


def test_scope_snapshot_rejects_head_drift() -> None:
    with pytest.raises(ValueError, match="HEAD changed"):
        agent_harness.validate_scope_snapshot(
            {"mode": "staged", "head_oid": "a" * 40, "changed_paths": ["one.py"]},
            {"mode": "staged", "git_head": "b" * 40, "changed_paths": ["one.py"]},
        )


def test_staged_workspace_rejects_index_drift_after_snapshot(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    tracked.write_text("first\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    scope = agent_harness.discover_scope(tmp_path, staged=True)
    snapshot = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")
    tracked.write_text("second\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")

    with pytest.raises(ValueError, match="source scope changed"):
        with agent_harness.isolated_verification_workspace(
            tmp_path, scope, source_snapshot=snapshot
        ):
            pytest.fail("drifted snapshot must not execute")


def test_staged_verification_workspace_excludes_unstaged_changes(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("baseline\n", encoding="utf-8")
    _git(tmp_path, "add", "unrelated.txt")
    _git(tmp_path, "commit", "-qm", "add unrelated")
    tracked.write_text("staged task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    unrelated.write_text("unrelated dirty work\n", encoding="utf-8")
    scope = agent_harness.discover_scope(tmp_path, staged=True)

    with agent_harness.isolated_verification_workspace(tmp_path, scope) as checkout:
        assert (checkout / "tracked.txt").read_text(encoding="utf-8") == "staged task\n"
        assert (checkout / "unrelated.txt").read_text(encoding="utf-8") == "baseline\n"


def test_verification_workspace_surfaces_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tracked = _committed_repository(tmp_path)
    tracked.write_text("staged task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    scope = agent_harness.discover_scope(tmp_path, staged=True)
    original_run = subprocess.run

    def fail_remove(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        argv = args[0]
        if isinstance(argv, list) and argv[:3] == ["git", "worktree", "remove"]:
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, argv)
            return subprocess.CompletedProcess(argv, 1, b"", b"cleanup failed")
        return original_run(*args, **kwargs)  # type: ignore[return-value]

    monkeypatch.setattr(subprocess, "run", fail_remove)

    with pytest.raises(subprocess.CalledProcessError):
        with agent_harness.isolated_verification_workspace(tmp_path, scope):
            pass


def test_verification_writes_integrity_bound_receipt_and_logs(tmp_path: Path) -> None:
    policy = _minimal_policy()
    inspection = {
        "changed_paths": ["src/example.py"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit"],
    }
    scope = {
        "mode": "commit_range",
        "changed_paths": ["src/example.py"],
        "base_ref": "HEAD^",
        "base_oid": "a" * 40,
        "head_ref": "HEAD",
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    snapshot = {"mode": "commit_range", "scope_sha256": "c" * 64}

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot=snapshot,
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="test-run",
        policy_sha256="d" * 64,
    )

    assert passed is True
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema"] == "ai-video-agent-harness-run/2"
    assert receipt["status"] == "passed"
    assert receipt["closure_eligible"] is True
    assert receipt["scope"] == scope
    assert receipt["source_snapshot_before"] == snapshot
    assert receipt["source_snapshot_after"] == snapshot
    assert receipt["workspace_stable"] is True
    assert receipt["checks"][0]["stdout"]["sha256"] == hashlib.sha256(
        b"ok\n"
    ).hexdigest()
    assert (receipt_path.parent / receipt["checks"][0]["stdout"]["path"]).is_file()
    assert agent_harness.verify_receipt_integrity(receipt) is True
    assert agent_harness.verify_receipt_artifacts(receipt, receipt_path.parent) is True

    stdout_path = receipt_path.parent / receipt["checks"][0]["stdout"]["path"]
    stdout_path.write_text("tampered\n", encoding="utf-8")
    assert agent_harness.verify_receipt_artifacts(receipt, receipt_path.parent) is False


def test_runner_exception_finalizes_failed_receipt(tmp_path: Path) -> None:
    policy = _minimal_policy()
    policy["checks"]["later"] = {
        "argv": [sys.executable, "-c", "print('later')"],
        "cwd": ".",
        "description": "Must be marked skipped.",
    }
    inspection = {
        "changed_paths": ["src/example.py"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit", "later"],
    }
    scope = {
        "mode": "commit_range",
        "changed_paths": ["src/example.py"],
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }

    def broken_runner(*_args: object, **_kwargs: object) -> agent_harness.CommandResult:
        raise RuntimeError("runner exploded")

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="failed-run",
        runner=broken_runner,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert passed is False
    assert receipt["status"] == "failed"
    assert receipt["checks"][0]["status"] == "failed"
    assert "runner exploded" in receipt["checks"][0]["error"]
    assert receipt["checks"][1]["status"] == "skipped"


def test_runner_times_out_without_shell(tmp_path: Path) -> None:
    result = agent_harness.run_command(
        (sys.executable, "-c", "import time; time.sleep(2)"),
        tmp_path,
        timeout_seconds=0.01,
        env=os.environ.copy(),
    )

    assert result.status == "timed_out"
    assert result.exit_code is None
    assert result.timed_out is True


def test_runner_timeout_terminates_descendant_processes(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    code = (
        "import pathlib, subprocess, sys, time; "
        "child = subprocess.Popen([sys.executable, '-c', "
        "'import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
        "time.sleep(60)"
    )
    child_pid: int | None = None
    try:
        result = agent_harness.run_command(
            (sys.executable, "-c", code),
            tmp_path,
            timeout_seconds=0.5,
            env=os.environ.copy(),
        )
        child_pid = int(child_pid_path.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.02)

        assert result.status == "timed_out"
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)
    finally:
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def test_check_argv_pins_policy_python_to_controller_interpreter() -> None:
    argv = agent_harness._check_argv(
        {"argv": ["python", "-m", "pytest", "-q"]},
        {"mode": "staged", "head_oid": "a" * 40},
        None,
    )

    assert argv[0] == sys.executable


def test_harness_environment_drops_credentials_and_proxies() -> None:
    env = agent_harness.build_check_environment(
        {
            "PATH": os.environ.get("PATH", ""),
            "OPENAI_API_KEY": "secret",
            "MINIMAX_TOKEN": "secret",
            "AWS_ACCESS_KEY_ID": "secret",
            "SSH_AUTH_SOCK": "/tmp/agent.sock",
            "HTTPS_PROXY": "http://proxy.invalid",
            "PYTEST_ADDOPTS": "--collect-only",
            "PYTEST_PLUGINS": "untrusted.plugin",
            "PYTHONPATH": "/tmp/untrusted",
        }
    )

    assert env["PATH"] == os.environ.get("PATH", "")
    assert env["AI_VIDEO_HARNESS_NO_NETWORK"] == "1"
    assert env["NO_PROXY"] == "127.0.0.1,localhost,::1"
    assert env["PYTEST_PLUGINS"] == "scripts.harness_pytest_guard"
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert "PYTEST_ADDOPTS" not in env
    assert "PYTHONPATH" not in env
    assert "OPENAI_API_KEY" not in env
    assert "MINIMAX_TOKEN" not in env
    assert "AWS_ACCESS_KEY_ID" not in env
    assert "SSH_AUTH_SOCK" not in env
    assert "HTTPS_PROXY" not in env


def test_network_guard_allows_loopback_and_rejects_external_hosts() -> None:
    assert harness_pytest_guard.is_loopback_host("localhost") is True
    assert harness_pytest_guard.is_loopback_host("127.0.0.1") is True
    assert harness_pytest_guard.is_loopback_host("::1") is True
    assert harness_pytest_guard.is_loopback_host("api.openai.com") is False
    with pytest.raises(RuntimeError, match="external network disabled"):
        harness_pytest_guard.require_loopback(("203.0.113.1", 443))


def test_network_guard_installation_blocks_external_dns() -> None:
    was_installed = harness_pytest_guard.network_guard_installed()
    harness_pytest_guard.remove_network_guard()
    harness_pytest_guard.install_network_guard()
    try:
        with pytest.raises(RuntimeError, match="DNS lookup rejected"):
            harness_pytest_guard.socket.getaddrinfo("api.openai.com", 443)
        with harness_pytest_guard.socket.socket(
            harness_pytest_guard.socket.AF_INET,
            harness_pytest_guard.socket.SOCK_DGRAM,
        ) as udp_socket:
            with pytest.raises(RuntimeError, match="non-loopback address rejected"):
                udp_socket.sendto(b"blocked", ("203.0.113.1", 443))
    finally:
        harness_pytest_guard.remove_network_guard()
        if was_installed:
            harness_pytest_guard.install_network_guard()


def test_receipt_integrity_detects_tampering() -> None:
    receipt = {"schema": "ai-video-agent-harness-run/2", "status": "passed"}
    agent_harness.seal_receipt(receipt)

    assert agent_harness.verify_receipt_integrity(receipt) is True
    receipt["status"] = "failed"
    assert agent_harness.verify_receipt_integrity(receipt) is False


def test_receipt_freshness_uses_the_selected_repository_policy(tmp_path: Path) -> None:
    _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    head_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": {
            "mode": "commit_range",
            "head_ref": "HEAD",
            "head_oid": head_oid,
        },
    }
    agent_harness.seal_receipt(receipt)

    report = agent_harness.receipt_freshness(receipt, tmp_path)

    assert report["policy_matches"] is True
    assert report["snapshot_matches"] is True
    assert report["fresh"] is True


def test_staged_receipt_becomes_stale_when_scope_gets_unstaged_edits(
    tmp_path: Path,
) -> None:
    tracked = _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    tracked.write_text("staged task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    scope = agent_harness.discover_scope(tmp_path, staged=True)
    snapshot = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": scope,
        "source_snapshot_after": snapshot,
    }
    agent_harness.seal_receipt(receipt)
    assert agent_harness.receipt_freshness(receipt, tmp_path)["fresh"] is True

    tracked.write_text("new unstaged edit\n", encoding="utf-8")

    report = agent_harness.receipt_freshness(receipt, tmp_path)
    assert report["scope_worktree_clean"] is False
    assert report["fresh"] is False


def test_staged_receipt_rejects_snapshot_from_different_head(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    scope_head = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("moves head\n", encoding="utf-8")
    _git(tmp_path, "add", "unrelated.txt")
    _git(tmp_path, "commit", "-qm", "move head")
    tracked.write_text("staged task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    scope = {
        "mode": "staged",
        "head_oid": scope_head,
        "changed_paths": ["tracked.txt"],
        "closure_eligible": True,
    }
    snapshot = agent_harness.capture_scope_snapshot(tmp_path, mode="staged")
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": scope,
        "source_snapshot_after": snapshot,
    }
    agent_harness.seal_receipt(receipt)

    report = agent_harness.receipt_freshness(receipt, tmp_path)

    assert report["snapshot_matches"] is False
    assert report["fresh"] is False


def test_commit_range_receipt_becomes_stale_after_new_staged_edit(
    tmp_path: Path,
) -> None:
    tracked = _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    tracked.write_text("committed task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-qm", "task")
    head_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": {
            "mode": "commit_range",
            "head_ref": "HEAD",
            "head_oid": head_oid,
            "changed_paths": ["tracked.txt"],
        },
    }
    agent_harness.seal_receipt(receipt)
    assert agent_harness.receipt_freshness(receipt, tmp_path)["fresh"] is True

    tracked.write_text("new staged edit\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")

    report = agent_harness.receipt_freshness(receipt, tmp_path)
    assert report["scope_worktree_clean"] is False
    assert report["fresh"] is False


def test_commit_range_freshness_uses_committed_policy_bytes(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    base_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    tracked.write_text("committed task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-qm", "task")
    head_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    scope = {
        "mode": "commit_range",
        "base_oid": base_oid,
        "head_ref": "HEAD",
        "head_oid": head_oid,
        "changed_paths": ["tracked.txt"],
    }
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": scope,
    }
    agent_harness.seal_receipt(receipt)
    policy_path.write_text("version: 999\n", encoding="utf-8")

    report = agent_harness.receipt_freshness(receipt, tmp_path)

    assert report["policy_matches"] is True
    assert report["scope_worktree_clean"] is True
    assert report["fresh"] is True


def test_commit_range_freshness_rejects_moved_head_ref(tmp_path: Path) -> None:
    tracked = _committed_repository(tmp_path)
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text("version: 2\n", encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    base_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    tracked.write_text("committed task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    _git(tmp_path, "commit", "-qm", "task")
    _git(tmp_path, "branch", "receipt-head")
    scope = agent_harness.discover_scope(
        tmp_path, base_ref=base_oid, head_ref="receipt-head"
    )
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "status": "passed",
        "closure_eligible": True,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "scope": scope,
    }
    agent_harness.seal_receipt(receipt)
    _git(tmp_path, "branch", "-f", "receipt-head", base_oid)

    report = agent_harness.receipt_freshness(receipt, tmp_path)

    assert report["snapshot_matches"] is False
    assert report["fresh"] is False


def test_repository_policy_audit_has_no_unmapped_owned_files() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.audit_policy_coverage(policy, ROOT)

    assert report["unmapped_paths"] == []
    assert report["unverified_paths"] == []
    assert report["missing_check_test_paths"] == []
    assert report["docs_contract_diagnostics"] == []

    canonical_docs = {
        "README.md",
        "docs/agent-primary-contract-matrix.md",
        "docs/v0.2-runtime-baseline.md",
        "docs/v0.2-agentic-production-roadmap.md",
        "docs/superpowers/specs/2026-08-21-ai-video-video-planner-subagent.md",
        "docs/superpowers/plans/2026-08-21-ai-video-shot-readiness-gate-v3.md",
    }
    assert canonical_docs.isdisjoint(report["unmapped_paths"])
    assert canonical_docs.isdisjoint(report["unverified_paths"])


def test_policy_audit_rejects_code_mapped_without_executable_check(
    tmp_path: Path,
) -> None:
    _committed_repository(tmp_path)
    source = tmp_path / "src/example.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "src/example.py")
    _git(tmp_path, "commit", "-qm", "add source")
    policy = _minimal_policy()
    policy["audit_patterns"] = ["src/*.py"]
    policy["categories"] = {
        "formal_only": {"patterns": ["src/*.py"], "check_ids": []}
    }

    report = agent_harness.audit_policy_coverage(policy, tmp_path)

    assert report["unmapped_paths"] == []
    assert report["unverified_paths"] == ["src/example.py"]


def test_makefile_exposes_completion_and_repository_harness_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "harness-inspect:" in makefile
    assert "harness-verify:" in makefile
    assert "harness-verify-range:" in makefile
    assert "harness-receipt:" in makefile
    assert "harness-audit:" in makefile
    assert "harness-repository:" in makefile
    assert "harness-test:" in makefile
