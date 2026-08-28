from __future__ import annotations

import pytest

from ai_video.production.caption_quality import (
    adjudicate_caption_review_evidence,
    caption_context_hash,
)
from ai_video.production.caption_quality_contracts import (
    CAPTION_REQUIREMENT_GROUPS,
    CaptionCoverageStatus,
    CaptionCueSubject,
    CaptionEvidenceAuthority,
    CaptionEvidencePayload,
    CaptionEvidenceStrength,
    CaptionFindingReasonCode,
    CaptionGroupCoverageDomain,
    CaptionQualityPolicy,
    CaptionRequirementFinding,
    CaptionRequirementGroup,
    CaptionReviewContext,
    CaptionTrackPolicy,
    CaptionTrackReviewBinding,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaVerdict,
    ReviewEvidence,
    SourceReference,
    ToolIdentity,
)


ZERO_HASH = "0" * 64


def _caption_policy() -> CaptionQualityPolicy:
    return CaptionQualityPolicy.create(
        delivery_profile_fingerprint="1" * 64,
        measurement_contract_version="caption-measurements/1",
        track_policies=(
            CaptionTrackPolicy(
                caption_track_id="captions-zh",
                language_tag="zh-Hans",
                max_lines_per_cue=2,
                max_graphemes_per_line=18,
                max_reading_rate_milli_graphemes_per_second=8_000,
                min_cue_duration_milliseconds=300,
                max_cue_duration_milliseconds=8_000,
                max_audio_sync_offset_milliseconds=150,
                caption_overflow_tolerance_milli=0,
            ),
        ),
        evidence_authorities=(
            CaptionEvidenceAuthority(
                tool_name="renderer-audit",
                tool_version="1",
                requirement_groups=CAPTION_REQUIREMENT_GROUPS[:2],
                allowed_strengths=(
                    CaptionEvidenceStrength.MEASURED,
                    CaptionEvidenceStrength.RENDERER_BOUND,
                ),
            ),
            CaptionEvidenceAuthority(
                tool_name="final-media-evaluator",
                tool_version="1",
                requirement_groups=CAPTION_REQUIREMENT_GROUPS[2:],
                allowed_strengths=(CaptionEvidenceStrength.EXPLICIT_EVALUATOR,),
            ),
        ),
    )


def _context(policy: CaptionQualityPolicy) -> CaptionReviewContext:
    cue_id = "2" * 64
    whole_render_id = "3" * 64
    domains = tuple(
        CaptionGroupCoverageDomain.create(
            requirement_group=group,
            subject_ids=(
                (whole_render_id,)
                if group is CaptionRequirementGroup.UNINTENDED_TEXT
                else (cue_id,)
            ),
            start_frame=0,
            end_frame_exclusive=48,
            frame_width=1080,
            frame_height=1920,
        )
        for group in CAPTION_REQUIREMENT_GROUPS
    )
    return CaptionReviewContext(
        caption_policy_hash=policy.content_hash,
        measurement_contract_version=policy.measurement_contract_version,
        caption_tracks=(
            CaptionTrackReviewBinding(
                caption_asset_id="caption-asset",
                caption_asset_sha256="4" * 64,
                caption_track_id="captions-zh",
                language_tag="zh-Hans",
                timing_fingerprint="5" * 64,
                style_reference_id="caption-style",
                style_content_hash="6" * 64,
                source_audio_track_id="dialogue-track",
                source_audio_asset_id="dialogue-asset",
                source_audio_sha256="7" * 64,
            ),
        ),
        cue_subjects=(
            CaptionCueSubject(
                subject_id=cue_id,
                caption_track_id="captions-zh",
                segment_id="segment-1",
                text_sha256="8" * 64,
                start_sample=0,
                end_sample=48_000,
                start_frame=0,
                end_frame_exclusive=24,
                style_reference_id="caption-style",
                style_content_hash="6" * 64,
            ),
        ),
        coverage_domains=domains,
        timeline_fingerprint="9" * 64,
        render_output_sha256="a" * 64,
        dependency_graph_revision_id="b" * 64,
        expected_cue_coverage_manifest_hash=canonical_sha256(
            {"subject_ids": (cue_id,)}
        ),
    )


def _finding(
    group: CaptionRequirementGroup,
    *,
    verdict: str = "pass",
    covered_subject_ids: tuple[str, ...],
    coverage_status: CaptionCoverageStatus = CaptionCoverageStatus.COMPLETE,
) -> CaptionRequirementFinding:
    return CaptionRequirementFinding(
        requirement_group=group,
        verdict=verdict,
        reason_code=(
            CaptionFindingReasonCode.REQUIREMENT_CONFIRMED
            if verdict == "pass"
            else CaptionFindingReasonCode.RENDER_CONTENT_MISMATCH
        ),
        covered_subject_ids=covered_subject_ids,
        raw_evidence_references=(f"evidence:{group.value}",),
        coverage_status=coverage_status,
        observation_fingerprint=canonical_sha256(
            {"group": group.value, "verdict": verdict}
        ),
    )


