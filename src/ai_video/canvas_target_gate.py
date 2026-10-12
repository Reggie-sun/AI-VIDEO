"""Project selected state checks into the existing generation QA/receipt owner."""
from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance
from ai_video.production.hashing import canonical_sha256


def target_state_requirements(row):
    plan = row.get("state_reference")
    if plan is None:
        return {}
    return {f"canvas-state-{row['occurrence_id']}-{dimension}": (dimension, expected)
            for dimension, expected in plan["checks"].items()}


def target_state_qa_rules(*, direction, row, proof="analyzer"):
    """Data projection for the operator's normal selected QA approval, no activation."""
    source_hash = canonical_sha256(direction)
    result = []
    for identity, (dimension, expected) in target_state_requirements(row).items():
        locator = f"shots/{row['occurrence_id']}/state_reference/checks/{dimension}"
        result.append({"requirement_id": identity, "level": "acceptance", "stage": "raw_generation",
            "dimension": dimension, "observable": expected, "tolerance": "Retain the selected required continuity state",
            "measurement": "Compare the successor media to its actual bound accepted-state reference and source evidence",
            "proof": proof, "intent_paths": ["generation_intent.subject_action.progression"], "production_owner": "qa_acceptance",
            "semantics": {"version": "requirement-semantics/1", "category": "quality_critical",
                "intent_role": "must_happen", "source_refs": [{"source_hash": source_hash, "locator": locator,
                    "intent_item_id": identity, "quote": expected, "origin": "director_choice"}],
                "hard_basis": {"kind": "approved_narrative", "source_hash": source_hash, "locator": locator,
                    "necessity": "The approved successor continuity requirement must be checked"}, "derived_from": []}})
    return result


def require_target_state_inventory(*, loaded, row):
    required = target_state_requirements(row)
    if not required:
        return required
    acceptance = selected_shot_generation_acceptance(loaded, row["shot"]["shot_id"])
    rules = {item["requirement_id"]: item for item in
             acceptance.profile_payload.get("generation_requirements", ())} if acceptance else {}
    for identity, (dimension, expected) in required.items():
        rule = rules.get(identity)
        if (rule is None or identity not in acceptance.required_requirement_ids
                or rule["level"] != "acceptance" or rule["stage"] != "raw_generation"
                or rule["dimension"] != dimension or rule["observable"] != expected):
            raise ValueError(f"Successor state Gate needs selected QA criterion {identity}: {expected}")
    return required


def require_target_state_findings(*, loaded, row, entry):
    required = require_target_state_inventory(loaded=loaded, row=row)
    for identity in required:
        findings = [finding for finding in entry.findings if finding.requirement_id == identity]
        if not findings or any(f.verdict != "PASS" for f in findings):
            raise ValueError(f"Successor state Gate is FAIL or NOT_EVALUATED: {identity}")
