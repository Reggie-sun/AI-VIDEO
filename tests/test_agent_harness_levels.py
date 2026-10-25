"""Stage-specific selection and proof boundaries for the development Harness."""

import copy
import json
from pathlib import Path

import pytest
import yaml

from scripts import agent_harness
from scripts import agent_harness_policy


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy():
    return {
        "version": 2,
        "runs_dir": ".agent/harness/runs",
        "default_timeout_seconds": 10,
        "ignored_patterns": [],
        "sensitive_patterns": [".env"],
        "always_check_ids": ["guard"],
        "fallback_check_ids": ["full_tests"],
        "checks": {
            name: {"argv": ["python", "-c", "print('ok')"]}
            for name in ("guard", "module", "contract", "full_tests", "web")
        },
        "categories": {
            "module": {
                "patterns": ["src/module.py", "tests/test_module.py"],
                "focused_check_ids": ["module"],
                "check_ids": ["module", "contract"],
            }
        },
    }


def test_focused_runs_only_affected_module_checks(policy):
    report = agent_harness.inspect_paths(["src/module.py"], policy, level="focused")
    assert report["check_ids"] == ["module"]
    assert report["verification_level"] == "focused"
    assert report["unfocused_paths"] == []


def test_related_preserves_module_and_interface_contract_checks(policy):
    report = agent_harness.inspect_paths(["src/module.py"], policy, level="related")
    assert report["check_ids"] == ["guard", "module", "contract"]
    assert agent_harness.inspect_paths(["src/module.py"], policy) == report


def test_full_runs_every_suite_even_for_a_small_change(policy):
    report = agent_harness.inspect_paths(["src/module.py"], policy, level="full")
    assert set(report["check_ids"]) == set(policy["checks"])


def test_focused_unmapped_paths_do_not_silently_run_full_regression(policy, tmp_path):
    report = agent_harness.inspect_paths(["src/unknown.py"], policy, level="focused")
    assert report["check_ids"] == []
    assert report["unfocused_paths"] == ["src/unknown.py"]
    with pytest.raises(ValueError, match="focused.*mapping"):
        agent_harness.verify_inspection(
            report, policy, scope={"mode": "staged", "closure_eligible": True,
                                  "head_oid": "a" * 40,
                                  "changed_paths": ["src/unknown.py"]},
            source_snapshot={}, project_root=tmp_path,
        )
    assert not (tmp_path / policy["runs_dir"]).exists()


def test_missing_focused_mapping_fails_closed(policy):
    del policy["categories"]["module"]["focused_check_ids"]
    report = agent_harness.inspect_paths(["src/module.py"], policy, level="focused")
    assert report["unfocused_paths"] == ["src/module.py"]
    assert report["check_ids"] == []


def test_focused_unions_overlapping_module_owners_without_contract_expansion(policy):
    policy["categories"]["second"] = {
        "patterns": ["src/module.py"], "focused_check_ids": ["web", "module"],
        "check_ids": ["web", "contract"],
    }
    report = agent_harness.inspect_paths(["src/module.py"], policy, level="focused")
    assert report["check_ids"] == ["module", "web"]


@pytest.mark.parametrize("ids", [["missing"], ["full_tests"]])
def test_policy_rejects_invalid_focused_check_references(policy, ids):
    policy["categories"]["module"]["focused_check_ids"] = ids
    with pytest.raises(ValueError, match="unknown checks|full_tests"):
        agent_harness_policy.validate_policy(policy, source="test")


def test_invalid_level_is_rejected(policy):
    with pytest.raises(ValueError, match="verification level"):
        agent_harness.inspect_paths(["src/module.py"], policy, level="typo")


def test_focused_receipt_cannot_close_engineering_completion(policy, tmp_path):
    inspection = agent_harness.inspect_paths(["src/module.py"], policy, level="focused")
    path, passed = agent_harness.verify_inspection(
        inspection, policy,
        scope={"mode": "staged", "closure_eligible": True,
               "head_oid": "a" * 40, "changed_paths": ["src/module.py"]},
        source_snapshot={}, project_root=tmp_path,
    )
    receipt = json.loads(path.read_text())
    assert passed
    assert receipt["verification_level"] == "focused"
    assert receipt["closure_eligible"] is False
    assert receipt["checks"][0]["check_id"] == "module"


