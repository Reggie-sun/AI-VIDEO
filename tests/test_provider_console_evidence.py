from __future__ import annotations

import json
import hashlib
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

from scripts import provider_console_cases
from scripts.agent_harness_receipt import write_artifact, write_receipt
from scripts.provider_console_evidence import project_module_evidence


REPOSITORY = Path(__file__).resolve().parents[1]
PERFORMANCE_RECEIPT = ".agent/harness/runs/character-performance-control-20261020-r4/receipt.json"
PERFORMANCE_ANCHOR = "src/ai_video/production/performance_authoring.py"
PERFORMANCE_DIRECTION_ANCHOR = "src/ai_video/production/performance_direction.py"
PERFORMANCE_CHECK = "generation_feedback_tests"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "--all")
    _git(root, "-c", "user.name=Evidence Test", "-c", "user.email=evidence@example.invalid", "commit", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _fixture_repo(tmp_path: Path) -> tuple[Path, str, str, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "--quiet")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    base = _commit(root, "base")
    anchor = root / PERFORMANCE_ANCHOR
    anchor.parent.mkdir(parents=True)
    anchor.write_text("performance implementation at proof head\n", encoding="utf-8")
    direction_anchor = root / PERFORMANCE_DIRECTION_ANCHOR
    direction_anchor.write_text("direction implementation at proof head\n", encoding="utf-8")
    head = _commit(root, "performance implementation")

    catalog_path = root / "provider-console/scripts/module-evidence-catalog.json"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_bytes(
        (REPOSITORY / "provider-console/scripts/module-evidence-catalog.json").read_bytes()
    )
    run_dir = root / Path(PERFORMANCE_RECEIPT).parent
    run_dir.mkdir(parents=True)
    stdout = write_artifact(run_dir, run_dir / "08-generation_feedback_tests.stdout.log", "test output\n")
    stderr = write_artifact(run_dir, run_dir / "08-generation_feedback_tests.stderr.log", b"")
    junit = write_artifact(run_dir, run_dir / "08-generation_feedback_tests.junit.xml", "<testsuite tests='1' failures='0'/>\n")
    scope = {
        "mode": "commit_range",
        "base_oid": base,
        "head_oid": head,
        "changed_paths": sorted([PERFORMANCE_ANCHOR, PERFORMANCE_DIRECTION_ANCHOR]),
    }
    snapshot = {
        "mode": "commit_range",
        "base_oid": base,
        "head_oid": head,
        "git_head": head,
        "changed_paths": sorted([PERFORMANCE_ANCHOR, PERFORMANCE_DIRECTION_ANCHOR]),
        "scope_sha256": "a" * 64,
    }
    receipt = {
        "schema": "ai-video-agent-harness-run/2",
        "run_id": run_dir.name,
        "status": "passed",
        "workspace_stable": True,
        "workspace_cleanup_status": "passed",
        "finished_at": "2026-10-20T10:00:00+00:00",
        "scope": scope,
        "source_snapshot_before": snapshot,
        "source_snapshot_after": snapshot,
        "selected_check_ids": [PERFORMANCE_CHECK],
        "checks": [
            {
                "check_id": PERFORMANCE_CHECK,
                "status": "passed",
                "exit_code": 0,
                "argv": ["python", "-m", "pytest", "tests/test_performance_authoring.py"],
                "stdout": stdout,
                "stderr": stderr,
                "junit": junit,
            }
        ],
    }
    write_receipt(root / PERFORMANCE_RECEIPT, receipt)
    return root, base, head, root / PERFORMANCE_RECEIPT


def _module(document: dict, module_id: str) -> dict:
    return next(module for module in document["modules"] if module["id"] == module_id)


def test_historical_pass_requires_sealed_receipt_artifacts_and_exact_git_scope(tmp_path: Path) -> None:
    root, base, head, _ = _fixture_repo(tmp_path)

    document = project_module_evidence(root)

    assert document["schema"] == "ai-video-module-evidence/1"
    assert document["source_kind"] == "local_readonly"
    assert document["repository"]["head"] == head
    performance = _module(document, "performance")
    assert performance["kind"] == "media"
    assert performance["media"] == {"applicable": True, "state": "not_evaluated"}
    assert performance["human"] == {"applicable": True, "state": "not_evaluated"}
    assert performance["engineering"]["state"] == "historical_pass"
    evidence = performance["engineering"]["evidence"]
    assert len(evidence) == 1
    assert evidence[0]["base_commit"] == base
    assert evidence[0]["head_commit"] == head
    assert evidence[0]["check_id"] == PERFORMANCE_CHECK
    assert evidence[0]["status"] == "passed"
    assert evidence[0]["anchor_match"] == "match"
    receipt_bytes = (root / PERFORMANCE_RECEIPT).read_bytes()
    assert evidence[0]["receipt_sha256"] == hashlib.sha256(receipt_bytes).hexdigest()
    assert evidence[0]["receipt_seal_sha256"] != evidence[0]["receipt_sha256"]
    assert all(not Path(artifact["path"]).is_absolute() for artifact in evidence[0]["artifacts"])


@pytest.mark.parametrize("tamper", ["stdout", "missing_receipt"])
def test_tampered_or_missing_evidence_never_looks_like_a_pass(tmp_path: Path, tamper: str) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    artifact = root / receipt_path.parent / receipt["checks"][0]["stdout"]["path"]
    if tamper == "stdout":
        artifact.write_text("tampered\n", encoding="utf-8")
    else:
        receipt_path.unlink()

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "unavailable"
    expected_reason = "receipt_artifact_invalid" if tamper == "stdout" else "receipt_missing"
    assert performance["engineering"]["reason"] == expected_reason
    assert performance["engineering"]["evidence"] == []


def test_unsafe_receipt_symlink_ancestor_is_rejected(tmp_path: Path) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    run_dir = receipt_path.parent
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "receipt.json").write_bytes(receipt_path.read_bytes())
    receipt_path.unlink()
    shutil.rmtree(run_dir)
    run_dir.symlink_to(outside, target_is_directory=True)

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "unavailable"
    assert performance["engineering"]["reason"] == "receipt_unsafe"
    assert performance["engineering"]["evidence"] == []


