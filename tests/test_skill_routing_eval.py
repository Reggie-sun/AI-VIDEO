from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest

from scripts.skill_routing_eval import DEFAULT_CASES, ROOT, evaluate, validate_cases


def cases():
    return json.loads(DEFAULT_CASES.read_text(encoding="utf-8"))


def observation(case, runtime="codex", **changes):
    row = {"case_id": case["id"], "skills": case["expected_skills"],
           "role": case["expected_roles"][runtime], "evidence": "fixture-only:not-a-real-trace"}
    row.update(changes)
    return {"runtime": runtime, "version": "test-fixture", "results": [row]}


def test_static_contract_never_claims_real_trigger_or_token_measurement():
    report = evaluate(validate_cases(cases()))
    assert report["case_count"] >= 20
    assert report["real_routing"] == report["token_cost"] == "NOT_EVALUATED"
    assert "observed_pass_rate" not in report


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "overlap", "missing", "role"])
def test_invalid_contract_fails(mutation):
    data = cases()
    if mutation == "duplicate":
        data[1]["id"] = data[0]["id"]
    elif mutation == "unknown":
        data[0]["expected_skills"] = ["nonexistent"]
    elif mutation == "overlap":
        data[0]["forbidden_skills"] += data[0]["expected_skills"]
    elif mutation == "missing":
        del data[0]["rationale"]
    else:
        data[0]["expected_roles"]["codex"] = "invented"
    with pytest.raises(ValueError):
        validate_cases(data)


def test_partial_observations_do_not_claim_full_coverage():
    data = validate_cases(cases())
    report = evaluate(data, observation(data[0]))
    assert report["observed_pass_rate"] == 1
    assert report["observed_count"] == 1
    assert len(report["unobserved_cases"]) == len(data) - 1
    assert report["token_cost"] == "NOT_EVALUATED"


@pytest.mark.parametrize("changes", [
    {"skills": []}, {"skills": ["h3-video", "vidu-authoring"]},
    {"skills": ["h3-video", "open-video"]}, {"role": "executor"},
])
def test_missing_forbidden_extra_or_wrong_role_fails(changes):
    data = cases()
    assert evaluate(data, observation(data[0], **changes))["passed_count"] == 0


@pytest.mark.parametrize("changes", [{"evidence": ""}, {"skills": "h3-video"},
                                     {"case_id": "unknown"}, {"role": None}])
def test_invalid_observation_rejected(changes):
    data = cases()
    with pytest.raises(ValueError):
        evaluate(data, observation(data[0], **changes))


def test_duplicate_observation_rejected():
    data = cases()
    obs = observation(data[0])
    obs["results"].append(copy.deepcopy(obs["results"][0]))
    with pytest.raises(ValueError):
        evaluate(data, obs)


def test_cli_static_and_failed_observation_exit_codes(tmp_path):
    cmd = [sys.executable, str(ROOT / "scripts/skill_routing_eval.py")]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert json.loads(result.stdout)["real_routing"] == "NOT_EVALUATED"
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(observation(cases()[0], skills=[])))
    result = subprocess.run(cmd + ["--observations", str(path)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
    path.write_text("{}")
    result = subprocess.run(cmd + ["--observations", str(path)], capture_output=True, text=True, check=False)
    assert result.returncode == 2


@pytest.mark.parametrize("runtime", ["codex", "claude"])
@pytest.mark.parametrize("case_id,codex_role,claude_role", [
    ("blender-blockout", "executor", "blender-artist"),
    ("memory-retrieve", "executor", "memory-keeper"),
    ("shot-review", "verifier", "shot-gate-reviewer"),
    ("simple-code", "executor", "oh-my-claudecode:executor"),
    ("provider-negation", "executor", "oh-my-claudecode:executor"),
])
def test_runtime_roles_use_actual_dispatch(runtime, case_id, codex_role, claude_role):
    data = validate_cases(cases())
    case = next(c for c in data if c["id"] == case_id)
    correct = codex_role if runtime == "codex" else claude_role
    wrong = claude_role if runtime == "codex" else codex_role
    assert evaluate(data, observation(case, runtime=runtime, role=correct))["passed_count"] == 1
    assert evaluate(data, observation(case, runtime=runtime, role=wrong))["passed_count"] == 0


def test_case_cannot_declare_project_role_as_codex_native_role():
    data = cases()
    data[0]["expected_roles"]["codex"] = "shot-gate-reviewer"
    with pytest.raises(ValueError, match="invalid codex role"):
        validate_cases(data)


def test_case_requires_both_runtime_roles():
    data = cases()
    del data[0]["expected_roles"]["claude"]
    with pytest.raises(ValueError, match="both runtimes"):
        validate_cases(data)
