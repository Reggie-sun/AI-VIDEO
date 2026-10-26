"""Deterministic semantic reference planning. No Provider selection or timeline."""

from ai_video.production.hashing import canonical_sha256
from ai_video.production.reference_planning_contracts import (
    ReferenceNeed, ReferencePlanningIntent, ReferenceRole as Role,
    ShotFacet as Facet, ShotReferencePlan,
)

_MOTION = {Facet.HIGH_SPEED, Facet.CONTACT, Facet.PHYSICS, Facet.COMPLEX_CAMERA}
_SPATIAL = {Facet.BLOCKING, Facet.OCCLUSION, Facet.SPATIAL}
_TRANSITIONS = {Facet.TRANSFORMATION, Facet.DISAPPEARANCE, Facet.ENVIRONMENT_CHANGE}


def plan_shot_references(intent) -> ShotReferencePlan:
    """Use typed facts only; duration never determines image count.

    Legacy intent gets bounded advice. Authored reference_planning opts into
    execution requirements, without inventing semantics from free-form prose.
    """
    authored = intent.reference_planning or ReferencePlanningIntent()
    facets = set(authored.facets)
    camera = intent.primary_camera_motion
    if camera and camera.movement_kind.value != "locked":
        if camera.speed_class.value in {"very_slow", "slow"}:
            facets.add(Facet.SLOW_CAMERA)
        if camera.movement_kind.value.startswith(("orbit", "crane")):
            facets.add(Facet.COMPLEX_CAMERA)
    if intent.dialogue_intent and intent.dialogue_intent.mode != "none":
        facets.add(Facet.DIALOGUE)
    if intent.identity_continuity.character_ids:
        facets.add(Facet.IDENTITY)
    for event in authored.events:
        facets.update({"contact": {Facet.CONTACT}, "impact": {Facet.PHYSICS},
            "force": {Facet.PHYSICS}, "blocking": {Facet.BLOCKING},
            "occlusion": {Facet.OCCLUSION}, "disappearance": {Facet.DISAPPEARANCE},
            "state_change": {Facet.TRANSFORMATION}, "graphic": {Facet.EXACT_GRAPHICS},
            "performance": {Facet.EMOTIONAL_CHANGE}}.get(event.kind, set()))
    needs, omitted, risks, alternatives = [], [], [], []

    def add(need_id, role, scope, purpose, mechanism="reference", priority="preferred", **kw):
        needs.append(ReferenceNeed(need_id=need_id, role=role, scope=scope,
            purpose=purpose, mechanism=mechanism, priority=priority, **kw))

    for anchor in authored.anchors:
        add(anchor.anchor_id, anchor.role, "persistent", anchor.purpose,
            priority=anchor.priority, owner_id=anchor.owner_id)
    anchored = {(n.role, n.owner_id) for n in needs}
    for character_id in intent.identity_continuity.character_ids:
        if (Role.IDENTITY, character_id) not in anchored:
            add(f"auto:identity:{character_id}", Role.IDENTITY, "persistent",
                "Preserve the selected character identity, not an action timestamp.",
                priority="required", owner_id=character_id)
    if intent.scene_continuity and (Role.SCENE, intent.scene_continuity.scene_id) not in anchored:
        add("auto:scene", Role.SCENE, "persistent", "Preserve environment and spatial continuity.",
            owner_id=intent.scene_continuity.scene_id)
    if facets & {Facet.PRODUCT, Facet.PRODUCT_ROTATION} and not any(n.role is Role.PRODUCT for n in needs):
        add("auto:product", Role.PRODUCT, "persistent",
            "Anchor exact product shape, materials and visible structure.", priority="required")
    if facets & {Facet.PRODUCT_ROTATION, Facet.SPATIAL}:
        alternatives.append("Prepare a 3D object/blocking reference when unseen surfaces or exact geometry matter.")

    # Preserve authored event order, including recurrence of the same state.
    # Only adjacent equivalent review states can be coalesced; causal events cannot.
    previous = None
    causal_targets = {predecessor for event in authored.events for predecessor in event.after_event_ids}
    for event in authored.events:
        signature = (event.segment_id, event.phase, event.kind, event.visual_state, event.purpose)
        if (signature == previous and event.control == "review_only"
                and event.kind in {"composition", "performance"}
                and not event.after_event_ids and event.event_id not in causal_targets
                and event.priority == "preferred"):
            omitted.append(f"{event.event_id}: redundant adjacent review state")
            continue
        previous = signature
        mechanism = {"review_only": "review_only", "model_guidance": "reference",
            "endpoint": "first_frame" if event.phase == "start" else "last_frame",
            "exact_time": "exact_time"}[event.control]
        if event.kind == "graphic":
            add(event.event_id, Role.GRAPHICS, "postproduction", event.purpose,
                "composition", "required", event_id=event.event_id)
            continue
        add(event.event_id, Role.POSE if event.kind in {"contact", "force", "impact"} else Role.KEYFRAME,
            "shot_state", f"{event.visual_state} — {event.purpose}", mechanism, event.priority,
            event_id=event.event_id, segment_id=event.segment_id, phase=event.phase,
            at_seconds=event.at_seconds, after_event_ids=event.after_event_ids)

    event_kinds = {event.kind for event in authored.events}
    endpoint = intent.camera_endpoint
    composition_phases = {e.phase for e in authored.events if e.kind == "composition"}
    if (Facet.SLOW_CAMERA in facets
            and endpoint.start_framing != "unspecified" and endpoint.end_framing != "unspecified"
            and endpoint.start_framing != endpoint.end_framing):
        for phase, text in (("start", endpoint.start_framing), ("end", endpoint.end_framing)):
            if phase in composition_phases:
                continue
            add(f"auto:camera:{phase}", Role.KEYFRAME, "shot_state", text,
                "first_frame" if phase == "start" else "last_frame", phase=phase)
    performance_count = sum(e.kind == "performance" for e in authored.events)
    performance = intent.performance_intent
    if performance_count == 0 and performance:
        for direction in performance.character_directions:
            if direction.visibility != "visible" or len(direction.beats) < 2:
                continue
            facets.add(Facet.EMOTIONAL_CHANGE)
            for beat in direction.beats:
                add(f"auto:performance:{direction.character_id}:{beat.phase}", Role.KEYFRAME,
                    "shot_state", f"{beat.trigger}: {beat.emotion}; {beat.gaze_target}; {beat.body_behavior}",
                    "review_only", owner_id=direction.character_id,
                    phase={"opening": "start", "response": "interior", "settle": "end"}[beat.phase])
                performance_count += 1
    if Facet.EMOTIONAL_CHANGE in facets and performance_count < 2:
        risks.append("PERFORMANCE_BEATS_REQUIRED")
    if facets & _TRANSITIONS:
        transitions = [e for e in authored.events if e.kind in {"state_change", "appearance", "disappearance"}]
        phases = {e.phase for e in transitions}
        if "start" not in phases and intent.subject_action.start_state != "unspecified":
            add("auto:state:start", Role.KEYFRAME, "shot_state", intent.subject_action.start_state,
                "review_only", phase="start")
            phases.add("start")
        if "end" not in phases and intent.subject_action.endpoint.state_text:
            add("auto:state:end", Role.KEYFRAME, "shot_state", intent.subject_action.endpoint.state_text,
                "review_only", phase="end")
            phases.add("end")
        if not {"start", "end"}.issubset(phases):
            risks.append("TRANSITION_ENDPOINT_STATES_REQUIRED" if transitions else "STATE_TRANSITION_EVENTS_REQUIRED")
    spatial_coverage = {Facet.BLOCKING: {"blocking"}, Facet.OCCLUSION: {"occlusion"},
                        Facet.SPATIAL: {"blocking", "occlusion", "composition"}}
    if any(facet in facets and not event_kinds.intersection(kinds)
           for facet, kinds in spatial_coverage.items()):
        risks.append("SPATIAL_EVENT_STATES_REQUIRED")

    if facets & _MOTION:
        add("auto:motion", Role.MOTION, "continuous_motion",
            "Constrain continuous camera/action trajectory and causal contact order; isolated poses are insufficient.",
            "reference_video", "required")
        add("auto:previs", Role.BLOCKING, "preparation",
            "Prepare continuous physical/camera blocking if suitable motion footage is unavailable.",
            "previsualization")
        risks.append("MOTION_REFERENCE_IS_GUIDANCE_NOT_PHYSICS_PROOF")
        alternatives.extend(("Use an authorized motion video or rendered physical/camera previsualization.",
                             "Consider the existing video-edit or controlled animation path; retain continuous Shot intent."))
    elif facets & _SPATIAL:
        add("auto:blocking", Role.BLOCKING, "preparation",
            "Review crossings, relative positions and occlusions before selecting reference inputs.",
            "previsualization")
        alternatives.append("Evaluate a blocking video when static spatial states do not constrain the trajectory.")
    if Facet.EXACT_GRAPHICS in facets:
        if not any(n.role is Role.GRAPHICS for n in needs):
            add("auto:graphics", Role.GRAPHICS, "postproduction",
                "Render exact text, logo and graphic animation through the existing composition owner.",
                "composition", "required")
        risks.append("COMPOSITION_HANDOFF_REQUIRED")
        alternatives.append("Use existing CompositionSpec/HyperFrames and authored graphic assets.")
    if authored.structure == "multi_shot":
        risks.append("MULTI_SHOT_NATIVE_CONTROL_UNDECLARED")
        alternatives.append("Keep the authored segment order for Director review; use explicit Storyboard Shots if native cuts are unsupported.")
    if not any(n.scope == "shot_state" for n in needs):
        omitted.append("No visual event requires an additional temporal image; duration alone adds none.")
    omitted.extend(("Persistent identity/environment/style assets are excluded from keyframe density.",
                    "Provider input maxima are not recommended reference counts."))
    natural = authored.natural_generation or (
        ("Interpolate between authored visual states; no strict time or physical guarantee is inferred.",)
        if any(n.scope == "shot_state" for n in needs) else
        ("Allow ordinary micro-expression, ambience and noncritical motion within the authored intent.",))
    return ShotReferencePlan(source_intent_hash=canonical_sha256(intent.model_dump(mode="json")),
        facets=tuple(sorted(facets, key=lambda f: f.value)), structure=authored.structure,
        needs=tuple(needs), natural_generation=natural, omitted=tuple(omitted),
        risks=tuple(sorted(set(risks))), alternatives=tuple(dict.fromkeys(alternatives)))


def reference_plan_report(intent):
    plan = plan_shot_references(intent)
    return {**plan.model_dump(mode="json"), "keyframe_count": len(plan.keyframes),
            "image_reference_needed": plan.image_reference_needed,
            "enforcement": "authored" if intent.reference_planning is not None else "legacy_advisory"}
