"""Coverage audit for Harness policy-owned repository files."""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


NON_BEHAVIORAL_CHECK_IDS = {"scope_diff_check", "task_architecture_gate"}


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        candidates = [pattern, pattern[:-3].rstrip("/")]
        if pattern.startswith("**/"):
            candidates.extend(candidate[3:] for candidate in list(candidates))
        return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)
    return fnmatch.fnmatchcase(path, pattern)


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(_matches(path, pattern) for pattern in patterns)


def audit_policy_coverage(
    policy: Mapping[str, Any], project_root: Path, tracked: Sequence[str]
) -> dict[str, Any]:
    candidates = [
        path
        for path in tracked
        if _matches_any(path, policy["audit_patterns"])
        and not _matches_any(path, policy["audit_exempt_patterns"])
    ]
    categories = policy["categories"].values()
    category_patterns = [
        pattern for category in categories for pattern in category["patterns"]
    ]
    unmapped = [path for path in candidates if not _matches_any(path, category_patterns)]
    unverified = []
    for path in candidates:
        check_ids = {
            check_id
            for category in policy["categories"].values()
            if _matches_any(path, category["patterns"])
            for check_id in category.get("check_ids", [])
        }
        if path not in unmapped and not (check_ids - NON_BEHAVIORAL_CHECK_IDS):
            unverified.append(path)
    referenced_test_paths = {
        argument
        for check in policy["checks"].values()
        for argument in check["argv"]
        if argument.startswith("tests/") and argument.endswith(".py")
    }
    missing = sorted(
        path for path in referenced_test_paths if not (project_root / path).is_file()
    )
    return {
        "candidate_count": len(candidates),
        "unmapped_paths": sorted(unmapped),
        "unverified_paths": sorted(unverified),
        "missing_check_test_paths": missing,
    }
