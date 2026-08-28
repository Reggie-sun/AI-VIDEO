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


def _complete_receipt_fixture(
    tmp_path: Path, *, mode: str = "commit_range"
) -> tuple[Path, Path, Path, dict[str, object]]:
    tracked = _committed_repository(tmp_path)
    policy = _minimal_policy()
    policy["checks"]["covered"] = {
        "argv": [sys.executable, "-c", "raise SystemExit('must not run')"],
        "cwd": ".",
        "covered_by_check_ids": ["unit"],
    }
    policy["categories"] = {
        "example": {
            "patterns": ["tracked.txt"],
            "check_ids": ["unit", "covered"],
        }
    }
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "add policy")
    base_oid = _git(tmp_path, "rev-parse", "HEAD").stdout.strip()
    tracked.write_text(f"{mode} task\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")
    if mode == "commit_range":
        _git(tmp_path, "commit", "-qm", "task")
        scope = agent_harness.discover_scope(
            tmp_path, base_ref=base_oid, head_ref="HEAD"
        )
    elif mode == "staged":
        scope = agent_harness.discover_scope(tmp_path, staged=True)
    else:
        raise ValueError(f"unsupported receipt fixture mode: {mode}")
    loaded_policy = agent_harness.load_policy(policy_path)
    inspection = agent_harness.inspect_paths(scope["changed_paths"], loaded_policy)
    snapshot = agent_harness._scope_snapshot(tmp_path, scope)
    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        loaded_policy,
        scope=scope,
        source_snapshot=snapshot,
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id=f"complete-{mode}",
        policy_sha256=hashlib.sha256(policy_path.read_bytes()).hexdigest(),
    )
    assert passed is True
    return receipt_path, tracked, policy_path, scope


def test_repository_policy_v2_loads_and_references_known_checks() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    assert policy["version"] == 2
    assert policy["runs_dir"] == ".agent/harness/runs"
    assert policy["always_check_ids"] == [
        "scope_diff_check",
        "docs_contract_check",
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
    ]
    assert policy["checks"]["policy_audit_check"]["argv"] == [
        "python",
        "-m",
        "scripts.agent_harness",
        "policy-audit",
    ]
    assert policy["checks"]["policy_audit_check"]["execution_priority"] == 15
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


def test_policy_rejects_unknown_coverage_dependency(tmp_path: Path) -> None:
    policy = _minimal_policy()
    policy["checks"]["unit"]["covered_by_check_ids"] = ["missing"]
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown checks.*missing"):
        agent_harness.load_policy(policy_path)


def test_policy_rejects_cyclic_check_coverage(tmp_path: Path) -> None:
    policy = _minimal_policy()
    policy["checks"]["unit"]["covered_by_check_ids"] = ["other"]
    policy["checks"]["other"] = {
        "argv": [sys.executable, "-c", "print('other')"],
        "cwd": ".",
        "covered_by_check_ids": ["unit"],
    }
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(ValueError, match="coverage contains a cycle"):
        agent_harness.load_policy(policy_path)


def test_policy_rejects_invalid_execution_priority(tmp_path: Path) -> None:
    policy = _minimal_policy()
    policy["checks"]["unit"]["execution_priority"] = "fast"
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(ValueError, match="execution_priority must be an integer"):
        agent_harness.load_policy(policy_path)


def test_policy_rejects_unsafe_npm_workspace_dependency_path(
    tmp_path: Path,
) -> None:
    policy = _minimal_policy()
    policy["checks"]["unit"]["npm_workspace_dependency_paths"] = [
        "../node_modules"
    ]
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(ValueError, match="npm workspace dependency path"):
        agent_harness.load_policy(policy_path)


def test_policy_rejects_unknown_reverse_coverage_target(tmp_path: Path) -> None:
    policy = _minimal_policy()
    policy["checks"]["unit"]["covers_check_ids"] = ["missing"]
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown checks.*missing"):
        agent_harness.load_policy(policy_path)


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
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
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
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
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


def test_local_comfyui_supervisor_routes_to_focused_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    assert policy["checks"]["local_comfyui_supervisor_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_comfyui_supervisor.py",
        "-q",
    ]
    for path in (
        "scripts/comfyui_supervisor.py",
        "tests/test_comfyui_supervisor.py",
    ):
        report = agent_harness.inspect_paths([path], policy)

        assert report["categories"] == ["local_comfyui_supervisor"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "local_comfyui_supervisor_tests",
        ]


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
    setup_node = steps["Set up Node"]
    assert setup_node["uses"] == (
        "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020"
    )
    assert setup_node["with"] == {
        "node-version": "22.21.0",
        "package-manager-cache": False,
    }
    node_condition = "steps.harness-routes.outputs.npm_dependencies == 'true'"
    assert setup_node["if"] == node_condition
    install_node = steps["Install Provider Console test dependencies"]
    assert install_node["if"] == node_condition
    assert install_node["run"] == (
        "npm ci --ignore-scripts --prefix provider-console"
    )
    step_names = [step["name"] for step in verify_job["steps"]]
    assert step_names.index("Install test dependencies") < step_names.index(
        "Inspect exact PR routes"
    )
    assert step_names.index("Install Provider Console test dependencies") < (
        step_names.index("Audit Harness policy")
    )
    inspect_routes = steps["Inspect exact PR routes"]
    assert inspect_routes["id"] == "harness-routes"
    assert "npm_workspace_dependency_paths" in inspect_routes["run"]
    assert '--base-ref "${BASE_SHA}"' in inspect_routes["run"]
    assert '--head-ref "${HEAD_SHA}"' in inspect_routes["run"]
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

    for path in (
        "src/ai_video/production/models.py",
        "src/ai_video/production/_immutable_models.py",
        "src/ai_video/production/_state_lifecycle.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["production_shared_contracts"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "production_contract_tests",
            "cli_config_tests",
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
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "production_shot_router_tests",
            "provider_neutral_video_requirement_tests",
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
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "video_planner_tests",
            "provider_neutral_video_requirement_tests",
            "shot_readiness_gate_tests",
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
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "shot_readiness_gate_tests",
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
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
        "task_architecture_gate",
        "video_planner_tests",
        "provider_neutral_video_requirement_tests",
        "shot_readiness_gate_tests",
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
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "quality_intelligence_tests",
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


def test_agent_memory_routes_to_its_focused_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/agent_memory/indexer.py",
        "scripts/agent_memory.py",
        "tests/test_agent_memory.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["agent_memory_dev_tool"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "agent_memory_tests",
        ]
        assert report["npm_workspace_dependency_paths"] == []

    assert policy["checks"]["agent_memory_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_agent_memory.py",
        "-q",
    ]


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


