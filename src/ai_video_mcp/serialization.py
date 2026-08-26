from __future__ import annotations

import asyncio
import fcntl
import os
from collections.abc import Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncIterator, TypeVar


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ResultT = TypeVar("ResultT")


def _git_dir(project_root: Path) -> Path:
    dot_git = project_root / ".git"
    if dot_git.is_dir():
        return dot_git.resolve()
    try:
        marker = dot_git.read_text(encoding="utf-8")
    except OSError:
        return dot_git
    prefix = "gitdir:"
    if not marker.lower().startswith(prefix):
        return dot_git
    candidate = Path(marker[len(prefix) :].strip())
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate.resolve()


def serialization_state_root(project_root: Path = PROJECT_ROOT) -> Path:
    return _git_dir(project_root.resolve()) / "ai-video-analysis-hook"


def default_serialization_lock_path(project_root: Path = PROJECT_ROOT) -> Path:
    return serialization_state_root(project_root) / "worker.lock"


def _open_lock(path: Path) -> int:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise OSError(f"unsafe MCP serialization directory: {path.parent}")
    os.chmod(path.parent, 0o700)
    lock_fd = os.open(
        path,
        os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.fchmod(lock_fd, 0o600)
    except Exception:
        os.close(lock_fd)
        raise
    return lock_fd


@contextmanager
def serialized_execution(lock_path: Path | None = None) -> Iterator[None]:
    path = lock_path or default_serialization_lock_path()
    lock_fd = _open_lock(path)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(lock_fd)


@asynccontextmanager
async def async_serialized_execution(
    lock_path: Path | None = None,
    *,
    poll_interval_seconds: float = 0.05,
) -> AsyncIterator[None]:
    path = lock_path or default_serialization_lock_path()
    lock_fd = _open_lock(path)
    try:
        while True:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                await asyncio.sleep(poll_interval_seconds)
        yield
    finally:
        os.close(lock_fd)


async def _finish_started_operation(operation_task: asyncio.Task[Any]) -> None:
    while not operation_task.done():
        try:
            await asyncio.shield(operation_task)
        except asyncio.CancelledError:
            continue
        except Exception:
            return
    if not operation_task.cancelled():
        operation_task.exception()


async def run_serialized(
    operation: Callable[..., ResultT],
    *args: Any,
    lock_path: Path | None = None,
    poll_interval_seconds: float = 0.05,
    **kwargs: Any,
) -> ResultT:
    async with async_serialized_execution(
        lock_path, poll_interval_seconds=poll_interval_seconds
    ):
        operation_task = asyncio.create_task(
            asyncio.to_thread(operation, *args, **kwargs)
        )
        try:
            return await asyncio.shield(operation_task)
        except asyncio.CancelledError:
            await _finish_started_operation(operation_task)
            raise
