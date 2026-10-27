"""Evidence eligibility for the existing production-means resolver.

These calculations never accept media, write state, or dispatch an effect.
"""
from decimal import Decimal

from ai_video.production.hashing import canonical_sha256
from ai_video.production.production_strategy_salvage_contracts import (
    FrameWindow, QualityDimension, SalvageOperation as Op,
)


def candidate_plan_key(candidate):
    """Exclude derived blockers and QA, avoiding a self-referential review hash."""
    return canonical_sha256(candidate.model_dump(mode="json", exclude={"blockers"}))


def salvage_review_for(policy, parent):
    reviews = getattr(policy, "production_salvage_reviews", ()) if policy else ()
    return next((r for r in reviews if r.parent_shot_id == parent.shot_id
                 and r.task_id == parent.production_intent.task_id), None)


def has_materialized_salvage(bundle, parent):
    return any(s.production_lineage is not None
               and s.production_lineage.parent_shot_id == parent.shot_id
               and s.production_lineage.salvage_review_hash is not None for s in bundle.shots)


def validate_salvage_policy(policy):
    """QA owns observations; post-edit obligations stay in its final contract."""
    reviews = policy.production_salvage_reviews
    identities = [(r.task_id, r.parent_shot_id) for r in reviews]
    if len(set(identities)) != len(identities):
        raise ValueError("Salvage review parent/task identities must be unique")
    acceptance = policy.domain_acceptance or policy.selected_generation_acceptance()
    for review in reviews:
        if acceptance is None or review.acceptance_profile_hash != acceptance.profile_content_hash:
            raise ValueError("Salvage review must bind the selected acceptance profile")
        if not set(review.required_events) <= set(acceptance.required_requirement_ids):
            raise ValueError("Salvage events must retain canonical acceptance requirements")
        final = policy.final_output
        obligations = set(review.transition_requirement_ids) | set(review.scene_requirement_ids)
        if final is None or not obligations <= {r.requirement_id for r in final.requirements}:
            raise ValueError("Salvage needs canonical transition and scene final-output requirements")
        for take in review.takes:
            playback = take.playback
            if playback.evaluator not in policy.semantic_authorities or not any(
                a.evaluator == playback.evaluator and a.proof == playback.proof
                for a in policy.generation_evaluation_authorities
            ):
                raise ValueError("Salvage playback requires policy-selected evaluator and proof")


def _covers(windows, target):
    cursor = target.start
    for window in sorted(windows, key=lambda w: w.start):
        if window.end <= cursor:
            continue
        if window.start > cursor:
            return False
        cursor = max(cursor, window.end)
        if cursor >= target.end:
            return True
    return False


def review_context_blockers(loaded, parent, review):
    blockers = []
    intent = parent.production_intent
    if review.parent_shot_content_hash != parent.content_hash:
        blockers.append("evidence_required:salvage_stale_parent")
    if set(review.required_events) != set(intent.protected_requirement_ids):
        blockers.append("needs_authoring_revision:salvage_event_inventory")
    obligations = set(review.transition_requirement_ids) | set(review.scene_requirement_ids)
    if not obligations <= set(intent.assembly_requirement_ids):
        blockers.append("needs_authoring_revision:salvage_assembly_allocation")
    assets = {a.asset_id: a for a in loaded.registry.assets}
    family = {parent.shot_id, *(u.shot_id for c in intent.coverage_options for u in c.units)}
    for take in review.takes:
        asset = assets.get(take.asset_id)
        meta = asset.video_metadata if asset else None
        if (asset is None or meta is None or asset.sha256 != take.asset_sha256
                or asset.size_bytes != take.size_bytes
                or asset.creation_receipt_id != take.source_revision
                or meta.frame_count != take.total_frames
                or Decimal(meta.duration_milliseconds) / 1000 != take.duration_seconds
                or take.scene_id != parent.scene_id or take.shot_id not in family):
            blockers.append("evidence_required:salvage_source_identity:" + take.take_id)
        playback = take.playback
        if (playback.mode != "continuous_playback" or playback.viewing_speed_milli != 1000
                or not playback.audio_reviewed
                or not _covers(playback.reviewed_windows, FrameWindow(start=0, end=take.total_frames))
                or {o.dimension for o in take.observations} != set(QualityDimension)
                or any(o.verdict == "UNREVIEWED" for o in take.observations)):
            blockers.append("evidence_required:salvage_unreviewed:" + take.take_id)
        if any(asset_id not in assets for asset_id in take.alternative_asset_ids):
            blockers.append("evidence_required:salvage_alternative_identity:" + take.take_id)
    authored_assets = {s.asset_id for c in intent.coverage_options for u in c.units
                       for s in (*u.source_options, *u.additional_sources) if s.timebase == "frames"}
    if not authored_assets <= {t.asset_id for t in review.takes}:
        blockers.append("evidence_required:salvage_missing_take")
    alternatives = {a for t in review.takes for a in t.alternative_asset_ids}
    if not alternatives <= authored_assets:
        blockers.append("evidence_required:salvage_alternatives_not_evaluated")
    return tuple(dict.fromkeys(blockers))