def _evidence(
    *,
    evidence_id: str,
    context: CaptionReviewContext,
    policy: CaptionQualityPolicy,
    tool: ToolIdentity,
    strength: EvidenceStrength,
    findings: tuple[CaptionRequirementFinding, ...],
) -> ReviewEvidence:
    payload = CaptionEvidencePayload(
        caption_policy_hash=policy.content_hash,
        caption_context_hash=caption_context_hash(context),
        findings=findings,
    )
    return seal_artifact(
        ReviewEvidence(
            artifact_id=evidence_id,
            schema_version="2.1",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id=evidence_id,
            source_provenance=(
                SourceReference(kind="derived", reference=evidence_id),
            ),
            evidence_id=evidence_id,
            layer=QaLayer.CAPTION,
            strength=strength,
            render_output_sha256=context.render_output_sha256,
            timeline_fingerprint=context.timeline_fingerprint,
            dependency_graph_revision_id=context.dependency_graph_revision_id,
            tool_identity=tool,
            measurement_contract_version=context.measurement_contract_version,
            subject_ids=tuple(
                dict.fromkeys(
                    subject
                    for finding in findings
                    for subject in finding.covered_subject_ids
                )
            )
            or ("c" * 64,),
            measured_payload=payload.model_dump(mode="json"),
        )
    )


def _passing_evidence(
    policy: CaptionQualityPolicy, context: CaptionReviewContext
) -> tuple[ReviewEvidence, ...]:
    domains = {
        item.requirement_group: item.subject_ids for item in context.coverage_domains
    }
    return (
        _evidence(
            evidence_id="caption-structural",
            context=context,
            policy=policy,
            tool=ToolIdentity(name="renderer-audit", version="1"),
            strength=EvidenceStrength.RENDERER_BOUND,
            findings=tuple(
                _finding(group, covered_subject_ids=domains[group])
                for group in CAPTION_REQUIREMENT_GROUPS[:2]
            ),
        ),
        _evidence(
            evidence_id="caption-final-media",
            context=context,
            policy=policy,
            tool=ToolIdentity(name="final-media-evaluator", version="1"),
            strength=EvidenceStrength.EXPLICIT_EVALUATOR,
            findings=tuple(
                _finding(group, covered_subject_ids=domains[group])
                for group in CAPTION_REQUIREMENT_GROUPS[2:]
            ),
        ),
    )


def test_caption_policy_requires_all_groups_and_explicit_authority() -> None:
    policy = _caption_policy()
    with pytest.raises(ValueError, match="all six"):
        CaptionQualityPolicy.model_validate(
            {
                **policy.model_dump(mode="json"),
                "required_groups": CAPTION_REQUIREMENT_GROUPS[:-1],
            }
        )
    with pytest.raises(ValueError, match="every group"):
        CaptionQualityPolicy.create(
            **{
                **policy.model_dump(
                    mode="python", exclude={"content_hash", "evidence_authorities"}
                ),
                "evidence_authorities": policy.evidence_authorities[:1],
            }
        )

    with pytest.raises(ValueError, match="final-media groups require"):
        CaptionEvidenceAuthority(
            tool_name="renderer-only",
            tool_version="1",
            requirement_groups=CAPTION_REQUIREMENT_GROUPS,
            allowed_strengths=(CaptionEvidenceStrength.RENDERER_BOUND,),
        )


@pytest.mark.parametrize(
    "reason_code",
    (
        CaptionFindingReasonCode.LOW_CONFIDENCE,
        CaptionFindingReasonCode.CONFLICTING_EVIDENCE,
    ),
)
def test_caption_pass_requires_confirmed_reason(
    reason_code: CaptionFindingReasonCode,
) -> None:
    with pytest.raises(ValueError, match="requires confirmed evidence"):
        CaptionRequirementFinding(
            requirement_group=CaptionRequirementGroup.RENDER_COMPLETENESS,
            verdict="pass",
            reason_code=reason_code,
            covered_subject_ids=("2" * 64,),
            raw_evidence_references=("evidence:ambiguous",),
            coverage_status=CaptionCoverageStatus.COMPLETE,
            observation_fingerprint="3" * 64,
        )


def test_caption_adjudication_requires_all_exact_group_domains() -> None:
    policy = _caption_policy()
    context = _context(policy)
    assert (
        adjudicate_caption_review_evidence(
            policy=policy,
            context=context,
            evidence=_passing_evidence(policy, context),
        )
        is QaVerdict.PASS
    )
    structural, final_media = _passing_evidence(policy, context)
    incomplete_payload = CaptionEvidencePayload.model_validate(
        dict(final_media.measured_payload)
    ).model_copy(update={"findings": tuple(CaptionEvidencePayload.model_validate(dict(final_media.measured_payload)).findings[:-1])})
    incomplete = ReviewEvidence.model_validate(
        {
            **final_media.model_dump(mode="json"),
            "measured_payload": incomplete_payload.model_dump(mode="json"),
            "content_hash": ZERO_HASH,
        }
    )
    incomplete = seal_artifact(incomplete)
    assert (
        adjudicate_caption_review_evidence(
            policy=policy, context=context, evidence=(structural, incomplete)
        )
        is QaVerdict.NOT_EVALUATED
    )


