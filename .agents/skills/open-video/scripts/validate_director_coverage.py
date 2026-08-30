#!/usr/bin/env python3
"""Validate Agent-side Director coverage without touching Product Runtime state."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "1"
PROMPTLESS_LONG_FORM_THRESHOLD_SECONDS = 15.0
REQUEST_FIELDS = {
    "user_creative_brief_supplied",
    "user_creative_brief_evidence",
    "target_duration_seconds",
    "explicit_single_take_requested",
    "single_take_request_evidence",
    "director_skill",
}
COVERAGE_FIELDS = {
    "unit_id",
    "duration_seconds",
    "beat_function",
    "objective",
    "open_state",
    "close_state",
    "shot_scale",
    "camera_treatment",
    "camera_intent",
    "visible_change",
    "transition_out",
}
CONTINUOUS_ONLY_TRANSITIONS = {
    "continuous",
    "no_cut",
    "uninterrupted",
    "video_extend",
}
BEAT_FUNCTIONS = {
    "decision",
    "detail",
    "escalate",
    "establish",
    "payoff",
    "reaction",
    "reveal",
    "reversal",
    "transition",
}
SHOT_SCALES = {
    "close_up",
    "extreme_close_up",
    "extreme_wide",
    "full",
    "medium",
    "mixed_progression",
    "wide",
}
CAMERA_TREATMENTS = {
    "arc",
    "compound",
    "crane",
    "handheld",
    "pan",
    "pov",
    "pull_out",
    "push_in",
    "static",
    "tilt",
    "tracking",
    "truck",
}
TRANSITIONS = {
    "continuous",
    "cut",
    "dissolve",
    "end",
    "match_cut",
    "motivated_cut",
    "no_cut",
    "occlusion_cut",
    "uninterrupted",
    "video_extend",
    "wipe",
}


class CoverageValidationError(ValueError):
    """Raised when promptless long-form coverage is incomplete or misleading."""


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CoverageValidationError(f"{label} must be an object")
    return value


def _exact_fields(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        raise CoverageValidationError(
            f"{label} fields mismatch: missing={missing}, unknown={unknown}"
        )


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageValidationError(f"{label} must be a non-empty string")
    return value.strip()


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CoverageValidationError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise CoverageValidationError(f"{label} must be finite and greater than zero")
    return number


def _boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise CoverageValidationError(f"{label} must be a boolean")
    return value


def _normalized(value: str) -> str:
    return re.sub(r"[^\w]+", "_", value.casefold(), flags=re.UNICODE).strip("_")


def _enum(value: Any, allowed: set[str], label: str) -> str:
    normalized = _normalized(_text(value, label))
    if normalized not in allowed:
        raise CoverageValidationError(
            f"{label} must be one of {sorted(allowed)}"
        )
    return normalized


def validate_director_coverage(payload: Mapping[str, Any]) -> dict[str, Any]:
    _exact_fields(payload, {"schema_version", "request", "coverage_units"}, "root")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise CoverageValidationError(
            f"schema_version must be {SCHEMA_VERSION!r}"
        )

    request = _mapping(payload["request"], "request")
    _exact_fields(request, REQUEST_FIELDS, "request")
    user_brief_supplied = _boolean(
        request["user_creative_brief_supplied"],
        "request.user_creative_brief_supplied",
    )
    user_brief_evidence = request["user_creative_brief_evidence"]
    if user_brief_supplied:
        _text(
            user_brief_evidence,
            "request.user_creative_brief_evidence",
        )
    elif user_brief_evidence is not None:
        raise CoverageValidationError(
            "request.user_creative_brief_evidence must be null when the user did "
            "not supply a creative brief"
        )
    target_duration = _number(
        request["target_duration_seconds"], "request.target_duration_seconds"
    )
    explicit_single_take = _boolean(
        request["explicit_single_take_requested"],
        "request.explicit_single_take_requested",
    )
    single_take_evidence = request["single_take_request_evidence"]
    if explicit_single_take:
        _text(
            single_take_evidence,
            "request.single_take_request_evidence",
        )
    elif single_take_evidence is not None:
        raise CoverageValidationError(
            "request.single_take_request_evidence must be null when single-take "
            "was not explicitly requested"
        )
    director_skill = _text(request["director_skill"], "request.director_skill")

    raw_units = payload["coverage_units"]
    if not isinstance(raw_units, Sequence) or isinstance(raw_units, (str, bytes)):
        raise CoverageValidationError("coverage_units must be an array")
    if not raw_units:
        raise CoverageValidationError("coverage_units must not be empty")

    units: list[dict[str, Any]] = []
    for index, raw_unit in enumerate(raw_units):
        unit = _mapping(raw_unit, f"coverage_units[{index}]")
        _exact_fields(unit, COVERAGE_FIELDS, f"coverage_units[{index}]")
        parsed = {
            field: _text(unit[field], f"coverage_units[{index}].{field}")
            for field in COVERAGE_FIELDS - {"duration_seconds"}
        }
        for field, allowed in (
            ("beat_function", BEAT_FUNCTIONS),
            ("shot_scale", SHOT_SCALES),
            ("camera_treatment", CAMERA_TREATMENTS),
            ("transition_out", TRANSITIONS),
        ):
            parsed[field] = _enum(
                unit[field], allowed, f"coverage_units[{index}].{field}"
            )
        parsed["duration_seconds"] = _number(
            unit["duration_seconds"], f"coverage_units[{index}].duration_seconds"
        )
        units.append(parsed)

    unit_ids = [_normalized(unit["unit_id"]) for unit in units]
    if len(unit_ids) != len(set(unit_ids)):
        raise CoverageValidationError("coverage unit IDs must be unique")

    planned_duration = sum(unit["duration_seconds"] for unit in units)
    if not math.isclose(planned_duration, target_duration, abs_tol=0.05):
        raise CoverageValidationError(
            "coverage duration must match target_duration_seconds within 0.05s"
        )

    promptless_request = not user_brief_supplied
    if promptless_request and director_skill != "open-video":
        raise CoverageValidationError(
            "PROMPTLESS_REQUEST requires director_skill='open-video'"
        )
    promptless_long_form = (
        promptless_request
        and target_duration > PROMPTLESS_LONG_FORM_THRESHOLD_SECONDS
    )
    if promptless_long_form:
        if len(units) < 2:
            raise CoverageValidationError(
                "PROMPTLESS_LONG_FORM requires at least two ordered coverage units"
            )

        for field in ("objective", "visible_change"):
            normalized = [_normalized(unit[field]) for unit in units]
            if len(normalized) != len(set(normalized)):
                raise CoverageValidationError(
                    f"PROMPTLESS_LONG_FORM requires distinct {field} values"
                )
        for field in ("beat_function", "shot_scale", "camera_treatment"):
            normalized = [_normalized(unit[field]) for unit in units]
            if any(left == right for left, right in zip(normalized, normalized[1:])):
                raise CoverageValidationError(
                    f"PROMPTLESS_LONG_FORM requires adjacent {field} values to differ"
                )

        nonfinal_transitions = [
            _normalized(unit["transition_out"]) for unit in units[:-1]
        ]
        if explicit_single_take and not all(
            transition in CONTINUOUS_ONLY_TRANSITIONS
            for transition in nonfinal_transitions
        ):
            raise CoverageValidationError(
                "explicit single-take coverage requires continuous non-final transitions"
            )
        if not explicit_single_take and set(nonfinal_transitions).intersection(
            CONTINUOUS_ONLY_TRANSITIONS
        ):
            raise CoverageValidationError(
                "VIDEO_EXTEND/no-cut continuity cannot replace Director coverage unless "
                "the user explicitly requested a single take"
            )
    if units[-1]["transition_out"] != "end":
        raise CoverageValidationError("the final coverage unit transition_out must be 'end'")
    if any(unit["transition_out"] == "end" for unit in units[:-1]):
        raise CoverageValidationError(
            "only the final coverage unit may use transition_out='end'"
        )

    return {
        "status": "passed",
        "schema_version": SCHEMA_VERSION,
        "promptless_request": promptless_request,
        "promptless_long_form": promptless_long_form,
        "coverage_unit_count": len(units),
        "planned_duration_seconds": planned_duration,
        "explicit_single_take_requested": explicit_single_take,
    }


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