def test_traversal_artifact_path_and_malformed_check_status_fail_closed(tmp_path: Path) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["checks"][0]["stdout"]["path"] = "../../../../etc/passwd"
    write_receipt(receipt_path, receipt)

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "unavailable"
    assert performance["engineering"]["reason"] == "receipt_artifact_invalid"
    assert performance["engineering"]["evidence"] == []


@pytest.mark.parametrize(
    ("status", "exit_code", "expected_state"),
    [("passed", None, "unavailable"), ("mystery", 0, "unavailable"), ("failed", 7, "failed")],
)
def test_check_result_requires_a_known_status_and_integer_exit(
    tmp_path: Path, status: str, exit_code: int | None, expected_state: str
) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["checks"][0]["status"] = status
    receipt["checks"][0]["exit_code"] = exit_code
    write_receipt(receipt_path, receipt)

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == expected_state
    if expected_state == "unavailable":
        assert performance["engineering"]["reason"] == "check_status_invalid"
    if expected_state == "unavailable":
        assert performance["engineering"]["evidence"] == []
    else:
        assert len(performance["engineering"]["evidence"]) == 1


def test_anchor_drift_is_reported_without_erasing_historical_result(tmp_path: Path) -> None:
    root, _, _, _ = _fixture_repo(tmp_path)
    (root / PERFORMANCE_ANCHOR).write_text("changed after historical proof\n", encoding="utf-8")

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "historical_pass"
    assert performance["engineering"]["evidence"][0]["anchor_match"] == "changed"


