"""Policy loading, routing, ordering, and coverage for the development Harness."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_ID_PATTERN = re.compile(r"[A-Za-z0-9._-]+")
DEFAULT_EXECUTION_PRIORITY = 100


def unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def relative_repository_path(path: str | Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(PROJECT_ROOT)
        except ValueError as exc:
            raise ValueError(f"path is outside repository: {path}") from exc
    normalized = candidate.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized or normalized == "." or ".." in Path(normalized).parts:
        raise ValueError(f"invalid repository path: {path}")
    return normalized


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        candidates = [pattern, pattern[:-3].rstrip("/")]
        if pattern.startswith("**/"):
            candidates.extend(candidate[3:] for candidate in list(candidates))
        return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)
    return fnmatch.fnmatchcase(path, pattern)


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(matches(path, pattern) for pattern in patterns)


def string_list(mapping: Mapping[str, Any], key: str) -> list[str]:
    value = mapping.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list[str]")
    return value


def load_policy_bytes(
    payload: bytes | str, *, source: str | Path = "<policy>"
) -> dict[str, Any]:
    policy = yaml.safe_load(payload) or {}
    return validate_policy(policy, source=source)


def load_policy(path: Path) -> dict[str, Any]:
    return load_policy_bytes(path.read_bytes(), source=path)


def validate_policy(policy: object, *, source: str | Path) -> dict[str, Any]:
    if not isinstance(policy, dict) or policy.get("version") != 2:
        raise ValueError(f"Harness policy version must be 2: {source}")

    runs_dir = policy.get("runs_dir")
    if not isinstance(runs_dir, str) or Path(runs_dir).is_absolute():
        raise ValueError("runs_dir must be repository-relative")
    timeout = policy.get("default_timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("default_timeout_seconds must be positive")

    checks = policy.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise ValueError("checks must be a non-empty mapping")
    direct_dependencies: dict[str, list[str]] = {}
    reverse_coverage: dict[str, list[str]] = {}
    for check_id, config in checks.items():
        if not isinstance(check_id, str) or not isinstance(config, dict):
            raise ValueError("each check must be a named mapping")
        if not CHECK_ID_PATTERN.fullmatch(check_id):
            raise ValueError(f"unsafe check id: {check_id!r}")
        argv = config.get("argv")
        cwd = config.get("cwd", ".")
        if not isinstance(argv, list) or not argv or not all(
            isinstance(item, str) for item in argv
        ):
            raise ValueError(f"check {check_id!r} argv must be a non-empty list[str]")
        if not isinstance(cwd, str) or Path(cwd).is_absolute() or ".." in Path(cwd).parts:
            raise ValueError(f"check {check_id!r} cwd must stay inside repository")
        check_timeout = config.get("timeout_seconds", timeout)
        if not isinstance(check_timeout, (int, float)) or check_timeout <= 0:
            raise ValueError(f"check {check_id!r} timeout_seconds must be positive")
        for flag in ("scope_diff", "task_architecture"):
            if not isinstance(config.get(flag, False), bool):
                raise ValueError(f"check {check_id!r} {flag} must be boolean")
        for dependency_path in string_list(
            config, "npm_workspace_dependency_paths"
        ):
            candidate = Path(dependency_path)
            if (
                candidate.is_absolute()
                or not dependency_path
                or ".." in candidate.parts
                or candidate.name != "node_modules"
            ):
                raise ValueError(
                    f"check {check_id!r} has unsafe npm workspace dependency path"
                )
        priority = config.get("execution_priority", DEFAULT_EXECUTION_PRIORITY)
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ValueError(f"check {check_id!r} execution_priority must be an integer")
        covered_by = string_list(config, "covered_by_check_ids")
        covers = string_list(config, "covers_check_ids")
        if check_id in covered_by or check_id in covers:
            raise ValueError(f"check {check_id!r} cannot cover itself")
        direct_dependencies[check_id] = covered_by
        reverse_coverage[check_id] = covers

    known_check_ids = set(checks)
    referenced = [
        *string_list(policy, "always_check_ids"),
        *string_list(policy, "fallback_check_ids"),
        *(
            dependency
            for dependencies in direct_dependencies.values()
            for dependency in dependencies
        ),
        *(
            target
            for targets in reverse_coverage.values()
            for target in targets
        ),
    ]
    categories = policy.get("categories")
    if not isinstance(categories, dict):
        raise ValueError("categories must be a mapping")
    for category_name, category in categories.items():
        if not isinstance(category_name, str) or not isinstance(category, dict):
            raise ValueError("each category must be a named mapping")
        patterns = category.get("patterns")
        if not isinstance(patterns, list) or not patterns or not all(
            isinstance(item, str) for item in patterns
        ):
            raise ValueError(f"category {category_name!r} patterns must be list[str]")
        referenced.extend(string_list(category, "check_ids"))
    unknown = sorted(set(referenced) - known_check_ids)
    if unknown:
        raise ValueError(f"policy references unknown checks: {unknown}")

    coverage_dependencies = {
        check_id: list(dependencies)
        for check_id, dependencies in direct_dependencies.items()
    }
    for covering_check_id, covered_check_ids in reverse_coverage.items():
        for covered_check_id in covered_check_ids:
            coverage_dependencies[covered_check_id].append(covering_check_id)
    coverage_dependencies = {
        check_id: unique(dependencies)
        for check_id, dependencies in coverage_dependencies.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit_coverage_dependencies(check_id: str) -> None:
        if check_id in visited:
            return
        if check_id in visiting:
            raise ValueError(f"check coverage contains a cycle at {check_id!r}")
        visiting.add(check_id)
        for dependency in coverage_dependencies[check_id]:
            visit_coverage_dependencies(dependency)
        visiting.remove(check_id)
        visited.add(check_id)

    for check_id in checks:
        visit_coverage_dependencies(check_id)

    for key in (
        "ignored_patterns",
        "sensitive_patterns",
        "audit_patterns",
        "audit_exempt_patterns",
        "audit_explicit_test_patterns",
        "audit_unreferenced_test_exempt_patterns",
    ):
        string_list(policy, key)
    if not isinstance(policy.get("capture_pytest_junit", False), bool):
        raise ValueError("capture_pytest_junit must be boolean")
    return policy


def coverage_groups(policy: Mapping[str, Any], check_id: str) -> list[list[str]]:
    groups: list[list[str]] = []
    direct = list(policy["checks"][check_id].get("covered_by_check_ids", []))
    if direct:
        groups.append(direct)
    for covering_check_id, config in policy["checks"].items():
        if check_id in config.get("covers_check_ids", []):
            groups.append([covering_check_id])
    return groups


def ordered_check_ids(
    check_ids: Iterable[str], policy: Mapping[str, Any]
) -> list[str]:
    selected = unique(check_ids)
    original_order = {check_id: index for index, check_id in enumerate(selected)}
    return sorted(
        selected,
        key=lambda check_id: (
            policy["checks"][check_id].get(
                "execution_priority", DEFAULT_EXECUTION_PRIORITY
            ),
            original_order[check_id],
        ),
    )


def inspect_paths(paths: Iterable[str | Path], policy: Mapping[str, Any]) -> dict[str, Any]:
    normalized_paths = sorted(unique(relative_repository_path(path) for path in paths))
    sensitive_patterns = [
        pattern.casefold() for pattern in policy["sensitive_patterns"]
    ]
    sensitive_paths = [
        path
        for path in normalized_paths
        if matches_any(path.casefold(), sensitive_patterns)
    ]
    ignored_paths = [
        path
        for path in normalized_paths
        if path not in sensitive_paths and matches_any(path, policy["ignored_patterns"])
    ]
    active_paths = [
        path
        for path in normalized_paths
        if path not in ignored_paths and path not in sensitive_paths
    ]

    categories: list[str] = []
    category_checks: list[str] = []
    matched_paths: set[str] = set()
    for category_name, category in policy["categories"].items():
        patterns = category["patterns"]
        category_matches = [
            path for path in active_paths if matches_any(path, patterns)
        ]
        if category_matches:
            categories.append(category_name)
            category_checks.extend(category.get("check_ids", []))
            matched_paths.update(category_matches)

    fallback_paths = [path for path in active_paths if path not in matched_paths]
    selected = [*policy.get("always_check_ids", []), *category_checks]
    if fallback_paths or sensitive_paths:
        selected.extend(policy.get("fallback_check_ids", []))
    check_ids = ordered_check_ids(selected, policy)
    npm_workspace_dependency_paths = unique(
        dependency_path
        for check_id in check_ids
        for dependency_path in policy["checks"][check_id].get(
            "npm_workspace_dependency_paths", []
        )
    )
    return {
        "changed_paths": active_paths,
        "ignored_paths": ignored_paths,
        "sensitive_paths": sensitive_paths,
        "categories": categories,
        "fallback_paths": fallback_paths,
        "check_ids": check_ids,
        "npm_workspace_dependency_paths": npm_workspace_dependency_paths,
    }
