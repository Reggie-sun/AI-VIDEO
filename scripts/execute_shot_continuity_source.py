#!/usr/bin/env python3
"""Execute one explicit local Shot Continuity source qualification action."""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai_video.errors import AiVideoError  # noqa: E402
from ai_video.production.shot_continuity_source_operator import (  # noqa: E402
    open_source_qualification_operator,
)


DEFAULT_QUALIFICATION_PROFILE = Path(
    "workflows/qualification/minimax_h3_fl2va_rainy_station_source_v1_profile.json"
)
DEFAULT_M0_PROFILE = Path(
    "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=(
            "inspect",
            "preflight",
            "status",
            "submit",
            "poll",
            "fetch",
            "upgrade-manifest",
            "validate",
        ),
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--comfy-root", type=Path, required=True)
    parser.add_argument(
        "--qualification-profile",
        type=Path,
        default=DEFAULT_QUALIFICATION_PROFILE,
    )
    parser.add_argument("--m0-profile", type=Path, default=DEFAULT_M0_PROFILE)
    parser.add_argument("--generation-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--require-new-attempt", action="store_true")
    parser.add_argument("--human-decision", type=Path)
    parser.add_argument("--ffmpeg", type=Path)
    return parser


def execute(
    args: argparse.Namespace,
    *,
    opener: Callable[..., Any] = open_source_qualification_operator,
) -> object:
    if args.require_new_attempt and args.action not in {"preflight", "submit"}:
        raise ValueError("--require-new-attempt is only valid for preflight or submit")
    operator = opener(
        project_root=args.root,
        artifact_root=args.artifact_root,
        comfy_root=args.comfy_root,
        qualification_profile_path=args.qualification_profile,
        m0_profile_path=args.m0_profile,
        generation_id=args.generation_id,
        attempt_id=args.attempt_id,
    )
    if args.action in {"inspect", "status"}:
        return operator.status()
    if args.action == "preflight":
        return operator.preflight(require_new_attempt=args.require_new_attempt)
    if args.action == "submit":
        return operator.submit(require_new_attempt=args.require_new_attempt)
    if args.action == "poll":
        return operator.poll()
    if args.action == "fetch":
        return operator.fetch()
    if args.action == "upgrade-manifest":
        return operator.upgrade_manifest_214()
    if args.action == "validate":
        if args.human_decision is None or args.ffmpeg is None:
            raise ValueError("validate requires --human-decision and --ffmpeg")
        return operator.validate(
            human_decision_path=args.human_decision,
            ffmpeg_path=args.ffmpeg,
        )
    raise AssertionError(f"unhandled action: {args.action}")


def _jsonable(value: object) -> object:
    if isinstance(value, (bytes, bytearray, memoryview)):
        raise ValueError("binary payload is forbidden in source operator output")
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json"))
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return value.value
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError(f"unsupported source operator output type: {type(value).__name__}")


def main() -> int:
    args = _parser().parse_args()
    try:
        result = execute(args)
        rendered = json.dumps(
            _jsonable(result),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    except AiVideoError as exc:
        print(
            json.dumps(
                {
                    "error_code": exc.code.value,
                    "message": exc.user_message,
                    "retryable": exc.retryable,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error_code": "source_operator_invalid",
                    "message": str(exc),
                    "retryable": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
