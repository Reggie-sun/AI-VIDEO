from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import re

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "open-video"
    / "scripts"
    / "validate_director_coverage.py"
)
SKILL_PATH = ROOT / ".agents" / "skills" / "open-video" / "SKILL.md"
SEEDANCE_CAPABILITIES_PATH = (
    ROOT / "src" / "ai_video" / "production" / "seedance_capabilities.py"
)


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "open_video_director_coverage_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seedance_max_duration(model_id: str) -> int:
    tree = ast.parse(
        SEEDANCE_CAPABILITIES_PATH.read_text(encoding="utf-8"),
        filename=str(SEEDANCE_CAPABILITIES_PATH),
    )
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if not (
            isinstance(node.target, ast.Name)
            and node.target.id == "_MODEL_SPECS"
            and isinstance(node.value, ast.Dict)
        ):
            continue
        for key, value in zip(node.value.keys, node.value.values, strict=True):
            if not isinstance(key, ast.Constant) or key.value != model_id:
                continue
            assert isinstance(value, ast.Call)
            for keyword in value.keywords:
                if keyword.arg == "max_duration":
                    assert isinstance(keyword.value, ast.Constant)
                    assert isinstance(keyword.value.value, int)
                    return keyword.value.value
    raise AssertionError(f"missing Seedance capability for {model_id}")


def test_skill_discovery_includes_promptless_duration_only_requests() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    frontmatter = yaml.safe_load(match.group(1))

    assert frontmatter["name"] == "open-video"
    description = frontmatter["description"]
    assert "promptless duration-only request" in description
    assert "ordered Shots" in description
    assert "advisory" in description


def _unit(
    unit_id: str,
    *,
    beat_function: str,
    objective: str,
    open_state: str,
    close_state: str,
    shot_scale: str,
    camera_treatment: str,
    camera_intent: str,
    visible_change: str,
    transition_out: str,
) -> dict[str, object]:
    return {
        "unit_id": unit_id,
        "duration_seconds": 15,
        "beat_function": beat_function,
        "objective": objective,
        "open_state": open_state,
        "close_state": close_state,
        "shot_scale": shot_scale,
        "camera_treatment": camera_treatment,
        "camera_intent": camera_intent,
        "visible_change": visible_change,
        "transition_out": transition_out,
    }


def _payload(*, explicit_single_take_requested: bool = False) -> dict[str, object]:
    return {
        "schema_version": "1",
        "request": {
            "user_creative_brief_supplied": False,
            "user_creative_brief_evidence": None,
            "target_duration_seconds": 30,
            "explicit_single_take_requested": explicit_single_take_requested,
            "single_take_request_evidence": (
                "User explicitly requested one uninterrupted take."
                if explicit_single_take_requested
                else None
            ),
            "director_skill": "open-video",
        },
        "coverage_units": [
            _unit(
                "shot-01",
                beat_function="establish",
                objective="Establish the vessel's danger and scale.",
                open_state="The vessel is trapped below the storm shelf.",
                close_state="Lightning exposes the blocked mountain pass.",
                shot_scale="extreme_wide",
                camera_treatment="tracking",
                camera_intent="Fast lateral tracking reveals the blocked pass.",
                visible_change="The route closes as the storm front descends.",
                transition_out="match_cut",
            ),
            _unit(
                "shot-02",
                beat_function="reveal",
                objective="Reveal the escape decision and destination.",
                open_state="The vessel turns away from the blocked pass.",
                close_state="The vessel clears the clouds toward the citadel.",
                shot_scale="mixed_progression",
                camera_treatment="compound",
                camera_intent="Whip pan into a crane reveal of the destination.",
                visible_change="A risky turn opens the citadel route.",
                transition_out="end",
            ),
        ],
    }


def test_promptless_30s_requires_distinct_director_coverage() -> None:
    validator = _load_validator()

    result = validator.validate_director_coverage(_payload())

    assert result == {
        "status": "passed",
        "schema_version": "1",
        "promptless_request": True,
        "promptless_long_form": True,
        "coverage_unit_count": 2,
        "planned_duration_seconds": 30.0,
        "explicit_single_take_requested": False,
    }


@pytest.mark.parametrize("transition", ["VIDEO_EXTEND", "no cut", "uninterrupted"])
def test_promptless_30s_rejects_continuous_treatment_as_coverage(
    transition: str,
) -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][0]["transition_out"] = transition

    with pytest.raises(validator.CoverageValidationError, match="VIDEO_EXTEND"):
        validator.validate_director_coverage(payload)


