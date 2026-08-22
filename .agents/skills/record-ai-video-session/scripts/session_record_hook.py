from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MAXIMUM_STDIN_BYTES = 65_536
STATE_SCHEMA = "ai-video-session-record-hook/1"


def _git_bytes(project_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        timeout=3,
    )
    return completed.stdout


def _worktree_content_digest(project_root: Path) -> str:
    paths = _git_bytes(
        project_root,
        "ls-files",
        "-z",
        "-m",
        "-o",
        "--exclude-standard",
    ).split(b"\0")
    digest = hashlib.sha256()
    root = os.fsencode(project_root)
    for relative_path in sorted(path for path in paths if path):
        full_path = os.path.join(root, relative_path)
        digest.update(relative_path)
        digest.update(b"\0")
        try:
            metadata = os.lstat(full_path)
        except FileNotFoundError:
            digest.update(b"missing\0")
            continue
        if stat.S_ISLNK(metadata.st_mode):
            digest.update(b"symlink\0")
            digest.update(os.readlink(full_path))
            digest.update(b"\0")
            continue
        if not stat.S_ISREG(metadata.st_mode):
            digest.update(f"mode:{metadata.st_mode:o}".encode("ascii"))
            digest.update(b"\0")
            continue
        digest.update(b"file\0")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(full_path, flags)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError("repository path changed type during snapshot")
            while chunk := os.read(descriptor, 1_048_576):
                digest.update(chunk)
        finally:
            os.close(descriptor)
        digest.update(b"\0")
    return digest.hexdigest()


def _repository_snapshot(project_root: Path) -> dict[str, object]:
    try:
        head = _git_bytes(project_root, "rev-parse", "HEAD").decode("ascii").strip()
    except (OSError, UnicodeDecodeError, subprocess.SubprocessError):
        head = "unborn"
    status = _git_bytes(
        project_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    index_sha256 = hashlib.sha256(
        _git_bytes(project_root, "ls-files", "--stage", "-z")
    ).hexdigest()
    worktree_sha256 = _worktree_content_digest(project_root)
    fingerprint = hashlib.sha256(
        head.encode("ascii", errors="replace")
        + b"\0"
        + status
        + b"\0"
        + index_sha256.encode("ascii")
        + b"\0"
        + worktree_sha256.encode("ascii")
    ).hexdigest()
    return {
        "head": head,
        "dirty": bool(status),
        "status_sha256": hashlib.sha256(status).hexdigest(),
        "index_sha256": index_sha256,
        "worktree_sha256": worktree_sha256,
        "fingerprint": fingerprint,
    }


def default_state_root(project_root: Path) -> Path:
    raw_path = _git_bytes(
        project_root, "rev-parse", "--git-path", "ai-video-session-record-hook"
    ).decode("utf-8").strip()
    state_root = Path(raw_path)
    if not state_root.is_absolute():
        state_root = project_root / state_root
    return state_root.resolve()


def _state_path(state_root: Path, session_id: str) -> Path:
    session_key = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]
    return state_root / f"{session_key}.json"


def _load_state(path: Path) -> dict[str, Any] | None:
    try:
        if path.is_symlink() or path.stat().st_size > 16_384:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("schema") != STATE_SCHEMA:
        return None
    return payload


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _event_cwd(payload: Mapping[str, Any], project_root: Path) -> Path | None:
    raw_cwd = payload.get("cwd")
    candidate = Path(str(raw_cwd)).resolve() if raw_cwd else Path.cwd().resolve()
    project_root = project_root.resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError:
        return None
    return candidate


def _new_state(snapshot: Mapping[str, object]) -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "baseline": dict(snapshot),
        "last_handled_fingerprint": snapshot["fingerprint"],
        "last_requested_fingerprint": None,
    }