def test_provider_console_bridge_routes_to_python_and_node_contracts() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/provider_console.py",
        "src/ai_video/provider_console_continuity.py",
        "tests/test_provider_console.py",
        "provider-console/scripts/experiment-evidence.mjs",
        "provider-console/scripts/external-media.mjs",
        "provider-console/scripts/runs-api.mjs",
        "provider-console/tests/external-media.test.mjs",
        "provider-console/tests/runs-api.test.mjs",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["provider_console"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "provider_console_python_tests",
            "provider_console_node_tests",
        ]
        assert report["npm_workspace_dependency_paths"] == [
            "provider-console/node_modules"
        ]

    python_argv = policy["checks"]["provider_console_python_tests"]["argv"]
    assert "tests/test_provider_console.py" in python_argv


def test_provider_console_web_routes_to_node_contracts() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "provider-console/src/App.jsx",
        "provider-console/src/continuity-review.js",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["provider_console_web"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "provider_console_node_tests",
            "provider_console_web_build",
        ]
        assert report["npm_workspace_dependency_paths"] == [
            "provider-console/node_modules"
        ]

    for path in (
        "provider-console/tests/continuity-review-contract.test.mjs",
        "provider-console/tests/continuity-review.test.mjs",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["provider_console_web_tests"]
        assert report["fallback_paths"] == []
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "provider_console_node_tests",
        ]
        assert report["npm_workspace_dependency_paths"] == [
            "provider-console/node_modules"
        ]

    node_argv = policy["checks"]["provider_console_node_tests"]["argv"]
    assert node_argv == [
        "node",
        "--test",
        "provider-console/tests/runs-api.test.mjs",
        "provider-console/tests/external-media.test.mjs",
        "provider-console/tests/continuity-review-contract.test.mjs",
        "provider-console/tests/continuity-review.test.mjs",
    ]
    assert policy["checks"]["provider_console_web_build"]["argv"] == [
        "npm",
        "exec",
        "--offline",
        "--",
        "vite",
        "build",
    ]
    assert policy["checks"]["provider_console_web_build"]["cwd"] == (
        "provider-console"
    )

    for path in (
        "provider-console/.npmrc",
        "provider-console/worker/index.js",
        "provider-console/scripts/prepare-sites-build.mjs",
        "provider-console/tests/sites-worker.test.mjs",
        "provider-console/.openai/hosting.json",
        "provider-console/index.html",
        "provider-console/package.json",
        "provider-console/package-lock.json",
        "provider-console/public/assets/alice-cafe-first-frame.png",
        "provider-console/vite.config.mjs",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert report["categories"] == ["provider_console_sites"]
        assert report["check_ids"] == [
            "scope_diff_check",
            "docs_contract_check",
            "policy_audit_check",
            "product_runtime_skill_boundary_tests",
            "task_architecture_gate",
            "provider_console_sites_build",
            "provider_console_sites_tests",
        ]
        assert report["npm_workspace_dependency_paths"] == [
            "provider-console/node_modules"
        ]

    assert policy["checks"]["provider_console_sites_build"]["argv"] == [
        "npm",
        "--prefix",
        "provider-console",
        "run",
        "build",
    ]
    assert policy["checks"]["provider_console_sites_tests"]["argv"] == [
        "node",
        "--test",
        "provider-console/tests/sites-worker.test.mjs",
    ]


def test_every_tracked_provider_console_path_has_an_explicit_route() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    tracked_paths = subprocess.run(
        ["git", "ls-files", "-z", "provider-console"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")

    for raw_path in tracked_paths:
        if not raw_path:
            continue
        path = raw_path.decode("utf-8", "surrogateescape")
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == [], path


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
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
        "task_architecture_gate",
        "production_composition_audio_tests",
    ]


def test_ad_creative_runtime_routes_to_composition_audio_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/ad_composition.py",
        "src/ai_video/production/ad_creative.py",
        "src/ai_video/production/ad_creative_review.py",
        "src/ai_video/production/ad_creative_types.py",
        "src/ai_video/production/commercial_graphics.py",
        "src/ai_video/production/composition_contracts.py",
        "tests/test_production_ad_creative.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["categories"] == ["production_composition_audio"]
        assert report["fallback_paths"] == []
        assert "production_composition_audio_tests" in report["check_ids"]

    assert "tests/test_production_ad_creative.py" in policy["checks"][
        "production_composition_audio_tests"
    ]["argv"]

    artifact_report = agent_harness.inspect_paths(
        ["src/ai_video/production/artifact_contracts.py"], policy
    )
    assert artifact_report["categories"] == ["production_shared_contracts"]
    assert artifact_report["fallback_paths"] == []
    assert "production_contract_tests" in artifact_report["check_ids"]


def test_commercial_source_preparation_routes_to_focused_cross_owner_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/planning/_commercial_video_planning.py",
        "src/ai_video/production/_commercial_source_state.py",
        "src/ai_video/production/_commercial_project_reader.py",
        "src/ai_video/production/commercial_execution.py",
        "src/ai_video/production/commercial_dependency.py",
        "src/ai_video/production/commercial_image_import.py",
        "src/ai_video/production/commercial_reference.py",
        "src/ai_video/production/commercial_source_preparation.py",
        "src/ai_video/production/commercial_visual_review.py",
        "src/ai_video/production/_state_commit_commercial_source.py",
        "src/ai_video/production/_state_commit_commercial_source_recovery.py",
        "tests/test_production_commercial_execution.py",
        "tests/test_production_commercial_reference.py",
        "tests/test_production_commercial_source_preparation.py",
        "tests/test_production_commercial_visual_review.py",
        "tests/test_production_ecommerce_product_interaction_e2e.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == [], path
        assert "commercial_source_preparation_tests" in report["check_ids"], path

    command = policy["checks"]["commercial_source_preparation_tests"]["argv"]
    for path in (
        "tests/test_production_commercial_execution.py",
        "tests/test_production_commercial_reference.py",
        "tests/test_production_commercial_source_preparation.py",
        "tests/test_production_commercial_visual_review.py",
        "tests/test_production_ecommerce_product_interaction_e2e.py",
    ):
        assert path in command


def test_production_policy_commands_cover_repository_mandatory_contract_tests() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    dependency_argv = policy["checks"]["production_dependency_tests"]["argv"]
    image_argv = policy["checks"]["production_image_tests"]["argv"]
    composition_audio_argv = policy["checks"][
        "production_composition_audio_tests"
    ]["argv"]
    video_provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    state_argv = policy["checks"]["production_state_tests"]["argv"]

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
    for path in (
        "tests/test_production_state_commit.py",
        "tests/test_production_state_recovery.py",
    ):
        assert path in state_argv
        assert path not in video_provider_argv


def test_production_policy_declares_only_complete_cross_check_coverage() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    assert policy["checks"]["production_reader_tests"]["covered_by_check_ids"] == [
        "production_contract_tests",
        "cli_config_tests",
    ]
    for check_id in (
        "production_state_tests",
        "production_composition_audio_tests",
        "production_dependency_tests",
        "production_video_provider_tests",
        "production_shot_router_tests",
    ):
        assert policy["checks"][check_id]["covered_by_check_ids"] == [
            "production_contract_tests"
        ]
    for check_id in (
        "production_review_tests",
        "production_image_tests",
        "provider_neutral_video_requirement_tests",
    ):
        assert "covered_by_check_ids" not in policy["checks"][check_id]

    python_pytest_check_ids = {
        check_id
        for check_id, check in policy["checks"].items()
        if check_id != "full_tests" and "pytest" in check["argv"]
    }
    assert set(policy["checks"]["full_tests"]["covers_check_ids"]) == (
        python_pytest_check_ids
    )


def test_fail_fast_order_and_full_suite_reverse_coverage(tmp_path: Path) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    inspection = agent_harness.inspect_paths(
        ["src/ai_video/production/seedance.py", "unmapped.task"], policy
    )

    assert inspection["check_ids"][:5] == [
        "scope_diff_check",
        "docs_contract_check",
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
        "task_architecture_gate",
    ]
    assert inspection["check_ids"].index("full_tests") < inspection["check_ids"].index(
        "production_video_provider_tests"
    )

    scope = {
        "mode": "commit_range",
        "changed_paths": inspection["changed_paths"],
        "base_oid": "a" * 40,
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    argv_to_check_id = {
        tuple(agent_harness._check_argv(policy["checks"][check_id], scope, None)): check_id
        for check_id in inspection["check_ids"]
    }
    executed: list[str] = []

    def recording_runner(
        argv: tuple[str, ...],
        _cwd: Path,
        _timeout_seconds: float,
        _env: dict[str, str],
    ) -> agent_harness.CommandResult:
        argv_without_junit = tuple(
            argument for argument in argv if not argument.startswith("--junitxml=")
        )
        executed.append(argv_to_check_id[argv_without_junit])
        return agent_harness.CommandResult(
            status="passed", exit_code=0, stdout="ok\n", stderr=""
        )

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="fail-fast-full-coverage",
        runner=recording_runner,
    )

    assert passed is True
    assert executed == [
        "scope_diff_check",
        "docs_contract_check",
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
        "task_architecture_gate",
        "full_tests",
    ]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["npm_workspace_dependency_paths"] == []
    assert {
        check["check_id"]
        for check in receipt["checks"]
        if check["status"] == "skipped"
    } >= {
        "production_video_provider_tests",
        "provider_neutral_video_requirement_tests",
    }


def test_policy_audit_failure_stops_before_expensive_checks(tmp_path: Path) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    inspection = agent_harness.inspect_paths(
        ["src/ai_video/production/seedance.py", "unmapped.task"], policy
    )
    scope = {
        "mode": "commit_range",
        "changed_paths": inspection["changed_paths"],
        "base_oid": "a" * 40,
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    argv_to_check_id = {
        tuple(agent_harness._check_argv(policy["checks"][check_id], scope, None)): check_id
        for check_id in inspection["check_ids"]
    }
    executed: list[str] = []

    def failing_audit_runner(
        argv: tuple[str, ...],
        _cwd: Path,
        _timeout_seconds: float,
        _env: dict[str, str],
    ) -> agent_harness.CommandResult:
        argv_without_junit = tuple(
            argument for argument in argv if not argument.startswith("--junitxml=")
        )
        check_id = argv_to_check_id[argv_without_junit]
        executed.append(check_id)
        if check_id == "policy_audit_check":
            return agent_harness.CommandResult(
                status="failed", exit_code=1, stdout="unmapped\n", stderr=""
            )
        return agent_harness.CommandResult(
            status="passed", exit_code=0, stdout="ok\n", stderr=""
        )

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="policy-audit-fail-fast",
        runner=failing_audit_runner,
    )

    assert passed is False
    assert executed == [
        "scope_diff_check",
        "docs_contract_check",
        "policy_audit_check",
    ]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "failed"
    assert receipt["checks"][2]["check_id"] == "policy_audit_check"
    assert receipt["checks"][2]["status"] == "failed"
    assert all(
        check["status"] == "skipped" for check in receipt["checks"][3:]
    )
    assert all(
        check["reason"] == "blocked by failed check policy_audit_check"
        for check in receipt["checks"][3:]
    )


def test_repository_production_coverage_executes_only_uncovered_checks(
    tmp_path: Path,
) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    selected_check_ids = [
        "production_contract_tests",
        "cli_config_tests",
        "production_reader_tests",
        "production_state_tests",
        "production_composition_audio_tests",
        "production_dependency_tests",
        "production_review_tests",
        "production_image_tests",
        "production_video_provider_tests",
        "provider_neutral_video_requirement_tests",
        "production_shot_router_tests",
    ]
    inspection = {
        "changed_paths": ["src/ai_video/production/models.py"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["production_shared_contracts"],
        "fallback_paths": [],
        "check_ids": selected_check_ids,
    }
    scope = {
        "mode": "commit_range",
        "changed_paths": inspection["changed_paths"],
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    executed_check_ids: list[str] = []
    argv_to_check_id = {
        tuple(
            agent_harness._check_argv(policy["checks"][check_id], scope, None)
        ): check_id
        for check_id in selected_check_ids
    }

    def recording_runner(
        argv: tuple[str, ...],
        _cwd: Path,
        _timeout_seconds: float,
        _env: dict[str, str],
    ) -> agent_harness.CommandResult:
        argv_without_junit = tuple(
            argument for argument in argv if not argument.startswith("--junitxml=")
        )
        executed_check_ids.append(argv_to_check_id[argv_without_junit])
        return agent_harness.CommandResult(
            status="passed", exit_code=0, stdout="ok\n", stderr=""
        )

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="repository-coverage-run",
        runner=recording_runner,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert passed is True
    assert receipt["selected_check_ids"] == selected_check_ids
    assert executed_check_ids == [
        "production_contract_tests",
        "cli_config_tests",
        "production_review_tests",
        "production_image_tests",
        "provider_neutral_video_requirement_tests",
    ]
    assert {
        check["check_id"]
        for check in receipt["checks"]
        if check["status"] == "skipped"
    } == {
        "production_reader_tests",
        "production_state_tests",
        "production_composition_audio_tests",
        "production_dependency_tests",
        "production_video_provider_tests",
        "production_shot_router_tests",
    }


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


def test_video_execution_control_paths_route_to_complete_provider_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        "src/ai_video/production/video_candidate.py",
        "src/ai_video/production/video_generation.py",
        "tests/test_video_candidate.py",
        "tests/test_video_generation.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert "production_video_provider" in report["categories"]
        assert "production_video_provider_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]

    provider_argv = policy["checks"]["production_video_provider_tests"]["argv"]
    production_argv = policy["checks"]["production_contract_tests"]["argv"]
    for path in ("tests/test_video_candidate.py", "tests/test_video_generation.py"):
        assert path in provider_argv
    assert "production or video_candidate or video_generation" in production_argv


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


def test_shot_continuity_p0_surfaces_route_to_exact_offline_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)
    paths = (
        "scripts/materialize_shot_continuity_m0.py",
        "scripts/prepare_shot_continuity_endpoint_repair.py",
        "scripts/prepare_shot_continuity_p0.py",
        "scripts/execute_shot_continuity_source.py",
        "src/ai_video/production/execution_stack_materialization.py",
        "src/ai_video/production/_state_commit_p0_qualification.py",
        "src/ai_video/production/shot_continuity_m0_qualification.py",
        "src/ai_video/production/shot_continuity_m0_fast_validation.py",
        "src/ai_video/production/shot_continuity_m0_policy.py",
        "src/ai_video/production/shot_continuity_source_qualification.py",
        "src/ai_video/production/shot_continuity_source_operator.py",
        "src/ai_video/production/shot_continuity_source_contracts.py",
        "src/ai_video/production/shot_continuity_source_runtime.py",
        "src/ai_video/production/shot_continuity_source_schema.py",
        "src/ai_video/production/shot_continuity_source_transport.py",
        "src/ai_video/production/video_candidate_composition.py",
        "src/ai_video/production/video_execution_stack.py",
        "src/ai_video/production/video_transition.py",
        "tests/fixtures/shot_continuity/m0_fast_v1_prepared_receipt.json",
        "tests/test_prepare_shot_continuity_endpoint_repair.py",
        "tests/test_prepare_shot_continuity_p0.py",
        "tests/test_production_p0_qualification.py",
        "tests/test_production_video_transition.py",
        "tests/test_shot_continuity_m0_materialization.py",
        "tests/test_shot_continuity_m0_fast_validation.py",
        "tests/test_shot_continuity_m0_policy.py",
        "tests/test_shot_continuity_m0_policy_preparation.py",
        "tests/test_shot_continuity_m0_validation.py",
        "tests/test_shot_continuity_source_qualification.py",
        "tests/test_shot_continuity_source_operator.py",
        "tests/test_shot_continuity_source_runtime.py",
        "tests/test_shot_continuity_source_transport.py",
        "workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json",
        "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_api.json",
        "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_binding.yaml",
        "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json",
        "workflows/qualification/minimax_h3_t8_c4_m0_fast_v1_api.json",
        "workflows/qualification/minimax_h3_t8_c4_m0_fast_v1_binding.yaml",
        "workflows/qualification/minimax_h3_t8_c4_m0_fast_v1_profile.json",
    )
    provider_lifecycle_paths = {
        "src/ai_video/production/shot_continuity_source_qualification.py",
        "src/ai_video/production/shot_continuity_source_operator.py",
        "src/ai_video/production/shot_continuity_source_contracts.py",
        "src/ai_video/production/shot_continuity_source_runtime.py",
        "src/ai_video/production/shot_continuity_source_schema.py",
        "src/ai_video/production/shot_continuity_source_transport.py",
        "src/ai_video/production/video_candidate_composition.py",
        "scripts/execute_shot_continuity_source.py",
        "tests/test_shot_continuity_source_qualification.py",
        "tests/test_shot_continuity_source_operator.py",
        "tests/test_shot_continuity_source_runtime.py",
        "tests/test_shot_continuity_source_transport.py",
    }
    production_state_paths = {
        "src/ai_video/production/_state_commit_p0_qualification.py",
    }

    for path in paths:
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert "shot_continuity_p0" in report["categories"]
        if path.startswith("workflows/qualification/"):
            assert "workflow" in report["categories"]
        elif path in provider_lifecycle_paths:
            assert set(report["categories"]) == {
                "production_video_provider",
                "shot_continuity_p0",
            }
            assert "production_video_provider_tests" in report["check_ids"]
        elif path in production_state_paths:
            assert set(report["categories"]) == {
                "production_state",
                "shot_continuity_p0",
            }
            assert "production_state_tests" in report["check_ids"]
        else:
            assert report["categories"] == ["shot_continuity_p0"]
        assert "shot_continuity_p0_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]

    argv = policy["checks"]["shot_continuity_p0_tests"]["argv"]
    for path in (
        "tests/test_prepare_shot_continuity_endpoint_repair.py",
        "tests/test_prepare_shot_continuity_p0.py",
        "tests/test_production_p0_qualification.py",
        "tests/test_production_video_transition.py",
        "tests/test_shot_continuity_m0_materialization.py",
        "tests/test_shot_continuity_m0_fast_validation.py",
        "tests/test_shot_continuity_m0_policy.py",
        "tests/test_shot_continuity_m0_policy_preparation.py",
        "tests/test_shot_continuity_m0_validation.py",
        "tests/test_shot_continuity_source_qualification.py",
        "tests/test_shot_continuity_source_operator.py",
        "tests/test_shot_continuity_source_runtime.py",
        "tests/test_shot_continuity_source_transport.py",
        "tests/test_video_candidate.py",
    ):
        assert path in argv


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
        (
            "src/ai_video/production/_state_commit_video.py",
            "production_video_provider",
            "production_video_provider_tests",
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
    assert "production_state" in report["categories"]
    assert "production_state_tests" in report["check_ids"]


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
    "path",
    [
        ".agents/skills/ecommerce-ad-workflow/SKILL.md",
        ".agents/skills/ecommerce-ad-workflow/references/hooks.md",
        ".agents/skills/ecommerce-ad-workflow/schemas/ecommerce-ad-input.schema.json",
        ".agents/skills/ecommerce-ad-workflow/templates/30s-vertical-product-ad.package.example.json",
        ".agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py",
    ],
)
def test_ecommerce_ad_skill_paths_route_to_focused_and_control_plane_checks(
    path: str,
) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert report["fallback_paths"] == []
    assert {"control_plane", "ecommerce_ad_workflow"}.issubset(
        report["categories"]
    )
    assert {
        "ecommerce_ad_workflow_skill_tests",
        "harness_tests",
    }.issubset(report["check_ids"])
    assert "production_contract_tests" not in report["check_ids"]
    assert "production_video_provider_tests" not in report["check_ids"]


def test_ecommerce_ad_contract_test_has_an_exact_focused_route() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        ["tests/test_ecommerce_ad_workflow_skill.py"], policy
    )

    assert report["fallback_paths"] == []
    assert "ecommerce_ad_workflow" in report["categories"]
    assert "ecommerce_ad_workflow_skill_tests" in report["check_ids"]
    assert policy["checks"]["ecommerce_ad_workflow_skill_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_ecommerce_ad_workflow_skill.py",
        "-q",
    ]


@pytest.mark.parametrize(
    "path",
    [
        ".agents/skills/seedance-authoring/SKILL.md",
        ".agents/skills/seedance-authoring/references/authoring-common.md",
        ".agents/skills/seedance-authoring/references/seedance-2.0.md",
        ".agents/skills/seedance-authoring/references/seedance-2.5.md",
        "tests/test_seedance_authoring_skill.py",
    ],
)
def test_seedance_authoring_paths_have_one_focused_route(path: str) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert report["fallback_paths"] == []
    assert "seedance_authoring" in report["categories"]
    assert "seedance_authoring_skill_tests" in report["check_ids"]
    assert "production_contract_tests" not in report["check_ids"]
    assert "production_video_provider_tests" not in report["check_ids"]
    assert policy["checks"]["seedance_authoring_skill_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_seedance_authoring_skill.py",
        "-q",
    ]


@pytest.mark.parametrize(
    "path",
    [
        "src/ai_video/production/video.py",
        "src/ai_video/planning/video_planner.py",
        "tests/test_runtime_skill_boundary.py",
    ],
)
def test_product_runtime_paths_select_agent_skill_boundary_guard(path: str) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert report["fallback_paths"] == []
    assert "product_runtime_skill_boundary_tests" in report["check_ids"]
    assert "product_runtime_skill_boundary_tests" in policy["always_check_ids"]
    if path == "tests/test_runtime_skill_boundary.py":
        assert "product_runtime_skill_boundary_test" in report["categories"]
    assert policy["checks"]["product_runtime_skill_boundary_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_runtime_skill_boundary.py",
        "-q",
    ]


def test_session_record_hook_routes_to_control_plane_harness() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        ".codex/hooks.json",
        ".agents/skills/record-ai-video-session/scripts/session_record_hook.py",
        "tests/test_record_ai_video_session_hook.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert "control_plane" in report["categories"]
        assert "harness_tests" in report["check_ids"]

    harness_argv = policy["checks"]["harness_tests"]["argv"]
    assert "tests/test_record_ai_video_session_hook.py" in harness_argv


def test_experience_learning_skill_routes_to_focused_suite() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    for path in (
        ".agents/skills/distill-ai-video-learning/SKILL.md",
        ".agents/skills/distill-ai-video-learning/templates/learning-claim.md",
        "docs/record_for_agent/learning/example-claim.md",
        "tests/test_distill_ai_video_learning_skill.py",
    ):
        report = agent_harness.inspect_paths([path], policy)
        assert report["fallback_paths"] == []
        assert "experience_learning" in report["categories"]
        assert "experience_learning_skill_tests" in report["check_ids"]
        assert "task_architecture_gate" in report["check_ids"]

    assert policy["checks"]["experience_learning_skill_tests"]["argv"] == [
        "python",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "tests/test_distill_ai_video_learning_skill.py",
        "-q",
    ]


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
        "policy_audit_check",
        "product_runtime_skill_boundary_tests",
        "task_architecture_gate",
        "full_tests",
    ]


@pytest.mark.parametrize(
    ("path", "expected_category"),
    [
        (".architecture/architecture-baseline.json", "architecture_tooling"),
        (".codex/config.toml", "control_plane"),
        (".mcp.json", "control_plane"),
        ("configs/example.project.yaml", "legacy_cli_config"),
        ("package.json", "renderer_toolchain"),
        ("package-lock.json", "renderer_toolchain"),
        ("pyproject.toml", "python_toolchain"),
        ("tests/fixtures/generated_video/fake-video.mp4", "production_video_provider"),
        (
            "tests/fixtures/hyperframes/silent_image/timeline.json",
            "production_composition_audio",
        ),
        ("tests/fixtures/p7_1/flux_profile.json", "production_image"),
        (
            "tests/fixtures/voice_captions/elevenlabs-with-timestamps.json",
            "production_composition_audio",
        ),
        ("tests/fixtures/wan22_i2v_ui.json", "workflow"),
    ],
)
def test_previously_broad_fallback_paths_have_explicit_owners(
    path: str, expected_category: str
) -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths([path], policy)

    assert expected_category in report["categories"]
    assert report["fallback_paths"] == []


def test_non_authoritative_workflow_and_codegraph_artifacts_are_ignored() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(
        [".workflow/active/example/workflow-session.json", "index.json"], policy
    )

    assert report["changed_paths"] == []
    assert report["ignored_paths"] == [
        ".workflow/active/example/workflow-session.json",
        "index.json",
    ]
    assert report["fallback_paths"] == []


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


def test_materialize_npm_workspace_dependencies_links_lock_matched_tree(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "source"
    execution_root = tmp_path / "checkout"
    source_modules = project_root / "provider-console/node_modules"
    target_package = execution_root / "provider-console"
    source_modules.mkdir(parents=True)
    target_package.mkdir(parents=True)
    locked_package = {
        "version": "1.0.0",
        "resolved": "https://registry.example.invalid/react.tgz",
        "integrity": "sha512-example",
    }
    repository_lock = {
        "lockfileVersion": 3,
        "packages": {
            "": {"dependencies": {"react": "1.0.0"}},
            "node_modules/react": locked_package,
        },
    }
    installed_lock = {
        "lockfileVersion": 3,
        "packages": {"node_modules/react": locked_package},
    }
    (target_package / "package-lock.json").write_text(
        json.dumps(repository_lock), encoding="utf-8"
    )
    (source_modules / ".package-lock.json").write_text(
        json.dumps(installed_lock), encoding="utf-8"
    )
    policy = _minimal_policy()
    policy["checks"]["unit"]["npm_workspace_dependency_paths"] = [
        "provider-console/node_modules"
    ]

    linked = agent_harness.materialize_npm_workspace_dependencies(
        project_root,
        execution_root,
        policy,
        ["unit"],
    )

    target_modules = execution_root / "provider-console/node_modules"
    assert linked == ["provider-console/node_modules"]
    assert target_modules.is_symlink()
    assert target_modules.resolve() == source_modules.resolve()

    installed_lock["packages"]["node_modules/react"]["version"] = "2.0.0"
    target_modules.unlink()
    (source_modules / ".package-lock.json").write_text(
        json.dumps(installed_lock), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="does not match exact package-lock"):
        agent_harness.materialize_npm_workspace_dependencies(
            project_root,
            execution_root,
            policy,
            ["unit"],
        )


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


def test_verification_records_covered_check_without_executing_it(
    tmp_path: Path,
) -> None:
    policy = _minimal_policy()
    policy["checks"]["covered"] = {
        "argv": [sys.executable, "-c", "raise SystemExit('must not run')"],
        "cwd": ".",
        "description": "Covered by the unit check.",
        "covered_by_check_ids": ["unit"],
    }
    inspection = {
        "changed_paths": ["src/example.py"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit", "covered"],
    }
    scope = {
        "mode": "commit_range",
        "changed_paths": ["src/example.py"],
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    executed: list[tuple[str, ...]] = []

    def recording_runner(
        argv: tuple[str, ...],
        _cwd: Path,
        _timeout_seconds: float,
        _env: dict[str, str],
    ) -> agent_harness.CommandResult:
        executed.append(argv)
        return agent_harness.CommandResult(
            status="passed", exit_code=0, stdout="ok\n", stderr=""
        )

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="covered-run",
        runner=recording_runner,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert passed is True
    assert len(executed) == 1
    assert receipt["selected_check_ids"] == ["unit", "covered"]
    assert receipt["checks"][0]["status"] == "passed"
    assert receipt["checks"][1] == {
        "check_id": "covered",
        "status": "skipped",
        "reason": "covered by passed checks",
        "covered_by_check_ids": ["unit"],
    }
    assert agent_harness.verify_receipt_integrity(receipt) is True


def test_verification_executes_check_when_not_all_covering_checks_passed(
    tmp_path: Path,
) -> None:
    policy = _minimal_policy()
    policy["checks"]["covered"] = {
        "argv": [sys.executable, "-c", "print('covered')"],
        "cwd": ".",
        "description": "Requires two covering checks.",
        "covered_by_check_ids": ["unit", "not-selected"],
    }
    policy["checks"]["not-selected"] = {
        "argv": [sys.executable, "-c", "print('not selected')"],
        "cwd": ".",
        "description": "Known covering check outside this routed scope.",
    }
    inspection = {
        "changed_paths": ["src/example.py"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit", "covered"],
    }
    scope = {
        "mode": "commit_range",
        "changed_paths": ["src/example.py"],
        "head_oid": "b" * 40,
        "closure_eligible": True,
    }
    executed: list[tuple[str, ...]] = []

    def recording_runner(
        argv: tuple[str, ...],
        _cwd: Path,
        _timeout_seconds: float,
        _env: dict[str, str],
    ) -> agent_harness.CommandResult:
        executed.append(argv)
        return agent_harness.CommandResult(
            status="passed", exit_code=0, stdout="ok\n", stderr=""
        )

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        scope=scope,
        source_snapshot={"scope_sha256": "c" * 64},
        project_root=tmp_path,
        execution_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="not-covered-run",
        runner=recording_runner,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert passed is True
    assert len(executed) == 2
    assert [check["status"] for check in receipt["checks"]] == ["passed", "passed"]


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


def test_legacy_receipt_dependency_field_only_defaults_for_empty_route() -> None:
    receipt = {
        "changed_paths": ["tracked.txt"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "selected_check_ids": ["unit"],
    }
    inspection = {
        "changed_paths": ["tracked.txt"],
        "ignored_paths": [],
        "sensitive_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit"],
        "npm_workspace_dependency_paths": ["provider-console/node_modules"],
    }

    assert agent_harness.inspection_matches_receipt(receipt, inspection) is False


def test_receipt_freshness_requires_complete_routing_and_execution_proof(
    tmp_path: Path,
) -> None:
    receipt_path, _tracked, _policy_path, _scope = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )

    assert report["self_consistent"] is True
    assert report["fresh_for_snapshot"] is True
    assert report["complete_completion_proof"] is True
    assert report["scope_well_formed"] is True
    assert report["scope_paths_match"] is True
    assert report["inspection_matches"] is True
    assert report["check_records_complete"] is True
    assert report["check_records_valid"] is True
    assert report["coverage_closed_same_run"] is True
    assert report["fresh"] is True

    legacy_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    legacy_receipt.pop("npm_workspace_dependency_paths")
    agent_harness.seal_receipt(legacy_receipt)
    legacy_report = agent_harness.receipt_freshness(
        legacy_receipt, tmp_path, receipt_dir=receipt_path.parent
    )
    assert legacy_report["inspection_matches"] is True
    assert legacy_report["fresh"] is True

    mutations = (
        (lambda value: value.__setitem__("changed_paths", ["wrong.txt"]), "inspection_matches"),
        (lambda value: value.__setitem__("categories", []), "inspection_matches"),
        (
            lambda value: value.__setitem__("selected_check_ids", ["unit"]),
            "inspection_matches",
        ),
        (
            lambda value: value.__setitem__(
                "npm_workspace_dependency_paths",
                ["provider-console/node_modules"],
            ),
            "inspection_matches",
        ),
        (
            lambda value: value.__setitem__(
                "npm_workspace_dependency_paths", None
            ),
            "inspection_matches",
        ),
        (lambda value: value.__setitem__("checks", []), "check_records_complete"),
        (
            lambda value: value["checks"][0].__setitem__("argv", ["tampered"]),
            "check_records_valid",
        ),
        (
            lambda value: value["checks"][0].pop("stdout"),
            "check_records_valid",
        ),
        (
            lambda value: value["checks"][0].__setitem__("duration_ms", True),
            "check_records_valid",
        ),
        (
            lambda value: value["checks"][1].__setitem__(
                "covered_by_check_ids", ["missing"]
            ),
            "coverage_closed_same_run",
        ),
    )
    for mutate, failed_key in mutations:
        tampered = json.loads(receipt_path.read_text(encoding="utf-8"))
        mutate(tampered)
        agent_harness.seal_receipt(tampered)

        tampered_report = agent_harness.receipt_freshness(
            tampered, tmp_path, receipt_dir=receipt_path.parent
        )

        assert tampered_report["integrity"] is True
        assert tampered_report[failed_key] is False
        assert tampered_report["complete_completion_proof"] is False
        assert tampered_report["fresh"] is False


def test_receipt_freshness_fails_closed_on_malformed_scope(tmp_path: Path) -> None:
    receipt_path, _tracked, _policy_path, _scope = _complete_receipt_fixture(tmp_path)

    for malformed_paths in (None, 17, [None], []):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["scope"]["changed_paths"] = malformed_paths
        agent_harness.seal_receipt(receipt)

        report = agent_harness.receipt_freshness(
            receipt, tmp_path, receipt_dir=receipt_path.parent
        )

        assert report["scope_well_formed"] is False
        assert report["fresh"] is False


def test_receipt_freshness_uses_the_selected_repository_policy(tmp_path: Path) -> None:
    receipt_path, _tracked, _policy_path, _scope = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )

    assert report["policy_matches"] is True
    assert report["snapshot_matches"] is True
    assert report["complete_completion_proof"] is True
    assert report["fresh"] is True


def test_staged_receipt_becomes_stale_when_scope_gets_unstaged_edits(
    tmp_path: Path,
) -> None:
    receipt_path, tracked, _policy_path, _scope = _complete_receipt_fixture(
        tmp_path, mode="staged"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )["fresh"] is True

    tracked.write_text("new unstaged edit\n", encoding="utf-8")

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )
    assert report["scope_worktree_clean"] is False
    assert report["fresh"] is False


def test_staged_receipt_rejects_snapshot_from_different_head(tmp_path: Path) -> None:
    receipt_path, _tracked, _policy_path, _scope = _complete_receipt_fixture(
        tmp_path, mode="staged"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("moves head\n", encoding="utf-8")
    _git(tmp_path, "add", "unrelated.txt")
    _git(tmp_path, "commit", "--only", "-qm", "move head", "--", "unrelated.txt")

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )

    assert report["snapshot_matches"] is False
    assert report["fresh"] is False


def test_commit_range_receipt_becomes_stale_after_new_staged_edit(
    tmp_path: Path,
) -> None:
    receipt_path, tracked, _policy_path, _scope = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )["fresh"] is True

    tracked.write_text("new staged edit\n", encoding="utf-8")
    _git(tmp_path, "add", "tracked.txt")

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )
    assert report["scope_worktree_clean"] is False
    assert report["fresh"] is False


