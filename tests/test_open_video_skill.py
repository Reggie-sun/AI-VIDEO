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


def test_skill_discovery_includes_all_raw_creative_inputs() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match is not None
    frontmatter = yaml.safe_load(match.group(1))

    assert frontmatter["name"] == "open-video"
    description = frontmatter["description"]
    assert "raw creative input" in description
    assert "draft prompt" in description
    assert "approved Shots" in description
    assert "ordered coverage" in description
    assert "advisory" in description


def _unit(
    unit_id: str,
    *,
    duration_seconds: float = 15,
    constraint_ids: list[str] | None = None,
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
        "duration_seconds": duration_seconds,
        "beat_function": beat_function,
        "objective": objective,
        "open_state": open_state,
        "close_state": close_state,
        "shot_scale": shot_scale,
        "camera_treatment": camera_treatment,
        "camera_intent": camera_intent,
        "visible_change": visible_change,
        "transition_out": transition_out,
        "constraint_ids": [] if constraint_ids is None else constraint_ids,
    }


def _payload(
    *,
    creative_input_kind: str = "missing",
    coverage_strategy: str = "multi_shot",
    strategy_source: str = "agent_directed",
    target_duration_seconds: float = 30,
) -> dict[str, object]:
    unit_duration = target_duration_seconds / 2
    supplied_input = creative_input_kind != "missing"
    constraint_ids = (
        ["constraint-product", "constraint-surface", "constraint-people"]
        if supplied_input
        else []
    )
    return {
        "schema_version": "3",
        "request": {
            "creative_input_kind": creative_input_kind,
            "creative_input_evidence": (
                None
                if not supplied_input
                else "Show a red product alone on a dark table; no people."
            ),
            "creative_constraints": (
                []
                if not supplied_input
                else [
                    {
                        "constraint_id": "constraint-product",
                        "scope": "global",
                        "source_text": "red product",
                    },
                    {
                        "constraint_id": "constraint-surface",
                        "scope": "global",
                        "source_text": "dark table",
                    },
                    {
                        "constraint_id": "constraint-people",
                        "scope": "global",
                        "source_text": "no people",
                    },
                ]
            ),
            "target_duration_seconds": target_duration_seconds,
            "coverage_strategy": coverage_strategy,
            "strategy_source": strategy_source,
            "director_decision_rationale": (
                "The ordered beats need a viewpoint reset."
                if coverage_strategy == "multi_shot"
                else "One continuous camera trajectory can carry both evolving beats."
            ),
            "strategy_request_evidence": (
                "User explicitly requested this coverage strategy."
                if strategy_source == "user_requested"
                else None
            ),
            "director_skill": "open-video",
        },
        "coverage_units": [
            _unit(
                "shot-01",
                duration_seconds=unit_duration,
                constraint_ids=constraint_ids,
                beat_function="establish",
                objective=(
                    "Establish the red product alone on the dark table."
                    if supplied_input
                    else "Establish the vessel's danger and scale."
                ),
                open_state=(
                    "The red product rests alone on the dark table; no people appear."
                    if supplied_input
                    else "The vessel is trapped below the storm shelf."
                ),
                close_state=(
                    "A narrow rim light defines the red product against the empty set."
                    if supplied_input
                    else "Lightning exposes the blocked mountain pass."
                ),
                shot_scale="extreme_wide",
                camera_treatment="tracking",
                camera_intent=(
                    "Track laterally across the dark table while keeping the product alone."
                    if supplied_input
                    else "Fast lateral tracking reveals the blocked pass."
                ),
                visible_change=(
                    "The red surface moves from silhouette into a clean rim-lit profile."
                    if supplied_input
                    else "The route closes as the storm front descends."
                ),
                transition_out=(
                    "video_extend"
                    if coverage_strategy == "single_take"
                    else "match_cut"
                ),
            ),
            _unit(
                "shot-02",
                duration_seconds=unit_duration,
                constraint_ids=constraint_ids,
                beat_function="reveal",
                objective=(
                    "Reveal the red product's material detail without introducing people."
                    if supplied_input
                    else "Reveal the escape decision and destination."
                ),
                open_state=(
                    "The red product remains alone in profile on the dark table."
                    if supplied_input
                    else "The vessel turns away from the blocked pass."
                ),
                close_state=(
                    "The camera resolves on its embossed detail in the same empty setup."
                    if supplied_input
                    else "The vessel clears the clouds toward the citadel."
                ),
                shot_scale="mixed_progression",
                camera_treatment="compound",
                camera_intent=(
                    "Arc into a closer detail while preserving the dark table and empty set."
                    if supplied_input
                    else "Whip pan into a crane reveal of the destination."
                ),
                visible_change=(
                    "The embossed surface detail becomes readable while the product stays red."
                    if supplied_input
                    else "A risky turn opens the citadel route."
                ),
                transition_out="end",
            ),
        ],
    }


