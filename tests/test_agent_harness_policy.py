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
