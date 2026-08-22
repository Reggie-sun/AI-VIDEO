"""Strict independent Q0 human-review evidence projection."""

from pathlib import Path

from ai_video.production.hashing import canonical_sha256
from ai_video.production.paths import _read_regular_file_nofollow
from ai_video.production.review import (
    GeneratedShotContinuityEvidence,
    TrackedGeneratedShotContinuityMeasurements,
)
from ai_video.quality_intelligence._capture_contracts import (
    CaptureErrorCode,
    PostQaHumanReviewDocument,
    PostQaHumanReviewMetadata,
    QualityExperienceCaptureError,
)
from ai_video.quality_intelligence.models import (
    EvidenceState,
    EvidenceString,
    EvidenceTimestamp,
    HumanReviewBinding,
    HumanReviewStatus,
    RubricItems,
)


def _reject() -> QualityExperienceCaptureError:
    return QualityExperienceCaptureError(CaptureErrorCode.BINDING_INVALID)


def _not_reviewed() -> HumanReviewBinding:
    reason = "independent_q0_human_review_not_supplied"
    not_applicable = EvidenceString(
        state=EvidenceState.NOT_APPLICABLE, reason=reason
    )
    return HumanReviewBinding(
        status=HumanReviewStatus.NOT_REVIEWED,
        reviewer_id=not_applicable,
        reviewer_kind=not_applicable,
        rubric_id="continuity_fallback_v1",
        rubric_version="1",
        rubric_hash=canonical_sha256(
            {"domain": "ai-video.q0.continuity-rubric/v1"}
        ),
        watched_at=EvidenceTimestamp(state="not_applicable", reason=reason),
        items=RubricItems(),
    )


def build_human_review(
    metadata: PostQaHumanReviewMetadata | None,
    document: PostQaHumanReviewDocument | None,
    project_root: Path,
    evidence: GeneratedShotContinuityEvidence,
) -> HumanReviewBinding:
    if metadata is None:
        return _not_reviewed()
    if document is None:
        raise _reject()
    measurements = evidence.raw_measurements
    fallback = (
        measurements.fallback_evidence
        if isinstance(measurements, TrackedGeneratedShotContinuityMeasurements)
        else None
    )
    if fallback is None:
        raise _reject()
    reopened = _read_regular_file_nofollow(
        project_root / document.relative_path,
        contained_by=project_root / "reviews",
    )
    if (
        reopened.file_sha256 != document.file_sha256
        or document.evaluation_fingerprint != evidence.evaluation_fingerprint
        or document.human_fallback_hash != fallback.content_hash
        or PostQaHumanReviewMetadata.model_validate_json(reopened.data) != metadata
        or metadata.reviewer_id.source_document != document.relative_path
        or metadata.reviewer_id.source_span != "reviewer.id"
        or metadata.reviewer_kind.source_document != document.relative_path
        or metadata.reviewer_kind.source_span != "reviewer.kind"
        or metadata.watched_at.source_document != document.relative_path
        or metadata.watched_at.source_span != "watched_at"
    ):
        raise _reject()
    expected = {
        "camera_axis": fallback.camera_axis_match,
        "entrance_state": fallback.entrance_state_match,
        "exit_state": fallback.exit_state_match,
        "framing": fallback.framing_match,
        "identity": fallback.identity_match,
        "motion_direction": fallback.motion_direction_match,
        "unexpected_reentry": not fallback.unexpected_reentry,
    }
    actual = {item.item_id: item.verdict for item in metadata.items.items}
    if set(actual) != set(expected) or any(
        actual[key] != ("pass" if matches else "fail")
        for key, matches in expected.items()
    ):
        raise _reject()
    if any(
        item.state is not EvidenceState.KNOWN
        for item in (metadata.reviewer_id, metadata.reviewer_kind)
    ) or metadata.watched_at.state != "known":
        raise _reject()
    return HumanReviewBinding(
        status=(
            HumanReviewStatus.GO
            if all(expected.values())
            else HumanReviewStatus.NO_GO
        ),
        reviewer_id=metadata.reviewer_id,
        reviewer_kind=metadata.reviewer_kind,
        rubric_id=metadata.rubric_id,
        rubric_version=metadata.rubric_version,
        rubric_hash=metadata.rubric_hash,
        watched_at=metadata.watched_at,
        items=metadata.items,
    )


__all__ = ["build_human_review"]
