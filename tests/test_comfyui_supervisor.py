from __future__ import annotations

import importlib.util
from pathlib import Path
import threading
import time
from types import SimpleNamespace


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "comfyui_supervisor.py"
TEST_UNIT = f"ai-video-comfyui-{'a' * 32}.service"


def _load_supervisor():
    assert SCRIPT_PATH.is_file(), "the explicit ComfyUI supervisor script is missing"
    spec = importlib.util.spec_from_file_location("comfyui_supervisor", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _comfy_root(tmp_path: Path) -> Path:
    root = tmp_path / "ComfyUI"
    (root / ".venv" / "bin").mkdir(parents=True)
    (root / "main.py").write_text("# test fixture\n", encoding="utf-8")
    (root / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    return root


def test_start_uses_detached_user_systemd_service(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    unit = TEST_UNIT
    states = iter(
        [
            {"LoadState": "loaded", "ActiveState": "activating", "InvocationID": "run-1"},
            {
                "LoadState": "loaded",
                "ActiveState": "active",
                "MainPID": "1234",
                "InvocationID": "run-1",
            },
        ]
    )
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda actual: next(states) if actual == unit else None,
    )
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor, "_wait_for_health", lambda _port, _timeout: True)
    monkeypatch.setattr(
        supervisor,
        "_pid_owns_loopback_listener",
        lambda pid, port: (pid, port) == (1234, 8188),
    )

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 0
    assert len(commands) == 1
    command = commands[0]
    assert command[:3] == ["systemd-run", "--user", "--collect"]
    assert f"--unit={unit.removesuffix('.service')}" in command
    assert "--service-type=exec" in command
    assert f"--working-directory={root}" in command
    assert "--property=Restart=no" in command
    assert "--property=KillMode=mixed" in command
    assert "--property=TimeoutStopSec=30s" in command
    assert command[-9:] == [
        str(root / ".venv" / "bin" / "python"),
        str(root / "main.py"),
        "--listen",
        "127.0.0.1",
        "--port",
        "8188",
        "--disable-auto-launch",
        "--lowvram",
        "--use-sage-attention",
    ]


def test_start_novram_replaces_lowvram_without_changing_other_runtime_flags(
    monkeypatch, tmp_path
):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    states = iter(
        [
            {"LoadState": "loaded", "ActiveState": "activating", "InvocationID": "run-1"},
            {
                "LoadState": "loaded",
                "ActiveState": "active",
                "MainPID": "1234",
                "InvocationID": "run-1",
            },
        ]
    )
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_unit_state", lambda _actual: next(states))
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor, "_wait_for_health", lambda _port, _timeout: True)
    monkeypatch.setattr(
        supervisor,
        "_pid_owns_loopback_listener",
        lambda pid, port: (pid, port) == (1234, 8188),
    )

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root), "--novram"]) == 0
    command = commands[0]
    assert "--novram" in command
    assert "--lowvram" not in command
    assert command[-1] == "--use-sage-attention"


def test_start_refuses_occupied_port_without_touching_systemd(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: True)
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor, "_run", lambda command: commands.append(command))

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert commands == []


def test_unit_discovery_accepts_only_exact_lowercase_hex_namespace(monkeypatch):
    supervisor = _load_supervisor()
    valid = TEST_UNIT
    output = "\n".join(
        [
            f"{valid} loaded active running valid",
            "ai-video-comfyui-backup.service loaded active running unrelated",
            f"ai-video-comfyui-{'A' * 32}.service loaded active running uppercase",
            "other.service loaded active running unrelated",
        ]
    )
    monkeypatch.setattr(
        supervisor,
        "_run",
        lambda _command: SimpleNamespace(returncode=0, stdout=output, stderr=""),
    )

    assert supervisor._list_units() == [valid]


