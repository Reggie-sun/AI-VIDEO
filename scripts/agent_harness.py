#!/usr/bin/env python3
"""Route changed files to required repository checks and record run receipts."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import time
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / ".agent/harness/policy.yaml"
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

Runner = Callable[[tuple[str, ...], Path], int]


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
        prefix = pattern[:-3].rstrip("/")
        return path == prefix or path.startswith(f"{prefix}/")
    return fnmatch.fnmatchcase(path, pattern)


def _check_ids(mapping: dict[str, Any], key: str) -> list[str]:
    value = mapping.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list[str]")
    return value


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle) or {}
    if not isinstance(policy, dict) or policy.get("version") != 1:
        raise ValueError(f"Harness policy version must be 1: {path}")

    runs_dir = policy.get("runs_dir")
    if not isinstance(runs_dir, str) or Path(runs_dir).is_absolute():
        raise ValueError("runs_dir must be repository-relative")

    checks = policy.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise ValueError("checks must be a non-empty mapping")
    for check_id, config in checks.items():
        if not isinstance(check_id, str) or not isinstance(config, dict):
            raise ValueError("each check must be a named mapping")
        argv = config.get("argv")
        cwd = config.get("cwd", ".")
        if not isinstance(argv, list) or not argv or not all(
            isinstance(item, str) for item in argv
        ):
            raise ValueError(f"check {check_id!r} argv must be a non-empty list[str]")
        if not isinstance(config.get("append_changed_paths", False), bool):
            raise ValueError(f"check {check_id!r} append_changed_paths must be boolean")
        if not isinstance(cwd, str) or Path(cwd).is_absolute() or ".." in Path(cwd).parts:
            raise ValueError(f"check {check_id!r} cwd must stay inside repository")

    known_check_ids = set(checks)
    referenced = [
        *_check_ids(policy, "always_check_ids"),
        *_check_ids(policy, "fallback_check_ids"),
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
        referenced.extend(_check_ids(category, "check_ids"))
    unknown = sorted(set(referenced) - known_check_ids)
    if unknown:
        raise ValueError(f"policy references unknown checks: {unknown}")

    ignored = policy.get("ignored_patterns", [])
    if not isinstance(ignored, list) or not all(isinstance(item, str) for item in ignored):
        raise ValueError("ignored_patterns must be a list[str]")
    return policy


def inspect_paths(paths: Iterable[str | Path], policy: dict[str, Any]) -> dict[str, Any]:
    normalized_paths = sorted(_unique(_relative_repository_path(path) for path in paths))
    ignored_patterns = policy.get("ignored_patterns", [])
    ignored_paths = [
        path
        for path in normalized_paths
        if any(_matches(path, pattern) for pattern in ignored_patterns)
    ]
    active_paths = [path for path in normalized_paths if path not in ignored_paths]

    categories: list[str] = []
    category_checks: list[str] = []
    matched_paths: set[str] = set()
    for category_name, category in policy["categories"].items():
        patterns = category["patterns"]
        if any(_matches(path, pattern) for path in active_paths for pattern in patterns):
            categories.append(category_name)
            category_checks.extend(category.get("check_ids", []))
            matched_paths.update(
                path
                for path in active_paths
                if any(_matches(path, pattern) for pattern in patterns)
            )

    fallback_paths = [path for path in active_paths if path not in matched_paths]
    selected = [*policy.get("always_check_ids", []), *category_checks]
    if fallback_paths:
        selected.extend(policy.get("fallback_check_ids", []))
    return {
        "changed_paths": active_paths,
        "ignored_paths": ignored_paths,
        "categories": categories,
        "fallback_paths": fallback_paths,
        "check_ids": _unique(selected),
    }


def _git_paths(project_root: Path, *, staged_only: bool) -> list[str]:
    commands = [["git", "diff", "--cached", "--name-only", "-z"]]
    if not staged_only:
        commands.extend(
            [
                ["git", "diff", "--name-only", "-z"],
                ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            ]
        )
    paths: list[str] = []
    for argv in commands:
        completed = subprocess.run(
            argv,
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        paths.extend(
            item.decode("utf-8", "surrogateescape")
            for item in completed.stdout.split(b"\0")
            if item
        )
    return _unique(paths)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _default_runner(argv: tuple[str, ...], cwd: Path) -> int:
    return subprocess.run(list(argv), cwd=cwd, check=False, shell=False).returncode


def _git_head(project_root: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def verify_inspection(
    inspection: dict[str, Any],
    policy: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    runs_dir: Path | None = None,
    run_id: str | None = None,
    runner: Runner = _default_runner,
) -> tuple[Path, bool]:
    run_id = run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id must contain only letters, digits, dot, underscore or dash")

    resolved_root = project_root.resolve()
    selected_runs_dir = runs_dir or (resolved_root / policy["runs_dir"])
    resolved_runs_dir = selected_runs_dir.resolve()
    if not resolved_runs_dir.is_relative_to(resolved_root):
        raise ValueError("runs_dir must stay inside repository")
    run_dir = resolved_runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt_path = run_dir / "receipt.json"
    receipt: dict[str, Any] = {
        "schema": "ai-video-agent-harness-run/1",
        "run_id": run_id,
        "status": "running",
        "started_at": _timestamp(),
        "finished_at": None,
        "git_head": _git_head(resolved_root),
        "policy_sha256": hashlib.sha256(
            json.dumps(policy, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "changed_paths": inspection["changed_paths"],
        "ignored_paths": inspection["ignored_paths"],
        "categories": inspection["categories"],
        "fallback_paths": inspection["fallback_paths"],
        "selected_check_ids": inspection["check_ids"],
        "checks": [],
    }
    _atomic_write_json(receipt_path, receipt)

    passed = True
    for check_id in inspection["check_ids"]:
        config = policy["checks"][check_id]
        argv = tuple(config["argv"])
        if config.get("append_changed_paths", False):
            argv = (*argv, "--", *inspection["changed_paths"])
        cwd = (resolved_root / config.get("cwd", ".")).resolve()
        started = time.monotonic()
        exit_code = runner(argv, cwd)
        receipt["checks"].append(
            {
                "check_id": check_id,
                "argv": list(argv),
                "cwd": cwd.relative_to(resolved_root).as_posix() or ".",
                "description": config.get("description", ""),
                "exit_code": exit_code,
                "duration_ms": round((time.monotonic() - started) * 1000),
                "status": "passed" if exit_code == 0 else "failed",
            }
        )
        if exit_code != 0:
            passed = False
            break
        _atomic_write_json(receipt_path, receipt)

    receipt["status"] = "passed" if passed else "failed"
    receipt["finished_at"] = _timestamp()
    _atomic_write_json(receipt_path, receipt)
    return receipt_path, passed


def _paths_from_args(args: argparse.Namespace) -> list[str]:
    if args.path:
        return args.path
    return _git_paths(PROJECT_ROOT, staged_only=args.staged)


def _add_path_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path", action="append", help="Task-owned changed path; repeatable.")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect only staged paths instead of all Git changes.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Show required checks.")
    verify_parser = subparsers.add_parser("verify", help="Run checks and write a receipt.")
    _add_path_arguments(inspect_parser)
    _add_path_arguments(verify_parser)
    verify_parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.path and args.staged:
        parser.error("--path and --staged are mutually exclusive")

    policy = load_policy()
    inspection = inspect_paths(_paths_from_args(args), policy)
    if args.command == "inspect":
        print(json.dumps(inspection, ensure_ascii=False, sort_keys=True, indent=2))
        return 0

    receipt_path, passed = verify_inspection(
        inspection,
        policy,
        run_id=args.run_id,
    )
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
