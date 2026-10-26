"""Execution feasibility and evidence-scoped advice using canonical capabilities."""

from ai_video.production.reference_planning import plan_shot_references, reference_plan_report
from ai_video.production.reference_planning_contracts import ReferenceRole as Role

_NATIVE = {
    "character_reference": "reference", "identity": "reference",
    "scene_reference": "reference", "scene": "reference",
    "approved_keyframe": "first_frame", "approved_reusable_plate": "first_frame",
    "first_frame": "first_frame", "previous_shot_terminal": "first_frame",
    "continuity_terminal": "first_frame", "last_frame": "last_frame",
    "approved_endpoint": "last_frame", "existing_video": "reference_video",
    "video_reference": "reference_video", "continuity_motion_tail": "reference_video",
    "reference_audio": "reference_audio", "audio_reference": "reference_audio",
}


def native_role(asset):
    return _NATIVE.get(asset.role.value)


def _matches(need, asset, product_first_frame_id=None):
    role = native_role(asset)
    if need.owner_id is not None and need.owner_id != asset.canonical_owner_id:
        return False
    if need.mechanism == "reference_video":
        return role == "reference_video" and asset.mime_type.startswith("video/")
    if need.mechanism in {"first_frame", "last_frame"}:
        return role == need.mechanism and asset.mime_type.startswith("image/")
    if need.mechanism not in {"reference", "exact_time"} or not asset.mime_type.startswith("image/"):
        return False
    if need.role is Role.IDENTITY:
        return asset.role.value in {"identity", "character_reference"}
    if need.role is Role.PRODUCT and asset.asset_id == product_first_frame_id:
        return role == "first_frame"
    return role == "reference"


def select_reference_inputs(intent, assets, *, product_first_frame_id=None):
    """Select by explicit duty, or an unambiguous canonical persistent owner.

    The caller supplies only assets that passed its existing identity/readiness
    seam. This function cannot bless unregistered images or infer motion from one.
    """
    plan = plan_shot_references(intent)
    authored = intent.reference_planning
    if authored is None:
        return (), (), ()
    selected, gaps, bindings = [], [], []
    needs = {need.need_id: need for need in plan.needs}
    selections = {s.need_id: s.asset_id for s in authored.selections}
    gaps.extend(f"UNKNOWN_REFERENCE_NEED:{key}" for key in sorted(set(selections) - needs.keys()))
    for need in plan.needs:
        asset_id = selections.get(need.need_id)
        if need.mechanism in {"review_only", "composition", "previsualization"}:
            if asset_id is not None:
                gaps.append(f"NON_PROVIDER_REFERENCE_SELECTION:{need.need_id}")
            continue
        candidates = [a for a in assets if _matches(need, a, product_first_frame_id)]
        if asset_id is not None:
            candidates = [a for a in candidates if a.asset_id == asset_id]
        elif need.scope == "persistent" and need.role in {Role.IDENTITY, Role.SCENE}:
            # Same owner, competing interpretations: require a director choice.
            pass
        elif need.mechanism in {"first_frame", "last_frame"}:
            pass
        elif need.role is Role.PRODUCT and product_first_frame_id is not None:
            candidates = [a for a in candidates if a.asset_id == product_first_frame_id]
        else:
            candidates = []  # Ordinary footage cannot silently acquire a motion duty.
        if len(candidates) == 1:
            asset = candidates[0]
            if asset not in selected:
                selected.append(asset)
            bindings.append((need.need_id, asset.asset_id))
        elif asset_id is not None or need.priority == "required":
            gaps.append(f"{'AMBIGUOUS' if len(candidates) > 1 else 'MISSING'}_REFERENCE:{need.need_id}")
    independent = {}
    for need_id, asset_id in bindings:
        need = needs[need_id]
        if need.role is Role.IDENTITY:
            asset = next(a for a in selected if a.asset_id == asset_id)
            independent.setdefault(asset.asset_sha256, set()).add(need.owner_id)
    if any(len(owners) > 1 for owners in independent.values()):
        gaps.append("INDEPENDENT_IDENTITY_BYTES_CONFLICT")
    return tuple(selected), tuple(sorted(set(gaps))), tuple(bindings)


def _requirement_selection(requirement):
    approval = requirement.approved_commercial_source
    return select_reference_inputs(requirement.generation_intent, requirement.asset_evidence,
        product_first_frame_id=approval.keyframe_asset_id if approval is not None
        and requirement.capability_need.needs_product_fidelity else None)


def reference_event_timing_gaps(plan, output):
    """Check events against the sealed OutputNeed bound, without a new timeline."""
    duration = (output.frame_count / output.fps
        if output.frame_count is not None and output.fps is not None
        else output.duration_seconds)
    return tuple(f"EVENT_OUTSIDE_SHOT:{need.need_id}" for need in plan.needs
        if duration is not None and need.at_seconds is not None and need.at_seconds > duration)


