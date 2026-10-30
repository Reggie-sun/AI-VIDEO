"""Read one exact Provider key from the fixed repository-root ``.env``.

User-authorized 2026-10-30: suppliers try this file first, then their exact
Secret Service reference. Never expands variables, searches cwd, or reads the
process environment; errors never carry the value or file content.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat


REPOSITORY_DOTENV = Path(__file__).resolve().parents[3] / ".env"
_MAX_BYTES = 64 * 1024
_MAX_VALUE = 4096
_NAME = re.compile(r"[A-Z][A-Z0-9_]*\Z")
_LINE = re.compile(r"(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=(.*)\Z")


class DotenvSourceError(ValueError):
    """The repository ``.env`` exists but cannot be trusted; fail closed."""

    def __init__(self) -> None:
        super().__init__("The repository .env credential source is invalid.")


def read_dotenv_value(name: str, *, path: Path | None = None) -> str | None:
    """Return the exact non-empty value, ``None`` when absent, or raise on an invalid file."""
    if not _NAME.match(name):
        raise ValueError("Invalid dotenv variable name.")
    target = REPOSITORY_DOTENV if path is None else path
    try:
        descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except FileNotFoundError:
        return None
    except OSError:
        raise DotenvSourceError() from None
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BYTES
                or info.st_uid != os.getuid() or info.st_mode & 0o022):
            raise DotenvSourceError()
        data = os.read(descriptor, _MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise DotenvSourceError()
    except OSError:
        raise DotenvSourceError() from None
    finally:
        os.close(descriptor)
    try:
        text = data.decode("utf-8").removeprefix("\ufeff")
    except UnicodeDecodeError:
        raise DotenvSourceError() from None
    found: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _LINE.match(line)
        if match is None:
            # A malformed line that names the target must not silently fall through.
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", line):
                raise DotenvSourceError()
            continue
        if match.group(1) != name:
            continue
        found.append(match.group(2).strip())
    if len(found) > 1:
        raise DotenvSourceError()
    if not found:
        return None
    value = found[0]
    if value[:1] in ("'", '"'):
        if len(value) < 2 or value[-1] != value[0]:
            raise DotenvSourceError()
        value = value[1:-1]
    if "'" in value or '"' in value:
        raise DotenvSourceError()
    if not value:
        return None
    if len(value) > _MAX_VALUE or any(not 0x21 <= ord(char) <= 0x7E for char in value):
        raise DotenvSourceError()
    return value