def test_caption_current_authorized_fail_has_priority_over_pass() -> None:
    policy = _caption_policy()
    context = _context(policy)
    evidence = list(_passing_evidence(policy, context))
    domain = context.coverage_domains[2]
    evidence.append(
        _evidence(
            evidence_id="caption-render-failure",
            context=context,
            policy=policy,
            tool=ToolIdentity(name="final-media-evaluator", version="1"),
            strength=EvidenceStrength.EXPLICIT_EVALUATOR,
            findings=(
                _finding(
                    CaptionRequirementGroup.RENDER_COMPLETENESS,
                    verdict="fail",
                    covered_subject_ids=domain.subject_ids,
                ),
            ),
        )
    )
    assert (
        adjudicate_caption_review_evidence(
            policy=policy, context=context, evidence=tuple(evidence)
        )
        is QaVerdict.FAIL
    )


def test_caption_authorized_uncertainty_blocks_an_otherwise_complete_pass() -> None:
    policy = _caption_policy()
    context = _context(policy)
    evidence = list(_passing_evidence(policy, context))
    domain = context.coverage_domains[2]
    evidence.append(
        _evidence(
            evidence_id="caption-render-uncertain",
            context=context,
            policy=policy,
            tool=ToolIdentity(name="final-media-evaluator", version="1"),
            strength=EvidenceStrength.EXPLICIT_EVALUATOR,
            findings=(
                CaptionRequirementFinding(
                    requirement_group=CaptionRequirementGroup.RENDER_COMPLETENESS,
                    verdict="not_evaluated",
                    reason_code=CaptionFindingReasonCode.LOW_CONFIDENCE,
                    covered_subject_ids=domain.subject_ids,
                    raw_evidence_references=("evidence:low-confidence",),
                    coverage_status=CaptionCoverageStatus.PARTIAL,
                    observation_fingerprint="4" * 64,
                ),
            ),
        )
    )
    assert (
        adjudicate_caption_review_evidence(
            policy=policy, context=context, evidence=tuple(evidence)
        )
        is QaVerdict.NOT_EVALUATED
    )


def test_unintended_text_requires_whole_render_domain_not_cue_roster() -> None:
    policy = _caption_policy()
    context = _context(policy)
    structural, final_media = _passing_evidence(policy, context)
    payload = CaptionEvidencePayload.model_validate(dict(final_media.measured_payload))
    wrong = tuple(
        (
            _finding(
                item.requirement_group,
                covered_subject_ids=(context.cue_subjects[0].subject_id,),
            )
            if item.requirement_group is CaptionRequirementGroup.UNINTENDED_TEXT
            else item
        )
        for item in payload.findings
    )
    replaced = _evidence(
        evidence_id="caption-wrong-whole-render-coverage",
        context=context,
        policy=policy,
        tool=ToolIdentity(name="final-media-evaluator", version="1"),
        strength=EvidenceStrength.EXPLICIT_EVALUATOR,
        findings=wrong,
    )
    assert (
        adjudicate_caption_review_evidence(
            policy=policy, context=context, evidence=(structural, replaced)
        )
        is QaVerdict.NOT_EVALUATED
    )


def test_caption_evidence_is_bound_to_exact_context_identity() -> None:
    policy = _caption_policy()
    context = _context(policy)
    evidence = _passing_evidence(policy, context)
    changed_context = context.model_copy(update={"render_output_sha256": "d" * 64})
    assert (
        adjudicate_caption_review_evidence(
            policy=policy, context=changed_context, evidence=evidence
        )
        is QaVerdict.NOT_EVALUATED
    )


def test_review_evidence_20_rejects_caption_payload() -> None:
    with pytest.raises(ValueError, match="CAPTION evidence"):
        ReviewEvidence.model_validate(
            {
                "artifact_id": "caption-evidence",
                "schema_version": "2.0",
                "revision": 1,
                "content_hash": ZERO_HASH,
                "creation_receipt_id": "caption-evidence",
                "source_provenance": (
                    {"kind": "derived", "reference": "caption-evidence"},
                ),
                "evidence_id": "caption-evidence",
                "layer": "caption",
                "strength": "measured",
                "render_output_sha256": "1" * 64,
                "timeline_fingerprint": "2" * 64,
                "dependency_graph_revision_id": "3" * 64,
                "tool_identity": {"name": "tool", "version": "1"},
                "measurement_contract_version": "caption-measurements/1",
                "subject_ids": ("subject",),
                "measured_payload": {},
            }
        )
