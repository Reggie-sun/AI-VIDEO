"""Fresh-generation reference-planning obligations.

The Director layer decides Shot type, reference duties, whitebox use and what a
camera move should reveal. This module only checks that those decisions were
declared before a new generation; it never judges their quality and never runs
on history reads, so legacy requests reopen unchanged.

Structured reference planning is shared by every genre. Director evidence stays
per domain: drama binds exact Director coverage sealed in the Project, while
ecommerce binds its own AdCreativePlan through the commercial request binding,
which the commercial owners verify. Neither domain borrows the other's layer.
"""
from ai_video.errors import AiVideoError, ErrorCode

_ROOT = "generation_intent.reference_planning"
_UNCOMPILED = object()


def _camera_moves(intent) -> bool:
    motion = intent.primary_camera_motion
    return motion is not None and motion.movement_kind.value != "locked"


def is_ecommerce_requirement(requirement, commercial_binding=None) -> bool:
    return (commercial_binding is not None and commercial_binding is not _UNCOMPILED) or (
        getattr(requirement, "commercial_execution_class", None) is not None)


def reference_authoring_issues(intent, *, ecommerce: bool = False) -> tuple[str, ...]:
    authored = intent.reference_planning
    if authored is None:
        return (_ROOT,)
    issues = []
    if _camera_moves(intent) and not any(event.kind == "composition" for event in authored.events):
        # A moving camera must name the visible relation it changes; the existing
        # compiler then requires that visual_state/purpose in the native text.
        issues.append(f"{_ROOT}.events[composition]")
    if ecommerce:
        if authored.director_coverage is not None:
            issues.append(f"{_ROOT}.director_coverage[ecommerce_uses_ad_creative_plan]")
    elif authored.director_coverage is None:
        issues.append(f"{_ROOT}.director_coverage")
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
        issues.extend(director_coverage_evidence_issues(intent.reference_planning.director_coverage, project))
    if issues:
        raise AiVideoError(code=ErrorCode.VIDEO_REQUEST_INVALID,
            user_message="Author Director reference planning before new generation: " + ", ".join(issues))


__all__ = ["director_coverage_authoring_input", "director_coverage_evidence_issues", "is_ecommerce_requirement",
           "reference_authoring_issues", "require_reference_authoring"]
