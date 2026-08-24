"""Local detached refresh queue for derived Agent Memory shards."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence


REFRESHABLE_KINDS = frozenset(
    {
        "experience",
        "superpowers",
        "current_docs",
        "research",
        "deferred",
        "run_summaries",
    }
)


@dataclass(frozen=True)
class RefreshRequest:
    index_root: str
    runs_index_path: str
    corpus_roots: Mapping[str, str]
    desired_sources: Mapping[str, str]
    embedding_backend: str
    batch_size: int

    def normalized(self) -> "RefreshRequest":
        if self.embedding_backend not in {"local", "fake"}:
            raise ValueError("unsupported refresh embedding backend")
        if self.batch_size < 1:
            raise ValueError("refresh batch_size must be positive")
        roots = {
            str(kind): str(Path(path).resolve())
            for kind, path in self.corpus_roots.items()
        }
        unknown = set(roots) - REFRESHABLE_KINDS
        if unknown:
            raise ValueError(f"unknown refresh corpus kinds: {sorted(unknown)}")
        desired = {
            str(kind): str(value)
            for kind, value in self.desired_sources.items()
        }
        if set(desired) != set(roots):
            raise ValueError(
                "refresh desired source identities must match corpus roots"
            )
        return RefreshRequest(
            index_root=str(Path(self.index_root).resolve()),
            runs_index_path=str(Path(self.runs_index_path).resolve()),
            corpus_roots=roots,
            desired_sources=desired,
            embedding_backend=self.embedding_backend,
            batch_size=self.batch_size,
        )


@dataclass(frozen=True)
class EnqueueResult:
    queue_key: str
    kinds: tuple[str, ...]
    worker_started: bool


def _queue_key(request: RefreshRequest) -> str:
    identity = asdict(request.normalized())
    identity.pop("desired_sources")
    payload = json.dumps(identity, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Agent Memory refresh state: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid Agent Memory refresh state: {path}")
    return value


def _pid_alive(pid: int, expected_queue_dir: Path | None = None) -> bool:
    if pid < 1:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    if expected_queue_dir is not None:
        command_path = Path("/proc") / str(pid) / "cmdline"
        try:
            arguments = command_path.read_bytes().split(b"\0")
        except OSError:
            # A false negative can launch a duplicate process, but worker.lock
            # prevents duplicate builders. A false positive can strand pending
            # work indefinitely, so fail open to launching here.
            return False
        expected = str(Path(expected_queue_dir).resolve()).encode("utf-8")
        try:
            worker_index = arguments.index(b"_refresh-worker")
        except ValueError:
            return False
        return arguments[worker_index + 1 : worker_index + 3] == [
            b"--queue-dir",
            expected,
        ]
    return True


def _default_launch(command: Sequence[str], queue_dir: Path):
    log_path = queue_dir / "worker.log"
    log_handle = log_path.open("ab")
    os.chmod(log_path, 0o600)
    allowed_environment = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "PYTHONPATH",
            "XDG_CACHE_HOME",
            "AGENT_MEMORY_MODEL_DIR",
        }
    }
    try:
        return subprocess.Popen(
            list(command),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).resolve().parents[3],
            env=allowed_environment,
            shell=False,
            start_new_session=True,
            close_fds=True,
        )
    finally:
        log_handle.close()


def enqueue_refresh(
    request: RefreshRequest,
    kinds: Sequence[str],
    *,
    queue_root: Path,
    launch: Callable[[Sequence[str]], object] | None = None,
    process_alive: Callable[[int], bool] = _pid_alive,
) -> EnqueueResult:
    """Merge a request and ensure one detached worker is scheduled."""
    request = request.normalized()
    normalized_kinds = tuple(sorted(set(kinds)))
    if not normalized_kinds:
        raise ValueError("at least one refresh corpus kind is required")
    unknown = set(normalized_kinds) - set(request.corpus_roots)
    if unknown:
        raise ValueError(f"refresh roots missing for kinds: {sorted(unknown)}")
    key = _queue_key(request)
    resolved_queue_root = Path(queue_root).resolve()
    resolved_queue_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(resolved_queue_root, 0o700)
    queue_dir = resolved_queue_root / key
    queue_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(queue_dir, 0o700)
    lock_path = queue_dir / "queue.lock"
    with lock_path.open("a+b") as handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        pending_path = queue_dir / "pending.json"
        pending = _read_json(pending_path)
        pid_path = queue_dir / "worker.json"
        worker = _read_json(pid_path)
        active_pid = int(worker.get("pid", 0) or 0)
        worker_is_active = (
            _pid_alive(active_pid, queue_dir)
            if process_alive is _pid_alive
            else process_alive(active_pid)
        )
        active = (
            {str(kind): str(value) for kind, value in worker.get("active", {}).items()}
            if worker_is_active
            else {}
        )
        pending_desired = {
            str(kind): str(value)
            for kind, value in pending.get("desired", {}).items()
        }
        for kind in normalized_kinds:
            desired = request.desired_sources[kind]
            if active.get(kind) == desired:
                pending_desired.pop(kind, None)
            else:
                pending_desired[kind] = desired
        merged = tuple(sorted(pending_desired))
        if merged:
            _atomic_json(
                pending_path,
                {
                    "request": asdict(request),
                    "kinds": list(merged),
                    "desired": pending_desired,
                },
            )
        else:
            pending_path.unlink(missing_ok=True)
        started = False
        if not worker_is_active:
            command = (
                sys.executable,
                "-m",
                "scripts.agent_memory",
                "_refresh-worker",
                "--queue-dir",
                str(queue_dir),
            )
            process = (
                launch(command)
                if launch is not None
                else _default_launch(command, queue_dir)
            )
            pid = int(getattr(process, "pid"))
            _atomic_json(pid_path, {"pid": pid})
            started = True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    reported = tuple(sorted(set(active) | set(merged)))
    return EnqueueResult(queue_key=key, kinds=reported, worker_started=started)


def run_refresh_worker(
    queue_dir: Path,
    builder: Callable[[RefreshRequest, tuple[str, ...]], Mapping[str, int]],
) -> int:
    """Drain one queue under an exclusive worker lock."""
    queue_dir = Path(queue_dir).resolve()
    worker_lock = queue_dir / "worker.lock"
    worker_lock.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with worker_lock.open("a+b") as worker_handle:
        os.chmod(worker_lock, 0o600)
        try:
            fcntl.flock(
                worker_handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except BlockingIOError:
            return 0
        _atomic_json(queue_dir / "worker.json", {"pid": os.getpid()})
        marker_cleared = False
        exit_code = 0
        try:
            while True:
                queue_lock = queue_dir / "queue.lock"
                with queue_lock.open("a+b") as queue_handle:
                    os.chmod(queue_lock, 0o600)
                    fcntl.flock(queue_handle.fileno(), fcntl.LOCK_EX)
                    pending_path = queue_dir / "pending.json"
                    pending = _read_json(pending_path)
                    if not pending:
                        (queue_dir / "worker.json").unlink(missing_ok=True)
                        marker_cleared = True
                        return exit_code
                    pending_path.unlink()
                    request = RefreshRequest(**pending["request"]).normalized()
                    kinds = tuple(str(item) for item in pending["kinds"])
                    _atomic_json(
                        queue_dir / "worker.json",
                        {
                            "pid": os.getpid(),
                            "active": {
                                kind: request.desired_sources[kind]
                                for kind in kinds
                            },
                        },
                    )
                try:
                    counts = dict(builder(request, kinds))
                except Exception as exc:
                    _atomic_json(
                        queue_dir / "status.json",
                        {
                            "status": "failed",
                            "error_type": type(exc).__name__,
                            "kinds": list(kinds),
                        },
                    )
                    exit_code = 2
                    continue
                _atomic_json(
                    queue_dir / "status.json",
                    {
                        "status": "ready",
                        "counts": counts,
                        "kinds": list(kinds),
                    },
                )
                exit_code = 0
        finally:
            if not marker_cleared:
                queue_lock = queue_dir / "queue.lock"
                with queue_lock.open("a+b") as queue_handle:
                    os.chmod(queue_lock, 0o600)
                    fcntl.flock(queue_handle.fileno(), fcntl.LOCK_EX)
                    (queue_dir / "worker.json").unlink(missing_ok=True)
            fcntl.flock(worker_handle.fileno(), fcntl.LOCK_UN)
