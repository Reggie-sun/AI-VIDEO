#!/usr/bin/env python3
"""Route an exact Git task scope to mandatory checks and write proof receipts."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from scripts import agent_harness_audit as audit_io
except ModuleNotFoundError:  # Direct ``python scripts/agent_harness.py`` execution.
    import agent_harness_audit as audit_io  # type: ignore[no-redef]

try:
    from scripts import agent_harness_receipt as receipt_io
except ModuleNotFoundError:  # Direct ``python scripts/agent_harness.py`` execution.
    import agent_harness_receipt as receipt_io  # type: ignore[no-redef]

try:
    from scripts.agent_harness_runtime import (
        CommandResult,
        Runner,
        build_check_environment,
        build_git_environment,
        canonical_bytes as _canonical_bytes,
        environment_fingerprint as _environment_fingerprint,
        run_command,
        sha256 as _sha256,
        verify_receipt_integrity,
    )
except ModuleNotFoundError:  # Direct ``python scripts/agent_harness.py`` execution.
    from agent_harness_runtime import (  # type: ignore[no-redef]
        CommandResult,
        Runner,
        build_check_environment,
        build_git_environment,
        canonical_bytes as _canonical_bytes,
        environment_fingerprint as _environment_fingerprint,
        run_command,
        sha256 as _sha256,
        verify_receipt_integrity,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / ".agent/harness/policy.yaml"
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
GIT_OID_PATTERN = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?")
verify_receipt_artifacts = receipt_io.verify_receipt_artifacts
seal_receipt = receipt_io.seal_receipt


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _relative_repository_path(raw_path: str | Path) -> str:
    path = Path(raw_path)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(PROJECT_ROOT)
        except ValueError as exc:
            raise ValueError(f"path is outside repository: {raw_path}") from exc
    normalized = path.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized in {"", "."} or normalized == ".." or normalized.startswith("../"):
        raise ValueError(f"invalid repository-relative path: {raw_path}")
    return normalized


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        candidates = [pattern, pattern[:-3].rstrip("/")]
        if pattern.startswith("**/"):
            candidates.extend(candidate[3:] for candidate in list(candidates))
        return any(fnmatch.fnmatchcase(path, candidate) for candidate in candidates)
    return fnmatch.fnmatchcase(path, pattern)


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(_matches(path, pattern) for pattern in patterns)


def _string_list(mapping: Mapping[str, Any], key: str) -> list[str]:
    value = mapping.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list[str]")
    return value


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle) or {}
    if not isinstance(policy, dict) or policy.get("version") != 2:
        raise ValueError(f"Harness policy version must be 2: {path}")

    runs_dir = policy.get("runs_dir")
    if not isinstance(runs_dir, str) or Path(runs_dir).is_absolute():
        raise ValueError("runs_dir must be repository-relative")
    timeout = policy.get("default_timeout_seconds")
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("default_timeout_seconds must be positive")

    checks = policy.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise ValueError("checks must be a non-empty mapping")
    coverage_dependencies: dict[str, list[str]] = {}
    for check_id, config in checks.items():
        if not isinstance(check_id, str) or not isinstance(config, dict):
            raise ValueError("each check must be a named mapping")
        if not RUN_ID_PATTERN.fullmatch(check_id):
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
        covered_by_check_ids = _string_list(config, "covered_by_check_ids")
        if check_id in covered_by_check_ids:
            raise ValueError(f"check {check_id!r} cannot cover itself")
        coverage_dependencies[check_id] = covered_by_check_ids

    known_check_ids = set(checks)
    referenced = [
        *_string_list(policy, "always_check_ids"),
        *_string_list(policy, "fallback_check_ids"),
        *(
            dependency
            for dependencies in coverage_dependencies.values()
            for dependency in dependencies
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
        referenced.extend(_string_list(category, "check_ids"))
    unknown = sorted(set(referenced) - known_check_ids)
    if unknown:
        raise ValueError(f"policy references unknown checks: {unknown}")

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
    ):
        _string_list(policy, key)
    if not isinstance(policy.get("capture_pytest_junit", False), bool):
        raise ValueError("capture_pytest_junit must be boolean")
    return policy


def inspect_paths(paths: Iterable[str | Path], policy: Mapping[str, Any]) -> dict[str, Any]:
    normalized_paths = sorted(_unique(_relative_repository_path(path) for path in paths))
    sensitive_patterns = [
        pattern.casefold() for pattern in policy["sensitive_patterns"]
    ]
    sensitive_paths = [
        path
        for path in normalized_paths
        if _matches_any(path.casefold(), sensitive_patterns)
    ]
    ignored_paths = [
        path
        for path in normalized_paths
        if path not in sensitive_paths and _matches_any(path, policy["ignored_patterns"])
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
            path for path in active_paths if _matches_any(path, patterns)
        ]
        if category_matches:
            categories.append(category_name)
            category_checks.extend(category.get("check_ids", []))
            matched_paths.update(category_matches)

    fallback_paths = [path for path in active_paths if path not in matched_paths]
    selected = [*policy.get("always_check_ids", []), *category_checks]
    if fallback_paths or sensitive_paths:
        selected.extend(policy.get("fallback_check_ids", []))
    return {
        "changed_paths": active_paths,
        "ignored_paths": ignored_paths,
        "sensitive_paths": sensitive_paths,
        "categories": categories,
        "fallback_paths": fallback_paths,
        "check_ids": _unique(selected),
    }


def parse_name_status_z(payload: bytes) -> list[str]:
    records = [
        part.decode("utf-8", "surrogateescape")
        for part in payload.split(b"\0")
        if part
    ]
    paths: list[str] = []
    index = 0
    while index < len(records):
        status = records[index]
        index += 1
        if index >= len(records):
            raise ValueError("truncated git --name-status -z output")
        paths.append(records[index])
        index += 1
        if status[:1] in {"R", "C"}:
            if index >= len(records):
                raise ValueError("truncated git rename/copy record")
            paths.append(records[index])
            index += 1
    return _unique(paths)


def parse_porcelain_z(payload: bytes) -> list[str]:
    records = payload.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4:
            raise ValueError("invalid git porcelain record")
        status = record[:2].decode("ascii", "replace")
        paths.append(record[3:].decode("utf-8", "surrogateescape"))
        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise ValueError("truncated git porcelain rename/copy record")
            paths.append(records[index].decode("utf-8", "surrogateescape"))
            index += 1
    return _unique(paths)


def _git_bytes(project_root: Path, argv: Sequence[str]) -> bytes:
    return subprocess.run(
        ["git", *argv],
        cwd=project_root,
        check=True,
        capture_output=True,
        env=build_git_environment(),
    ).stdout


def _git_text(project_root: Path, argv: Sequence[str]) -> str:
    return _git_bytes(project_root, argv).decode("utf-8", "surrogateescape").strip()


def _resolve_commit(project_root: Path, ref: str) -> str:
    if not ref or ref.startswith("-") or "\0" in ref:
        raise ValueError(f"invalid Git ref: {ref!r}")
    return _git_text(
        project_root,
        ["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
    )


def _git_name_status(project_root: Path, diff_args: Sequence[str]) -> list[str]:
    return parse_name_status_z(
        _git_bytes(
            project_root,
            ["diff", "--name-status", "-z", "--find-renames", *diff_args],
        )
    )


def _unstaged_or_untracked_paths(project_root: Path) -> list[str]:
    unstaged = _git_name_status(project_root, [])
    untracked = [
        item.decode("utf-8", "surrogateescape")
        for item in _git_bytes(
            project_root, ["ls-files", "--others", "--exclude-standard", "-z"]
        ).split(b"\0")
        if item
    ]
    return _unique([*unstaged, *untracked])


def discover_scope(
    project_root: Path,
    *,
    paths: Sequence[str] | None = None,
    staged: bool = False,
    base_ref: str | None = None,
    head_ref: str = "HEAD",
) -> dict[str, Any]:
    selected_modes = sum((bool(paths), staged, base_ref is not None))
    if selected_modes > 1:
        raise ValueError("--path, --staged and --base-ref are mutually exclusive")
    if paths:
        changed_paths = sorted(_unique(_relative_repository_path(path) for path in paths))
        return {
            "mode": "explicit",
            "changed_paths": changed_paths,
            "closure_eligible": False,
        }
    if staged:
        head_oid = _git_text(project_root, ["rev-parse", "HEAD"])
        changed_paths = _git_name_status(project_root, ["--cached"])
        return {
            "mode": "staged",
            "changed_paths": changed_paths,
            "head_oid": head_oid,
            "closure_eligible": bool(changed_paths),
        }
    if base_ref is not None:
        head_oid = _resolve_commit(project_root, head_ref)
        current_head_oid = _resolve_commit(project_root, "HEAD")
        requested_base_oid = _resolve_commit(project_root, base_ref)
        base_oid = _git_text(project_root, ["merge-base", requested_base_oid, head_oid])
        changed_paths = _git_name_status(project_root, [f"{base_oid}...{head_oid}"])
        return {
            "mode": "commit_range",
            "changed_paths": changed_paths,
            "base_ref": base_ref,
            "base_oid": base_oid,
            "head_ref": head_ref,
            "head_oid": head_oid,
            "closure_eligible": bool(changed_paths) and head_oid == current_head_oid,
        }
    payload = _git_bytes(
        project_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    return {
        "mode": "working_tree",
        "changed_paths": parse_porcelain_z(payload),
        "closure_eligible": False,
    }


def validate_completion_scope(scope: Mapping[str, Any]) -> None:
    if scope.get("mode") not in {"staged", "commit_range"}:
        raise ValueError("completion scope must use --staged or --base-ref")
    if not scope.get("changed_paths"):
        raise ValueError("completion scope is empty")
    if not scope.get("closure_eligible"):
        raise ValueError("completion scope is not closure eligible")


def capture_scope_snapshot(
    project_root: Path,
    *,
    mode: str,
    base_oid: str | None = None,
    head_oid: str | None = None,
) -> dict[str, Any]:
    git_head = _git_text(project_root, ["rev-parse", "HEAD"])
    if mode == "staged":
        patch = _git_bytes(project_root, ["diff", "--cached", "--binary", "--full-index"])
        snapshot: dict[str, Any] = {
            "mode": mode,
            "git_head": git_head,
            "changed_paths": _git_name_status(project_root, ["--cached"]),
            "index_tree": _git_text(project_root, ["write-tree"]),
            "cached_patch_sha256": _sha256(patch),
        }
    elif mode == "commit_range":
        if not base_oid or not head_oid:
            raise ValueError("commit_range snapshot requires base_oid and head_oid")
        snapshot = {
            "mode": mode,
            "git_head": git_head,
            "base_oid": base_oid,
            "head_oid": head_oid,
            "changed_paths": _git_name_status(
                project_root, [f"{base_oid}...{head_oid}"]
            ),
        }
    else:
        raise ValueError(f"unsupported completion snapshot mode: {mode}")
    snapshot["scope_sha256"] = _sha256(_canonical_bytes(snapshot))
    return snapshot


def validate_scope_snapshot(scope: Mapping[str, Any], snapshot: Mapping[str, Any]) -> None:
    if sorted(scope.get("changed_paths", [])) != sorted(snapshot.get("changed_paths", [])):
        raise ValueError("scope changed before verification")
    if scope.get("mode") in {"staged", "commit_range"} and scope.get(
        "head_oid"
    ) != snapshot.get("git_head"):
        raise ValueError("source HEAD changed before verification")


def _scope_snapshot(project_root: Path, scope: Mapping[str, Any]) -> dict[str, Any]:
    return capture_scope_snapshot(
        project_root,
        mode=str(scope["mode"]),
        base_oid=scope.get("base_oid"),
        head_oid=scope.get("head_oid"),
    )


@contextmanager
def isolated_verification_workspace(
    project_root: Path,
    scope: Mapping[str, Any],
    *,
    source_snapshot: Mapping[str, Any] | None = None,
) -> Iterator[Path]:
    validate_completion_scope(scope)
    if source_snapshot is not None and dict(source_snapshot) != _scope_snapshot(
        project_root, scope
    ):
        raise ValueError("source scope changed before isolated verification")
    if scope["mode"] == "staged":
        working_paths = set(_unstaged_or_untracked_paths(project_root))
        overlap = sorted(working_paths.intersection(scope["changed_paths"]))
        if overlap:
            raise ValueError(f"staged scope also has unstaged edits: {overlap}")
        checkout_oid = str(scope["head_oid"])
        staged_patch = _git_bytes(
            project_root,
            ["diff", "--cached", "--binary", "--full-index"],
        )
        if source_snapshot is not None and source_snapshot.get(
            "cached_patch_sha256"
        ) != _sha256(staged_patch):
            raise ValueError("source scope changed before isolated verification")
    else:
        checkout_oid = str(scope["head_oid"])
        staged_patch = b""

    with tempfile.TemporaryDirectory(prefix="ai-video-harness-") as temporary:
        checkout = Path(temporary) / "checkout"
        added = False
        try:
            subprocess.run(
                ["git", "worktree", "add", "--detach", "--quiet", str(checkout), checkout_oid],
                cwd=project_root,
                check=True,
                capture_output=True,
                env=build_git_environment(),
            )
            added = True
            if staged_patch:
                subprocess.run(
                    ["git", "apply", "--index", "--binary", "--whitespace=nowarn", "-"],
                    cwd=checkout,
                    input=staged_patch,
                    check=True,
                    capture_output=True,
                    env=build_git_environment(),
                )
            yield checkout
        finally:
            if added:
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(checkout)],
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    env=build_git_environment(),
                )


def _check_argv(
    config: Mapping[str, Any],
    scope: Mapping[str, Any],
    junit_path: Path | None,
) -> tuple[str, ...]:
    argv = tuple(config["argv"])
    if argv[0] == "python":
        argv = (sys.executable, *argv[1:])
    if config.get("scope_diff"):
        if scope["mode"] == "staged":
            argv = ("git", "diff", "--cached", "--check")
        else:
            argv = ("git", "diff", "--check", f"{scope['base_oid']}..{scope['head_oid']}")
    if config.get("task_architecture"):
        base_oid = scope["head_oid"] if scope["mode"] == "staged" else scope["base_oid"]
        argv = (*argv, "--base-ref", str(base_oid))
    if junit_path is not None and "pytest" in argv:
        argv = (*argv, f"--junitxml={junit_path}")
    return argv


def verify_inspection(
    inspection: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    scope: Mapping[str, Any],
    source_snapshot: Mapping[str, Any],
    project_root: Path = PROJECT_ROOT,
    execution_root: Path | None = None,
    runs_dir: Path | None = None,
    run_id: str | None = None,
    policy_sha256: str | None = None,
    workspace_cleanup_required: bool = False,
    snapshot_after: Callable[[], Mapping[str, Any]] | None = None,
    runner: Runner = run_command,
) -> tuple[Path, bool]:
    validate_completion_scope(scope)
    if inspection.get("sensitive_paths"):
        raise ValueError(
            f"completion scope contains sensitive paths: {inspection['sensitive_paths']}"
        )
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, digits, dot, underscore or dash")

    resolved_root = project_root.resolve()
    resolved_execution_root = (execution_root or project_root).resolve()
    selected_runs_dir = runs_dir or (resolved_root / str(policy["runs_dir"]))
    resolved_runs_dir = selected_runs_dir.resolve()
    if not resolved_runs_dir.is_relative_to(resolved_root):
        raise ValueError("runs_dir must stay inside repository")
    run_dir = resolved_runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt_path = run_dir / "receipt.json"
    receipt: dict[str, Any] = {
        "schema": "ai-video-agent-harness-run/2",
        "run_id": run_id,
        "status": "running",
        "closure_eligible": bool(scope["closure_eligible"]),
        "started_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "scope": dict(scope),
        "policy_sha256": policy_sha256
        or _sha256(_canonical_bytes(dict(policy))),
        "environment": _environment_fingerprint(),
        "changed_paths": list(inspection["changed_paths"]),
        "ignored_paths": list(inspection["ignored_paths"]),
        "sensitive_paths": list(inspection.get("sensitive_paths", [])),
        "categories": list(inspection["categories"]),
        "fallback_paths": list(inspection["fallback_paths"]),
        "selected_check_ids": list(inspection["check_ids"]),
        "source_snapshot_before": dict(source_snapshot),
        "source_snapshot_after": None,
        "workspace_stable": None,
        "workspace_cleanup_status": (
            "pending" if workspace_cleanup_required else "not_required"
        ),
        "checks": [],
    }
    receipt_io.write_receipt(receipt_path, receipt)

    env = build_check_environment()
    passed = True
    passed_check_ids: set[str] = set()
    check_ids = list(inspection["check_ids"])
    for check_index, check_id in enumerate(check_ids, start=1):
        config = policy["checks"][check_id]
        covered_by_check_ids = list(config.get("covered_by_check_ids", []))
        if covered_by_check_ids and all(
            covering_check_id in passed_check_ids
            for covering_check_id in covered_by_check_ids
        ):
            receipt["checks"].append(
                {
                    "check_id": check_id,
                    "status": "skipped",
                    "reason": "covered by passed checks",
                    "covered_by_check_ids": covered_by_check_ids,
                }
            )
            receipt_io.write_receipt(receipt_path, receipt)
            continue
        junit_path = None
        if policy.get("capture_pytest_junit", False) and "pytest" in config["argv"]:
            junit_path = run_dir / f"{check_index:02d}-{check_id}.junit.xml"
        argv = _check_argv(config, scope, junit_path)
        cwd = (resolved_execution_root / config.get("cwd", ".")).resolve()
        if not cwd.is_relative_to(resolved_execution_root):
            raise ValueError(f"check {check_id!r} cwd escaped execution root")
        started = time.monotonic()
        try:
            result = runner(
                argv,
                cwd,
                float(config.get("timeout_seconds", policy["default_timeout_seconds"])),
                env,
            )
        except Exception as exc:
            result = CommandResult(
                status="failed",
                exit_code=None,
                stdout="",
                stderr="",
                error=f"{type(exc).__name__}: {exc}",
            )
        duration_ms = round((time.monotonic() - started) * 1000)
        stdout_path = run_dir / f"{check_index:02d}-{check_id}.stdout.log"
        stderr_path = run_dir / f"{check_index:02d}-{check_id}.stderr.log"
        check_record: dict[str, Any] = {
            "check_id": check_id,
            "argv": list(argv),
            "cwd": cwd.relative_to(resolved_execution_root).as_posix() or ".",
            "description": config.get("description", ""),
            "exit_code": result.exit_code,
            "duration_ms": duration_ms,
            "status": result.status,
            "timed_out": result.timed_out,
            "error": result.error,
        }
        try:
            check_record["stdout"] = receipt_io.write_artifact(
                run_dir, stdout_path, result.stdout
            )
            check_record["stderr"] = receipt_io.write_artifact(
                run_dir, stderr_path, result.stderr
            )
            if junit_path is not None and junit_path.is_file():
                check_record["junit"] = receipt_io.write_artifact(
                    run_dir, junit_path, junit_path.read_bytes()
                )
        except OSError as exc:
            check_record["status"] = "failed"
            check_record["error"] = f"artifact write failed: {type(exc).__name__}: {exc}"
        receipt["checks"].append(check_record)
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.stderr:
            print(
                result.stderr,
                end="" if result.stderr.endswith("\n") else "\n",
                file=sys.stderr,
            )
        if check_record["status"] != "passed":
            passed = False
            for skipped_id in check_ids[check_index:]:
                receipt["checks"].append(
                    {
                        "check_id": skipped_id,
                        "status": "skipped",
                        "reason": f"blocked by failed check {check_id}",
                    }
                )
            break
        passed_check_ids.add(check_id)
        receipt_io.write_receipt(receipt_path, receipt)

    try:
        after = dict(snapshot_after() if snapshot_after else source_snapshot)
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        after = {"error": f"{type(exc).__name__}: {exc}"}
    receipt["source_snapshot_after"] = after
    receipt["workspace_stable"] = dict(source_snapshot) == after
    if not receipt["workspace_stable"]:
        passed = False
        receipt["failure_reason"] = "source scope changed during verification"
    receipt["status"] = "passed" if passed else "failed"
    receipt["finished_at"] = datetime.now(UTC).isoformat()
    receipt_io.write_receipt(receipt_path, receipt)
    return receipt_path, passed


def audit_policy_coverage(
    policy: Mapping[str, Any], project_root: Path = PROJECT_ROOT
) -> dict[str, Any]:
    tracked = [
        item.decode("utf-8", "surrogateescape")
        for item in _git_bytes(project_root, ["ls-files", "-z"]).split(b"\0")
        if item
    ]
    return audit_io.audit_policy_coverage(policy, project_root, tracked)


def receipt_freshness(
    receipt: Mapping[str, Any],
    project_root: Path = PROJECT_ROOT,
    receipt_dir: Path | None = None,
) -> dict[str, Any]:
    integrity = verify_receipt_integrity(receipt)
    receipt_checks = receipt.get("checks", [])
    has_artifacts = isinstance(receipt_checks, list) and any(
        key in check
        for check in receipt_checks
        if isinstance(check, dict)
        for key in ("stdout", "stderr", "junit")
    )
    artifact_integrity = (
        verify_receipt_artifacts(receipt, receipt_dir)
        if receipt_dir is not None
        else not has_artifacts
    )
    schema_supported = receipt.get("schema") == "ai-video-agent-harness-run/2"
    workspace_cleanup_confirmed = receipt.get(
        "workspace_cleanup_status", "not_required"
    ) in {"passed", "not_required"}
    scope = receipt.get("scope", {})
    policy_matches = False
    try:
        if scope.get("mode") == "commit_range" and isinstance(
            scope.get("head_oid"), str
        ):
            if not GIT_OID_PATTERN.fullmatch(scope["head_oid"]):
                raise ValueError("receipt has invalid head_oid")
            policy_bytes = _git_bytes(
                project_root,
                ["show", f"{scope['head_oid']}:.agent/harness/policy.yaml"],
            )
        else:
            policy_bytes = (project_root / ".agent/harness/policy.yaml").read_bytes()
        policy_matches = receipt.get("policy_sha256") == _sha256(policy_bytes)
    except (OSError, subprocess.CalledProcessError, ValueError):
        policy_matches = False
    snapshot_matches = False
    scope_worktree_clean = False
    try:
        working_paths = set(_unstaged_or_untracked_paths(project_root))
        if scope.get("mode") == "commit_range":
            working_paths.update(_git_name_status(project_root, ["--cached"]))
        scope_worktree_clean = not working_paths.intersection(
            scope.get("changed_paths", [])
        )
        if scope.get("mode") == "staged":
            current_snapshot = _scope_snapshot(project_root, scope)
            snapshot_matches = (
                dict(receipt.get("source_snapshot_after") or {}) == current_snapshot
                and current_snapshot.get("git_head") == scope.get("head_oid")
            )
        elif scope.get("mode") == "commit_range":
            head_oid = scope.get("head_oid")
            head_ref = scope.get("head_ref")
            snapshot_matches = (
                isinstance(head_oid, str)
                and GIT_OID_PATTERN.fullmatch(head_oid) is not None
                and isinstance(head_ref, str)
                and _resolve_commit(project_root, "HEAD") == head_oid
                and _resolve_commit(project_root, head_ref) == head_oid
            )
    except (OSError, subprocess.CalledProcessError, ValueError):
        snapshot_matches = False
        scope_worktree_clean = False
    fresh = all(
        (
            integrity,
            artifact_integrity,
            schema_supported,
            workspace_cleanup_confirmed,
            receipt.get("status") == "passed",
            receipt.get("closure_eligible") is True,
            policy_matches,
            snapshot_matches,
            scope_worktree_clean,
        )
    )
    return {
        "integrity": integrity,
        "artifact_integrity": artifact_integrity,
        "schema_supported": schema_supported,
        "workspace_cleanup_confirmed": workspace_cleanup_confirmed,
        "passed": receipt.get("status") == "passed",
        "closure_eligible": receipt.get("closure_eligible") is True,
        "policy_matches": policy_matches,
        "snapshot_matches": snapshot_matches,
        "scope_worktree_clean": scope_worktree_clean,
        "fresh": fresh,
    }


def _add_scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", action="append", help="Advisory inspect path; repeatable.")
    parser.add_argument("--staged", action="store_true", help="Use the exact staged index delta.")
    parser.add_argument("--base-ref", help="Use merge-base(base-ref, head-ref)..head-ref.")
    parser.add_argument("--head-ref", default="HEAD", help="Commit-range head (default: HEAD).")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Show required checks.")
    verify_parser = subparsers.add_parser("verify", help="Run checks and write a receipt.")
    receipt_parser = subparsers.add_parser(
        "verify-receipt", help="Verify receipt integrity and freshness."
    )
    subparsers.add_parser("policy-audit", help="Fail on unmapped owned repository files.")
    _add_scope_arguments(inspect_parser)
    _add_scope_arguments(verify_parser)
    verify_parser.add_argument("--run-id")
    receipt_parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)

    if args.command == "verify-receipt":
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        report = receipt_freshness(receipt, receipt_dir=args.receipt.resolve().parent)
        print(json.dumps(report, sort_keys=True))
        return 0 if report["fresh"] else 1

    policy = load_policy()
    if args.command == "policy-audit":
        report = audit_policy_coverage(policy)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if not any(
            report[key]
            for key in (
                "unmapped_paths",
                "unverified_paths",
                "missing_check_test_paths",
                "docs_contract_diagnostics",
            )
        ) else 1

    receipt_path: Path | None = None
    try:
        scope = discover_scope(
            PROJECT_ROOT,
            paths=args.path,
            staged=args.staged,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
        )
    except (ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))

    if args.command == "inspect":
        inspection = inspect_paths(scope["changed_paths"], policy)
        inspection["scope"] = scope
        print(json.dumps(inspection, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    try:
        validate_completion_scope(scope)
        source_snapshot = _scope_snapshot(PROJECT_ROOT, scope)
        validate_scope_snapshot(scope, source_snapshot)
        with isolated_verification_workspace(
            PROJECT_ROOT, scope, source_snapshot=source_snapshot
        ) as execution_root:
            execution_policy_path = execution_root / ".agent/harness/policy.yaml"
            execution_policy = load_policy(execution_policy_path)
            inspection = inspect_paths(scope["changed_paths"], execution_policy)
            receipt_path, passed = verify_inspection(
                inspection,
                execution_policy,
                scope=scope,
                source_snapshot=source_snapshot,
                project_root=PROJECT_ROOT,
                execution_root=execution_root,
                run_id=args.run_id,
                policy_sha256=_sha256(execution_policy_path.read_bytes()),
                workspace_cleanup_required=True,
                snapshot_after=lambda: _scope_snapshot(PROJECT_ROOT, scope),
            )
        receipt_io.record_workspace_cleanup(receipt_path, status="passed")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        if receipt_path is not None and receipt_path.is_file():
            try:
                receipt_io.record_workspace_cleanup(
                    receipt_path,
                    status="failed",
                    error=f"isolated workspace cleanup failed: {exc}",
                )
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        print(json.dumps({"status": "failed", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "passed" if passed else "failed",
                "receipt": receipt_path.relative_to(PROJECT_ROOT).as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
