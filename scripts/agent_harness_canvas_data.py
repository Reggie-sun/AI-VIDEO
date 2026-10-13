"""Validate changed Canvas project inputs without running Production lifecycle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from ai_video.errors import AiVideoError
from scripts.canvas_production import run as canvas_run
from scripts.harness_pytest_guard import install_network_guard


def check_paths(repository: Path, paths: list[str]) -> dict:
    repository = repository.resolve(strict=True)
    data_root = repository / "docs/canvas-projects"
    projects: set[Path] = set()
    for value in paths:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("changed path must be repository-relative without traversal")
        path = repository / relative
        if not path.is_relative_to(data_root) or path.suffix.lower() == ".md":
            continue
        for component in (path, *path.parents):
            if component == repository:
                break
            if component.is_symlink():
                raise ValueError("Canvas input path contains a symlink")
        parent = path.parent
        while parent.is_relative_to(data_root):
            definition = parent / "project.json"
            if definition.exists():
                projects.add(definition)
                break
            if parent == data_root:
                # A complete deletion has no inputs left to validate.
                remaining = path.parent.rglob("*") if path.parent.exists() else ()
                if any(p.is_file() and p.suffix.lower() != ".md" for p in remaining):
                    raise ValueError("Canvas inputs remain without project.json")
                break
            parent = parent.parent
    checked = []
    for definition in sorted(projects):
        with tempfile.TemporaryDirectory(prefix="canvas-data-check-") as temporary:
            production = Path(temporary)
            canvas_run(data_path=definition, project_root=production, action="author")
            if any(production.iterdir()):
                raise ValueError("read-only Canvas authoring wrote Production state")
        checked.append(definition.relative_to(repository).as_posix())
    return {"checked_projects": checked, "production_acceptance": "NOT_EVALUATED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", action="append", required=True)
    args = parser.parse_args(argv)
    install_network_guard()
    try:
        result = check_paths(Path.cwd(), args.paths)
    except (AiVideoError, ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__,
                          "production_acceptance": "NOT_EVALUATED"}))
        return 1
    print(json.dumps({"status": "passed", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
