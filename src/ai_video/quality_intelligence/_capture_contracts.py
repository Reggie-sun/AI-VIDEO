"""Typed caller-owned context for explicit post-QA Q0 capture."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import Field, model_validator

from ai_video.quality_intelligence.models import (
    AnalyzerBinding,
    AttemptKind,
    BoundedFreeText,
    EvidenceString,
    EvidenceTimestamp,
    InterventionBinding,
    QualityRecordPointer,
    RubricItems,
    StrictModel,
)
from ai_video.quality_intelligence.store import QualityExperienceError


class CaptureErrorCode(str, Enum):
    NOT_READY = "QUALITY_EXPERIENCE_CAPTURE_NOT_READY"
    BINDING_INVALID = "QUALITY_EXPERIENCE_CAPTURE_BINDING_INVALID"
    PRIVACY_REJECTED = "QUALITY_EXPERIENCE_CAPTURE_PRIVACY_REJECTED"


class QualityExperienceCaptureError(QualityExperienceError):
    """Sanitized capture failure that never embeds rejected runtime values."""

    def __init__(self, code: CaptureErrorCode) -> None:
        self.code = code.value
        super().__init__("post-QA capture rejected")


class PostQaHumanReviewMetadata(StrictModel):
    reviewer_id: EvidenceString
    reviewer_kind: EvidenceString
    rubric_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    rubric_version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    rubric_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    watched_at: EvidenceTimestamp
    items: RubricItems


class PostQaHumanReviewDocument(StrictModel):
    relative_path: str
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evaluation_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    human_fallback_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _require_review_relative_path(self) -> "PostQaHumanReviewDocument":
        path = Path(self.relative_path)
        if (
            path.is_absolute()
            or not path.parts
            or path.parts[0] != "reviews"
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("human review document must be a clean reviews path")
        return self


class PostQaAnalyzerDocument(StrictModel):
    relative_path: str
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")

    @model_validator(mode="after")
    def _require_analysis_relative_path(self) -> "PostQaAnalyzerDocument":
        path = Path(self.relative_path)
        if (
            path.is_absolute()
            or not path.parts
            or path.parts[0] != "analysis"
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("analyzer document must be a clean analysis path")
        return self


class PostQaQ0CaptureRequest(StrictModel):
    project_root: Path = Field(repr=False)
    attempt_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    pilot_dataset_root: Path = Field(repr=False)
    experiment_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    pilot_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    captured_at: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
    )
    repository_commit: str = Field(pattern=r"^[0-9a-f]{40,64}$")
    purpose: BoundedFreeText
    hypothesis: BoundedFreeText
    capture_actor: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
    authorization_boundary: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
    )
    attempt_sequence: int = Field(ge=1)
    attempt_kind: AttemptKind
    predecessor: QualityRecordPointer | None = None
    analyzer: AnalyzerBinding
    analyzer_documents: tuple[PostQaAnalyzerDocument, ...]
    human_review: PostQaHumanReviewMetadata | None = None
    human_review_document: PostQaHumanReviewDocument | None = None
    intervention: InterventionBinding
    allowed_conclusions: tuple[BoundedFreeText, ...] = Field(min_length=1)
    forbidden_extrapolations: tuple[BoundedFreeText, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _pair_human_review_document(self) -> "PostQaQ0CaptureRequest":
        if (self.human_review is None) != (self.human_review_document is None):
            raise ValueError("human review metadata requires its exact document")
        return self


__all__ = [
    "CaptureErrorCode",
    "PostQaAnalyzerDocument",
    "PostQaHumanReviewDocument",
    "PostQaHumanReviewMetadata",
    "PostQaQ0CaptureRequest",
    "QualityExperienceCaptureError",
]
