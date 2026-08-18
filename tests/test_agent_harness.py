from __future__ import annotations

import json
from pathlib import Path

from scripts import agent_harness


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agent/harness/policy.yaml"


def test_repository_policy_loads_and_references_known_checks() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    assert policy["version"] == 1
    assert policy["runs_dir"] == ".agent/harness/runs"
    assert "full_tests" in policy["fallback_check_ids"]
    assert "architecture_gate" in policy["fallback_check_ids"]
    referenced_test_files = {
        argument
        for check in policy["checks"].values()
        for argument in check["argv"]
        if argument.startswith("tests/") and argument.endswith(".py")
    }
    assert referenced_test_files
    assert not [path for path in referenced_test_files if not (ROOT / path).is_file()]


def test_inspection_routes_cli_change_to_required_checks() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(["src/ai_video/cli.py"], policy)

    assert report["changed_paths"] == ["src/ai_video/cli.py"]
    assert report["categories"] == ["legacy_cli_config"]
    assert report["fallback_paths"] == []
    assert report["check_ids"] == [
        "diff_check",
        "staged_diff_check",
        "cli_config_tests",
        "architecture_gate",
    ]


def test_inspection_falls_back_for_unmapped_path() -> None:
    policy = agent_harness.load_policy(POLICY_PATH)

    report = agent_harness.inspect_paths(["src/ai_video/new_surface.py"], policy)

    assert report["categories"] == []
    assert report["fallback_paths"] == ["src/ai_video/new_surface.py"]
    assert report["check_ids"] == [
        "diff_check",
        "staged_diff_check",
        "full_tests",
        "architecture_gate",
    ]


def test_verification_writes_a_run_receipt(tmp_path: Path) -> None:
    policy = {
        "version": 1,
        "runs_dir": ".agent/harness/runs",
        "always_check_ids": [],
        "fallback_check_ids": [],
        "ignored_patterns": [],
        "checks": {
            "unit": {
                "argv": ["python", "-m", "pytest", "tests/test_example.py", "-q"],
                "cwd": ".",
                "append_changed_paths": True,
                "description": "Example unit test.",
            }
        },
        "categories": {},
    }
    inspection = {
        "changed_paths": ["src/example.py"],
        "ignored_paths": [],
        "categories": ["example"],
        "fallback_paths": [],
        "check_ids": ["unit"],
    }
    calls: list[tuple[tuple[str, ...], Path]] = []

    def runner(argv: tuple[str, ...], cwd: Path) -> int:
        calls.append((argv, cwd))
        return 0

    receipt_path, passed = agent_harness.verify_inspection(
        inspection,
        policy,
        project_root=tmp_path,
        runs_dir=tmp_path / "runs",
        run_id="test-run",
        runner=runner,
    )

    assert passed is True
    assert calls == [
        (
            (
                "python",
                "-m",
                "pytest",
                "tests/test_example.py",
                "-q",
                "--",
                "src/example.py",
            ),
            tmp_path,
        )
    ]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema"] == "ai-video-agent-harness-run/1"
    assert receipt["run_id"] == "test-run"
    assert receipt["status"] == "passed"
    assert receipt["changed_paths"] == ["src/example.py"]
    assert receipt["checks"][0]["check_id"] == "unit"
    assert receipt["checks"][0]["exit_code"] == 0


def test_makefile_exposes_harness_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    assert "harness-inspect:" in makefile
    assert "harness-verify:" in makefile
    assert "harness-test:" in makefile