def _candidate_sources(candidate):
    return tuple((selected, source) for selected in candidate.units
                 for source in ((selected.source,) if selected.source else ())
                 + selected.component.additional_sources if source.timebase == "frames")


def require_current_salvage_lineage(bundle, parent, lineage):
    """Shared composition and pre-effect generation eligibility, including removal."""
    from ai_video.errors import AiVideoError, ErrorCode

    review = salvage_review_for(bundle.qa_policy, parent)
    if review is None and lineage.salvage_review_hash is None:
        return
    plan = next((p for p in review.candidate_plans if p.plan_key == lineage.salvage_plan_key), None) if review else None
    if (review is None or lineage.salvage_review_hash != review.review_hash
            or plan is None or plan.viability != "feasible"
            or review_context_blockers(bundle, parent, review)):
        raise AiVideoError(ErrorCode.PRODUCTION_PROJECT_INVALID,
            "Production execution requires the current exact salvage review and materialized plan.")


def assess_salvage_candidate(loaded, parent, candidate, review):
    """Add semantic vetoes; a plan can never override an existing QA blocker."""
    blockers = list(review_context_blockers(loaded, parent, review))
    plan = next((p for p in review.candidate_plans if p.plan_key == candidate_plan_key(candidate)), None)
    if plan is None:
        return (*blockers, "evidence_required:salvage_candidate_unreviewed")
    evidence = {t.playback.evidence_sha256 for t in review.takes}
    evidence.update(e.evidence_hash for e in loaded.qa_policy.production_source_evidence)
    if not plan.evidence_sha256s or not set(plan.evidence_sha256s) <= evidence:
        blockers.append("evidence_required:salvage_candidate_evidence")
    if plan.viability == "unreviewed":
        blockers.append("evidence_required:salvage_candidate_unreviewed")
    if plan.viability == "infeasible":
        blockers.extend("salvage_infeasible:" + r for r in plan.rejection_reasons)
    if set(plan.protected_requirement_ids) != set(parent.production_intent.protected_requirement_ids):
        blockers.append("needs_authoring_revision:salvage_protected_requirements")
    family = {parent.shot_id, *(u.component.shot_id for u in candidate.units)}
    if not set(plan.affected_shot_ids) <= family:
        blockers.append("blocked_scope:salvage_unrelated_shot")
    operations = set(plan.operations)
    if plan.uses_provider_generation != bool(candidate.new_generation_count):
        blockers.append("capability_gap:salvage_generation_operation_mismatch")
    if Op.GENERATIVE_REPAIR in operations:
        blockers.append("capability_gap:generative_repair_requires_selected_edit_executor")
    if Op.REPLAN in operations:
        blockers.append("needs_authoring_revision:salvage_replan")
    if Op.GENERATE_INSERT in operations and len(candidate.units) < 2:
        blockers.append("needs_authoring_revision:salvage_insert_coverage")
    if Op.KEEP in operations and (len(operations) != 1 or candidate.new_generation_count):
        blockers.append("needs_authoring_revision:salvage_keep_mismatch")
    if Op.REUSE in operations and not _candidate_sources(candidate):
        blockers.append("needs_authoring_revision:salvage_reuse_without_source")
    if Op.OMIT in operations and not plan.alternative_expression:
        blockers.append("needs_authoring_revision:omission_needs_explicit_event_preservation")
    if not candidate.new_generation_count and (
        plan.provider_cost.lower != 0 or plan.provider_cost.upper != 0
    ):
        blockers.append("needs_authoring_revision:local_render_is_not_provider_generation")
    defects = {d.defect_id for t in review.takes for d in t.defects}
    if not defects <= set(plan.defect_ids):
        blockers.append("evidence_required:salvage_unaddressed_defects")
    sources = _candidate_sources(candidate)
    for take in review.takes:
        uses = [(s, source, FrameWindow(start=source.start, end=source.start + source.duration))
                for s, source in sources if source.asset_id == take.asset_id]
        retained = [window for _, _, window in uses]
        for protected in take.protected_windows:
            if not _covers(retained, protected):
                blockers.append("salvage_infeasible:approved_window_removed:" + take.take_id)
        for selected, source, window in uses:
            if source.source_time_map is not None and any(w.overlaps(window) for w in take.protected_windows):
                blockers.append("salvage_infeasible:protected_performance_retimed:" + take.take_id)
            if not _covers(take.usable_windows, window):
                blockers.append("salvage_infeasible:outside_usable_windows:" + take.take_id)
            if Op.KEEP in operations and (window.start or window.end != take.total_frames
                    or source.source_time_map is not None):
                blockers.append("needs_authoring_revision:salvage_keep_changes_source")
            requirements = set(source.requirement_ids or selected.component.requirement_ids)
            for observation in take.observations:
                if (observation.requirement_id in requirements and observation.verdict == "FAIL"
                        and (observation.window is None or observation.window.overlaps(window))):
                    blockers.append("salvage_infeasible:retained_failed_requirement:" + observation.requirement_id)
            for defect in take.defects:
                structural = defect.extent == "structural" and bool(requirements & set(defect.requirement_ids))
                if defect.window.overlaps(window) or structural:
                    # Local surface repair must produce a separately reviewed exact
                    # asset. Merely naming a mask/V2V/transition cannot erase FAIL.
                    blockers.append("salvage_infeasible:retained_defect:" + defect.defect_id)
    if Op.LOCAL_REPAIR in operations and not any(
        op.value in {"REFRAME", "REPLACE_AUDIO", "COMPOSITE_MULTIPLE_ASSETS"}
        for op in candidate.operations
    ):
        blockers.append("capability_gap:local_repair_requires_materialized_source_or_supported_operation")
    if plan.alternative_expression and not parent.production_intent.assembly_requirement_ids:
        blockers.append("needs_authoring_revision:alternative_expression_requires_scene_review")
    return tuple(dict.fromkeys(blockers))