def test_commit_range_freshness_uses_committed_policy_bytes(tmp_path: Path) -> None:
    receipt_path, _tracked, policy_path, _scope = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    policy_path.write_text("version: 999\n", encoding="utf-8")

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )

    assert report["policy_matches"] is True
    assert report["scope_worktree_clean"] is True
    assert report["fresh"] is True


def test_commit_range_freshness_rejects_moved_head_ref(tmp_path: Path) -> None:
    receipt_path, _tracked, _policy_path, scope = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    _git(tmp_path, "branch", "receipt-head", scope["head_oid"])
    receipt["scope"]["head_ref"] = "receipt-head"
    agent_harness.seal_receipt(receipt)
    assert agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )["fresh"] is True
    _git(tmp_path, "branch", "-f", "receipt-head", scope["base_oid"])

    report = agent_harness.receipt_freshness(
        receipt, tmp_path, receipt_dir=receipt_path.parent
    )

    assert report["snapshot_matches"] is False
    assert report["fresh"] is False


def test_repository_policy_audit_has_no_unmapped_owned_files() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.audit_policy_coverage(policy, ROOT)

    assert report["unmapped_paths"] == []
    assert report["unverified_paths"] == []
    assert report["missing_check_test_paths"] == []
    assert report["unreferenced_test_paths"] == []
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

    for path in (
        "provider-console/tests/continuity-review.test.mjs",
        "provider-console/tests/sites-worker.test.mjs",
        "provider-console/package-lock.json",
        "pyproject.toml",
        "package-lock.json",
        ".codex/config.toml",
        ".mcp.json",
    ):
        assert path not in report["unmapped_paths"]
        assert path not in report["unverified_paths"]


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


