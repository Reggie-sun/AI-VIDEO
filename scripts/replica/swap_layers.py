"""Load a sibling split part into an explicitly selected open Agentcut project."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from ._local import agentcut_project, cli, write_bytes
from .layers_kit import _exclusive_directory, _json_bytes, _project_error

_FILES = ("layers.json", "project.json")


def _read_pair(directory: Path) -> tuple[bytes, bytes, dict]:
    layers_path, project_path = (directory / name for name in _FILES)
    for path in (layers_path, project_path):
        if path.is_symlink() or not path.is_file():
            raise _project_error(f"{path.name} must be a regular file.")
    try:
        layers = layers_path.read_bytes()
        metadata = project_path.read_bytes()
        valid_layers = isinstance(json.loads(layers), dict)
        project = json.loads(metadata)
    except (OSError, ValueError):
        raise _project_error("Agentcut project files are unreadable.") from None
    duration = project.get("durationInFrames") if isinstance(project, dict) else None
    if not valid_layers or type(duration) is not int or duration < 1:
        raise _project_error("Agentcut project files must define layers and a positive frame duration.")
    return layers, metadata, project


def swap(main_dir: Path, part_dir: Path | None = None) -> int:
    """Apply one part, or restore when part_dir is absent. Keep the original pair until restoration."""
    main_dir = agentcut_project(main_dir)
    part = agentcut_project(part_dir) if part_dir is not None else None
    if part is not None and (part == main_dir or part.parent != main_dir.parent):
        raise _project_error("The main and part must be distinct sibling Agentcut projects.")
    backup = main_dir / ".full-backup"
    with _exclusive_directory(main_dir):
        if backup.is_symlink() or (backup.exists() and not backup.is_dir()):
            raise _project_error("Agentcut full backup must be a local directory.")
        if part is None:
            if not backup.is_dir():
                raise _project_error("No full Agentcut backup is available.")
            if {entry.name for entry in backup.iterdir()} != set(_FILES):
                raise _project_error("Agentcut full backup does not contain the expected file pair.")
            layers, metadata, project = _read_pair(backup)
        else:
            with _exclusive_directory(part):
                layers, _, part_project = _read_pair(part)
            original_layers, original_metadata, project = _read_pair(main_dir)
            if not backup.exists():
                with tempfile.TemporaryDirectory(prefix=".replica-backup-", dir=main_dir) as work:
                    pending = Path(work) / "backup"
                    pending.mkdir()
                    write_bytes(pending / "layers.json", original_layers)
                    write_bytes(pending / "project.json", original_metadata)
                    pending.rename(backup)
            else:
                _read_pair(backup)
            project["durationInFrames"] = part_project["durationInFrames"]
            metadata = _json_bytes(project, 2)
        for name, payload in zip(_FILES, (layers, metadata), strict=True):
            path = main_dir / name
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise _project_error(f"{path.name} must be a regular file.")
            write_bytes(path, payload)
        if part is None:
            # Rename the intact backup out of the active slot only after both restores complete.
            with tempfile.TemporaryDirectory(prefix=".replica-restore-", dir=main_dir) as work:
                backup.rename(Path(work) / "restored")
        return project["durationInFrames"]


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main", type=Path)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("part", type=Path, nargs="?")
    operation.add_argument("--restore", action="store_true")
    args = parser.parse_args(argv)
    duration = swap(args.main, args.part)
    print("restored" if args.restore else f"loaded {args.part.name}", duration)


if __name__ == "__main__":
    cli(main)