def preferred_salvage_candidates(feasible, review):
    """Pareto risk comparison, then generation count; never sum quality scores."""
    plans = {p.plan_key: p for p in review.candidate_plans}
    dimensions = ("narrative", "identity", "continuity", "performance", "approved_content")
    rank = {"low": 0, "medium": 1, "high": 2}

    def dominates(left, right):
        a, b = plans[candidate_plan_key(left)], plans[candidate_plan_key(right)]
        values = [(getattr(a.risks, d), getattr(b.risks, d)) for d in dimensions]
        if any(x == "unknown" or y == "unknown" for x, y in values):
            return False
        if not all(rank[x] <= rank[y] for x, y in values):
            return False
        if any(rank[x] < rank[y] for x, y in values):
            return True
        if left.new_generation_count != right.new_generation_count:
            return left.new_generation_count < right.new_generation_count
        estimates = [(a.provider_cost, b.provider_cost), (a.local_render_cost, b.local_render_cost),
                     (a.elapsed_time, b.elapsed_time)]
        return (all(x.unit == y.unit and x.upper is not None and y.lower is not None
                    and x.upper <= y.lower for x, y in estimates)
                and any(x.upper < y.lower for x, y in estimates))

    # Risk comes first. Equal known risk prefers fewer generated components;
    # unknown or conflicting dimensions cannot be resolved by cheap editing.
    return tuple(c for c in feasible if not any(dominates(other, c) for other in feasible if other != c))


def _same_generation_design(shot, parent, unit, fps):
    """Compare authored action/coverage, excluding revisions, receipts and seeds."""
    from ai_video.production.composition import _frames_for_fixed_seconds

    first_frames = tuple(a for r in shot.required_asset_roles if r.role == "first_frame" for a in r.asset_ids)
    return (shot.intent == unit.intent and shot.dialogue == unit.dialogue
        and shot.scene_id == parent.scene_id and shot.storyboard_beat_id == parent.storyboard_beat_id
        and shot.narration == unit.narration and shot.character_ids == parent.character_ids
        and shot.continuity_constraints == parent.continuity_constraints
        and shot.preserved_source_expression == unit.preserved_source_expression
        and shot.duration_policy.mode == "fixed" and shot.duration_policy.seconds is not None
        and _frames_for_fixed_seconds(shot.duration_policy.seconds, fps) == unit.duration_frames
        and first_frames == ((unit.first_frame_asset_id,) if unit.first_frame_asset_id else ()))