def _single_unit_payload(*, target_duration_seconds: float = 30) -> dict[str, object]:
    payload = _payload(
        coverage_strategy="single_take",
        target_duration_seconds=target_duration_seconds,
    )
    unit = payload["coverage_units"][0]
    unit["duration_seconds"] = target_duration_seconds
    unit["transition_out"] = "end"
    payload["coverage_units"] = [unit]
    payload["request"]["director_decision_rationale"] = (
        "A single uninterrupted reveal has one coherent spatial and action trajectory."
    )
    return payload


def test_missing_input_30s_agent_can_choose_multi_shot() -> None:
    validator = _load_validator()

    result = validator.validate_director_coverage(_payload())

    assert result == {
        "status": "passed",
        "schema_version": "3",
        "director_preflight_request": True,
        "creative_input_kind": "missing",
        "coverage_strategy": "multi_shot",
        "strategy_source": "agent_directed",
        "coverage_unit_count": 2,
        "planned_duration_seconds": 30.0,
    }


@pytest.mark.parametrize("transition", ["VIDEO_EXTEND", "no cut", "uninterrupted"])
def test_multi_shot_rejects_continuous_treatment_as_a_cut(
    transition: str,
) -> None:
    validator = _load_validator()
    payload = _payload()
    payload["coverage_units"][0]["transition_out"] = transition

    with pytest.raises(validator.CoverageValidationError, match="multi_shot"):
        validator.validate_director_coverage(payload)


def test_seedance_2_5_native_30s_does_not_choose_coverage_strategy() -> None:
    validator = _load_validator()

    assert _seedance_max_duration("doubao-seedance-2-5-260628") == 30
    multi_shot = validator.validate_director_coverage(_payload())
    single_take = validator.validate_director_coverage(_single_unit_payload())

    assert multi_shot["coverage_strategy"] == "multi_shot"
    assert single_take["coverage_strategy"] == "single_take"


def test_missing_input_30s_agent_can_choose_one_coverage_unit_single_take() -> None:
    validator = _load_validator()

    result = validator.validate_director_coverage(_single_unit_payload())

    assert result["coverage_strategy"] == "single_take"
    assert result["coverage_unit_count"] == 1
    assert result["planned_duration_seconds"] == 30.0


def test_missing_input_10s_agent_can_choose_multi_shot() -> None:
    validator = _load_validator()

    result = validator.validate_director_coverage(
        _payload(target_duration_seconds=10)
    )

    assert result["coverage_strategy"] == "multi_shot"
    assert result["coverage_unit_count"] == 2
    assert result["planned_duration_seconds"] == 10.0


def test_missing_input_still_requires_open_video() -> None:
    validator = _load_validator()
    payload = _single_unit_payload(target_duration_seconds=10)
    payload["request"]["director_skill"] = "seedance-authoring"

    with pytest.raises(
        validator.CoverageValidationError, match="DIRECTOR_PREFLIGHT_REQUEST"
    ):
        validator.validate_director_coverage(payload)


@pytest.mark.parametrize("creative_input_kind", ["direction", "draft_prompt"])
def test_supplied_raw_creative_input_still_requires_open_video(
    creative_input_kind: str,
) -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind=creative_input_kind)
    payload["request"]["director_skill"] = "seedance-authoring"

    with pytest.raises(
        validator.CoverageValidationError, match="DIRECTOR_PREFLIGHT_REQUEST"
    ):
        validator.validate_director_coverage(payload)


@pytest.mark.parametrize("creative_input_kind", ["direction", "draft_prompt"])
def test_supplied_raw_creative_input_can_pass_structural_director_preflight(
    creative_input_kind: str,
) -> None:
    validator = _load_validator()

    result = validator.validate_director_coverage(
        _payload(creative_input_kind=creative_input_kind)
    )

    assert result["director_preflight_request"] is True
    assert result["creative_input_kind"] == creative_input_kind


@pytest.mark.parametrize("creative_input_kind", ["direction", "draft_prompt"])
def test_supplied_raw_creative_input_requires_evidence(
    creative_input_kind: str,
) -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind=creative_input_kind)
    payload["request"]["creative_input_evidence"] = None

    with pytest.raises(
        validator.CoverageValidationError, match="creative_input_evidence"
    ):
        validator.validate_director_coverage(payload)


@pytest.mark.parametrize("creative_input_kind", ["direction", "draft_prompt"])
def test_supplied_raw_creative_input_requires_constraint_inventory(
    creative_input_kind: str,
) -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind=creative_input_kind)
    payload["request"]["creative_constraints"] = []
    for unit in payload["coverage_units"]:
        unit["constraint_ids"] = []

    with pytest.raises(
        validator.CoverageValidationError, match="creative_constraints"
    ):
        validator.validate_director_coverage(payload)


def test_constraint_source_text_must_be_verbatim_input_evidence() -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind="draft_prompt")
    payload["request"]["creative_constraints"][0]["source_text"] = (
        "Keep the product red."
    )

    with pytest.raises(validator.CoverageValidationError, match="exact substring"):
        validator.validate_director_coverage(payload)


