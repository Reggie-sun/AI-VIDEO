from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MAXIMUM_STDIN_BYTES = 65_536
MAXIMUM_STATE_BYTES = 16_384
MAXIMUM_OWNED_PATHS = 128
MAXIMUM_OWNED_PATH_LIST_BYTES = 12_000
STATE_SCHEMA = "ai-video-session-record-hook/2"
LEGACY_STATE_SCHEMA = "ai-video-session-record-hook/1"
ACK_OUTCOMES = frozenset({"recorded", "no_record"})
CAPTURE_REQUEST_ID_PATTERN = re.compile(r"^ai-video-record-[0-9a-f]{16}$")
PATCH_PATH_PATTERN = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (?P<path>.+)$", re.MULTILINE
)
PATCH_MOVE_PATTERN = re.compile(r"^\*\*\* Move to: (?P<path>.+)$", re.MULTILINE)
SESSION_RECORD_PREFIX = "docs/record_for_agent/"


def _git_bytes(project_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        timeout=3,
    )
    return completed.stdout


def _digest_repository_path(digest: Any, project_root: Path, relative_path: str) -> None:
    encoded_path = os.fsencode(relative_path)
    full_path = project_root / relative_path
    digest.update(encoded_path)
    digest.update(b"\0")
    try:
        metadata = full_path.lstat()
    except FileNotFoundError:
        digest.update(b"missing\0")
        return
    if stat.S_ISLNK(metadata.st_mode):
        digest.update(b"symlink\0")
        digest.update(os.fsencode(os.readlink(full_path)))
        digest.update(b"\0")
        return
    if not stat.S_ISREG(metadata.st_mode):
        digest.update(f"mode:{metadata.st_mode:o}".encode("ascii"))
        digest.update(b"\0")
        return
    digest.update(b"file\0")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(full_path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("repository path changed type during checkpoint")
        while chunk := os.read(descriptor, 1_048_576):
            digest.update(chunk)
    finally:
        os.close(descriptor)
    digest.update(b"\0")


def _scoped_fingerprint(project_root: Path, owned_paths: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for relative_path in sorted(dict.fromkeys(owned_paths)):
        _digest_repository_path(digest, project_root, relative_path)
    return digest.hexdigest()


def _checkpoint_fingerprint(state: Mapping[str, Any], project_root: Path) -> str:
    digest = hashlib.sha256()
    digest.update(
        _scoped_fingerprint(
            project_root, _validated_owned_paths(state, project_root)
        ).encode("ascii")
    )
    overflow_fingerprint = state.get("overflow_fingerprint")
    if isinstance(overflow_fingerprint, str):
        digest.update(b"\0overflow\0")
        digest.update(overflow_fingerprint.encode("ascii", errors="replace"))
    return digest.hexdigest()


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


def _new_state(project_root: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": STATE_SCHEMA,
        "owned_paths": [],
        "tracking_overflow": False,
        "overflow_fingerprint": None,
        "status": "ACKED",
        "acked_fingerprint": None,
        "pending_fingerprint": None,
        "pending_request_id": None,
        "precompact_reminded_fingerprint": None,
        "last_ack_capture_request_id": None,
        "last_ack_outcome": None,
    }
    state["acked_fingerprint"] = _checkpoint_fingerprint(state, project_root)
    return state


def _load_state(path: Path, project_root: Path) -> dict[str, Any] | None:
    try:
        if path.is_symlink() or path.stat().st_size > MAXIMUM_STATE_BYTES:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema") == LEGACY_STATE_SCHEMA:
        return _new_state(project_root)
    if payload.get("schema") != STATE_SCHEMA:
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
        if temporary.stat().st_size > MAXIMUM_STATE_BYTES:
            raise ValueError("session record hook state exceeds size limit")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@contextlib.contextmanager
def _state_lock(state_path: Path):
    state_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = state_path.with_suffix(f"{state_path.suffix}.lock")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("session record hook lock is not a regular file")
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _event_cwd(payload: Mapping[str, Any], project_root: Path) -> Path | None:
    raw_cwd = payload.get("cwd")
    candidate = Path(str(raw_cwd)).resolve() if raw_cwd else Path.cwd().resolve()
    project_root = project_root.resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError:
        return None
    return candidate


def _normalize_owned_path(
    project_root: Path, raw_path: object, *, base_dir: Path | None = None
) -> str | None:
    if not isinstance(raw_path, str) or not raw_path or "\0" in raw_path:
        return None
    if len(raw_path.encode("utf-8")) > 1_024:
        return None
    root = project_root.resolve()
    base = (base_dir or root).resolve()
    source = Path(raw_path)
    candidate = source.resolve() if source.is_absolute() else (base / source).resolve()
    try:
        relative = candidate.relative_to(root).as_posix()
    except ValueError:
        return None
    if relative in {"", ".git", "docs/record_for_agent"}:
        return None
    if relative.startswith(".git/") or relative.startswith(SESSION_RECORD_PREFIX):
        return None
    return relative


def _patch_text(tool_input: object) -> str | None:
    if isinstance(tool_input, str):
        return tool_input
    if not isinstance(tool_input, Mapping):
        return None
    for key in ("patch", "input"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return None


def _exact_git_add_paths(
    tool_input: object, project_root: Path, event_cwd: Path
) -> list[str]:
    if not isinstance(tool_input, Mapping):
        return []
    command = tool_input.get("command")
    if not isinstance(command, str) or "\n" in command or "\r" in command:
        return []
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    if any(token and set(token) <= set("();<>|&") for token in tokens):
        return []
    if len(tokens) < 3 or Path(tokens[0]).name != "git" or tokens[1] != "add":
        return []
    raw_paths: list[str] = []
    after_separator = False
    for token in tokens[2:]:
        if token == "--":
            after_separator = True
            continue
        if not after_separator and token.startswith("-"):
            if token not in {"-f", "--force", "-u", "--update"}:
                return []
            continue
        if token in {".", "./"} or any(character in token for character in "*?["):
            return []
        raw_paths.append(token)
    normalized = {
        relative
        for raw_path in raw_paths
        if (
            relative := _normalize_owned_path(
                project_root, raw_path, base_dir=event_cwd
            )
        )
        is not None
    }
    return sorted(normalized)


def _tool_succeeded(tool_response: object) -> bool:
    if isinstance(tool_response, str):
        try:
            decoded = json.loads(tool_response)
        except json.JSONDecodeError:
            lowered = tool_response.lstrip().lower()
            return not lowered.startswith(("script failed", "script error"))
        return _tool_succeeded(decoded)
    if not isinstance(tool_response, Mapping):
        return True
    if tool_response.get("isError") is True or tool_response.get("success") is False:
        return False
    exit_code = tool_response.get("exit_code")
    return not isinstance(exit_code, int) or exit_code == 0


def _task_owned_paths(
    payload: Mapping[str, Any], project_root: Path, event_cwd: Path
) -> list[str]:
    if not _tool_succeeded(payload.get("tool_response")):
        return []
    tool_name = payload.get("tool_name")
    if tool_name == "Bash":
        return _exact_git_add_paths(
            payload.get("tool_input"), project_root, event_cwd
        )
    if tool_name != "apply_patch":
        return []
    patch = _patch_text(payload.get("tool_input"))
    if patch is None:
        return []
    raw_paths = [match.group("path") for match in PATCH_PATH_PATTERN.finditer(patch)]
    raw_paths.extend(match.group("path") for match in PATCH_MOVE_PATTERN.finditer(patch))
    normalized = {
        relative
        for raw_path in raw_paths
        if (
            relative := _normalize_owned_path(
                project_root, raw_path, base_dir=event_cwd
            )
        )
        is not None
    }
    return sorted(normalized)


def _capture_request_id(session_id: str, fingerprint: object) -> str:
    digest = hashlib.sha256(
        f"{session_id}\0{fingerprint}".encode("utf-8")
    ).hexdigest()[:16]
    return f"ai-video-record-{digest}"


def _validated_owned_paths(state: Mapping[str, Any], project_root: Path) -> list[str]:
    raw_paths = state.get("owned_paths")
    if not isinstance(raw_paths, list):
        return []
    normalized = {
        relative
        for raw_path in raw_paths[:MAXIMUM_OWNED_PATHS]
        if (relative := _normalize_owned_path(project_root, raw_path)) is not None
    }
    return sorted(normalized)


def _owned_path_list_size(paths: Sequence[str]) -> int:
    return len(json.dumps(list(paths), ensure_ascii=True).encode("utf-8"))


def _clear_pending(state: dict[str, Any]) -> None:
    state["status"] = "ACKED"
    state["pending_fingerprint"] = None
    state["pending_request_id"] = None
    state["precompact_reminded_fingerprint"] = None


def _sync_checkpoint(
    state: dict[str, Any], session_id: str, project_root: Path
) -> bool:
    before = dict(state)
    owned_paths = _validated_owned_paths(state, project_root)
    state["owned_paths"] = owned_paths
    fingerprint = _checkpoint_fingerprint(state, project_root)
    if (
        not owned_paths
        and state.get("tracking_overflow") is not True
    ) or fingerprint == state.get("acked_fingerprint"):
        _clear_pending(state)
    else:
        if fingerprint != state.get("pending_fingerprint"):
            state["precompact_reminded_fingerprint"] = None
        state["status"] = "PENDING"
        state["pending_fingerprint"] = fingerprint
        state["pending_request_id"] = _capture_request_id(session_id, fingerprint)
    return state != before


def _mark_task_owned_paths(
    state: dict[str, Any], paths: Sequence[str], session_id: str, project_root: Path
) -> bool:
    current = _validated_owned_paths(state, project_root)
    kept = list(current)
    overflow_paths: list[str] = []
    for path in sorted(dict.fromkeys(paths)):
        if path in kept:
            continue
        candidate = sorted([*kept, path])
        if (
            len(candidate) <= MAXIMUM_OWNED_PATHS
            and _owned_path_list_size(candidate) <= MAXIMUM_OWNED_PATH_LIST_BYTES
        ):
            kept = candidate
        else:
            overflow_paths.append(path)
    state["owned_paths"] = kept
    if overflow_paths:
        previous = state.get("overflow_fingerprint")
        digest = hashlib.sha256()
        if isinstance(previous, str):
            digest.update(previous.encode("ascii", errors="replace"))
        digest.update(b"\0event\0")
        digest.update(
            _scoped_fingerprint(project_root, overflow_paths).encode("ascii")
        )
        state["overflow_fingerprint"] = digest.hexdigest()
        state["tracking_overflow"] = True
    return _sync_checkpoint(state, session_id, project_root)


def acknowledge_request(
    capture_request_id: str,
    *,
    outcome: str,
    project_root: Path = PROJECT_ROOT,
    state_root: Path | None = None,
) -> bool:
    if (
        not CAPTURE_REQUEST_ID_PATTERN.fullmatch(capture_request_id)
        or outcome not in ACK_OUTCOMES
    ):
        return False
    project_root = project_root.resolve()
    resolved_state_root = state_root or default_state_root(project_root)
    try:
        candidates = sorted(resolved_state_root.glob("*.json"))
    except OSError:
        return False
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in candidates:
        state = _load_state(path, project_root)
        if state is not None and state.get("pending_request_id") == capture_request_id:
            matches.append((path, state))
    if len(matches) != 1:
        return False
    path, _ = matches[0]
    with _state_lock(path):
        state = _load_state(path, project_root)
        if state is None or state.get("pending_request_id") != capture_request_id:
            return False
        owned_paths = _validated_owned_paths(state, project_root)
        current_fingerprint = _checkpoint_fingerprint(state, project_root)
        if (
            state.get("status") != "PENDING"
            or current_fingerprint != state.get("pending_fingerprint")
        ):
            return False
        state["owned_paths"] = owned_paths
        state["acked_fingerprint"] = current_fingerprint
        state["last_ack_capture_request_id"] = capture_request_id
        state["last_ack_outcome"] = outcome
        _clear_pending(state)
        _write_state(path, state)
    return True


def _process_stateful_event(
    payload: Mapping[str, Any],
    *,
    event_name: str,
    event_cwd: Path,
    session_id: str,
    project_root: Path,
    state_path: Path,
) -> dict[str, object]:
    state = _load_state(state_path, project_root)

    if event_name == "SessionStart":
        if state is None:
            state = _new_state(project_root)
        _write_state(state_path, state)
        return {"continue": True}

    if state is None:
        state = _new_state(project_root)

    if event_name == "PostToolUse":
        paths = _task_owned_paths(payload, project_root, event_cwd)
        if paths:
            _mark_task_owned_paths(state, paths, session_id, project_root)
            _write_state(state_path, state)
        return {"continue": True}

    if _sync_checkpoint(state, session_id, project_root):
        _write_state(state_path, state)
    if state.get("status") != "PENDING":
        return {"continue": True}

    fingerprint = state["pending_fingerprint"]
    request_id = str(state["pending_request_id"])
    if event_name == "PreCompact":
        if fingerprint == state.get("precompact_reminded_fingerprint"):
            return {"continue": True}
        state["precompact_reminded_fingerprint"] = fingerprint
        _write_state(state_path, state)
        return {
            "continue": True,
            "systemMessage": (
                "AI-VIDEO STRONG CHECKPOINT REMINDER: this session has an "
                "unacknowledged task-owned checkpoint before compaction "
                f"(capture_request_id={request_id}). Preserve the verified boundary "
                "and evaluate it with $record-ai-video-session. Whether a record is "
                "created or not, acknowledge this exact request after evaluation. "
                "The hook does not authorize Provider calls, tests, Git writes, or "
                "a record when the skill's stable-boundary test fails."
            ),
        }

    if payload.get("stop_hook_active") is True:
        return {"continue": True}
    return {
        "decision": "block",
        "reason": (
            "AI-VIDEO session-owned checkpoint requires record evaluation "
            f"(capture_request_id={request_id}). Before finishing, evaluate the "
            "current window with $record-ai-video-session. This is an expected "
            "checkpoint continuation, not a hook execution failure. If substantial "
            "work reached "
            "a stable checkpoint, completion, or genuine blocker, invoke the skill. "
            "Otherwise do not create a record. In both cases explicitly acknowledge "
            "this capture_request_id so the checkpoint returns to ACKED. Preserve "
            "unrelated dirty/index work and do not run Provider, media, network, or "
            "extra tests merely for the record."
        ),
    }


def process_event(
    payload: Mapping[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    state_root: Path | None = None,
) -> dict[str, object]:
    event_name = str(payload.get("hook_event_name") or "")
    if event_name not in {"SessionStart", "PostToolUse", "PreCompact", "Stop"}:
        return {"continue": True}
    event_cwd = _event_cwd(payload, project_root)
    if event_cwd is None:
        return {"continue": True}
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return {"continue": True}

    project_root = project_root.resolve()
    resolved_state_root = state_root or default_state_root(project_root)
    state_path = _state_path(resolved_state_root, session_id)
    with _state_lock(state_path):
        return _process_stateful_event(
            payload,
            event_name=event_name,
            event_cwd=event_cwd,
            session_id=session_id,
            project_root=project_root,
            state_path=state_path,
        )


def _acknowledge_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Acknowledge a session record request.")
    parser.add_argument("command", choices=["acknowledge"])
    parser.add_argument("--capture-request-id", required=True)
    parser.add_argument("--outcome", choices=sorted(ACK_OUTCOMES), required=True)
    arguments = parser.parse_args(argv)
    acknowledged = acknowledge_request(
        arguments.capture_request_id,
        outcome=arguments.outcome,
    )
    print(json.dumps({"acknowledged": acknowledged}, sort_keys=True))
    return 0 if acknowledged else 2


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        return _acknowledge_main(arguments)
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
