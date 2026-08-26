#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import uuid
from urllib.error import URLError
from urllib.request import urlopen


UNIT_PREFIX = "ai-video-comfyui-"
UNIT_GLOB = f"{UNIT_PREFIX}*.service"
UNIT_PATTERN = re.compile(r"^ai-video-comfyui-[0-9a-f]{32}\.service$")
START_LOCK_NAME = "ai-video-comfyui-supervisor.lock"
LOOPBACK_HOST = "127.0.0.1"


class SupervisorError(RuntimeError):
    pass


def _run(command: list[str]):
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _list_units() -> list[str]:
    result = _run(
        [
            "systemctl",
            "--user",
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
            UNIT_GLOB,
        ]
    )
    if result.returncode != 0:
        raise SupervisorError(result.stderr.strip() or "cannot list user systemd units")
    units = {
        line.split(None, 1)[0]
        for line in result.stdout.splitlines()
        if line.strip() and UNIT_PATTERN.fullmatch(line.split(None, 1)[0])
    }
    return sorted(units)


def _single_unit() -> str | None:
    units = _list_units()
    if len(units) > 1:
        raise SupervisorError(
            "multiple AI-VIDEO ComfyUI units exist; refusing ambiguous lifecycle control: "
            + ", ".join(units)
        )
    return units[0] if units else None


@contextmanager
def _serialized_start():
    runtime_dir = Path(
        os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    ).resolve()
    if not runtime_dir.is_dir():
        raise SupervisorError(f"user runtime directory does not exist: {runtime_dir}")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(runtime_dir / START_LOCK_NAME, flags, 0o600)
        os.fchmod(descriptor, 0o600)
    except OSError as error:
        if "descriptor" in locals():
            os.close(descriptor)
        raise SupervisorError(f"cannot acquire the supervisor start mutex: {error}") from error
    with os.fdopen(descriptor, "a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _unit_state(unit_service: str) -> dict[str, str]:
    result = _run(
        [
            "systemctl",
            "--user",
            "show",
            unit_service,
            "--no-pager",
            "--property=LoadState",
            "--property=ActiveState",
            "--property=SubState",
            "--property=MainPID",
            "--property=ExecMainStatus",
            "--property=InvocationID",
        ]
    )
    state = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            state[key] = value
    if not state and result.returncode != 0:
        raise SupervisorError(result.stderr.strip() or "cannot query the user systemd manager")
    return state


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.2)
        return connection.connect_ex((LOOPBACK_HOST, port)) == 0


def _wait_for_health(port: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    url = f"http://{LOOPBACK_HOST}:{port}/system_stats"
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=min(2.0, timeout_seconds)) as response:
                if response.status == 200:
                    return True
        except (OSError, URLError):
            pass
        time.sleep(0.25)
    return False


def _pid_owns_loopback_listener(
    pid: int, port: int, *, proc_root: Path = Path("/proc")
) -> bool:
    expected_port = f"{port:04X}"
    listener_inodes = set()
    try:
        with (proc_root / "net" / "tcp").open(encoding="ascii") as table:
            next(table, None)
            for line in table:
                fields = line.split()
                if len(fields) < 10 or fields[3] != "0A":
                    continue
                address, separator, port_hex = fields[1].partition(":")
                if separator and address == "0100007F" and port_hex == expected_port:
                    listener_inodes.add(fields[9])
    except OSError:
        return False
    if not listener_inodes:
        return False
    try:
        descriptors = list((proc_root / str(pid) / "fd").iterdir())
    except OSError:
        return False
    for descriptor in descriptors:
        try:
            target = os.readlink(descriptor)
        except OSError:
            continue
        if any(target == f"socket:[{inode}]" for inode in listener_inodes):
            return True
    return False


def _resolve_python(comfy_root: Path, explicit: str | None) -> Path:
    configured = explicit or os.environ.get("COMFYUI_PYTHON")
    if configured:
        return Path(configured).expanduser().resolve()
    local_venv = comfy_root / ".venv" / "bin" / "python"
    return local_venv if local_venv.is_file() else Path(sys.executable).resolve()


def _stop_unit(unit_service: str) -> tuple[bool, str]:
    result = _run(["systemctl", "--user", "stop", unit_service])
    detail = (result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}")[
        :500
    ]
    return result.returncode == 0, detail


def _start(args: argparse.Namespace) -> int:
    with _serialized_start():
        return _start_serialized(args)


