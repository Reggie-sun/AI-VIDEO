#!/usr/bin/env python3
"""Validate Agent-side Director coverage without touching Product Runtime state.

Structure validation lives once in ``ai_video.production.director_coverage``;
this entry only adds the Agent-side requirement that open-video authored it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

try:
    from ai_video.production import director_coverage as _core
except ModuleNotFoundError:  # direct script use outside the project environment
    import importlib.util

    _path = Path(__file__).resolve().parents[4] / "src/ai_video/production/director_coverage.py"
    _spec = importlib.util.spec_from_file_location("director_coverage_core", _path)
    _core = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_core)

for _name in dir(_core):
    if not _name.startswith("__") and _name != "validate_director_coverage":
        globals()[_name] = getattr(_core, _name)
CoverageValidationError = _core.CoverageValidationError


def _require_open_video(author: str) -> None:
    if author != "open-video":
        raise CoverageValidationError(
            "DIRECTOR_PREFLIGHT_REQUEST requires director_skill='open-video'"
        )


def validate_director_coverage(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _core.validate_director_coverage(payload, author_check=_require_open_video)


def _load_payload(source: str) -> Mapping[str, Any]:
    text = (
        sys.stdin.read()
        if source == "-"
        else Path(source).read_text(encoding="utf-8")
    )
    try:
        return _mapping(json.loads(text), "root")
    except json.JSONDecodeError as error:
        raise CoverageValidationError(f"invalid JSON: {error.msg}") from error


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Coverage JSON path, or '-' to read stdin")
    args = parser.parse_args(argv)
    try:
        result = validate_director_coverage(_load_payload(args.source))
    except (CoverageValidationError, OSError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