def test_engineering_module_does_not_claim_media_or_human_failure(tmp_path: Path) -> None:
    root, _, _, _ = _fixture_repo(tmp_path)

    committer = _module(project_module_evidence(root), "committer")

    assert committer["kind"] == "engineering"
    assert committer["media"] == {"applicable": False, "state": "not_applicable"}
    assert committer["human"] == {"applicable": False, "state": "not_applicable"}
    assert committer["engineering"]["state"] == "unavailable"


def test_unconfigured_creative_module_is_no_result_not_unavailable(tmp_path: Path) -> None:
    root, _, _, _ = _fixture_repo(tmp_path)

    creative = _module(project_module_evidence(root), "creative")

    assert creative["engineering"]["state"] == "no_result"
    assert creative["engineering"]["reason"] == "no_behavioral_check_configured"
    assert creative["media"] == {"applicable": False, "state": "not_applicable"}
    assert creative["human"] == {"applicable": False, "state": "not_applicable"}


def test_nonzero_check_exit_cannot_be_promoted_by_pass_labels(tmp_path: Path) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["checks"][0]["exit_code"] = 7
    write_receipt(receipt_path, receipt)

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "failed"
    assert performance["engineering"]["evidence"][0]["status"] == "failed"


def test_known_check_failure_dominates_another_historical_pass(tmp_path: Path) -> None:
    root, _, _, receipt_path = _fixture_repo(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    run_dir = receipt_path.parent
    failed_check = dict(receipt["checks"][0])
    failed_check["check_id"] = "shot_readiness_gate_tests"
    failed_check["status"] = "failed"
    failed_check["exit_code"] = 1
    failed_check["stdout"] = write_artifact(
        run_dir, run_dir / "09-shot_readiness_gate_tests.stdout.log", "failed output\n"
    )
    failed_check["stderr"] = write_artifact(run_dir, run_dir / "09-shot_readiness_gate_tests.stderr.log", b"")
    failed_check["junit"] = write_artifact(
        run_dir, run_dir / "09-shot_readiness_gate_tests.junit.xml", "<testsuite tests='1' failures='1'/>\n"
    )
    receipt["selected_check_ids"].append("shot_readiness_gate_tests")
    receipt["checks"].append(failed_check)
    write_receipt(receipt_path, receipt)

    performance = _module(project_module_evidence(root), "performance")

    assert performance["engineering"]["state"] == "failed"
    assert {item["status"] for item in performance["engineering"]["evidence"]} == {"passed", "failed"}


def test_projection_is_local_and_does_not_mutate_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _, head, receipt_path = _fixture_repo(tmp_path)
    before_files = {path.relative_to(root) for path in root.rglob("*") if path.is_file()}
    before_bytes = {path: (root / path).read_bytes() for path in before_files}

    def deny_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("module evidence projection attempted network access")

    monkeypatch.setattr(socket, "socket", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    document = project_module_evidence(root)

    after_files = {path.relative_to(root) for path in root.rglob("*") if path.is_file()}
    assert after_files == before_files
    assert {path: (root / path).read_bytes() for path in after_files} == before_bytes
    assert _git(root, "rev-parse", "HEAD") == head
    assert receipt_path.exists()
    assert document["delivery"] == {
        "state": "unavailable",
        "scope": "selected_case_audit",
        "autonomy": "not_measured",
    }
    assert document["cases"]
    assert all(case["artifact"]["state"] == "unavailable" for case in document["cases"])


def test_empty_case_projection_cannot_claim_delivery_not_established(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, _, _, _ = _fixture_repo(tmp_path)

    monkeypatch.setattr(
        provider_console_cases,
        "project_delivery_cases",
        lambda _: {
            "cases": [],
            "delivery": {
                "state": "not_established_in_reviewed_cases",
                "scope": "selected_case_audit",
                "autonomy": "not_measured",
            },
        },
    )

    document = project_module_evidence(root)

    assert document["cases"] == []
    assert document["delivery"] == {
        "state": "unavailable",
        "scope": "selected_case_audit",
        "autonomy": "not_measured",
    }