def _has_unhandled_change(
    state: Mapping[str, Any], snapshot: Mapping[str, object]
) -> bool:
    fingerprint = snapshot["fingerprint"]
    baseline = state.get("baseline")
    baseline_fingerprint = (
        baseline.get("fingerprint") if isinstance(baseline, Mapping) else None
    )
    return bool(
        fingerprint != baseline_fingerprint
        and fingerprint != state.get("last_handled_fingerprint")
    )


def _capture_request_id(session_id: str, fingerprint: object) -> str:
    digest = hashlib.sha256(
        f"{session_id}\0{fingerprint}".encode("utf-8")
    ).hexdigest()[:16]
    return f"ai-video-record-{digest}"


def process_event(
    payload: Mapping[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    state_root: Path | None = None,
) -> dict[str, object]:
    event_name = str(payload.get("hook_event_name") or "")
    if event_name not in {"SessionStart", "PreCompact", "Stop"}:
        return {"continue": True}
    if _event_cwd(payload, project_root) is None:
        return {"continue": True}
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return {"continue": True}

    project_root = project_root.resolve()
    resolved_state_root = state_root or default_state_root(project_root)
    state_path = _state_path(resolved_state_root, session_id)
    snapshot = _repository_snapshot(project_root)
    state = _load_state(state_path)

    if event_name == "SessionStart":
        if state is None:
            _write_state(state_path, _new_state(snapshot))
        return {"continue": True}

    if state is None:
        state = _new_state(snapshot)
        if snapshot["dirty"]:
            state["baseline"] = None
            state["last_handled_fingerprint"] = None
        _write_state(state_path, state)

    has_unhandled_change = _has_unhandled_change(state, snapshot)

    if event_name == "PreCompact":
        fingerprint = snapshot["fingerprint"]
        if (
            not has_unhandled_change
            or fingerprint == state.get("last_requested_fingerprint")
        ):
            return {"continue": True}
        state["last_requested_fingerprint"] = fingerprint
        _write_state(state_path, state)
        request_id = _capture_request_id(session_id, fingerprint)
        return {
            "continue": True,
            "systemMessage": (
                "AI-VIDEO has unhandled repository changes before compaction "
                f"(capture_request_id={request_id}). Preserve the verified session "
                "boundary and use $record-ai-video-session at the next stable "
                "checkpoint. The hook does not authorize Provider calls, tests, "
                "Git writes, or a record when the skill's stable-boundary test fails."
            ),
        }

    if payload.get("stop_hook_active") is True:
        state["last_handled_fingerprint"] = snapshot["fingerprint"]
        _write_state(state_path, state)
        return {"continue": True}
    if not has_unhandled_change:
        return {"continue": True}
    fingerprint = snapshot["fingerprint"]
    if fingerprint == state.get("last_requested_fingerprint"):
        return {"continue": True}
    state["last_requested_fingerprint"] = fingerprint
    _write_state(state_path, state)
    request_id = _capture_request_id(session_id, fingerprint)
    return {
        "decision": "block",
        "reason": (
            "AI-VIDEO session record checkpoint detected "
            f"(capture_request_id={request_id}). Before finishing, evaluate the "
            "current window with $record-ai-video-session. If substantial work "
            "reached a stable checkpoint, completion, or genuine blocker, invoke "
            "the skill now. Otherwise do not create a record and finish normally. "
            "Preserve unrelated dirty/index work and do not run Provider, media, "
            "network, or extra tests merely for the record."
        ),
    }


def main() -> int:
    raw = sys.stdin.buffer.read(MAXIMUM_STDIN_BYTES + 1)
    if len(raw) > MAXIMUM_STDIN_BYTES:
        print(json.dumps({"continue": True}))
        return 0
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        print(json.dumps({"continue": True}))
        return 0
    if not isinstance(payload, Mapping):
        print(json.dumps({"continue": True}))
        return 0
    try:
        result = process_event(payload)
    except (OSError, UnicodeError, subprocess.SubprocessError, ValueError):
        result = {"continue": True}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
