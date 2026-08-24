"""Materialize validated host tool dependencies into an isolated Harness checkout."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


LOCKED_PACKAGE_FIELDS = ("version", "resolved", "integrity", "link")


def _read_json_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return payload


def _validate_installed_npm_lock(
    repository_lock_path: Path, installed_lock_path: Path
) -> None:
    repository_lock = _read_json_mapping(
        repository_lock_path, label="repository package-lock"
    )
    installed_lock = _read_json_mapping(
        installed_lock_path, label="installed package lock"
    )
    repository_packages = repository_lock.get("packages")
    installed_packages = installed_lock.get("packages")
    if (
        repository_lock.get("lockfileVersion") != installed_lock.get("lockfileVersion")
        or not isinstance(repository_packages, dict)
        or not isinstance(installed_packages, dict)
    ):
        raise ValueError("installed npm dependency tree does not match exact package-lock")

    for package_path, installed_record in installed_packages.items():
        locked_record = repository_packages.get(package_path)
        if not isinstance(installed_record, dict) or not isinstance(locked_record, dict):
            raise ValueError(
                "installed npm dependency tree does not match exact package-lock"
            )
        if any(
            installed_record.get(field) != locked_record.get(field)
            for field in LOCKED_PACKAGE_FIELDS
        ):
            raise ValueError(
                "installed npm dependency tree does not match exact package-lock"
            )

    root_record = repository_packages.get("")
    if not isinstance(root_record, dict):
        raise ValueError("repository package-lock is missing its root package")
    required_names: set[str] = set()
    for dependency_key in ("dependencies", "devDependencies"):
        dependencies = root_record.get(dependency_key, {})
        if not isinstance(dependencies, dict):
            raise ValueError(
                f"repository package-lock {dependency_key} must be an object"
            )
        required_names.update(dependencies)
    if any(
        f"node_modules/{dependency_name}" not in installed_packages
        for dependency_name in required_names
    ):
        raise ValueError("installed npm dependency tree is incomplete for package-lock")


def materialize_npm_workspace_dependencies(
    project_root: Path,
    execution_root: Path,
    policy: Mapping[str, Any],
    check_ids: Sequence[str],
) -> list[str]:
    dependency_paths: list[str] = []
    for check_id in check_ids:
        for dependency_path in policy["checks"][check_id].get(
            "npm_workspace_dependency_paths", []
        ):
            if dependency_path not in dependency_paths:
                dependency_paths.append(dependency_path)

    linked: list[str] = []
    resolved_project_root = project_root.resolve()
    resolved_execution_root = execution_root.resolve()
    for dependency_path in dependency_paths:
        relative_path = Path(dependency_path)
        source = project_root / relative_path
        target = execution_root / relative_path
        if source.is_symlink() or not source.is_dir():
            raise ValueError(
                "preinstalled npm dependencies are required before Harness execution: "
                f"{dependency_path}"
            )
        resolved_source = source.resolve()
        resolved_parent = target.parent.resolve()
        if (
            not resolved_source.is_relative_to(resolved_project_root)
            or not resolved_parent.is_relative_to(resolved_execution_root)
            or target.exists()
            or target.is_symlink()
        ):
            raise ValueError(f"unsafe npm workspace dependency target: {dependency_path}")
        _validate_installed_npm_lock(
            resolved_parent / "package-lock.json",
            resolved_source / ".package-lock.json",
        )
        target.symlink_to(resolved_source, target_is_directory=True)
        linked.append(dependency_path)
    return linked
