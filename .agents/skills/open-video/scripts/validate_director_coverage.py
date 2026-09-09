#!/usr/bin/env python3
"""Validate Agent-side Director coverage without touching Product Runtime state."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


LEGACY_SCHEMA_VERSION = "3"
SCHEMA_VERSION = "4"
LEGACY_ROOT_FIELDS = {"schema_version", "request", "coverage_units"}
V4_ROOT_FIELDS = LEGACY_ROOT_FIELDS | {"intent_items", "intent_groups"}
REQUEST_FIELDS = {
    "creative_input_kind",
    "creative_input_evidence",
    "creative_constraints",
    "target_duration_seconds",
    "coverage_strategy",
    "strategy_source",
    "director_decision_rationale",
    "strategy_request_evidence",
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
    "constraint_ids",
}
CREATIVE_CONSTRAINT_FIELDS = {"constraint_id", "scope", "source_text"}
CONTINUOUS_ONLY_TRANSITIONS = {
    "continuous",
    "no_cut",
    "uninterrupted",
    "video_extend",
}
COVERAGE_STRATEGIES = {"multi_shot", "single_take"}
STRATEGY_SOURCES = {"agent_directed", "user_requested"}
CREATIVE_INPUT_KINDS = {"direction", "draft_prompt", "missing"}
CONSTRAINT_SCOPES = {"beat_specific", "global"}
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
INTENT_GROUPS = {
    "must_happen",
    "must_not_happen",
    "preferred_performance",
    "timing_targets",
    "acceptable_variation",
}
INTENT_ITEM_FIELDS = {
    "intent_item_id",
    "statement",
    "source_refs",
    "origin",
    "related_intent_ids",
}
INTENT_SOURCE_REQUIRED_FIELDS = {
    "source_hash",
    "locator",
    "intent_item_id",
    "quote",
    "origin",
}
INTENT_ORIGINS = {"explicit_user", "director_choice", "repair_margin"}
TIMING_TARGET_KINDS = {"delivery_constraint", "generation_margin"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CoverageValidationError(ValueError):
    """Raised when Director coverage evidence is incomplete or inconsistent."""


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


def _normalized(value: str) -> str:
    return re.sub(r"[^\w]+", "_", value.casefold(), flags=re.UNICODE).strip("_")


def _enum(value: Any, allowed: set[str], label: str) -> str:
    normalized = _normalized(_text(value, label))
    if normalized not in allowed:
        raise CoverageValidationError(
            f"{label} must be one of {sorted(allowed)}"
        )
    return normalized


def _normalized_text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CoverageValidationError(f"{label} must be an array")
    normalized = [
        _normalized(_text(item, f"{label}[{index}]"))
        for index, item in enumerate(value)
    ]
    if len(normalized) != len(set(normalized)):
        raise CoverageValidationError(f"{label} must not contain duplicates")
    return normalized


def _array(value: Any, label: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CoverageValidationError(f"{label} must be an array")
    return value


def _validate_v4_intent_handoff(
    payload: Mapping[str, Any], *, creative_input_text: str | None
) -> dict[str, int]:
    raw_items = _array(payload["intent_items"], "intent_items")

    items: dict[str, dict[str, Any]] = {}
    for index, raw_item in enumerate(raw_items):
        label = f"intent_items[{index}]"
        item = _mapping(raw_item, label)
        _exact_fields(item, INTENT_ITEM_FIELDS, label)
        intent_item_id = _text(item["intent_item_id"], f"{label}.intent_item_id")
        if intent_item_id in items:
            raise CoverageValidationError("intent_item_id values must be unique")
        _text(item["statement"], f"{label}.statement")
        origin = _enum(item["origin"], INTENT_ORIGINS, f"{label}.origin")
        source_refs = _array(item["source_refs"], f"{label}.source_refs")
        if not source_refs:
            raise CoverageValidationError(f"{label}.source_refs must not be empty")
        for source_index, raw_source in enumerate(source_refs):
            source_label = f"{label}.source_refs[{source_index}]"
            source = _mapping(raw_source, source_label)
            missing = sorted(INTENT_SOURCE_REQUIRED_FIELDS - set(source))
            unknown = sorted(
                set(source) - INTENT_SOURCE_REQUIRED_FIELDS - {"fixed"}
            )
            if missing or unknown:
                raise CoverageValidationError(
                    f"{source_label} fields mismatch: missing={missing}, unknown={unknown}"
                )
            _text(source["source_hash"], f"{source_label}.source_hash")
            source_hash = source["source_hash"]
            if SHA256.fullmatch(source_hash) is None:
                raise CoverageValidationError(
                    f"{source_label}.source_hash must be a lowercase SHA-256 hash"
                )
            _text(source["locator"], f"{source_label}.locator")
            _text(source["intent_item_id"], f"{source_label}.intent_item_id")
            _text(source["quote"], f"{source_label}.quote")
            quote = source["quote"]
            source_origin = _enum(
                source["origin"], INTENT_ORIGINS, f"{source_label}.origin"
            )
            if source_origin != origin:
                raise CoverageValidationError(
                    f"{source_label}.origin must match {label}.origin"
                )
            if "fixed" in source and not isinstance(source["fixed"], bool):
                raise CoverageValidationError(f"{source_label}.fixed must be boolean")
            if source_origin == "explicit_user":
                if creative_input_text is None or quote not in creative_input_text:
                    raise CoverageValidationError(
                        f"{source_label}.quote must be a verbatim substring of "
                        "request.creative_input_evidence"
                    )
                if source_hash != hashlib.sha256(
                    creative_input_text.encode("utf-8")
                ).hexdigest():
                    raise CoverageValidationError(
                        f"{source_label}.source_hash must bind the exact "
                        "creative_input_evidence"
                    )
        related_ids = _array(item["related_intent_ids"], f"{label}.related_intent_ids")
        parsed_related = [
            _text(related_id, f"{label}.related_intent_ids[{related_index}]")
            for related_index, related_id in enumerate(related_ids)
        ]
        if intent_item_id in parsed_related or len(parsed_related) != len(set(parsed_related)):
            raise CoverageValidationError(
                f"{label}.related_intent_ids must not contain self-references or duplicates"
            )
        items[intent_item_id] = {"origin": origin, "related_ids": parsed_related,
                                 "fixed": any(source.get("fixed", False) for source in source_refs)}

    groups = _mapping(payload["intent_groups"], "intent_groups")
    _exact_fields(groups, INTENT_GROUPS, "intent_groups")
    membership: dict[str, set[str]] = {intent_item_id: set() for intent_item_id in items}
    counts: dict[str, int] = {}
    for group_name in sorted(INTENT_GROUPS):
        raw_members = _array(groups[group_name], f"intent_groups.{group_name}")
        member_ids: list[str] = []
        for member_index, raw_member in enumerate(raw_members):
            member_label = f"intent_groups.{group_name}[{member_index}]"
            member = _mapping(raw_member, member_label)
            expected_fields = {"intent_item_id"}
            if group_name == "timing_targets":
                expected_fields.add("target_kind")
            _exact_fields(member, expected_fields, member_label)
            intent_item_id = _text(member["intent_item_id"], f"{member_label}.intent_item_id")
            if intent_item_id not in items:
                raise CoverageValidationError(
                    f"{member_label} contains unknown intent IDs: {[intent_item_id]}"
                )
            if group_name == "timing_targets":
                target_kind = _enum(
                    member["target_kind"], TIMING_TARGET_KINDS,
                    f"{member_label}.target_kind",
                )
                if items[intent_item_id]["fixed"] and target_kind != "delivery_constraint":
                    raise CoverageValidationError("fixed intent must remain a delivery constraint")
                if items[intent_item_id]["origin"] == "repair_margin" and target_kind != "generation_margin":
                    raise CoverageValidationError("repair margin cannot become a delivery constraint")
                if target_kind == "generation_margin":
                    related_ids = items[intent_item_id]["related_ids"]
                    if (
                        items[intent_item_id]["origin"] != "repair_margin"
                        or not related_ids
                        or not any(
                            items[related_id]["origin"] != "repair_margin"
                            for related_id in related_ids
                            if related_id in items
                        )
                    ):
                        raise CoverageValidationError(
                            f"{member_label}.generation_margin must bind an "
                            "original non-margin intent target"
                        )
            member_ids.append(intent_item_id)
            membership[intent_item_id].add(group_name)
        if len(member_ids) != len(set(member_ids)):
            raise CoverageValidationError(
                f"intent_groups.{group_name} must not contain duplicates"
            )
        counts[group_name] = len(member_ids)

    for intent_item_id, item in items.items():
        if item["fixed"] and membership[intent_item_id] & {"preferred_performance", "acceptable_variation"}:
            raise CoverageValidationError("fixed intent cannot be weakened from a constraint to advisory")
        unknown_related = set(item["related_ids"]) - set(items)
        if unknown_related:
            raise CoverageValidationError(
                f"intent_item_id={intent_item_id!r} contains unknown related intent IDs: "
                f"{sorted(unknown_related)}"
            )
        if not membership[intent_item_id]:
            raise CoverageValidationError(
                f"intent_item_id={intent_item_id!r} is not bound to an intent group"
            )
        if (
            "acceptable_variation" in membership[intent_item_id]
            and not item["related_ids"]
        ):
            raise CoverageValidationError(
                f"intent_item_id={intent_item_id!r} acceptable_variation needs a related target"
            )
        if len(membership[intent_item_id]) > 1 and membership[intent_item_id] != {
            "preferred_performance",
            "timing_targets",
        }:
            raise CoverageValidationError(
                f"intent_item_id={intent_item_id!r} must be split into independent atoms"
            )
    return counts


def validate_director_coverage(payload: Mapping[str, Any]) -> dict[str, Any]:
    schema_version = payload.get("schema_version")
    if schema_version == LEGACY_SCHEMA_VERSION:
        _exact_fields(payload, LEGACY_ROOT_FIELDS, "root")
    elif schema_version == SCHEMA_VERSION:
        _exact_fields(payload, V4_ROOT_FIELDS, "root")
    else:
        raise CoverageValidationError(
            f"schema_version must be {LEGACY_SCHEMA_VERSION!r} or {SCHEMA_VERSION!r}"
        )

    request = _mapping(payload["request"], "request")
    _exact_fields(request, REQUEST_FIELDS, "request")
    creative_input_kind = _enum(
        request["creative_input_kind"],
        CREATIVE_INPUT_KINDS,
        "request.creative_input_kind",
    )
    creative_input_evidence = request["creative_input_evidence"]
    raw_constraints = request["creative_constraints"]
    if not isinstance(raw_constraints, Sequence) or isinstance(
        raw_constraints, (str, bytes)
    ):
        raise CoverageValidationError("request.creative_constraints must be an array")
    if creative_input_kind == "missing":
        creative_input_text = None
        if creative_input_evidence is not None:
            raise CoverageValidationError(
                "request.creative_input_evidence must be null when "
                "creative_input_kind is 'missing'"
            )
        if raw_constraints:
            raise CoverageValidationError(
                "request.creative_constraints must be empty when "
                "creative_input_kind is 'missing'"
            )
    else:
        creative_input_text = _text(
            creative_input_evidence,
            "request.creative_input_evidence",
        )
        if not raw_constraints:
            raise CoverageValidationError(
                "request.creative_constraints must not be empty for supplied raw input"
            )

    constraints: list[dict[str, str]] = []
    for index, raw_constraint in enumerate(raw_constraints):
        constraint = _mapping(
            raw_constraint, f"request.creative_constraints[{index}]"
        )
        _exact_fields(
            constraint,
            CREATIVE_CONSTRAINT_FIELDS,
            f"request.creative_constraints[{index}]",
        )
        source_text = _text(
            constraint["source_text"],
            f"request.creative_constraints[{index}].source_text",
        )
        if creative_input_text is None or source_text not in creative_input_text:
            raise CoverageValidationError(
                f"request.creative_constraints[{index}].source_text must be an "
                "exact substring of request.creative_input_evidence"
            )
        constraints.append(
            {
                "constraint_id": _normalized(
                    _text(
                        constraint["constraint_id"],
                        f"request.creative_constraints[{index}].constraint_id",
                    )
                ),
                "scope": _enum(
                    constraint["scope"],
                    CONSTRAINT_SCOPES,
                    f"request.creative_constraints[{index}].scope",
                ),
                "source_text": source_text,
            }
        )
    constraint_ids = [constraint["constraint_id"] for constraint in constraints]
    if len(constraint_ids) != len(set(constraint_ids)):
        raise CoverageValidationError("creative constraint IDs must be unique")
    target_duration = _number(
        request["target_duration_seconds"], "request.target_duration_seconds"
    )
    coverage_strategy = _enum(
        request["coverage_strategy"],
        COVERAGE_STRATEGIES,
        "request.coverage_strategy",
    )
    strategy_source = _enum(
        request["strategy_source"],
        STRATEGY_SOURCES,
        "request.strategy_source",
    )
    _text(
        request["director_decision_rationale"],
        "request.director_decision_rationale",
    )
    strategy_request_evidence = request["strategy_request_evidence"]
    if strategy_source == "user_requested":
        _text(
            strategy_request_evidence,
            "request.strategy_request_evidence",
        )
    elif strategy_request_evidence is not None:
        raise CoverageValidationError(
            "request.strategy_request_evidence must be null when strategy_source "
            "is 'agent_directed'"
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
            for field in COVERAGE_FIELDS - {"constraint_ids", "duration_seconds"}
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
        parsed["constraint_ids"] = _normalized_text_list(
            unit["constraint_ids"], f"coverage_units[{index}].constraint_ids"
        )
        units.append(parsed)

    unit_ids = [_normalized(unit["unit_id"]) for unit in units]
    if len(unit_ids) != len(set(unit_ids)):
        raise CoverageValidationError("coverage unit IDs must be unique")

    known_constraint_ids = set(constraint_ids)
    global_constraint_ids = {
        constraint["constraint_id"]
        for constraint in constraints
        if constraint["scope"] == "global"
    }
    beat_specific_constraint_ids = known_constraint_ids - global_constraint_ids
    covered_constraint_ids: set[str] = set()
    for index, unit in enumerate(units):
        unit_constraint_ids = set(unit["constraint_ids"])
        unknown_constraint_ids = unit_constraint_ids - known_constraint_ids
        if unknown_constraint_ids:
            raise CoverageValidationError(
                f"coverage_units[{index}].constraint_ids contains unknown IDs: "
                f"{sorted(unknown_constraint_ids)}"
            )
        missing_global_ids = global_constraint_ids - unit_constraint_ids
        if missing_global_ids:
            raise CoverageValidationError(
                f"coverage_units[{index}].constraint_ids omits global constraints: "
                f"{sorted(missing_global_ids)}"
            )
        covered_constraint_ids.update(unit_constraint_ids)
    uncovered_beat_specific_ids = beat_specific_constraint_ids - covered_constraint_ids
    if uncovered_beat_specific_ids:
        raise CoverageValidationError(
            "beat-specific creative constraints must bind to at least one coverage unit: "
            f"{sorted(uncovered_beat_specific_ids)}"
        )

    planned_duration = sum(unit["duration_seconds"] for unit in units)
    if not math.isclose(planned_duration, target_duration, abs_tol=0.05):
        raise CoverageValidationError(
            "coverage duration must match target_duration_seconds within 0.05s"
        )

    if director_skill != "open-video":
        raise CoverageValidationError(
            "DIRECTOR_PREFLIGHT_REQUEST requires director_skill='open-video'"
        )
    if coverage_strategy == "multi_shot" and len(units) < 2:
        raise CoverageValidationError(
            "coverage_strategy='multi_shot' requires at least two ordered coverage units"
        )

    if len(units) > 1:
        for field in ("objective", "visible_change"):
            normalized = [_normalized(unit[field]) for unit in units]
            if len(normalized) != len(set(normalized)):
                raise CoverageValidationError(
                    f"multiple coverage units require distinct {field} values"
                )
        if coverage_strategy == "multi_shot":
            for field in ("beat_function", "shot_scale", "camera_treatment"):
                normalized = [_normalized(unit[field]) for unit in units]
                if any(
                    left == right for left, right in zip(normalized, normalized[1:])
                ):
                    raise CoverageValidationError(
                        f"adjacent multi-shot units require different {field} values"
                    )

        nonfinal_transitions = [
            _normalized(unit["transition_out"]) for unit in units[:-1]
        ]
        if coverage_strategy == "single_take" and not all(
            transition in CONTINUOUS_ONLY_TRANSITIONS
            for transition in nonfinal_transitions
        ):
            raise CoverageValidationError(
                "coverage_strategy='single_take' requires continuous non-final transitions"
            )
        if coverage_strategy == "multi_shot" and set(nonfinal_transitions).intersection(
            CONTINUOUS_ONLY_TRANSITIONS
        ):
            raise CoverageValidationError(
                "coverage_strategy='multi_shot' cannot use VIDEO_EXTEND/no-cut "
                "as a non-final transition"
            )
    if units[-1]["transition_out"] != "end":
        raise CoverageValidationError("the final coverage unit transition_out must be 'end'")
    if any(unit["transition_out"] == "end" for unit in units[:-1]):
        raise CoverageValidationError(
            "only the final coverage unit may use transition_out='end'"
        )

    intent_group_counts = (
        _validate_v4_intent_handoff(
            payload, creative_input_text=request["creative_input_evidence"] if creative_input_text is not None else None
        )
        if schema_version == SCHEMA_VERSION
        else None
    )

    result = {
        "status": "passed",
        "schema_version": schema_version,
        "director_preflight_request": True,
        "creative_input_kind": creative_input_kind,
        "coverage_strategy": coverage_strategy,
        "strategy_source": strategy_source,
        "coverage_unit_count": len(units),
        "planned_duration_seconds": planned_duration,
    }
    if intent_group_counts is not None:
        result.update(
            intent_group_counts=intent_group_counts,
            qa_admission_required=True,
            director_intent_is_not_acceptance=True,
        )
    return result


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
