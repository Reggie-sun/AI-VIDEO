"""Read-only responsibility projection of existing QA, intent and strategy owners.

This report never reallocates requirements, edits prompts, qualifies a source or
grants execution. Missing authoring remains explicit rather than inferred.
"""

from ai_video.production.domain_acceptance import production_allocation_issues
from ai_video.production.requirement_semantics import RequirementExpressionFields


def requirement_responsibility(rule):
    """Explain an authored rule without promoting preferences to acceptance."""
    semantics = rule.semantics
    if semantics is None:
        freedom = "NOT_EVALUATED"
    elif rule.level == "acceptance":
        freedom = "MUST_SATISFY"
    elif rule.level == "diagnostic":
        freedom = "OBSERVATION_ONLY"
    elif semantics.intent_role == "acceptable_variation":
        freedom = "ALLOWED_WITHIN_AUTHORED_SCOPE"
    else:
        freedom = "PREFERENCE_ONLY"
    return {
        "semantics": semantics.model_dump(mode="json") if semantics else None,
        "fixed_source_refs": [ref.model_dump(mode="json") for ref in
            (() if semantics is None else semantics.source_refs) if ref.fixed],
        "model_freedom": freedom,
        "responsibility_stage": rule.stage,
        "authored_owner": rule.production_owner,
        "raw_acceptance_required": rule.level == "acceptance" and rule.stage == "raw_generation",
        "raw_input_expected": rule.stage == "raw_generation" and rule.level != "diagnostic",
    }


def _inventory(acceptance):
    if acceptance is None:
        return []
    rows = []
    for raw in acceptance.profile_payload.get("generation_requirements") or ():
        try:
            rule = RequirementExpressionFields.model_validate(raw)
        except ValueError:
            # Legacy policy reading is not new execution admission. Do not
            # infer executable semantics from an incomplete historical rule.
            rows.append({"requirement_id": raw.get("requirement_id") if hasattr(raw, "get") else None,
                "requirement_definition": "NOT_EVALUATED", "input_issues": ["invalid_rule_shape"],
                "model_freedom": "NOT_EVALUATED"})
            continue
        rows.append({**rule.model_dump(mode="json"), **requirement_responsibility(rule)})
    return rows


def production_responsibility_report(*, qa_policy=None, shot=None, target_shot_id=None, decision=None,
                                     qa_authority="NOT_EVALUATED"):
    """Project one loaded snapshot; a global rubric is not implicit Shot binding."""
    intent = getattr(shot, "production_intent", None)
    parent = None if qa_policy is None else (
        qa_policy.domain_acceptance or qa_policy.selected_generation_acceptance())
    allocations = [] if qa_policy is None or intent is None else [
        allocation for allocation in qa_policy.production_allocations
        if allocation.parent_shot_id == shot.shot_id
        and allocation.parent_shot_content_hash == shot.content_hash
        and allocation.task_id == intent.task_id]
    # A project-wide inventory is shown once. Per-Shot views require the
    # existing explicit intent/allocation binding, never a guessed target.
    project_inventory = shot is None and target_shot_id is None
    show_inventory = project_inventory or bool(allocations)
    requirements = _inventory(parent) if show_inventory else []
    required_ids = set(() if parent is None else parent.required_requirement_ids)
    by_id = {row["requirement_id"]: row for row in requirements}
    final = None if qa_policy is None else qa_policy.final_output
    final_by_id = {} if final is None else {r.requirement_id: r for r in final.requirements}
    if show_inventory:
        for rid in sorted(required_ids - by_id.keys()):
            row = {"requirement_id": rid, "requirement_definition": "NOT_EVALUATED",
                   "model_freedom": "NOT_EVALUATED"}
            if rid in final_by_id:
                row["final_output_requirement"] = final_by_id[rid].model_dump(mode="json")
            requirements.append(row)
        for row in requirements:
            rid = row["requirement_id"]
            row["parent_required"] = rid in required_ids
            if rid in final_by_id:
                row["final_output_requirement"] = final_by_id[rid].model_dump(mode="json")
            row["allocations"] = [{"allocation_hash": a.allocation_hash,
                "component_ids": [c.component_id for c in a.components if rid in c.requirement_ids],
                "assembly": rid in a.assembly_requirement_ids} for a in allocations]
    allocation_rows = [{"allocation_id": a.allocation_id, "allocation_hash": a.allocation_hash,
        "issues": list(production_allocation_issues(qa_policy, a)),
        "assembly_requirement_ids": list(a.assembly_requirement_ids),
        "components": [{"component_id": c.component_id,
            "requirement_ids": list(c.requirement_ids),
            "generation_requirements": _inventory(c.generation_acceptance),
            "source_use_acceptance": "REQUIRES_EXACT_USE_EVIDENCE"}
            for c in a.components]} for a in allocations]
    strategy = {"disposition": "NOT_EVALUATED", "selected_candidate_hash": None,
                "units": [], "candidates": []}
    if decision is not None:
        strategy.update(disposition=decision.disposition, reasons=list(decision.reasons),
            selected_candidate_hash=decision.selected.candidate_hash if decision.selected else None,
            units=[u.model_dump(mode="json") for u in (() if decision.selected is None else decision.selected.units)],
            candidates=[{"candidate_hash": c.candidate_hash, "allocation_hash": c.allocation_hash,
                "operations": [operation.value for operation in c.operations],
                "blockers": list(c.blockers)} for c in decision.candidates])
    return {"schema_version": "production-responsibility-preview/1",
        "qa_authority": qa_authority if qa_policy is not None else "NOT_EVALUATED",
        "qa_policy_hash": qa_policy.content_hash if qa_policy is not None else None,
        "shot_id": getattr(shot, "shot_id", target_shot_id),
        "binding": ("PROJECT_INVENTORY_TARGET_NOT_ASSIGNED" if project_inventory else
            "REQUIRES_PRODUCTION_INTENT" if intent is None else
            "DECLARED_PRODUCTION_INTENT" if allocations else "REQUIRES_MATCHING_ALLOCATION"),
        "requirements": requirements, "allocations": allocation_rows,
        "selected_generation_requirements": _inventory(qa_policy.selected_generation_acceptance())
            if qa_policy is not None and show_inventory else [],
        "production_intent": intent.model_dump(mode="json") if intent else None,
        "strategy": strategy,
        "final_output_contract": final.model_dump(mode="json") if final else None,
        "actual_quality": "NOT_EVALUATED",
        "proof_boundary": "Authored responsibility and available operations are input facts; "
            "model compliance, source-use qualification and exact final audiovisual acceptance require evidence."}
