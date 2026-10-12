"""Serialize mutations of the one Grok OAuth Secret Service item."""

import os
import stat
from contextlib import ExitStack, contextmanager
from pathlib import Path


class GrokAuthLockError(RuntimeError):
    """Public, sanitized lock failure; no credential lookup fallback."""


def _runtime_directory() -> Path:
    return Path(f"/run/user/{os.getuid()}")


@contextmanager
def grok_auth_mutation_lock():
    try:
        import fcntl
    except ImportError:
        raise GrokAuthLockError("Grok OAuth requires a private Linux runtime directory.") from None
    with ExitStack() as handles:
        try:
            uid = os.getuid()
            directory = os.open(_runtime_directory(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            handles.callback(os.close, directory)
            parent = os.fstat(directory)
            if parent.st_uid != uid or stat.S_IMODE(parent.st_mode) & 0o077:
                raise GrokAuthLockError("Grok OAuth runtime directory is not private.")
            descriptor = os.open("ai-video-grok-oauth.lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            handles.callback(os.close, descriptor)
            item = os.fstat(descriptor)
            if (not stat.S_ISREG(item.st_mode) or item.st_uid != uid
                    or stat.S_IMODE(item.st_mode) != 0o600 or item.st_nlink != 1 or item.st_size != 0):
                raise GrokAuthLockError("Grok OAuth authentication lock is not private.")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise GrokAuthLockError("Grok OAuth authentication is busy; stop this command.") from None
        except OSError:
            raise GrokAuthLockError("Grok OAuth private authentication lock is unavailable.") from None
        # Closing releases the lock. Keep the empty inode so another process
        # cannot acquire a replacement inode while a mutation is in progress.
        yield
