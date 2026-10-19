"""Build a local, read-only evidence projection for the module overview."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from scripts.agent_harness_receipt import verify_receipt_artifacts
    from scripts.agent_harness_runtime import sha256, verify_receipt_integrity
except ModuleNotFoundError:  # Direct ``python scripts/provider_console_evidence.py`` use.
    from agent_harness_receipt import verify_receipt_artifacts
    from agent_harness_runtime import sha256, verify_receipt_integrity


CATALOG_RELATIVE_PATH = "provider-console/scripts/module-evidence-catalog.json"
ALLOWED_RECEIPT_CHECKS: dict[str, frozenset[str]] = {
    ".agent/harness/runs/character-performance-control-20261020-r4/receipt.json": frozenset(
        {
            "canvas_production_workflow_tests",
            "canvas_project_data_check",
            "generation_feedback_tests",
            "shot_readiness_gate_tests",
            "video_planner_tests",
            "production_shot_router_tests",
            "provider_neutral_video_requirement_tests",
            "production_video_provider_tests",
            "production_vidu_tests",
            "final_output_no_regression_tests",
            "harness_tests",
        }
    ),
    ".agent/harness/runs/reference-control-preview-20261016-r1/receipt.json": frozenset(
        {
            "generation_feedback_tests",
            "provider_neutral_video_requirement_tests",
            "production_shot_router_tests",
        }
    ),
    ".agent/harness/runs/native-audio-retime-20261018-r4/receipt.json": frozenset(
        {"production_composition_audio_tests", "native_audio_retime_tests"}
    ),
    ".agent/harness/runs/module-map-relations-20261020-r1/receipt.json": frozenset(
        {"provider_console_node_tests", "provider_console_web_build"}
    ),
    ".agent/harness/runs/edit-first-temporal-control-20261017-r4/receipt.json": frozenset(
        {
            "production_strategy_tests",
            "production_shot_router_tests",
            "production_composition_audio_tests",
        }
    ),
}
EXPECTED_MODULE_IDS = frozenset(
    {
        "creative", "canvas", "authoring", "performance", "references", "readiness",
        "planner", "routing", "feedback", "adapters", "continuity", "timeline",
        "retime", "cleanup", "audio", "renderer", "state", "committer", "dependency",
        "safety", "analysis", "qa", "console", "memory", "harness", "special",
    }
)

MAX_CATALOG_BYTES = 1_000_000
MAX_RECEIPT_BYTES = 2_000_000
MAX_SOURCE_BYTES = 8_000_000
MAX_ARTIFACT_BYTES = 12_000_000
MAX_RECEIPT_ARTIFACT_BYTES = 100_000_000
OID_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RECEIPT_READ_REASONS = {
    "file_missing": "receipt_missing",
    "unsafe_path": "receipt_unsafe",
    "not_regular_file": "receipt_unsafe",
    "file_too_large": "receipt_invalid",
    "file_changed_during_read": "receipt_unavailable",
    "file_unavailable": "receipt_unavailable",
    "json_invalid": "receipt_invalid",
    "json_duplicate_key": "receipt_invalid",
}


class EvidenceError(Exception):
    """A sanitized, expected projection failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise EvidenceError("invalid_relative_path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise EvidenceError("invalid_relative_path")
    return path.as_posix()


def _open_directory_without_symlinks(path: Path) -> int:
    absolute = Path(os.path.abspath(path))
    if not absolute.is_absolute():
        raise EvidenceError("repository_path_unavailable")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            next_descriptor = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise EvidenceError("repository_path_unavailable")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_relative_file(root_fd: int, relative_path: str, *, limit: int) -> tuple[bytes, tuple[int, ...]]:
    safe_path = _safe_relative_path(relative_path)
    parts = PurePosixPath(safe_path).parts
    directory_fd = os.dup(root_fd)
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        for component in parts[:-1]:
            next_fd = os.open(component, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(parts[-1], file_flags, dir_fd=directory_fd)
    except OSError as exc:
        if exc.errno in {getattr(os, "ENOENT", 2), 2}:
            raise EvidenceError("file_missing") from None
        if exc.errno in {getattr(os, "ELOOP", 40), 40, getattr(os, "ENOTDIR", 20), 20}:
            raise EvidenceError("unsafe_path") from None
        raise EvidenceError("file_unavailable") from None
    finally:
        os.close(directory_fd)

    try:
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise EvidenceError("not_regular_file")
        if before.st_size < 0 or before.st_size > limit:
            raise EvidenceError("file_too_large")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(file_fd, min(1024 * 1024, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise EvidenceError("file_too_large")
        after = os.fstat(file_fd)
        if _stat_identity(before) != _stat_identity(after) or total != before.st_size:
            raise EvidenceError("file_changed_during_read")
        return b"".join(chunks), _stat_identity(after)
    finally:
        os.close(file_fd)


def _strict_json(data: bytes) -> Any:
    def no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise EvidenceError("json_duplicate_key")
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
    except EvidenceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise EvidenceError("json_invalid") from None


class LocalGit:
    """Runs bounded local Git read commands with inherited GIT_* state removed."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.env = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "WINDIR"}
        }
        self.env.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_CONFIG_NOSYSTEM": "1"})
        self.cache: dict[tuple[str, ...], tuple[int, bytes]] = {}

    def run(self, *args: str, limit: int = 2_000_000) -> tuple[int, bytes]:
        key = tuple(args)
        if key in self.cache:
            return self.cache[key]
        try:
            result = subprocess.run(
                ["git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", *args],
                cwd=self.root,
                env=self.env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=4,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise EvidenceError("git_unavailable") from None
        if len(result.stdout) > limit:
            raise EvidenceError("git_output_too_large")
        answer = (result.returncode, result.stdout)
        self.cache[key] = answer
        return answer

    def text(self, *args: str) -> str | None:
        code, output = self.run(*args)
        if code != 0:
            return None
        try:
            return output.decode("ascii").strip()
        except UnicodeDecodeError:
            return None

    def commit_exists(self, oid: str) -> bool:
        if not OID_RE.fullmatch(oid):
            return False
        actual = self.text("rev-parse", "--verify", f"{oid}^{{commit}}")
        return actual == oid

    def is_ancestor(self, base: str, head: str) -> bool:
        code, _ = self.run("merge-base", "--is-ancestor", base, head, limit=0)
        return code == 0

    def changed_paths(self, base: str, head: str) -> list[str] | None:
        code, output = self.run("diff", "--name-only", "-z", "--no-ext-diff", base, head, limit=1_000_000)
        if code != 0:
            return None
        try:
            return [item.decode("utf-8") for item in output.split(b"\0") if item]
        except UnicodeDecodeError:
            return None

    def blob_at(self, oid: str, relative_path: str) -> bytes | None:
        safe_path = _safe_relative_path(relative_path)
        listing_code, listing = self.run("ls-tree", "-z", "--full-tree", oid, "--", safe_path)
        if listing_code != 0:
            return None
        records = listing.split(b"\0")
        if len(records) != 2 or not records[0]:
            return None
        metadata, separator, listed_path = records[0].partition(b"\t")
        fields = metadata.split()
        if separator != b"\t" or listed_path.decode("utf-8", "replace") != safe_path:
            return None
        if len(fields) != 3 or fields[0] not in {b"100644", b"100755"} or fields[1] != b"blob":
            return None
        blob_oid = fields[2].decode("ascii", "strict")
        code, content = self.run("cat-file", "blob", blob_oid, limit=MAX_SOURCE_BYTES)
        return content if code == 0 else None


def _load_catalog(root_fd: int) -> list[dict[str, Any]]:
    data, _ = _read_relative_file(root_fd, CATALOG_RELATIVE_PATH, limit=MAX_CATALOG_BYTES)
    catalog = _strict_json(data)
    if not isinstance(catalog, dict) or catalog.get("schema") != "ai-video-module-evidence-catalog/1":
        raise EvidenceError("catalog_schema_invalid")
    raw_modules = catalog.get("modules")
    if not isinstance(raw_modules, list) or len(raw_modules) != len(EXPECTED_MODULE_IDS):
        raise EvidenceError("catalog_modules_invalid")
    modules: list[dict[str, Any]] = []
    ids: set[str] = set()
    for raw_module in raw_modules:
        if not isinstance(raw_module, dict):
            raise EvidenceError("catalog_module_invalid")
        module_id = raw_module.get("id")
        kind = raw_module.get("kind")
        if not isinstance(module_id, str) or module_id not in EXPECTED_MODULE_IDS or module_id in ids:
            raise EvidenceError("catalog_module_id_invalid")
        if kind not in {"engineering", "media", "creative"}:
            raise EvidenceError("catalog_module_kind_invalid")
        ids.add(module_id)
        source_files = raw_module.get("source_files")
        receipts = raw_module.get("engineering_receipts")
        if not isinstance(source_files, list) or not source_files or not isinstance(receipts, list):
            raise EvidenceError("catalog_module_entries_invalid")
        try:
            for source_path in source_files:
                _safe_relative_path(source_path)
        except EvidenceError:
            raise EvidenceError("catalog_source_path_invalid") from None
        checked_receipts: list[dict[str, Any]] = []
        for raw_receipt in receipts:
            if not isinstance(raw_receipt, dict):
                raise EvidenceError("catalog_receipt_invalid")
            receipt_path = raw_receipt.get("path")
            check_ids = raw_receipt.get("check_ids")
            if receipt_path not in ALLOWED_RECEIPT_CHECKS or not isinstance(check_ids, list) or not check_ids:
                raise EvidenceError("catalog_receipt_not_allowlisted")
            if any(not isinstance(check_id, str) or check_id not in ALLOWED_RECEIPT_CHECKS[receipt_path] for check_id in check_ids):
                raise EvidenceError("catalog_check_not_allowlisted")
            if len(set(check_ids)) != len(check_ids):
                raise EvidenceError("catalog_check_duplicate")
            checked_receipts.append({"path": receipt_path, "check_ids": check_ids})
        modules.append({"id": module_id, "kind": kind, "source_files": source_files, "engineering_receipts": checked_receipts})
    if ids != EXPECTED_MODULE_IDS:
        raise EvidenceError("catalog_module_set_invalid")
    return modules


def _source_projection(root_fd: int, source_files: list[str]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    unavailable: list[str] = []
    for path in source_files:
        try:
            data, _ = _read_relative_file(root_fd, path, limit=MAX_SOURCE_BYTES)
            files.append({"path": path, "sha256": sha256(data), "bytes": len(data)})
        except EvidenceError as exc:
            if exc.code == "file_missing":
                missing.append(path)
            else:
                unavailable.append(path)
    state = "unavailable" if unavailable else "missing" if missing else "present"
    source: dict[str, Any] = {"state": state, "files": files}
    if missing:
        source["missing_paths"] = missing
    if unavailable:
        source["unavailable_paths"] = unavailable
    return source


def _stat_artifacts(root_fd: int, receipt_path: str, receipt: Mapping[str, Any]) -> tuple[bool, dict[tuple[str, str], tuple[str, int, tuple[int, ...]]]]:
    checks = receipt.get("checks")
    if not isinstance(checks, list):
        return False, {}
    descriptors: dict[tuple[str, str], tuple[str, int, tuple[int, ...]]] = {}
    total = 0
    for check in checks:
        if not isinstance(check, dict):
            return False, {}
        if check.get("status") == "skipped":
            continue
        check_id = check.get("check_id")
        if not isinstance(check_id, str):
            return False, {}
        for kind in ("stdout", "stderr", "junit"):
            if kind not in check:
                if kind in {"stdout", "stderr"}:
                    return False, {}
                continue
            descriptor = check[kind]
            if not isinstance(descriptor, dict):
                return False, {}
            relative = descriptor.get("path")
            size = descriptor.get("bytes")
            digest = descriptor.get("sha256")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > MAX_ARTIFACT_BYTES:
                return False, {}
            if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                return False, {}
            try:
                safe_relative = _safe_relative_path(relative)
                artifact_path = f"{PurePosixPath(receipt_path).parent.as_posix()}/{safe_relative}"
                data, identity = _read_relative_file(root_fd, artifact_path, limit=MAX_ARTIFACT_BYTES)
            except EvidenceError:
                return False, {}
            if len(data) != size or sha256(data) != digest:
                return False, {}
            total += size
            if total > MAX_RECEIPT_ARTIFACT_BYTES:
                return False, {}
            descriptors[(check_id, kind)] = (artifact_path, size, identity)
    return True, descriptors


def _verify_receipt_artifacts(root_fd: int, receipt_path: str, receipt: Mapping[str, Any], run_dir: Path) -> tuple[bool, dict[tuple[str, str], tuple[str, int, tuple[int, ...]]]]:
    safe, before = _stat_artifacts(root_fd, receipt_path, receipt)
    if not safe:
        return False, {}
    try:
        verified = verify_receipt_artifacts(receipt, run_dir)
    except (OSError, RuntimeError, ValueError):
        return False, {}
    if not verified:
        return False, {}
    for key, (path, size, identity) in before.items():
        try:
            data, after_identity = _read_relative_file(root_fd, path, limit=MAX_ARTIFACT_BYTES)
        except EvidenceError:
            return False, {}
        if len(data) != size or after_identity != identity:
            return False, {}
    return True, before


def _receipt_structure_valid(receipt: object) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != "ai-video-agent-harness-run/2":
        return False
    if receipt.get("status") != "passed" or receipt.get("workspace_stable") is not True:
        return False
    if receipt.get("workspace_cleanup_status") != "passed":
        return False
    finished_at = receipt.get("finished_at")
    if not isinstance(finished_at, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    scope = receipt.get("scope")
    before = receipt.get("source_snapshot_before")
    after = receipt.get("source_snapshot_after")
    if not isinstance(scope, dict) or not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if scope.get("mode") != "commit_range":
        return False
    base = scope.get("base_oid")
    head = scope.get("head_oid")
    if not isinstance(base, str) or not OID_RE.fullmatch(base) or not isinstance(head, str) or not OID_RE.fullmatch(head):
        return False
    changed_paths = scope.get("changed_paths")
    if not isinstance(changed_paths, list) or not changed_paths:
        return False
    try:
        normalized_paths = [_safe_relative_path(path) for path in changed_paths]
    except EvidenceError:
        return False
    if normalized_paths != changed_paths or len(set(changed_paths)) != len(changed_paths):
        return False
    snapshot_keys = ("mode", "base_oid", "head_oid", "git_head", "changed_paths", "scope_sha256")
    expected = {"mode": "commit_range", "base_oid": base, "head_oid": head, "git_head": head, "changed_paths": changed_paths}
    before_value = {key: before.get(key) for key in snapshot_keys}
    after_value = {key: after.get(key) for key in snapshot_keys}
    if before_value != after_value:
        return False
    if any(before.get(key) != value for key, value in expected.items()):
        return False
    if not isinstance(before.get("scope_sha256"), str) or not SHA256_RE.fullmatch(before["scope_sha256"]):
        return False
    selected = receipt.get("selected_check_ids")
    checks = receipt.get("checks")
    if not isinstance(selected, list) or not isinstance(checks, list):
        return False
    if any(not isinstance(value, str) for value in selected) or len(set(selected)) != len(selected):
        return False
    check_ids = [check.get("check_id") for check in checks if isinstance(check, dict)]
    if len(check_ids) != len(checks) or any(not isinstance(check_id, str) for check_id in check_ids):
        return False
    if len(set(check_ids)) != len(check_ids):
        return False
    return True


def _anchor_match(root_fd: int, source_files: list[str], git: LocalGit, head_commit: str) -> str:
    matches: list[bool] = []
    unknown = False
    for path in source_files:
        try:
            current, _ = _read_relative_file(root_fd, path, limit=MAX_SOURCE_BYTES)
        except EvidenceError:
            unknown = True
            continue
        historic = git.blob_at(head_commit, path)
        if historic is None:
            unknown = True
            continue
        matches.append(sha256(current) == sha256(historic))
    if any(not item for item in matches):
        return "changed"
    if unknown or not matches:
        return "unknown"
    return "match"


def _receipt_cache_entry(root: Path, root_fd: int, git: LocalGit, receipt_path: str) -> tuple[dict[str, Any] | None, str | None, dict[tuple[str, str], tuple[str, int, tuple[int, ...]]]]:
    try:
        raw, _ = _read_relative_file(root_fd, receipt_path, limit=MAX_RECEIPT_BYTES)
    except EvidenceError as exc:
        return None, RECEIPT_READ_REASONS.get(exc.code, "receipt_unavailable"), {}
    try:
        receipt = _strict_json(raw)
    except EvidenceError as exc:
        return None, RECEIPT_READ_REASONS.get(exc.code, "receipt_invalid"), {}
    if not isinstance(receipt, dict) or not verify_receipt_integrity(receipt):
        return None, "receipt_seal_invalid", {}
    if not _receipt_structure_valid(receipt):
        return None, "receipt_snapshot_or_schema_invalid", {}
    scope = receipt["scope"]
    base = scope["base_oid"]
    head = scope["head_oid"]
    if not git.commit_exists(base) or not git.commit_exists(head):
        return None, "receipt_commit_unavailable", {}
    if not git.is_ancestor(base, head) or git.changed_paths(base, head) != scope["changed_paths"]:
        return None, "receipt_snapshot_invalid", {}
    run_dir = root.joinpath(*PurePosixPath(receipt_path).parent.parts)
    artifacts_ok, descriptors = _verify_receipt_artifacts(root_fd, receipt_path, receipt, run_dir)
    if not artifacts_ok:
        return None, "receipt_artifact_invalid", {}
    try:
        run_id = receipt.get("run_id")
        if not isinstance(run_id, str) or run_id != PurePosixPath(receipt_path).parent.name:
            return None, "receipt_identity_invalid", {}
    except (IndexError, ValueError):
        return None, "receipt_identity_invalid", {}
    receipt["_projection_receipt_sha256"] = sha256(raw)
    return receipt, None, descriptors


def _project_engineering(
    root: Path,
    root_fd: int,
    git: LocalGit,
    module: Mapping[str, Any],
    receipt_cache: dict[str, tuple[dict[str, Any] | None, str | None, dict[tuple[str, str], tuple[str, int, tuple[int, ...]]]]],
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    unavailable: list[str] = []
    no_result: list[str] = []
    source_files = module["source_files"]
    for receipt_spec in module["engineering_receipts"]:
        receipt_path = receipt_spec["path"]
        if receipt_path not in receipt_cache:
            receipt_cache[receipt_path] = _receipt_cache_entry(root, root_fd, git, receipt_path)
        receipt, reason, descriptors = receipt_cache[receipt_path]
        if receipt is None:
            unavailable.append(reason or "receipt_unavailable")
            continue
        selected_ids = set(receipt["selected_check_ids"])
        checks = {check["check_id"]: check for check in receipt["checks"]}
        for check_id in receipt_spec["check_ids"]:
            if check_id not in selected_ids or check_id not in checks:
                no_result.append("check_not_in_receipt")
                continue
            check = checks[check_id]
            status = check.get("status")
            exit_code = check.get("exit_code")
            if status == "passed" and type(exit_code) is int and exit_code == 0:
                evidence_status = "passed"
            elif status == "failed" or (type(exit_code) is int and exit_code != 0):
                evidence_status = "failed"
            elif status == "skipped" or status == "not_selected":
                no_result.append("check_not_run")
                continue
            else:
                unavailable.append("check_status_invalid")
                continue
            artifact_items: list[dict[str, Any]] = []
            for kind in ("stdout", "stderr", "junit"):
                descriptor_record = descriptors.get((check_id, kind))
                if descriptor_record is None:
                    continue
                artifact_path, size, _ = descriptor_record
                descriptor = check.get(kind)
                if not isinstance(descriptor, dict):
                    continue
                artifact_items.append(
                    {
                        "path": artifact_path,
                        "sha256": descriptor["sha256"],
                        "bytes": size,
                        "kind": kind,
                    }
                )
            evidence.append(
                {
                    "receipt_path": receipt_path,
                    "receipt_sha256": receipt["_projection_receipt_sha256"],
                    "receipt_seal_sha256": receipt["receipt_sha256"],
                    "base_commit": receipt["scope"]["base_oid"],
                    "head_commit": receipt["scope"]["head_oid"],
                    "finished_at": receipt["finished_at"],
                    "check_id": check_id,
                    "status": evidence_status,
                    "anchor_match": _anchor_match(root_fd, source_files, git, receipt["scope"]["head_oid"]),
                    "artifacts": artifact_items,
                }
            )
    has_pass = any(item["status"] == "passed" for item in evidence)
    has_failure = any(item["status"] == "failed" for item in evidence)
    if has_failure:
        state = "failed"
    elif has_pass:
        state = "historical_pass"
    elif unavailable:
        state = "unavailable"
    else:
        state = "no_result"
    result: dict[str, Any] = {"state": state, "evidence": evidence}
    if state == "failed":
        result["reason"] = "check_failed"
    elif state == "unavailable":
        result["reason"] = sorted(set(unavailable))[0]
    elif state == "no_result":
        result["reason"] = sorted(set(no_result))[0] if no_result else (
            "no_behavioral_check_configured" if not module["engineering_receipts"] else "no_behavioral_result"
        )
    return result


def project_module_evidence(repo_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Return module source and allowlisted historical engineering evidence.

    The projection reads only the catalog, its anchor files, and the finite
    receipts named in that catalog. It makes no network calls or repository
    writes. Historical test results never imply current qualification.
    """

    root = Path(repo_root)
    root_fd = _open_directory_without_symlinks(root)
    try:
        modules = _load_catalog(root_fd)
        git = LocalGit(root)
        head = git.text("rev-parse", "--verify", "HEAD")
        if head is None or not OID_RE.fullmatch(head):
            raise EvidenceError("repository_head_unavailable")
        top_level = git.text("rev-parse", "--show-toplevel")
        if top_level is None:
            raise EvidenceError("repository_root_unavailable")
        if Path(top_level) != Path(os.path.abspath(root)):
            raise EvidenceError("repository_root_mismatch")
        status_code, status_bytes = git.run("status", "--porcelain=v1", "--untracked-files=normal", limit=1_000_000)
        if status_code != 0:
            raise EvidenceError("repository_status_unavailable")
        dirty = bool(status_bytes)

        receipt_cache: dict[str, tuple[dict[str, Any] | None, str | None, dict[tuple[str, str], tuple[str, int, tuple[int, ...]]]]] = {}
        projected: list[dict[str, Any]] = []
        for module in modules:
            source = _source_projection(root_fd, module["source_files"])
            engineering = _project_engineering(root, root_fd, git, module, receipt_cache)
            applies = module["kind"] == "media"
            projected.append(
                {
                    "id": module["id"],
                    "kind": module["kind"],
                    "source": source,
                    "engineering": engineering,
                    "media": {"applicable": applies, "state": "not_evaluated" if applies else "not_applicable"},
                    "human": {"applicable": applies, "state": "not_evaluated" if applies else "not_applicable"},
                }
            )
        try:
            from scripts.provider_console_cases import project_delivery_cases

            delivery_projection = project_delivery_cases(root)
            if not isinstance(delivery_projection, dict):
                raise EvidenceError("delivery_projection_invalid")
            cases = delivery_projection.get("cases")
            delivery = delivery_projection.get("delivery")
            if not isinstance(cases, list) or not isinstance(delivery, dict):
                raise EvidenceError("delivery_projection_invalid")
            if not cases:
                delivery = {"state": "unavailable", "scope": "selected_case_audit", "autonomy": "not_measured"}
        except (ImportError, OSError, KeyError, TypeError, ValueError, EvidenceError):
            cases = []
            delivery = {"state": "unavailable", "scope": "selected_case_audit", "autonomy": "not_measured"}
        return {
            "schema": "ai-video-module-evidence/1",
            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_kind": "local_readonly",
            "repository": {"head": head, "dirty": dirty},
            "modules": projected,
            "cases": cases,
            "delivery": delivery,
        }
    finally:
        os.close(root_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project local AI-VIDEO module evidence as JSON.")
    parser.add_argument("--repo-root", required=True, help="absolute or relative AI-VIDEO repository root")
    args = parser.parse_args(argv)
    try:
        result = project_module_evidence(args.repo_root)
    except EvidenceError as exc:
        parser.exit(2, f"module evidence unavailable: {exc.code}\n")
    except OSError:
        parser.exit(2, "module evidence unavailable: local_read_failed\n")
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
