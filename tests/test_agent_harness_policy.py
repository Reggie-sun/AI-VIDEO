"""Focused routing and diagnostic behavior for the exact-snapshot Harness."""

from pathlib import Path
import json
import sys

import pytest

from scripts import agent_harness


POLICY_PATH = Path(__file__).resolve().parents[1] / ".agent/harness/policy.yaml"


@pytest.mark.parametrize("path", [
    "src/ai_video/production/_causal_prompt_context.py",
    "src/ai_video/production/_causal_state_expression.py",
    "tests/test_typed_causal_native_expression.py",
    "tests/test_current_shot_close_expression.py",
])
def test_causal_expression_selects_related_boundaries_without_full_suite(path):
    policy = agent_harness.load_policy(POLICY_PATH)
    selected = agent_harness.inspect_paths([path], policy)
    assert selected["fallback_paths"] == []
    assert "full_tests" not in selected["check_ids"]
    assert "generation_feedback_tests" not in selected["check_ids"]
    assert set(selected["check_ids"]) >= {
        "typed_causal_native_expression_tests", "video_planner_tests",
        "provider_neutral_video_requirement_tests", "production_shot_router_tests",
        "production_video_provider_tests", "production_vidu_tests",
        "final_output_no_regression_tests",
        "task_architecture_gate",
    }
    assert "tests/test_typed_causal_native_expression.py" in policy["checks"][
        "generation_feedback_tests"
    ]["argv"]
    assert "tests/test_typed_causal_native_expression.py" in policy["checks"][
        "typed_causal_native_expression_tests"
    ]["argv"]
    for check_id in ("generation_feedback_tests", "typed_causal_native_expression_tests"):
        assert "tests/test_current_shot_close_expression.py" in policy["checks"][
            check_id
        ]["argv"]


def test_feedback_owner_keeps_repair_suite_and_covers_expression_after_pass():
    policy = agent_harness.load_policy(POLICY_PATH)
    selected = agent_harness.inspect_paths([
        "src/ai_video/production/generation_feedback.py",
        "src/ai_video/production/_causal_prompt_context.py",
    ], policy)
    assert "generation_feedback_tests" in selected["check_ids"]
    assert "tests/test_generation_runtime_repair.py" in policy["checks"][
        "generation_feedback_tests"
    ]["argv"]
    assert "typed_causal_native_expression_tests" in policy["checks"][
        "generation_feedback_tests"
    ]["covers_check_ids"]
    assert selected["check_ids"].index("generation_feedback_tests") < selected[
        "check_ids"
    ].index("typed_causal_native_expression_tests")


@pytest.mark.parametrize("path, expected", [
    ("src/ai_video/production/models.py", "production_contract_tests"),
    ("tests/conftest.py", "full_tests"),
    ("pyproject.toml", "full_tests"),
    ("src/ai_video/unknown_surface.py", "full_tests"),
])
def test_shared_and_unknown_changes_keep_broad_checks(path, expected):
    selected = agent_harness.inspect_paths([path], agent_harness.load_policy(POLICY_PATH))
    assert expected in selected["check_ids"]


def test_memory_coverage_is_complete_and_orders_covering_check_first():
    policy = agent_harness.load_policy(POLICY_PATH)
    covering = policy["checks"]["quality_intelligence_tests"]
    assert "agent_memory_tests" in covering.get("covers_check_ids", [])
    covered = policy["checks"]["agent_memory_tests"]
    assert {arg for arg in covered["argv"] if arg.startswith("tests/")} <= {
        arg for arg in covering["argv"] if arg.startswith("tests/")
    }
    selected = agent_harness.inspect_paths([
        "tests/test_agent_memory.py", "tests/test_quality_experience_capture.py",
    ], policy)
    assert selected["check_ids"].index("quality_intelligence_tests") < selected[
        "check_ids"
    ].index("agent_memory_tests")


def test_pytest_argv_reports_slow_tests_without_changing_selection():
    config = agent_harness.load_policy(POLICY_PATH)["checks"]["cli_config_tests"]
    argv = agent_harness._check_argv(
        config,
        {"mode": "staged", "head_oid": "a" * 40}, None,
    )
    assert "--durations=20" in argv
    assert "--durations-min=0.1" in argv
    assert "tests/test_cli.py" in argv
    assert not any(arg.startswith(("--maxfail", "--lf", "--ff")) for arg in argv)
    assert agent_harness._check_argv(
        {"argv": ["git", "diff", "--check"]}, {"mode": "staged"}, None,
    ) == ("git", "diff", "--check")
    # Historical policy argv still reconstructs without new diagnostic flags.
    assert agent_harness._check_argv(
        {"argv": ["python", "-m", "pytest", "-q"]}, {"mode": "staged"}, None,
    ) == (sys.executable, "-m", "pytest", "-q")


def test_full_suite_has_node_identity_and_stack_diagnostics():
    argv = agent_harness.load_policy(POLICY_PATH)["checks"]["full_tests"]["argv"]
    assert "-v" in argv
    assert "faulthandler_timeout=120" in argv
    assert "--maxfail=1" not in argv
    assert not any(argument.startswith("tests/") for argument in argv)


