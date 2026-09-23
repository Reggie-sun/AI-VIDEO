"""Tracked AOCI cognition assets stay portable and separate from runtime history."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_aoci_manifest_and_baseline_reference_contained_existing_files() -> None:
    manifest = (ROOT / "aoci.txt").read_text(encoding="utf-8")
    assert "path=aoci.meta.txt" in manifest
    assert "path=aoci.code.txt" in manifest
    assert (ROOT / "aoci.meta.txt").is_file()
    assert (ROOT / "aoci.code.txt").is_file()

    config = json.loads((ROOT / ".aoci/config.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / ".aoci/baseline.json").read_text(encoding="utf-8"))
    curation = json.loads((ROOT / ".aoci/curation.json").read_text(encoding="utf-8"))
    assert config["index_path"] == "aoci.txt"
    assert baseline["files"]
    assert curation["version"] == 1
    for relative in baseline["files"]:
        path = PurePosixPath(relative)
        assert not path.is_absolute() and ".." not in path.parts
        assert (ROOT / relative).is_file()


def test_aoci_runtime_history_is_git_ignored_but_governance_files_are_not() -> None:
    for relative in (
        ".aoci/transactions/example.json",
        ".aoci/scope-change/preview.json",
        ".aoci/drafts/candidate.json",
    ):
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "--no-index", relative],
            cwd=ROOT,
            check=False,
        )
        assert ignored.returncode == 0
    for relative in (
        ".aoci/.gitignore",
        ".aoci/baseline.json",
        ".aoci/config.json",
        ".aoci/curation.json",
    ):
        ignored = subprocess.run(
            ["git", "check-ignore", "--quiet", "--no-index", relative],
            cwd=ROOT,
            check=False,
        )
        assert ignored.returncode == 1
