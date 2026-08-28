"""Typed, side-effect-free contracts for caption-specific Production QA."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.hashing import canonical_sha256


_SHA256 = r"^[0-9a-f]{64}$"


class CaptionRequirementGroup(str, Enum):
    SOURCE_INTEGRITY = "source_integrity"
    TIMING_CONTRACT = "timing_contract"
    RENDER_COMPLETENESS = "render_completeness"
    LAYOUT_READABILITY = "layout_readability"
    AUDIO_SEMANTIC_SYNC = "audio_semantic_sync"
    UNINTENDED_TEXT = "unintended_text"


CAPTION_REQUIREMENT_GROUPS = tuple(CaptionRequirementGroup)

FINAL_MEDIA_REQUIREMENT_GROUPS = frozenset(
    {
        CaptionRequirementGroup.RENDER_COMPLETENESS,
        CaptionRequirementGroup.LAYOUT_READABILITY,
        CaptionRequirementGroup.AUDIO_SEMANTIC_SYNC,
        CaptionRequirementGroup.UNINTENDED_TEXT,
    }
)


class CaptionEvidenceStrength(str, Enum):
    MEASURED = "measured"
    RENDERER_BOUND = "renderer_bound"
    EXPLICIT_EVALUATOR = "explicit_evaluator"
    HUMAN = "human"


class CaptionCoverageStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class CaptionFindingReasonCode(str, Enum):
    REQUIREMENT_CONFIRMED = "requirement_confirmed"
    SOURCE_IDENTITY_MISMATCH = "source_identity_mismatch"
    TIMING_OUT_OF_BOUNDS = "timing_out_of_bounds"
    RENDER_CONTENT_MISMATCH = "render_content_mismatch"
    LAYOUT_UNREADABLE = "layout_unreadable"
    AUDIO_SYNC_MISMATCH = "audio_sync_mismatch"
    UNINTENDED_TEXT_DETECTED = "unintended_text_detected"
    COVERAGE_PARTIAL = "coverage_partial"
    UNSUPPORTED_LANGUAGE_OR_TOOL = "unsupported_language_or_tool"
    LOW_CONFIDENCE = "low_confidence"
    IDENTITY_MISMATCH = "identity_mismatch"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class CaptionTrackPolicy(StrictModel):
    caption_track_id: str = Field(min_length=1)
    language_tag: str = Field(min_length=1)
    max_lines_per_cue: int = Field(strict=True, gt=0)
    max_graphemes_per_line: int = Field(strict=True, gt=0)
    max_reading_rate_milli_graphemes_per_second: int = Field(strict=True, gt=0)
    min_cue_duration_milliseconds: int = Field(strict=True, ge=0)
    max_cue_duration_milliseconds: int = Field(strict=True, gt=0)
    max_audio_sync_offset_milliseconds: int = Field(strict=True, ge=0)
    caption_overflow_tolerance_milli: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def _validate_duration_bounds(self) -> "CaptionTrackPolicy":
        if self.max_cue_duration_milliseconds < self.min_cue_duration_milliseconds:
            raise ValueError("caption cue duration policy bounds are inverted")
        return self


class CaptionEvidenceAuthority(StrictModel):
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    requirement_groups: tuple[CaptionRequirementGroup, ...] = Field(min_length=1)
    allowed_strengths: tuple[CaptionEvidenceStrength, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_authority(self) -> "CaptionEvidenceAuthority":
        if len(set(self.requirement_groups)) != len(self.requirement_groups):
            raise ValueError("caption evidence authority groups must be unique")
        if len(set(self.allowed_strengths)) != len(self.allowed_strengths):
            raise ValueError("caption evidence authority strengths must be unique")
        if FINAL_MEDIA_REQUIREMENT_GROUPS.intersection(
            self.requirement_groups
        ) and not set(self.allowed_strengths).issubset(
            {
                CaptionEvidenceStrength.EXPLICIT_EVALUATOR,
                CaptionEvidenceStrength.HUMAN,
            }
        ):
            raise ValueError(
                "caption final-media groups require explicit evaluator or human evidence"
            )
        return self


class CaptionQualityPolicy(StrictModel):
    contract_version: Literal["caption-quality-policy/1"] = "caption-quality-policy/1"
    delivery_profile_fingerprint: str = Field(pattern=_SHA256)
    measurement_contract_version: str = Field(min_length=1)
    required_groups: tuple[CaptionRequirementGroup, ...] = CAPTION_REQUIREMENT_GROUPS
    track_policies: tuple[CaptionTrackPolicy, ...] = Field(min_length=1)
    evidence_authorities: tuple[CaptionEvidenceAuthority, ...] = Field(min_length=1)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_policy(self) -> "CaptionQualityPolicy":
        if self.required_groups != CAPTION_REQUIREMENT_GROUPS:
            raise ValueError("caption policy must require all six canonical groups in order")
        track_ids = tuple(item.caption_track_id for item in self.track_policies)
        if len(set(track_ids)) != len(track_ids):
            raise ValueError("caption track policies must be unique")
        authorized_groups = {
            group
            for authority in self.evidence_authorities
            for group in authority.requirement_groups
        }
        if authorized_groups != set(CAPTION_REQUIREMENT_GROUPS):
            raise ValueError("caption policy must authorize evidence for every group")
        expected_hash = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected_hash:
            raise ValueError("caption policy content hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "CaptionQualityPolicy":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    provisional.model_dump(
                        mode="json", exclude={"content_hash"}, warnings=False
                    )
                ),
            }
        )


class CaptionTrackReviewBinding(StrictModel):
    caption_asset_id: str = Field(min_length=1)
    caption_asset_sha256: str = Field(pattern=_SHA256)
    caption_track_id: str = Field(min_length=1)
    language_tag: str = Field(min_length=1)
    timing_fingerprint: str = Field(pattern=_SHA256)
    style_reference_id: str | None = None
    style_content_hash: str | None = Field(default=None, pattern=_SHA256)
    source_audio_track_id: str = Field(min_length=1)
    source_audio_asset_id: str = Field(min_length=1)
    source_audio_sha256: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_style_identity(self) -> "CaptionTrackReviewBinding":
        if (self.style_reference_id is None) != (self.style_content_hash is None):
            raise ValueError("caption review style identity must be all-or-none")
        return self


class CaptionCueSubject(StrictModel):
    subject_id: str = Field(pattern=_SHA256)
    caption_track_id: str = Field(min_length=1)
    segment_id: str = Field(min_length=1)
    text_sha256: str = Field(pattern=_SHA256)
    speaker_id: str | None = None
    start_sample: int = Field(strict=True, ge=0)
    end_sample: int = Field(strict=True, gt=0)
    start_frame: int = Field(strict=True, ge=0)
    end_frame_exclusive: int = Field(strict=True, gt=0)
    style_reference_id: str | None = None
    style_content_hash: str | None = Field(default=None, pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "CaptionCueSubject":
        if self.end_sample <= self.start_sample:
            raise ValueError("caption cue subject sample bounds are invalid")
        if self.end_frame_exclusive <= self.start_frame:
            raise ValueError("caption cue subject frame bounds are invalid")
        if (self.style_reference_id is None) != (self.style_content_hash is None):
            raise ValueError("caption cue subject style identity must be all-or-none")
        return self


class CaptionGroupCoverageDomain(StrictModel):
    requirement_group: CaptionRequirementGroup
    subject_ids: tuple[str, ...] = Field(min_length=1)
    start_frame: int = Field(strict=True, ge=0)
    end_frame_exclusive: int = Field(strict=True, gt=0)
    frame_width: int = Field(strict=True, gt=0)
    frame_height: int = Field(strict=True, gt=0)
    content_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_domain(self) -> "CaptionGroupCoverageDomain":
        if self.end_frame_exclusive <= self.start_frame:
            raise ValueError("caption coverage domain frame bounds are invalid")
        if len(set(self.subject_ids)) != len(self.subject_ids):
            raise ValueError("caption coverage domain subjects must be unique")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("caption coverage domain hash is invalid")
        return self

    @classmethod
    def create(cls, **values: object) -> "CaptionGroupCoverageDomain":
        provisional = cls.model_construct(**values, content_hash="0" * 64)
        return cls.model_validate(
            {
                **values,
                "content_hash": canonical_sha256(
                    provisional.model_dump(
                        mode="json", exclude={"content_hash"}, warnings=False
                    )
                ),
            }
        )


class ApprovedNonCaptionText(StrictModel):
    text_identity: str = Field(pattern=_SHA256)
    start_frame: int = Field(strict=True, ge=0)
    end_frame_exclusive: int = Field(strict=True, gt=0)
    region_identity: str = Field(pattern=_SHA256)


class CaptionReviewContext(StrictModel):
    contract_version: Literal["caption-review-context/1"] = "caption-review-context/1"
    caption_policy_hash: str = Field(pattern=_SHA256)
    measurement_contract_version: str = Field(min_length=1)
    caption_tracks: tuple[CaptionTrackReviewBinding, ...] = Field(min_length=1)
    cue_subjects: tuple[CaptionCueSubject, ...] = Field(min_length=1)
    coverage_domains: tuple[CaptionGroupCoverageDomain, ...] = Field(min_length=1)
    approved_non_caption_text: tuple[ApprovedNonCaptionText, ...] = ()
    timeline_fingerprint: str = Field(pattern=_SHA256)
    render_output_sha256: str = Field(pattern=_SHA256)
    dependency_graph_revision_id: str = Field(pattern=_SHA256)
    expected_cue_coverage_manifest_hash: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_context(self) -> "CaptionReviewContext":
        track_ids = tuple(item.caption_track_id for item in self.caption_tracks)
        if len(set(track_ids)) != len(track_ids):
            raise ValueError("caption review tracks must be unique")
        subject_ids = tuple(item.subject_id for item in self.cue_subjects)
        if len(set(subject_ids)) != len(subject_ids):
            raise ValueError("caption cue subjects must be unique")
        if any(item.caption_track_id not in set(track_ids) for item in self.cue_subjects):
            raise ValueError("caption cue subject references an unknown track")
        groups = tuple(item.requirement_group for item in self.coverage_domains)
        if groups != CAPTION_REQUIREMENT_GROUPS:
            raise ValueError("caption context must define all six coverage domains in order")
        cue_roster = set(subject_ids)
        for domain in self.coverage_domains:
            if domain.requirement_group is CaptionRequirementGroup.UNINTENDED_TEXT:
                continue
            if set(domain.subject_ids) != cue_roster:
                raise ValueError("caption cue coverage domain does not match exact cue roster")
        expected_manifest_hash = canonical_sha256({"subject_ids": subject_ids})
        if self.expected_cue_coverage_manifest_hash != expected_manifest_hash:
            raise ValueError("caption cue coverage manifest hash is invalid")
        return self


class CaptionRequirementFinding(StrictModel):
    requirement_group: CaptionRequirementGroup
    verdict: Literal["pass", "fail", "not_evaluated"]
    reason_code: CaptionFindingReasonCode
    covered_subject_ids: tuple[str, ...] = ()
    raw_evidence_references: tuple[str, ...] = Field(min_length=1)
    coverage_status: CaptionCoverageStatus
    observation_fingerprint: str = Field(pattern=_SHA256)

    @model_validator(mode="after")
    def _validate_finding(self) -> "CaptionRequirementFinding":
        if len(set(self.covered_subject_ids)) != len(self.covered_subject_ids):
            raise ValueError("caption finding covered subjects must be unique")
        if self.verdict == "pass" and self.coverage_status is not CaptionCoverageStatus.COMPLETE:
            raise ValueError("caption PASS finding requires complete coverage")
        if (
            self.verdict == "pass"
            and self.reason_code is not CaptionFindingReasonCode.REQUIREMENT_CONFIRMED
        ):
            raise ValueError("caption PASS finding requires confirmed evidence")
        return self


class CaptionEvidencePayload(StrictModel):
    contract_version: Literal["caption-evidence/1"] = "caption-evidence/1"
    caption_policy_hash: str = Field(pattern=_SHA256)
    caption_context_hash: str = Field(pattern=_SHA256)
    findings: tuple[CaptionRequirementFinding, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_findings(self) -> "CaptionEvidencePayload":
        groups = tuple(item.requirement_group for item in self.findings)
        if len(set(groups)) != len(groups):
            raise ValueError("caption evidence cannot contain duplicate requirement groups")
        return self