def test_check_start_is_visible_before_runner_and_result_after(tmp_path, capsys):
    policy = {
        "runs_dir": "runs", "default_timeout_seconds": 5,
        "checks": {"unit": {"argv": [sys.executable, "-c", "print('ok')"]}},
    }
    scope = {"mode": "staged", "closure_eligible": True, "head_oid": "a" * 40,
             "changed_paths": ["unit.py"]}
    inspection = {
        "changed_paths": ["unit.py"], "ignored_paths": [], "categories": [],
        "fallback_paths": [], "check_ids": ["unit"],
    }

    def runner(argv, cwd, timeout, env):
        assert "[harness] START unit timeout=5s" in capsys.readouterr().out
        return agent_harness.CommandResult("passed", 0, "ok\n", "")

    receipt_path, passed = agent_harness.verify_inspection(
        inspection, policy, scope=scope, source_snapshot={"tree_oid": "b" * 40},
        project_root=tmp_path, runner=runner,
    )
    assert passed
    assert "[harness] PASSED unit duration=" in capsys.readouterr().out
    receipt = json.loads(receipt_path.read_text())
    assert receipt["checks"][0]["status"] == "passed"
    assert agent_harness.verify_receipt_integrity(receipt)


def test_real_pytest_duration_output_is_captured(tmp_path):
    (tmp_path / "test_slow.py").write_text(
        "import time\ndef test_slow():\n    time.sleep(0.12)\n", encoding="utf-8",
    )
    config = agent_harness.load_policy(POLICY_PATH)["checks"]["full_tests"]
    argv = agent_harness._check_argv(
        {**config, "argv": [*config["argv"], str(tmp_path / "test_slow.py")]},
        {"mode": "staged"}, tmp_path / "result.xml",
    )
    result = agent_harness.run_command(
        argv, POLICY_PATH.parents[2], 15,
        agent_harness.build_check_environment({"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}),
    )
    assert result.status == "passed", result.stderr
    assert "slowest 20 durations" in result.stdout
    assert "test_slow.py::test_slow" in result.stdout
    assert (tmp_path / "result.xml").is_file()


@pytest.mark.parametrize("drift_at", [0, 1, 2])
def test_scope_drift_stops_remaining_checks(tmp_path, drift_at):
    policy = {"runs_dir": "runs", "default_timeout_seconds": 5,
              "checks": {name: {"argv": ["true"]} for name in ("first", "second")}}
    scope = {"mode": "staged", "closure_eligible": True, "head_oid": "a" * 40,
             "changed_paths": ["unit.py"]}
    inspection = {"changed_paths": ["unit.py"], "ignored_paths": [],
                  "categories": [], "fallback_paths": [],
                  "check_ids": ["first", "second"]}
    executed = []
    before = {"tree_oid": "b" * 40}

    def snapshot():
        return before if len(executed) < drift_at else {"tree_oid": "c" * 40}

    def runner(argv, cwd, timeout, env):
        executed.append(argv)
        return agent_harness.CommandResult("passed", 0, "", "")

    receipt_path, passed = agent_harness.verify_inspection(
        inspection, policy, scope=scope, source_snapshot=before,
        project_root=tmp_path, runner=runner, snapshot_after=snapshot,
    )
    receipt = json.loads(receipt_path.read_text())
    assert not passed
    assert len(executed) == drift_at
    assert receipt["workspace_stable"] is False
    assert receipt["failure_reason"] == "source scope changed during verification"
    assert [row["status"] for row in receipt["checks"]] == (
        ["passed"] * drift_at + ["skipped"] * (2 - drift_at)
    )
    assert agent_harness.verify_receipt_integrity(receipt)


def test_unreadable_snapshot_does_not_start_checks(tmp_path):
    def snapshot():
        raise OSError("snapshot unavailable")

    def runner(*args):
        pytest.fail("a check started without a readable exact snapshot")

    receipt_path, passed = agent_harness.verify_inspection(
        {"changed_paths": ["unit.py"], "ignored_paths": [], "categories": [],
         "fallback_paths": [], "check_ids": ["unit"]},
        {"runs_dir": "runs", "default_timeout_seconds": 5,
         "checks": {"unit": {"argv": ["true"]}}},
        scope={"mode": "staged", "closure_eligible": True, "head_oid": "a" * 40,
               "changed_paths": ["unit.py"]},
        source_snapshot={"tree_oid": "b" * 40}, project_root=tmp_path,
        runner=runner, snapshot_after=snapshot,
    )
    receipt = json.loads(receipt_path.read_text())
    assert not passed and receipt["workspace_stable"] is False
    assert receipt["checks"][0]["status"] == "skipped"
    assert "OSError" in receipt["source_snapshot_after"]["error"]


@pytest.mark.parametrize("path, data, runtime", [
    ("docs/canvas-projects/story/README.md", False, False),
    ("docs/canvas-projects/story/project.json", True, False),
    ("docs/canvas-projects/story/source.json", True, False),
    ("docs/canvas-projects/story/asset.png", True, False),
    ("docs/canvas-projects/story/new-format.bin", True, False),
    ("src/ai_video/canvas_recovery.py", False, True),
    ("scripts/canvas_production.py", False, True),
])
def test_canvas_data_and_runtime_select_their_own_checks(path, data, runtime):
    selected = agent_harness.inspect_paths([path], agent_harness.load_policy(POLICY_PATH))
    assert ("canvas_project_data_check" in selected["check_ids"]) == data
    assert ("canvas_production_workflow_tests" in selected["check_ids"]) == runtime
    assert selected["fallback_paths"] == []


def test_image_keeps_domain_e2e_and_shared_owners_keep_their_checks():
    policy = agent_harness.load_policy(POLICY_PATH)
    image = agent_harness.inspect_paths(["src/ai_video/production/image.py"], policy)
    assert "production_image_tests" in image["check_ids"]
    assert set(image["check_ids"]) >= {
        "production_image_reader_tests", "production_image_state_tests",
        "production_image_dependency_tests",
    }
    assert "production_state_tests" not in image["check_ids"]
    argv = policy["checks"]["production_image_tests"]["argv"]
    assert "tests/test_production_image_e2e.py" in argv
    assert "tests/test_production_p7_1_local_image_e2e.py" in argv
    for path, check in (
        ("src/ai_video/production/_image_project_reader.py", "production_reader_tests"),
        ("src/ai_video/production/_state_commit_image.py", "production_state_tests"),
        ("src/ai_video/production/dependency.py", "production_dependency_tests"),
        ("src/ai_video/production/state_commit.py", "production_contract_tests"),
    ):
        assert check in agent_harness.inspect_paths([path], policy)["check_ids"]


@pytest.mark.parametrize("path", ["src/ai_video/production/_image_project_reader.py",
                                  "src/ai_video/production/_image_video_lineage.py"])
def test_read_only_image_lineage_keeps_full_reader_without_generation_crash_suite(path):
    selected = agent_harness.inspect_paths([path], agent_harness.load_policy(POLICY_PATH))
    assert "production_reader_tests" in selected["check_ids"]
    assert "production_image_tests" not in selected["check_ids"]
    assert "production_image_state_tests" not in selected["check_ids"]
    assert "production_state_tests" not in selected["check_ids"]
    assert selected["fallback_paths"] == []


def test_scope_paths_argv_reconstructs_exact_paths_without_shell():
    config = agent_harness.load_policy(POLICY_PATH)["checks"]["canvas_project_data_check"]
    scope = {"mode": "staged", "changed_paths": ["docs/canvas-projects/a space/source.json"]}
    assert agent_harness._check_argv(config, scope, None) == (
        sys.executable, "-m", "scripts.agent_harness_canvas_data",
        "--paths=docs/canvas-projects/a space/source.json",
    )


def test_policy_exclusions_and_scope_paths_require_strict_types():
    from copy import deepcopy
    from scripts.agent_harness_policy import validate_policy
    policy = agent_harness.load_policy(POLICY_PATH)
    for invalid in ("true", 1, None):
        changed = deepcopy(policy)
        changed["checks"]["canvas_project_data_check"]["scope_paths"] = invalid
        with pytest.raises(ValueError, match="scope_paths"):
            validate_policy(changed, source="test")
    policy["categories"]["canvas_project_data"]["exclude_patterns"] = "*.md"
    with pytest.raises(ValueError, match="exclude_patterns"):
        validate_policy(policy, source="test")


def test_policy_audit_honors_the_same_category_exclusions(tmp_path):
    from scripts.agent_harness_audit import audit_policy_coverage
    policy = {"audit_patterns": ["*.py"], "audit_exempt_patterns": [],
              "categories": {"code": {"patterns": ["*.py"],
                             "exclude_patterns": ["excluded.py"], "check_ids": ["unit"]}},
              "checks": {"unit": {"argv": ["true"]}}}
    result = audit_policy_coverage(policy, tmp_path, ["included.py", "excluded.py"])
    assert result["unmapped_paths"] == ["excluded.py"]


def test_focused_image_boundaries_are_subsets_of_their_full_owners():
    policy = agent_harness.load_policy(POLICY_PATH)
    for concern in ("reader", "state", "dependency"):
        focused = "production_image_" + concern + "_tests"
        owner = "production_" + concern + "_tests"
        config = policy["checks"][focused]
        assert config["covered_by_check_ids"] == [owner]
        assert "image or p7" in config["argv"]
        assert {p for p in config["argv"] if p.startswith("tests/")} <= {
            p for p in policy["checks"][owner]["argv"] if p.startswith("tests/")
        }
        assert focused in policy["checks"]["production_contract_tests"]["covers_check_ids"]
        assert focused in policy["checks"]["full_tests"]["covers_check_ids"]