def _start_serialized(args: argparse.Namespace) -> int:
    if not 1 <= args.port <= 65535:
        raise SupervisorError("port must be between 1 and 65535")
    if args.health_timeout <= 0:
        raise SupervisorError("health timeout must be positive")
    comfy_root = Path(args.comfy_root).expanduser().resolve()
    main_path = comfy_root / "main.py"
    python_path = _resolve_python(comfy_root, args.python)
    if not main_path.is_file():
        raise SupervisorError(f"ComfyUI main.py does not exist: {main_path}")
    if not python_path.is_file():
        raise SupervisorError(f"ComfyUI Python does not exist: {python_path}")

    existing_units = _list_units()
    if existing_units:
        raise SupervisorError(
            "an AI-VIDEO ComfyUI unit already exists: " + ", ".join(existing_units)
        )
    if _port_in_use(args.port):
        raise SupervisorError(
            f"{LOOPBACK_HOST}:{args.port} is already in use; refusing to replace its owner"
        )

    unit_name = f"{UNIT_PREFIX}{uuid.uuid4().hex}"
    unit_service = f"{unit_name}.service"
    memory_mode = "--novram" if args.novram else "--lowvram"
    command = [
        "systemd-run",
        "--user",
        "--collect",
        f"--unit={unit_name}",
        "--description=AI-VIDEO local ComfyUI",
        "--service-type=exec",
        f"--working-directory={comfy_root}",
        "--property=Restart=no",
        "--property=KillMode=mixed",
        "--property=TimeoutStopSec=30s",
        "--property=StandardOutput=journal",
        "--property=StandardError=journal",
        "--setenv=PYTHONUNBUFFERED=1",
        str(python_path),
        str(main_path),
        "--listen",
        LOOPBACK_HOST,
        "--port",
        str(args.port),
        "--disable-auto-launch",
        memory_mode,
        "--use-sage-attention",
    ]
    result = _run(command)
    if result.returncode != 0:
        raise SupervisorError(result.stderr.strip() or result.stdout.strip())
    try:
        started_state = _unit_state(unit_service)
        invocation_id = started_state.get("InvocationID", "")
        if not invocation_id:
            raise SupervisorError(
                f"{unit_service} started without an observable InvocationID; "
                "refusing unbound lifecycle control"
            )
        if not _wait_for_health(args.port, args.health_timeout):
            raise SupervisorError(
                f"{unit_service} did not become healthy within "
                f"{args.health_timeout:g}s"
            )
        running_state = _unit_state(unit_service)
        try:
            main_pid = int(running_state.get("MainPID") or 0)
        except ValueError as error:
            raise SupervisorError(
                f"{unit_service} reported an invalid MainPID"
            ) from error
        if (
            running_state.get("InvocationID") != invocation_id
            or running_state.get("ActiveState") != "active"
            or main_pid <= 0
            or not _pid_owns_loopback_listener(main_pid, args.port)
        ):
            raise SupervisorError(
                f"{unit_service} did not retain the active systemd-owned loopback listener"
            )
    except SupervisorError as error:
        stopped, stop_detail = _stop_unit(unit_service)
        cleanup = (
            "the unique unit was stopped"
            if stopped
            else (
                "cleanup could not be confirmed; run status before further lifecycle "
                f"control ({stop_detail})"
            )
        )
        raise SupervisorError(f"{error}; {cleanup}") from error
    print(
        json.dumps(
            {
                "unit": unit_service,
                "active_state": "active",
                "invocation_id": invocation_id,
                "url": f"http://{LOOPBACK_HOST}:{args.port}",
            },
            sort_keys=True,
        )
    )
    return 0


def _status(_args: argparse.Namespace) -> int:
    unit_service = _single_unit()
    state = _unit_state(unit_service) if unit_service else {}
    try:
        main_pid = int(state.get("MainPID") or 0)
    except ValueError:
        main_pid = 0
    try:
        exec_main_status = int(state.get("ExecMainStatus") or 0)
    except ValueError:
        exec_main_status = 0
    print(
        json.dumps(
            {
                "unit": unit_service or UNIT_GLOB,
                "load_state": state.get("LoadState", "not-found"),
                "active_state": state.get("ActiveState", "inactive"),
                "sub_state": state.get("SubState", "dead"),
                "main_pid": main_pid,
                "exec_main_status": exec_main_status,
                "invocation_id": state.get("InvocationID", ""),
            },
            sort_keys=True,
        )
    )
    return 0


def _stop(_args: argparse.Namespace) -> int:
    unit_service = _single_unit()
    if unit_service is None:
        print(json.dumps({"unit": UNIT_GLOB, "active_state": "inactive"}, sort_keys=True))
        return 0
    result = _run(["systemctl", "--user", "stop", unit_service])
    if result.returncode != 0:
        raise SupervisorError(result.stderr.strip() or result.stdout.strip())
    print(json.dumps({"unit": unit_service, "active_state": "inactive"}, sort_keys=True))
    return 0


def _logs(args: argparse.Namespace) -> int:
    if args.lines < 0:
        raise SupervisorError("lines must not be negative")
    unit_service = _single_unit()
    if unit_service is None:
        raise SupervisorError("no active AI-VIDEO ComfyUI unit exists")
    result = _run(
        [
            "journalctl",
            "--user",
            "--unit",
            unit_service,
            "--no-pager",
            "--lines",
            str(args.lines),
        ]
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explicit user-systemd supervision for the local ComfyUI process."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument(
        "--comfy-root",
        default=os.environ.get("COMFYUI_ROOT", str(Path.home() / "ComfyUI")),
    )
    start.add_argument("--python")
    start.add_argument("--port", type=int, default=8188)
    start.add_argument("--health-timeout", type=float, default=60.0)
    start.add_argument(
        "--novram",
        action="store_true",
        help="use ComfyUI --novram instead of the default --lowvram",
    )
    start.set_defaults(handler=_start)

    status = subparsers.add_parser("status")
    status.set_defaults(handler=_status)

    stop = subparsers.add_parser("stop")
    stop.set_defaults(handler=_stop)

    logs = subparsers.add_parser("logs")
    logs.add_argument("--lines", type=int, default=100)
    logs.set_defaults(handler=_logs)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.handler(args)
    except SupervisorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