def repeated_failure_requirements(experiences, parent, review, *, candidate=None, fps=None):
    """Use canonical diagnoses, counting distinct requests rather than reviews."""
    from ai_video.production.generation_diagnosis import diagnose_exact_result

    family = {parent.shot_id, *(u.shot_id for c in parent.production_intent.coverage_options for u in c.units)}
    entries = {}
    for experience in experiences:
        design = None
        if candidate is not None:
            matches = tuple(u.component.component_id for u in candidate.units
                if u.source is None and _same_generation_design(
                    experience.projection.requirement.target_shot, parent, u.component, fps))
            if not matches:
                continue
            design = matches[0]
        for entry in experience.evidence:
            if (entry.task_id == review.task_id and entry.outcome == "media"
                    and (design is not None or entry.shot_id in family)):
                entries[(entry.shot_id, entry.request_hash)] = (experience, entry, design or entry.shot_id)
    counts = {}
    all_evidence = tuple(e for x in experiences for e in x.evidence)
    sources = tuple(s for x in experiences for s in x.evaluation_sources)
    for experience, entry, key in entries.values():
        diagnosis = diagnose_exact_result(entry, all_evidence, experience.candidate.recipe,
            evaluation_sources=sources, requirement=experience.projection.requirement)
        # New seeds/recipe scopes do not clear repeated failure of the same
        # authored action. A confirmed success or a changed design does.
        previous = counts.get(key, {})
        counts[key] = {requirement: previous.get(requirement, 0) + 1
                       for requirement in diagnosis.failed_requirements}
    return tuple(sorted({requirement for values in counts.values()
                         for requirement, count in values.items() if count >= review.repeated_failure_limit}))


def salvage_report(loaded, parent, decision):
    review = salvage_review_for(loaded.qa_policy, parent)
    if review is None:
        return {"status": "UNREVIEWED", "reason": "No current Take salvage assessment", "verification": "NOT_EVALUATED"}
    plans = {p.plan_key: p for p in review.candidate_plans}
    selected_key = candidate_plan_key(decision.selected) if decision.selected else None
    status = "BLOCKED"
    if decision.selected:
        status = "NEEDS_GENERATION" if decision.selected.new_generation_count else "EDIT_CANDIDATE"
    elif any("needs_authoring_revision" in r for r in decision.reasons):
        status = "NEEDS_REPLAN"
    elif decision.disposition == "evidence_required":
        status = "UNREVIEWED"
    acceptance = loaded.manifest.final_acceptance_state
    family = tuple(s for s in loaded.shots if s.production_lineage is not None
                   and s.production_lineage.parent_shot_id == parent.shot_id)
    verified = bool(decision.selected and family and acceptance
        and acceptance.lifecycle.value == "fresh" and acceptance.active_receipt is not None
        and acceptance.applied_fingerprint == acceptance.desired_fingerprint
        and all(s.production_lineage.salvage_review_hash == review.review_hash
                and s.production_lineage.salvage_plan_key == selected_key for s in family)
        and {s.shot_id for s in family} == {u.component.shot_id for u in decision.selected.units})
    if verified:
        status = "VERIFIED"
    return {"status": status, "review_hash": review.review_hash,
        "verification": "PASS" if verified else "NOT_EVALUATED", "selected_plan_key": selected_key,
        "final_acceptance_receipt": acceptance.active_receipt.model_dump(mode="json") if verified else None,
        "repair_outcome_receipts": [p.model_dump(mode="json") for p in loaded.manifest.repair_outcome_receipts],
        "scene_intent": review.scene_intent, "genre": review.genre,
        "take_assessments": [t.model_dump(mode="json") for t in review.takes],
        "required_post_edit_checks": [*review.transition_requirement_ids, *review.scene_requirement_ids],
        "reasons": list(decision.reasons), "candidates": [{
            "plan_key": candidate_plan_key(c), "selected": candidate_plan_key(c) == selected_key,
            "blockers": list(c.blockers), "new_generation_count": c.new_generation_count,
            "plan": plans[candidate_plan_key(c)].model_dump(mode="json") if candidate_plan_key(c) in plans else None,
        } for c in decision.candidates],
        "remaining_questions": [] if verified else ["Exact edited transition and scene playback", "Fresh P6 before/after no-regression review"],
        "execution_owner": "ProductionPlanningService / ProductionStateCommitter",
        "acceptance_owner": "P6 ReviewReceipt / RepairOutcomeReceipt"}