def test_seedance_2_5_native_30s_does_not_waive_director_coverage() -> None:
    validator = _load_validator()

    assert _seedance_max_duration("doubao-seedance-2-5-260628") == 30
    payload = _payload()

    result = validator.validate_director_coverage(payload)

    assert result["promptless_request"] is True
    assert result["promptless_long_form"] is True

    payload["coverage_units"][0]["transition_out"] = "VIDEO_EXTEND"
    with pytest.raises(validator.CoverageValidationError, match="VIDEO_EXTEND"):
        validator.validate_director_coverage(payload)


def test_short_promptless_request_still_requires_open_video() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["target_duration_seconds"] = 15
    payload["coverage_units"] = [payload["coverage_units"][0]]
    payload["request"]["director_skill"] = "seedance-authoring"

    with pytest.raises(validator.CoverageValidationError, match="PROMPTLESS_REQUEST"):
        validator.validate_director_coverage(payload)


def test_explicit_user_single_take_keeps_evolving_internal_coverage() -> None:
    validator = _load_validator()
    payload = _payload(explicit_single_take_requested=True)
    payload["coverage_units"][0]["transition_out"] = "VIDEO_EXTEND"

    result = validator.validate_director_coverage(payload)

    assert result["status"] == "passed"
    assert result["explicit_single_take_requested"] is True


def test_single_take_flag_requires_direct_user_request_evidence() -> None:
    validator = _load_validator()
    payload = _payload(explicit_single_take_requested=True)
    payload["request"]["single_take_request_evidence"] = None

    with pytest.raises(
        validator.CoverageValidationError, match="single_take_request_evidence"
    ):
        validator.validate_director_coverage(payload)


def test_coverage_duration_must_match_target() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][0]["duration_seconds"] = 14

    with pytest.raises(
        validator.CoverageValidationError, match="coverage duration must match"
    ):
        validator.validate_director_coverage(payload)


def test_punctuation_does_not_fake_a_distinct_objective() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][1]["objective"] = (
        payload["coverage_units"][0]["objective"] + "!"
    )

    with pytest.raises(validator.CoverageValidationError, match="objective"):
        validator.validate_director_coverage(payload)


def test_repeated_slow_camera_treatment_does_not_fake_coverage() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][1]["camera_treatment"] = "tracking"

    with pytest.raises(validator.CoverageValidationError, match="camera_treatment"):
        validator.validate_director_coverage(payload)


def test_unknown_camera_treatment_fails_closed() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][0]["camera_treatment"] = "slow tracking maybe"

    with pytest.raises(validator.CoverageValidationError, match="camera_treatment"):
        validator.validate_director_coverage(payload)


def test_long_film_can_reuse_non_adjacent_coverage_categories() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["target_duration_seconds"] = 120
    payload["coverage_units"] = [
        _unit(
            f"shot-{index + 1:02d}",
            beat_function=("establish" if index % 2 == 0 else "reveal"),
            objective=f"Advance story objective {index + 1}.",
            open_state=f"Story state {index}.",
            close_state=f"Story state {index + 1}.",
            shot_scale=("wide" if index % 2 == 0 else "close_up"),
            camera_treatment=("tracking" if index % 2 == 0 else "push_in"),
            camera_intent=f"Camera treatment for unit {index + 1}.",
            visible_change=f"Visible story change {index + 1} occurs.",
            transition_out=("end" if index == 7 else "cut"),
        )
        for index in range(8)
    ]

    result = validator.validate_director_coverage(payload)

    assert result["coverage_unit_count"] == 8
    assert result["planned_duration_seconds"] == 120.0


def test_transition_end_is_reserved_for_the_final_coverage_unit() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][0]["transition_out"] = "end"

    with pytest.raises(validator.CoverageValidationError, match="only the final"):
        validator.validate_director_coverage(payload)

    payload = _payload()
    payload["coverage_units"][-1]["transition_out"] = "cut"
    with pytest.raises(validator.CoverageValidationError, match="final coverage unit"):
        validator.validate_director_coverage(payload)


def test_explicit_single_take_rejects_a_cut_between_units() -> None:
    validator = _load_validator()
    payload = _payload(explicit_single_take_requested=True)

    with pytest.raises(
        validator.CoverageValidationError, match="continuous non-final transitions"
    ):
        validator.validate_director_coverage(payload)