def test_receipt_level_is_bound_to_recomputed_selection(tmp_path):
    from tests.test_agent_harness import _complete_receipt_fixture

    receipt_path, _, _, _ = _complete_receipt_fixture(tmp_path)
    receipt = json.loads(receipt_path.read_text())
    report = agent_harness.receipt_freshness(receipt, tmp_path, receipt_path.parent)
    assert report["fresh"]
    assert report["verification_level"] == "related"
    assert report["full_regression_passed"] is False
    forged = copy.deepcopy(receipt)
    forged["verification_level"] = "full"
    agent_harness.seal_receipt(forged)
    assert not agent_harness.receipt_freshness(
        forged, tmp_path, receipt_path.parent
    )["full_regression_passed"]


def test_repository_focused_selection_and_full_web_coverage():
    policy = agent_harness.load_policy()
    focused = agent_harness.inspect_paths(
        ["src/ai_video/production/repair_input_admission.py"], policy, level="focused"
    )
    assert set(focused["check_ids"]) == {
        "repair_input_admission_tests", "native_audio_retime_tests"
    }
    full = agent_harness.inspect_paths(["README.md"], policy, level="full")
    assert {"full_tests", "provider_console_node_tests", "provider_console_web_build",
            "provider_console_sites_tests"} <= set(full["check_ids"])


def test_full_receipt_requires_every_suite_and_cli_rejects_related_proof(
    policy, tmp_path, monkeypatch, capsys
):
    from tests.test_agent_harness import _committed_repository, _git

    tracked = _committed_repository(tmp_path)
    policy["categories"]["module"]["patterns"] = ["tracked.txt"]
    policy_path = tmp_path / ".agent/harness/policy.yaml"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(yaml.safe_dump(policy))
    policy = agent_harness.load_policy(policy_path)
    _git(tmp_path, "add", ".agent/harness/policy.yaml")
    _git(tmp_path, "commit", "-qm", "policy")
    tracked.write_text("changed\n")
    _git(tmp_path, "add", "tracked.txt")
    scope = agent_harness.discover_scope(tmp_path, staged=True)
    snapshot = agent_harness._scope_snapshot(tmp_path, scope)
    reports = {}
    for level in ("related", "full"):
        inspection = agent_harness.inspect_paths(scope["changed_paths"], policy, level=level)
        path, passed = agent_harness.verify_inspection(
            inspection, policy, scope=scope, source_snapshot=snapshot,
            project_root=tmp_path, run_id=level,
            policy_sha256=agent_harness._sha256(policy_path.read_bytes()),
        )
        assert passed
        receipt = json.loads(path.read_text())
        reports[level] = agent_harness.receipt_freshness(receipt, tmp_path, path.parent)
        assert reports[level]["fresh"]
        assert reports[level]["full_regression_passed"] == (level == "full")
    monkeypatch.setattr(agent_harness, "receipt_freshness", lambda *a, **kw: reports["related"])
    assert agent_harness.main(["verify-receipt", str(path), "--require-level", "full"]) == 1
    monkeypatch.setattr(agent_harness, "receipt_freshness", lambda *a, **kw: reports["full"])
    assert agent_harness.main(["verify-receipt", str(path), "--require-level", "full"]) == 0
    assert '"full_regression_passed": true' in capsys.readouterr().out


def test_ci_and_make_use_explicit_verification_stages():
    makefile = (ROOT / "Makefile").read_text()
    workflow = (ROOT / ".github/workflows/mandatory-gate.yml").read_text()
    assert "harness-focused:" in makefile
    assert "harness-related:" in makefile
    assert "harness-full:" in makefile
    assert "--level full" in workflow
    assert 'LEVEL="full"' in workflow
    assert "--require-level full" in workflow