def reference_execution_gaps(requirement, variant=None):
    """Additional semantic guard; ordinary mode/count/bytes checks stay in Router."""
    intent = requirement.generation_intent
    if intent.reference_planning is None:
        return ()
    plan = plan_shot_references(intent)
    _, missing, bindings = _requirement_selection(requirement)
    gaps = list(missing)
    bound = dict(bindings)
    gaps.extend(reference_event_timing_gaps(plan, requirement.output_need))
    for need in plan.needs:
        if need.mechanism == "exact_time":
            # Current capability schema has endpoints/reference guidance only.
            # Count capacity cannot imply timestamp binding.
            gaps.append(f"TIMED_KEYFRAME_CONTROL_UNSUPPORTED:{need.need_id}")
        if (plan.structure == "multi_shot" and need.segment_id is not None
                and need.mechanism in {"first_frame", "last_frame"}):
            gaps.append(f"SEGMENT_ENDPOINT_CONTROL_UNSUPPORTED:{need.need_id}")
        if variant is not None and need.need_id in bound:
            if need.mechanism == "reference_video":
                if not any(c.kind == "video" and c.max_count > 0 for c in variant.media_capabilities):
                    gaps.append("CONTINUOUS_MOTION_REFERENCE_UNSUPPORTED")
            elif need.mechanism in {"reference", "first_frame", "last_frame"}:
                asset = next(a for a in requirement.asset_evidence if a.asset_id == bound[need.need_id])
                binding_role = native_role(asset)
                if binding_role not in variant.allowed_image_roles:
                    gaps.append(f"REFERENCE_ROLE_UNSUPPORTED:{binding_role}")
    gaps.extend(risk for risk in plan.risks if risk in {
        "COMPOSITION_HANDOFF_REQUIRED", "MULTI_SHOT_NATIVE_CONTROL_UNDECLARED",
        "STATE_TRANSITION_EVENTS_REQUIRED", "TRANSITION_ENDPOINT_STATES_REQUIRED",
        "SPATIAL_EVENT_STATES_REQUIRED", "PERFORMANCE_BEATS_REQUIRED"})
    return tuple(sorted(set(gaps)))


def reference_strategy_report(requirement, variant=None):
    report = reference_plan_report(requirement.generation_intent)
    _, _, bindings = _requirement_selection(requirement)
    report.update(selected_inputs=[{"need_id": need, "asset_id": asset} for need, asset in bindings],
        execution_asset_count=len(requirement.asset_evidence),
        capability_id=variant.capability_id if variant is not None else None,
        capability_evaluation="evaluated" if variant is not None else "NOT_EVALUATED",
        execution_gaps=list(reference_execution_gaps(requirement, variant)))
    return report


def reference_prompt_issues(requirement, prompt):
    """Authored control duties must survive the selected native text compiler.

    Storyboard states remain creative intent even when their drawings are not
    uploaded. Control metadata is validated by planning/Router, not pasted into
    prose. This check does not claim that the Provider obeys the text.
    """
    authored = requirement.generation_intent.reference_planning
    if authored is None:
        return ()
    _, _, bindings = _requirement_selection(requirement)
    selected = {need for need, _ in bindings}
    issues = []
    for i, anchor in enumerate(authored.anchors):
        if anchor.anchor_id in selected and anchor.purpose not in prompt:
            issues.append(f"generation_intent.reference_planning.anchors.{i}.purpose")
    for i, event in enumerate(authored.events):
        if any(text not in prompt for text in (event.visual_state, event.purpose)):
            issues.append(f"generation_intent.reference_planning.events.{i}")
    for i, text in enumerate(authored.natural_generation):
        if text not in prompt:
            issues.append(f"generation_intent.reference_planning.natural_generation.{i}")
    return tuple(issues)


def reference_revision_advice(diagnosis, expressions, intent):
    """Use diagnosed requirement paths, never infer an observed failure from prose."""
    if "UNKNOWN_OUTCOME" in diagnosis.failure_classes:
        return ("Resolve unknown outcome through the canonical recovery owner; do not resubmit.",)
    if set(diagnosis.failure_classes) & {"EVIDENCE_GAP", "RUBRIC_OR_STAGE_ERROR"}:
        return ("Repair exact-media/rubric evidence before changing the reference strategy.",)
    paths = {p for expression in expressions if expression.requirement_id in diagnosis.failed_requirements
             for p in expression.intent_paths}
    advice = []
    for prefix, recommendation in (
        ("generation_intent.identity_continuity", "Revise the exact identity anchor selection and independent subject coverage."),
        ("generation_intent.performance_intent", "Review key performance beats; preserve successful expressions and gaze."),
        ("generation_intent.subject_action", "Evaluate continuous motion/video or physical previsualization; extra stills cannot prove causality."),
        ("generation_intent.motion_envelope", "Evaluate continuous motion/video or physical previsualization; extra stills cannot prove causality."),
        ("generation_intent.primary_camera_motion", "Review camera-motion reference and endpoint framing compatibility."),
        ("generation_intent.space_continuity", "Revise spatial blocking/occlusion event references."),
        ("generation_intent.reference_planning", "Review the failed reference duties and event states against exact media."),
        ("product_fidelity", "Review canonical product references and controlled product animation/composition."),
    ):
        if any(p == prefix or p.startswith(prefix + ".") for p in paths):
            advice.append(recommendation)
    if diagnosis.failed_requirements:
        advice.append("Preserve observed passing requirements: " + ", ".join(diagnosis.preserved_requirements))
        if intent.reference_planning is not None and intent.reference_planning.structure == "continuous":
            advice.append("Keep the continuous Shot intact; strategy changes require a new authored plan, not automatic splitting.")
    return tuple(dict.fromkeys(advice))
