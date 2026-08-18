"""Process execution and receipt primitives for the development Harness."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import signal
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SECRET_ENV_PATTERN = re.compile(
    r"(?:^|_)(?:API_?KEY|ACCESS_?KEY(?:_ID)?|TOKEN|SECRET|PASSWORD|"
    r"CREDENTIALS?|AUTH|COOKIE|SESSION)(?:$|_)",
    re.I,
)
PROXY_ENV_KEYS = {
    "ALL_PROXY",
    "FTP_PROXY",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
}
UNTRUSTED_TOOL_ENV_KEYS = {
    "COVERAGE_PROCESS_START",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "PYTHONWARNINGS",
    "PYTEST_ADDOPTS",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
    "PYTEST_PLUGINS",
}
@dataclass(frozen=True)
class CommandResult:
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False
    error: str | None = None


Runner = Callable[[tuple[str, ...], Path, float, Mapping[str, str]], CommandResult]


def canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_git_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(source or os.environ)
    for key in list(env):
        if key.upper().startswith("GIT_"):
            env.pop(key, None)
    return env


def build_check_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(source or os.environ)
    for key in list(env):
        upper_key = key.upper()
        if (
            upper_key in PROXY_ENV_KEYS
            or upper_key in UNTRUSTED_TOOL_ENV_KEYS
            or upper_key.startswith("GIT_")
            or SECRET_ENV_PATTERN.search(key)
        ):
            env.pop(key, None)
    env["AI_VIDEO_HARNESS_NO_NETWORK"] = "1"
    env["NO_PROXY"] = "127.0.0.1,localhost,::1"
    env["no_proxy"] = env["NO_PROXY"]
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTEST_PLUGINS"] = "scripts.harness_pytest_guard"
    return env


def run_command(
    argv: tuple[str, ...],
    cwd: Path,
    timeout_seconds: float,
    env: Mapping[str, str],
) -> CommandResult:
    def output_text(value: str | bytes | None) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8", "replace")
        return value or ""

    try:
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            env=dict(env),
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        return CommandResult(
            status="timed_out",
            exit_code=None,
            stdout=output_text(stdout or exc.stdout),
            stderr=output_text(stderr or exc.stderr),
            timed_out=True,
            error=f"command timed out after {timeout_seconds:g}s",
        )
    except OSError as exc:
        return CommandResult(
            status="failed",
            exit_code=None,
            stdout="",
            stderr="",
            error=f"{type(exc).__name__}: {exc}",
        )
    return CommandResult(
        status="passed" if process.returncode == 0 else "failed",
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def seal_receipt(receipt: dict[str, Any]) -> str:
    receipt.pop("receipt_sha256", None)
    digest = sha256(canonical_bytes(receipt))
    receipt["receipt_sha256"] = digest
    return digest


def verify_receipt_integrity(receipt: Mapping[str, Any]) -> bool:
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str):
        return False
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    return expected == sha256(canonical_bytes(unsigned))


def environment_fingerprint() -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "credential_like_environment_removed": True,
        "tool_injection_environment_removed": True,
        "pytest_guard": "scripts.harness_pytest_guard",
        "python_socket_policy": "loopback_only_address_apis",
        "subprocess_network_isolation": False,
    }
