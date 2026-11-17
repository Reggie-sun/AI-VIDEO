"""Validate routing expectations; score supplied observations, never infer routing.

Run without --observations for contract validation only. Observation JSON is
{"runtime": "codex|claude", "version": "...", "results": [
 {"case_id": "...", "skills": [...], "role": "...", "evidence": "trace reference"}
]}. Capture actual Skill invocations / SKILL.md reads and dispatched role from a
real trace; an agent's proposed plan is not an observation. This tool does not
launch agents, execute prompts, inspect credentials, or generate media. Supplied
The role is the actual runtime role (or parent), not a project-duty label.
Trace references remain operator-attested; scoring does not authenticate traces.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests/fixtures/skill-routing-cases.json"
RUNTIME_ROLES = {
    "codex": {"parent", "executor", "verifier"},
    "claude": {"parent", "oh-my-claudecode:executor", "blender-artist", "shot-gate-reviewer", "memory-keeper"},
}
ROLES = set().union(*RUNTIME_ROLES.values())


def string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(f"{label}: expected list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label}: duplicate values")
    return value


def validate_cases(cases: object, root: Path = ROOT) -> list[dict]:
    if not isinstance(cases, list) or len(cases) < 20:
        raise ValueError("at least 20 cases required")
    known = {p.parent.name for p in (root / ".agents/skills").glob("*/SKILL.md")}
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        for field in ("id", "input", "rationale"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError(f"case requires {field}")
        if case["id"] in ids:
            raise ValueError("duplicate case id")
        ids.add(case["id"])
        expected = set(string_list(case.get("expected_skills"), "expected_skills"))
        forbidden = set(string_list(case.get("forbidden_skills"), "forbidden_skills"))
        if expected & forbidden or not (expected | forbidden) <= known:
            raise ValueError(f"{case['id']}: overlapping or unknown skills")
        expected_roles = case.get("expected_roles")
        if not isinstance(expected_roles, dict) or set(expected_roles) != set(RUNTIME_ROLES):
            raise ValueError(f"{case['id']}: expected roles for both runtimes required")
        for runtime, role in expected_roles.items():
            if not isinstance(role, str) or role not in RUNTIME_ROLES[runtime]:
                raise ValueError(f"{case['id']}: invalid {runtime} role")
    return cases


def evaluate(cases: list[dict], observations: dict | None = None) -> dict:
    report = {"contract": "PASS", "case_count": len(cases),
              "real_routing": "NOT_EVALUATED", "token_cost": "NOT_EVALUATED"}
    if observations is None:
        return report
    if not isinstance(observations, dict):
        raise ValueError("observations must be an object")
    if observations.get("runtime") not in {"codex", "claude"}:
        raise ValueError("observation runtime must be codex or claude")
    if not isinstance(observations.get("version"), str) or not observations["version"].strip():
        raise ValueError("observation version required")
    rows = observations.get("results")
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonempty observation results required")
    by_id = {c["id"]: c for c in cases}
    seen, results = set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("observation must be an object")
        key = row.get("case_id")
        if not isinstance(key, str) or key not in by_id or key in seen:
            raise ValueError("unknown or duplicate observed case")
        seen.add(key)
        if not isinstance(row.get("evidence"), str) or not row["evidence"].strip():
            raise ValueError("actual trace evidence reference required")
        if row.get("role") not in ROLES:
            raise ValueError("observed role required")
        actual = set(string_list(row.get("skills"), "observed skills"))
        case = by_id[key]
        missing = sorted(set(case["expected_skills"]) - actual)
        forbidden = sorted(set(case["forbidden_skills"]) & actual)
        # Extra loads also fail: task-scoped context is part of the contract.
        unexpected = sorted(actual - set(case["expected_skills"]))
        expected_role = case["expected_roles"][observations["runtime"]]
        passed = not (missing or forbidden or unexpected) and row["role"] == expected_role
        results.append({"case_id": key, "status": "PASS" if passed else "FAIL",
                        "missing": missing, "forbidden": forbidden,
                        "unexpected": unexpected, "role_matches": row["role"] == expected_role,
                        "expected_role": expected_role, "observed_role": row["role"],
                        "evidence": row["evidence"]})
    count = sum(r["status"] == "PASS" for r in results)
    report.update(runtime=observations["runtime"], version=observations["version"],
                  real_routing="OBSERVATIONS_SCORED", observed_count=len(results),
                  unobserved_cases=sorted(set(by_id) - seen), passed_count=count,
                  observed_pass_rate=count / len(results), results=results)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    try:
        cases = validate_cases(json.loads(args.cases.read_text(encoding="utf-8")))
        observations = json.loads(args.observations.read_text(encoding="utf-8")) if args.observations else None
        report = evaluate(cases, observations)
    except (OSError, ValueError) as exc:
        print(json.dumps({"contract": "FAIL", "error": str(exc)}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if any(r["status"] == "FAIL" for r in report.get("results", [])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
