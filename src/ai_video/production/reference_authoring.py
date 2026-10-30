"""Fresh-generation reference-planning obligations.

The Director layer decides Shot type, reference duties, whitebox use and what a
camera move should reveal. This module only checks that those decisions were
declared before a new generation; it never judges their quality and never runs
on history reads, so legacy requests reopen unchanged.

Structured reference planning is shared by every genre. Director evidence stays
per domain: drama binds exact Director coverage sealed in the Project, while
ecommerce binds its own AdCreativePlan through the commercial request binding,
which the commercial owners verify. Neither domain borrows the other's layer.

Two obligations close shortcuts observed in practice (2026-10-30): drama must
bind the user's approval of a cheap visual preview before paid generation, and a
visibly performing character cannot be left out of identity continuity, because
that silently removes the identity reference the planner would otherwise require.
"""
from ai_video.errors import AiVideoError, ErrorCode

_ROOT = "generation_intent.reference_planning"
_UNCOMPILED = object()


# Exact tokens the native compilers already accept as a locked or unauthored camera.
_STILL_CAMERA_TOKENS = frozenset({"unspecified", "locked", "locked-off"})


def _camera_moves(intent) -> bool:
    """Structured motion decides when present; v1-v3 requirements cannot carry it.

    Without ``primary_camera_motion`` any camera prose other than the exact still
    tokens may describe movement, so the Director must state what it reveals. The
    prose itself is never parsed for meaning.
    """
    motion = intent.primary_camera_motion
    if motion is not None:
        return motion.movement_kind.value != "locked"
    camera = intent.camera_intent
    return camera is not None and camera.movement not in _STILL_CAMERA_TOKENS


def is_ecommerce_requirement(requirement, commercial_binding=None) -> bool:
    return (commercial_binding is not None and commercial_binding is not _UNCOMPILED) or (
        getattr(requirement, "commercial_execution_class", None) is not None)


def _visible_performers(intent) -> tuple[str, ...]:
    performance = intent.performance_intent
    if performance is None:
        return ()
    return tuple(direction.character_id for direction in performance.character_directions
                 if direction.visibility == "visible")


def reference_authoring_issues(intent, *, ecommerce: bool = False) -> tuple[str, ...]:
    authored = intent.reference_planning
    if authored is None:
        return (_ROOT,)
    issues = []
    identities = set(intent.identity_continuity.character_ids)
    for character_id in _visible_performers(intent):
        if character_id not in identities:
            # Dropping a performer from identity continuity is how a Shot dodges the
            # identity reference; the Director must prepare that reference instead.
            issues.append(f"generation_intent.identity_continuity.character_ids[{character_id}]")
    if _camera_moves(intent) and not any(event.kind == "composition" for event in authored.events):
        # A moving camera must name the visible relation it changes; the existing
        # compiler then requires that visual_state/purpose in the native text.
        issues.append(f"{_ROOT}.events[composition]")
    if ecommerce:
        if authored.director_coverage is not None:
            issues.append(f"{_ROOT}.director_coverage[ecommerce_uses_ad_creative_plan]")
    else:
        if authored.director_coverage is None:
            issues.append(f"{_ROOT}.director_coverage")
        if authored.preview_approval is None:
            issues.append(f"{_ROOT}.preview_approval")
    return tuple(issues)


def director_coverage_evidence_issues(binding, project) -> tuple[str, ...]:
    """Reopen the exact content-addressed coverage sealed into Project provenance."""
    from ai_video.production.authoring_input import PREFIX, reopen_authoring_input
    from ai_video.production.director_coverage import CoverageValidationError, validate_director_coverage
    from ai_video.production.models import SourceReference

    path = f"{_ROOT}.director_coverage"
    reference = SourceReference(kind="user_input", reference=f"{PREFIX}{binding.coverage_hash}.json",
                                content_hash=binding.coverage_hash)
    sealed = {*project.project.source_provenance,
              *(item for shot in project.shots for item in shot.source_provenance)}
    if reference not in sealed:
        return (f"{path}.coverage_hash",)
    try:
        coverage = reopen_authoring_input(project.root, reference)
        validate_director_coverage(coverage)
    except (CoverageValidationError, ValueError, OSError):
        return (f"{path}.coverage_hash",)
    if binding.unit_id not in {unit.get("unit_id") for unit in coverage["coverage_units"]}:
        return (f"{path}.unit_id",)
    return ()


def preview_approval_evidence_issues(binding, coverage, project) -> tuple[str, ...]:
    """Reopen the sealed user preview approval and bind it to this exact coverage unit."""
    from ai_video.production.authoring_input import PREFIX, reopen_authoring_input
    from ai_video.production.models import SourceReference
    from ai_video.production.preview_approval import PreviewApprovalError, validate_preview_approval

    path = f"{_ROOT}.preview_approval.approval_hash"
    reference = SourceReference(kind="user_input", reference=f"{PREFIX}{binding.approval_hash}.json",
                                content_hash=binding.approval_hash)
    sealed = {*project.project.source_provenance,
              *(item for shot in project.shots for item in shot.source_provenance)}
    if reference not in sealed:
        return (path,)
    try:
        approval = reopen_authoring_input(project.root, reference)
        validate_preview_approval(approval)
    except (PreviewApprovalError, ValueError, OSError):
        return (path,)
    if approval["coverage_hash"] != coverage.coverage_hash or coverage.unit_id not in approval["unit_ids"]:
        return (f"{_ROOT}.preview_approval[coverage_unit]",)
    return ()


def director_coverage_authoring_input(coverage):
    """Validate drama Director coverage and return its sealable authoring input.

    Pass the artifact to an existing authoring/bootstrap owner (for Canvas,
    ``author_canvas_project(asset_artifacts=...)``); bind ``coverage_hash`` in the
    Shot's ``reference_planning.director_coverage``. Nothing is written here.
    """
    import hashlib
    from pathlib import Path

    from ai_video.production.authoring_input import authoring_input_payload, authoring_input_reference
    from ai_video.production.director_coverage import validate_director_coverage
    from ai_video.production.state_commit import PreparedArtifact

    validate_director_coverage(coverage)
    reference = authoring_input_reference(coverage)
    payload = authoring_input_payload(coverage)
    return reference.content_hash, PreparedArtifact(Path(reference.reference), payload,
                                                    hashlib.sha256(payload).hexdigest())


def require_reference_authoring(requirement, *, project=None, commercial_binding=_UNCOMPILED) -> None:
    """Structural obligations always; exact evidence whenever its owner input is supplied.

    Before compilation the commercial binding is unknown; at execution-binding
    creation an ecommerce requirement must already be bound to its AdCreativePlan.
    """
    ecommerce = is_ecommerce_requirement(requirement, commercial_binding)
    intent = requirement.generation_intent
    issues = list(reference_authoring_issues(intent, ecommerce=ecommerce))
    if ecommerce:
        if commercial_binding is None:
            issues.append("commercial_binding.ad_creative_plan_hash")
    elif not issues and project is not None:
        planning = intent.reference_planning
        issues.extend(director_coverage_evidence_issues(planning.director_coverage, project))
        if not issues:
            issues.extend(preview_approval_evidence_issues(planning.preview_approval,
                                                           planning.director_coverage, project))
    if issues:
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Author Director reference planning before new generation: " + ", ".join(issues))


__all__ = ["director_coverage_authoring_input", "director_coverage_evidence_issues", "is_ecommerce_requirement",
           "preview_approval_evidence_issues", "reference_authoring_issues", "require_reference_authoring"]