def test_start_refuses_existing_supervisor_unit_before_port_probe(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    port_probes = []
    monkeypatch.setattr(
        supervisor,
        "_list_units",
        lambda: [TEST_UNIT],
    )
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(
        supervisor, "_port_in_use", lambda port: port_probes.append(port) or False
    )

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert port_probes == []


def test_failed_health_check_stops_only_the_unit_started_here(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    unit = TEST_UNIT
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor, "_wait_for_health", lambda _port, _timeout: False)
    states = iter(
        [
            {"LoadState": "loaded", "ActiveState": "activating", "InvocationID": "run-1"},
        ]
    )
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda actual: next(states) if actual == unit else None,
    )

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert commands[0][0] == "systemd-run"
    assert commands[1] == [
        "systemctl",
        "--user",
        "stop",
        unit,
    ]


def test_failed_health_check_uses_non_reusable_unit_identity(
    monkeypatch, tmp_path, capsys
):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    unit = TEST_UNIT
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    states = iter(
        [
            {"LoadState": "loaded", "ActiveState": "activating", "InvocationID": "run-1"},
        ]
    )
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda actual: next(states) if actual == unit else None,
    )
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor, "_wait_for_health", lambda _port, _timeout: False)

    def run(command):
        commands.append(command)
        return SimpleNamespace(
            returncode=1 if command[:3] == ["systemctl", "--user", "stop"] else 0,
            stdout="",
            stderr="unit disappeared",
        )

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert len(commands) == 2
    assert commands[0][0] == "systemd-run"
    assert commands[1] == ["systemctl", "--user", "stop", unit]
    error = capsys.readouterr().err
    assert "cleanup could not be confirmed" in error
    assert "unit disappeared" in error


def test_missing_invocation_id_cleans_up_unique_unit(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda actual: {"LoadState": "loaded", "ActiveState": "activating"}
        if actual == TEST_UNIT
        else None,
    )

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert commands[-1] == ["systemctl", "--user", "stop", TEST_UNIT]


def test_post_creation_state_query_failure_cleans_up_unique_unit(
    monkeypatch, tmp_path
):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda _actual: (_ for _ in ()).throw(supervisor.SupervisorError("show failed")),
    )

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert commands[-1] == ["systemctl", "--user", "stop", TEST_UNIT]


def test_health_from_another_process_cannot_satisfy_start(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    commands = []
    states = iter(
        [
            {"LoadState": "loaded", "ActiveState": "activating", "InvocationID": "run-1"},
            {
                "LoadState": "loaded",
                "ActiveState": "active",
                "MainPID": "1234",
                "InvocationID": "run-1",
            },
        ]
    )
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(supervisor, "_list_units", lambda: [])
    monkeypatch.setattr(supervisor, "_port_in_use", lambda _port: False)
    monkeypatch.setattr(supervisor, "_wait_for_health", lambda _port, _timeout: True)
    monkeypatch.setattr(supervisor, "_pid_owns_loopback_listener", lambda _pid, _port: False)
    monkeypatch.setattr(supervisor.uuid, "uuid4", lambda: SimpleNamespace(hex="a" * 32))
    monkeypatch.setattr(supervisor, "_unit_state", lambda _actual: next(states))

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert commands[-1] == ["systemctl", "--user", "stop", TEST_UNIT]


def test_listener_ownership_skips_vanished_fd_and_matches_exact_inode(
    monkeypatch, tmp_path
):
    supervisor = _load_supervisor()
    proc_root = tmp_path / "proc"
    (proc_root / "net").mkdir(parents=True)
    fd_root = proc_root / "1234" / "fd"
    fd_root.mkdir(parents=True)
    (proc_root / "net" / "tcp").write_text(
        "sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n"
        "0: 0100007F:1FFA 00000000:0000 0A 00000000:00000000 00:00000000 "
        "00000000 1000 0 4242 1\n",
        encoding="ascii",
    )
    vanished = fd_root / "3"
    owner = fd_root / "4"
    vanished.symlink_to("socket:[9999]")
    owner.symlink_to("socket:[4242]")
    real_readlink = supervisor.os.readlink

    def readlink(path):
        if Path(path).name == "3":
            raise FileNotFoundError(path)
        return real_readlink(path)

    monkeypatch.setattr(supervisor.os, "readlink", readlink)

    assert supervisor._pid_owns_loopback_listener(
        1234, 8186, proc_root=proc_root
    )
    assert not supervisor._pid_owns_loopback_listener(
        1234, 8188, proc_root=proc_root
    )


def test_start_mutex_open_failure_is_typed(monkeypatch, tmp_path, capsys):
    supervisor = _load_supervisor()
    root = _comfy_root(tmp_path)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(
        supervisor.os,
        "open",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )

    assert supervisor.main(["start", "--comfy-root", str(root)]) == 1
    assert "cannot acquire the supervisor start mutex" in capsys.readouterr().err


def test_start_mutex_serializes_concurrent_callers(monkeypatch, tmp_path):
    supervisor = _load_supervisor()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    calls = []

    def serialized(_args):
        calls.append(threading.current_thread().name)
        if len(calls) == 1:
            first_entered.set()
            assert release_first.wait(timeout=2.0)
        else:
            second_entered.set()
        return 0

    monkeypatch.setattr(supervisor, "_start_serialized", serialized)
    first = threading.Thread(target=supervisor._start, args=(SimpleNamespace(),), name="first")
    second = threading.Thread(target=supervisor._start, args=(SimpleNamespace(),), name="second")
    first.start()
    assert first_entered.wait(timeout=1.0)
    second.start()
    time.sleep(0.05)
    assert not second_entered.is_set()
    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)
    assert not first.is_alive()
    assert not second.is_alive()
    assert calls == ["first", "second"]