def test_global_creative_constraint_must_bind_to_every_coverage_unit() -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind="direction")
    payload["coverage_units"][1]["constraint_ids"] = []

    with pytest.raises(
        validator.CoverageValidationError, match="omits global constraints"
    ):
        validator.validate_director_coverage(payload)


def test_unknown_creative_constraint_binding_fails_closed() -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind="draft_prompt")
    payload["coverage_units"][0]["constraint_ids"].append("invented-constraint")

    with pytest.raises(validator.CoverageValidationError, match="unknown IDs"):
        validator.validate_director_coverage(payload)


def test_beat_specific_constraint_must_bind_to_at_least_one_unit() -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind="direction")
    payload["request"]["creative_input_evidence"] += (
        " Reveal the embossed logo during the payoff beat."
    )
    payload["request"]["creative_constraints"].append(
        {
            "constraint_id": "constraint-02",
            "scope": "beat_specific",
            "source_text": "Reveal the embossed logo during the payoff beat.",
        }
    )

    with pytest.raises(
        validator.CoverageValidationError, match="beat-specific creative constraints"
    ):
        validator.validate_director_coverage(payload)


def test_missing_creative_input_rejects_invented_user_evidence() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["creative_input_evidence"] = "Invented user prompt."

    with pytest.raises(
        validator.CoverageValidationError, match="creative_input_evidence"
    ):
        validator.validate_director_coverage(payload)


def test_missing_creative_input_rejects_invented_constraint_inventory() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["creative_constraints"] = [
        {
            "constraint_id": "invented-constraint",
            "scope": "global",
            "source_text": "Invented user constraint.",
        }
    ]

    with pytest.raises(validator.CoverageValidationError, match="must be empty"):
        validator.validate_director_coverage(payload)


def test_approved_shot_is_not_a_raw_creative_input_kind() -> None:
    validator = _load_validator()
    payload = _payload(creative_input_kind="approved_shot")

    with pytest.raises(validator.CoverageValidationError, match="creative_input_kind"):
        validator.validate_director_coverage(payload)


def test_single_take_can_keep_evolving_internal_coverage() -> None:
    validator = _load_validator()
    payload = _payload(coverage_strategy="single_take")

    result = validator.validate_director_coverage(payload)

    assert result["status"] == "passed"
    assert result["coverage_strategy"] == "single_take"


def test_single_take_can_keep_one_camera_language_across_internal_beats() -> None:
    validator = _load_validator()
    payload = _payload(coverage_strategy="single_take")
    payload["coverage_units"][1]["beat_function"] = "establish"
    payload["coverage_units"][1]["shot_scale"] = "extreme_wide"
    payload["coverage_units"][1]["camera_treatment"] = "tracking"

    result = validator.validate_director_coverage(payload)

    assert result["coverage_strategy"] == "single_take"
    assert result["coverage_unit_count"] == 2


def test_user_requested_strategy_requires_direct_request_evidence() -> None:
    validator = _load_validator()
    payload = _payload(strategy_source="user_requested")
    payload["request"]["strategy_request_evidence"] = None

    with pytest.raises(
        validator.CoverageValidationError, match="strategy_request_evidence"
    ):
        validator.validate_director_coverage(payload)


def test_agent_directed_strategy_rejects_user_request_evidence() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["strategy_request_evidence"] = "Invented user preference."

    with pytest.raises(
        validator.CoverageValidationError, match="agent_directed"
    ):
        validator.validate_director_coverage(payload)


def test_director_decision_requires_a_rationale() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["director_decision_rationale"] = ""

    with pytest.raises(
        validator.CoverageValidationError, match="director_decision_rationale"
    ):
        validator.validate_director_coverage(payload)


def test_unknown_coverage_strategy_fails_closed() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["request"]["coverage_strategy"] = "decide from duration"

    with pytest.raises(validator.CoverageValidationError, match="coverage_strategy"):
        validator.validate_director_coverage(payload)


def test_multi_shot_requires_multiple_units_regardless_of_duration() -> None:
    validator = _load_validator()
    payload = _payload()
    unit = payload["coverage_units"][0]
    unit["duration_seconds"] = 30
    unit["transition_out"] = "end"
    payload["coverage_units"] = [unit]

    with pytest.raises(validator.CoverageValidationError, match="at least two"):
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


def test_single_take_rejects_a_cut_between_units() -> None:
    validator = _load_validator()
    payload = _payload(coverage_strategy="single_take")
    payload["coverage_units"][0]["transition_out"] = "cut"

    with pytest.raises(
        validator.CoverageValidationError, match="continuous non-final transitions"
    ):
        validator.validate_director_coverage(payload)


def test_schema_v2_prompt_presence_routing_contract_is_retired() -> None:
    validator = _load_validator()
    payload = _payload()
    payload["schema_version"] = "2"

    with pytest.raises(validator.CoverageValidationError, match="schema_version"):
        validator.validate_director_coverage(payload)
