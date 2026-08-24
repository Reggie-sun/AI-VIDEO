"""Pure structural validation for completed development Harness receipts."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

try:
    from scripts.agent_harness_policy import coverage_groups
except ModuleNotFoundError:  # Direct ``python scripts/agent_harness.py`` execution.
    from agent_harness_policy import coverage_groups  # type: ignore[no-redef]


ArgvBuilder = Callable[
    [Mapping[str, Any], Mapping[str, Any], Path | None], tuple[str, ...]
]
GIT_OID_PATTERN = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?")


def completion_scope_is_well_formed(scope: Mapping[str, Any]) -> bool:
    mode = scope.get("mode")
    changed_paths = scope.get("changed_paths")
    head_oid = scope.get("head_oid")
    if (
        mode not in {"staged", "commit_range"}
        or not isinstance(changed_paths, list)
        or not changed_paths
        or not all(isinstance(path, str) and path for path in changed_paths)
        or len(changed_paths) != len(set(changed_paths))
        or not isinstance(head_oid, str)
        or GIT_OID_PATTERN.fullmatch(head_oid) is None
        or scope.get("closure_eligible") is not True
    ):
        return False
    if mode == "staged":
        return True
    base_oid = scope.get("base_oid")
    base_ref = scope.get("base_ref")
    head_ref = scope.get("head_ref")
    return bool(
        isinstance(base_oid, str)
        and GIT_OID_PATTERN.fullmatch(base_oid)
        and isinstance(base_ref, str)
        and base_ref
        and not base_ref.startswith("-")
        and "\0" not in base_ref
        and isinstance(head_ref, str)
        and head_ref
        and not head_ref.startswith("-")
        and "\0" not in head_ref
    )


def inspection_matches_receipt(
    receipt: Mapping[str, Any], inspection: Mapping[str, Any]
) -> bool:
    expected_fields = {
        "changed_paths": "changed_paths",
        "ignored_paths": "ignored_paths",
        "sensitive_paths": "sensitive_paths",
        "categories": "categories",
        "fallback_paths": "fallback_paths",
        "selected_check_ids": "check_ids",
        "npm_workspace_dependency_paths": "npm_workspace_dependency_paths",
    }
    fields_match = all(
        isinstance(receipt.get(receipt_key), list)
        and list(receipt[receipt_key]) == list(inspection[inspection_key])
        for receipt_key, inspection_key in expected_fields.items()
        if receipt_key != "npm_workspace_dependency_paths"
    )
    if not fields_match:
        return False
    expected_dependency_paths = list(
        inspection["npm_workspace_dependency_paths"]
    )
    if "npm_workspace_dependency_paths" not in receipt:
        return expected_dependency_paths == []
    receipt_dependency_paths = receipt["npm_workspace_dependency_paths"]
    return (
        isinstance(receipt_dependency_paths, list)
        and list(receipt_dependency_paths) == expected_dependency_paths
    )


def validate_execution_records(
    receipt: Mapping[str, Any],
    policy: Mapping[str, Any],
    scope: Mapping[str, Any],
    *,
    receipt_dir: Path | None,
    argv_builder: ArgvBuilder,
) -> dict[str, bool]:
    selected = receipt.get("selected_check_ids")
    records = receipt.get("checks")
    if (
        not isinstance(selected, list)
        or not all(isinstance(check_id, str) for check_id in selected)
        or len(selected) != len(set(selected))
        or not isinstance(records, list)
        or not all(isinstance(record, dict) for record in records)
    ):
        return {
            "check_records_complete": False,
            "check_records_valid": False,
            "coverage_closed_same_run": False,
        }

    record_ids = [record.get("check_id") for record in records]
    complete = record_ids == selected
    records_valid = True
    coverage_closed = True
    passed_check_ids: set[str] = set()
    for check_index, record in enumerate(records, start=1):
        check_id = record.get("check_id")
        if not isinstance(check_id, str) or check_id not in policy["checks"]:
            records_valid = False
            coverage_closed = False
            continue
        config = policy["checks"][check_id]
        status = record.get("status")
        if status == "skipped":
            recorded_covering_ids = record.get("covered_by_check_ids")
            allowed_groups = coverage_groups(policy, check_id)
            valid_coverage = (
                record.get("reason") == "covered by passed checks"
                and isinstance(recorded_covering_ids, list)
                and all(isinstance(item, str) for item in recorded_covering_ids)
                and recorded_covering_ids in allowed_groups
                and all(item in passed_check_ids for item in recorded_covering_ids)
            )
            coverage_closed = coverage_closed and valid_coverage
            records_valid = records_valid and valid_coverage
            continue
        if status != "passed":
            records_valid = False
            coverage_closed = False
            continue

        expects_junit = bool(
            policy.get("capture_pytest_junit", False)
            and "pytest" in config["argv"]
        )
        junit_path = None
        if expects_junit:
            if receipt_dir is None:
                records_valid = False
            else:
                junit_path = receipt_dir / f"{check_index:02d}-{check_id}.junit.xml"
        expected_argv = list(argv_builder(config, scope, junit_path))
        expected_cwd = Path(config.get("cwd", ".")).as_posix() or "."
        artifact_records_valid = (
            isinstance(record.get("stdout"), Mapping)
            and isinstance(record.get("stderr"), Mapping)
            and (
                isinstance(record.get("junit"), Mapping)
                if expects_junit
                else "junit" not in record
            )
        )
        exit_code = record.get("exit_code")
        duration_ms = record.get("duration_ms")
        valid_pass = (
            record.get("argv") == expected_argv
            and record.get("cwd") == expected_cwd
            and record.get("description") == config.get("description", "")
            and isinstance(exit_code, int)
            and not isinstance(exit_code, bool)
            and exit_code == 0
            and record.get("timed_out") is False
            and record.get("error") is None
            and isinstance(duration_ms, int)
            and not isinstance(duration_ms, bool)
            and duration_ms >= 0
            and artifact_records_valid
        )
        records_valid = records_valid and valid_pass
        passed_check_ids.add(check_id)

    return {
        "check_records_complete": complete,
        "check_records_valid": records_valid,
        "coverage_closed_same_run": coverage_closed,
    }