def test_stop_targets_only_the_named_unit(monkeypatch):
    supervisor = _load_supervisor()
    commands = []
    unit = TEST_UNIT
    monkeypatch.setattr(supervisor, "_single_unit", lambda: unit)

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["stop"]) == 0
    assert commands == [
        ["systemctl", "--user", "stop", unit]
    ]


def test_stop_refuses_ambiguous_multiple_units(monkeypatch):
    supervisor = _load_supervisor()
    commands = []
    monkeypatch.setattr(
        supervisor,
        "_list_units",
        lambda: [
            f"ai-video-comfyui-{'a' * 32}.service",
            f"ai-video-comfyui-{'b' * 32}.service",
        ],
    )
    monkeypatch.setattr(supervisor, "_run", lambda command: commands.append(command))

    assert supervisor.main(["stop"]) == 1
    assert commands == []


def test_status_is_read_only_and_returns_zero_for_failed_unit(monkeypatch, capsys):
    supervisor = _load_supervisor()
    unit = TEST_UNIT
    monkeypatch.setattr(supervisor, "_single_unit", lambda: unit)
    monkeypatch.setattr(
        supervisor,
        "_unit_state",
        lambda actual: (
            {
                "LoadState": "loaded",
                "ActiveState": "failed",
                "SubState": "failed",
                "MainPID": "0",
                "ExecMainStatus": "143",
            }
            if actual == unit
            else None
        ),
    )

    assert supervisor.main(["status"]) == 0
    output = capsys.readouterr().out
    assert '"active_state": "failed"' in output
    assert '"exec_main_status": 143' in output


def test_logs_reads_only_the_named_unit(monkeypatch):
    supervisor = _load_supervisor()
    commands = []
    unit = TEST_UNIT
    monkeypatch.setattr(supervisor, "_single_unit", lambda: unit)

    def run(command):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="recent log\n", stderr="")

    monkeypatch.setattr(supervisor, "_run", run)

    assert supervisor.main(["logs", "--lines", "25"]) == 0
    assert commands == [
        [
            "journalctl",
            "--user",
            "--unit",
            unit,
            "--no-pager",
            "--lines",
            "25",
        ]
    ]
