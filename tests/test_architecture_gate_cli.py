from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_architecture_gate_exposes_single_repository_entrypoint():
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.architecture_gate", "--help"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert "check" in completed.stdout
    assert "update-baseline" in completed.stdout


def test_architecture_gate_cli_updates_then_checks_a_repository(tmp_path):
    (tmp_path / "src/app").mkdir(parents=True)
    (tmp_path / "src/app/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "architecture_gate.toml").write_text(
        "schema_version = 1\n"
        'source_roots = ["src"]\n'
        'baseline = ".architecture/architecture-baseline.json"\n'
        "normal_loc = 800\nblocking_loc = 1500\nsevere_loc = 3000\n"
        "fan_out_warning = 14\nexclude = []\n",
        encoding="utf-8",
    )

    updated = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.architecture_gate",
            "update-baseline",
            "--root",
            str(tmp_path),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    checked = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.architecture_gate",
            "check",
            "--root",
            str(tmp_path),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert updated.returncode == 0, updated.stderr
    assert checked.returncode == 0, checked.stderr
    assert "Architecture gate: PASS" in checked.stdout
