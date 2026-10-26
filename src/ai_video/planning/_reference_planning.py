"""Reference rule adaptation at the existing VideoPlanner/asset readiness seam."""

from ai_video.planning._asset_readiness import asset_matches_role
from ai_video.planning._planner_models import (
    AssetRole, ContinuityMode, GenerationMode, PlanOutcome, PlanWarning,
    ReasonCode, RequiredAssetRole,
)
from ai_video.production.reference_planning import plan_shot_references
from ai_video.production.reference_strategy import select_reference_inputs, reference_event_timing_gaps

_ASSET_ROLES = {
    "identity": AssetRole.CHARACTER_REFERENCE, "scene": AssetRole.SCENE_REFERENCE,
    "first_frame": AssetRole.APPROVED_KEYFRAME, "last_frame": AssetRole.LAST_FRAME,
    "continuity_terminal": AssetRole.PREVIOUS_SHOT_TERMINAL,
    "video_reference": AssetRole.EXISTING_VIDEO, "audio_reference": AssetRole.REFERENCE_AUDIO,
}


def planned_reference_assets(request, continuity):
    projection = request.generation_intent
    intent = projection.generation_intent
    eligible = tuple(a for a in request.available_assets if asset_matches_role(request, a, a.role))
    chosen, issues, _ = select_reference_inputs(intent, eligible)
    chosen, gaps = list(chosen), list(issues)
    roles = {_ASSET_ROLES[r.value] for r in projection.semantic_reference_roles if r.value in _ASSET_ROLES}
    if continuity is ContinuityMode.EXACT_TERMINAL:
        roles.add(AssetRole.PREVIOUS_SHOT_TERMINAL)
    if projection.generation_operation.value in {"video_edit", "video_extend"}:
        roles.add(AssetRole.EXISTING_VIDEO)
    for role in sorted(roles, key=lambda r: r.value):
        candidates = [a for a in eligible if a.role is role]
        if not candidates:
            gaps.append(f"MISSING_DECLARED_REFERENCE:{role.value}")
            continue
        selected_for_role = [a for a in chosen if a.role is role]
        if selected_for_role and role is not AssetRole.CHARACTER_REFERENCE:
            continue
        if role is AssetRole.CHARACTER_REFERENCE:
            owners = request.target_shot.character_ids
        else:
            owners = (None,)
        for owner in owners:
            if any(a.canonical_owner_id == owner for a in selected_for_role):
                continue
            pool = [a for a in candidates if owner is None or a.canonical_owner_id == owner]
            if role in {AssetRole.EXISTING_VIDEO, AssetRole.REFERENCE_AUDIO} and projection.media_reference_asset_ids:
                selected = pool
            else:
                selected = pool if len(pool) == 1 else []
            if not selected:
                gaps.append(f"AMBIGUOUS_OR_MISSING_REFERENCE:{role.value}:{owner}")
            for asset in selected:
                if asset not in chosen:
                    chosen.append(asset)
    requested_media = set(projection.media_reference_asset_ids)
    if not requested_media.issubset({a.asset_id for a in chosen}):
        gaps.append("EXPLICIT_MEDIA_SELECTION_NOT_SATISFIED")
    return tuple(sorted(chosen, key=lambda a: (a.role.value, a.asset_id))), tuple(sorted(set(gaps)))


def reference_planning_decision(request, continuity, reasons, warnings):
    projection = request.generation_intent
    assets, issues = planned_reference_assets(request, continuity)
    plan = plan_shot_references(projection.generation_intent)
    issues = list(issues)
    roles = {a.role for a in assets}
    operation = projection.generation_operation.value
    if operation == "text_to_video":
        mode = GenerationMode.TEXT_TO_VIDEO
        if assets or any(n.priority == "required" and n.mechanism != "review_only" for n in plan.needs):
            issues.append("EXPLICIT_TEXT_ONLY_CONFLICTS_WITH_REFERENCES")
    elif operation in {"video_edit", "video_extend"}:
        mode = GenerationMode(operation)
    elif roles & {AssetRole.APPROVED_KEYFRAME, AssetRole.PREVIOUS_SHOT_TERMINAL}:
        mode = GenerationMode.FIRST_LAST_FRAME_VIDEO if AssetRole.LAST_FRAME in roles else GenerationMode.IMAGE_TO_VIDEO
    elif roles:
        mode = GenerationMode.REFERENCE_TO_VIDEO
    else:
        mode = GenerationMode.TEXT_TO_VIDEO
    if continuity is ContinuityMode.EXACT_TERMINAL and AssetRole.PREVIOUS_SHOT_TERMINAL not in roles:
        issues.append("MISSING_CONTINUITY_TERMINAL")
    if AssetRole.LAST_FRAME in roles and not roles & {AssetRole.APPROVED_KEYFRAME, AssetRole.PREVIOUS_SHOT_TERMINAL}:
        issues.append("LAST_FRAME_WITHOUT_OPENING")
    issues.extend(r for r in plan.risks if r.endswith("REQUIRED") or r == "MULTI_SHOT_NATIVE_CONTROL_UNDECLARED")
    if any(n.mechanism == "exact_time" for n in plan.needs):
        issues.append("TIMED_KEYFRAME_CONTROL_UNSUPPORTED")
    issues.extend(reference_event_timing_gaps(plan, projection.output_need))
    if issues:
        reasons.append(ReasonCode.REFERENCE_PLAN_UNSATISFIED)
        warnings.append(PlanWarning.REFERENCE_PLAN_REQUIRES_REVISION)
    else:
        reasons.append(ReasonCode.REFERENCE_PLAN_APPLIED)
    required = tuple(RequiredAssetRole(role=role, reason_code=ReasonCode.REFERENCE_PLAN_APPLIED)
                     for role in sorted(roles, key=lambda r: r.value))
    return mode, PlanOutcome.BLOCKED if issues else PlanOutcome.PROPOSED, required