def test_policy_audit_rejects_unreferenced_explicit_node_test(tmp_path: Path) -> None:
    _committed_repository(tmp_path)
    node_test = tmp_path / "provider-console/tests/missing.test.mjs"
    node_test.parent.mkdir(parents=True)
    node_test.write_text("export {};\n", encoding="utf-8")
    _git(tmp_path, "add", "provider-console/tests/missing.test.mjs")
    _git(tmp_path, "commit", "-qm", "add node test")
    policy = _minimal_policy()
    policy["audit_patterns"] = ["provider-console/tests/**"]
    policy["audit_explicit_test_patterns"] = ["provider-console/tests/*.test.mjs"]
    policy["categories"] = {
        "provider_console": {
            "patterns": ["provider-console/**"],
            "check_ids": ["unit"],
        }
    }

    report = agent_harness.audit_policy_coverage(policy, tmp_path)

    assert report["unmapped_paths"] == []
    assert report["unverified_paths"] == []
    assert report["unreferenced_test_paths"] == [
        "provider-console/tests/missing.test.mjs"
    ]


def test_policy_audit_requires_explicit_python_test_or_named_exemption(
    tmp_path: Path,
) -> None:
    _committed_repository(tmp_path)
    python_test = tmp_path / "tests/test_missing.py"
    python_test.parent.mkdir(parents=True)
    python_test.write_text("def test_missing():\n    assert True\n", encoding="utf-8")
    _git(tmp_path, "add", "tests/test_missing.py")
    _git(tmp_path, "commit", "-qm", "add Python test")
    policy = _minimal_policy()
    policy["audit_patterns"] = ["tests/**"]
    policy["audit_explicit_test_patterns"] = ["tests/test_*.py"]
    policy["categories"] = {
        "tests": {"patterns": ["tests/**"], "check_ids": ["unit"]}
    }

    report = agent_harness.audit_policy_coverage(policy, tmp_path)

    assert report["unreferenced_test_paths"] == ["tests/test_missing.py"]

    policy["audit_unreferenced_test_exempt_patterns"] = ["tests/test_missing.py"]
    exempt_report = agent_harness.audit_policy_coverage(policy, tmp_path)
    assert exempt_report["unreferenced_test_paths"] == []


def test_makefile_exposes_completion_and_repository_harness_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "harness-inspect:" in makefile
    assert "harness-verify:" in makefile
    assert "harness-verify-range:" in makefile
    assert "harness-receipt:" in makefile
    assert "harness-audit:" in makefile
    assert "harness-repository:" in makefile
    assert "harness-test:" in makefile
