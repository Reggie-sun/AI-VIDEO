"""Exact-bound context construction and deterministic caption QA adjudication."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import ValidationError

from ai_video.production.caption_quality_contracts import (
    CAPTION_REQUIREMENT_GROUPS,
    ApprovedNonCaptionText,
    CaptionCoverageStatus,
    CaptionCueSubject,
    CaptionEvidenceAuthority,
    CaptionEvidencePayload,
    CaptionEvidenceStrength,
    CaptionGroupCoverageDomain,
    CaptionQualityPolicy,
    CaptionRequirementGroup,
    CaptionReviewContext,
    CaptionTrackReviewBinding,
)
from ai_video.production.captions import _canonical_track_bytes
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.manifest_schema import ManifestCapability, manifest_supports
from ai_video.production.models import (
    CaptionTrack,
    LoadedProductionProject,
    QaLayer,
    QaPolicy,
    QaVerdict,
    RendererSourceReceipt,
    ResolvedTimeline,
    ReviewEvidence,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
)
from ai_video.production.paths import _read_regular_file_nofollow


def caption_context_hash(context: CaptionReviewContext) -> str:
    return canonical_sha256(context.model_dump(mode="json"))


def caption_cue_subject_id(*, cue: object) -> str:
    return canonical_sha256(
        {
            "schema": "caption-cue-subject/1",
            "caption_track_id": getattr(cue, "caption_track_id"),
            "segment_id": getattr(cue, "segment_id"),
            "text": getattr(cue, "text"),
            "speaker_id": getattr(cue, "speaker_id"),
            "start_sample": getattr(cue, "start_sample"),
            "end_sample": getattr(cue, "end_sample"),
            "start_frame": getattr(cue, "start_frame"),
            "end_frame_exclusive": getattr(cue, "end_frame_exclusive"),
            "style_reference_id": getattr(cue, "style_reference_id"),
            "style_content_hash": getattr(cue, "style_content_hash"),
        }
    )


def _reopen_render_artifact(project: LoadedProductionProject, pointer, model_type):
    snapshot = _read_regular_file_nofollow(
        project.root / pointer.path, contained_by=project.root
    )
    if snapshot.file_sha256 != pointer.file_sha256:
        raise ValueError("caption context render artifact file hash is stale")
    model = model_type.model_validate_json(snapshot.data)
    if (
        not verify_artifact_hash(model)
        or model.revision != pointer.revision
        or model.content_hash != pointer.content_hash
    ):
        raise ValueError("caption context render artifact identity is stale")
    return model


def build_caption_review_context(
    *,
    project: LoadedProductionProject,
    caption_policy: CaptionQualityPolicy,
) -> CaptionReviewContext:
    """Derive a caption context only from one strict-reopened active project."""
    state = project.render_state
    graph = project.dependency_graph
    if state is None or graph is None:
        raise ValueError("caption review requires active render and dependency graph")
    timeline = _reopen_render_artifact(project, state.timeline, ResolvedTimeline)
    source = _reopen_render_artifact(
        project, state.source_receipt, RendererSourceReceipt
    )
    if not timeline.caption_cues or not source.caption_bindings:
        raise ValueError("caption review requires canonical caption cues and bindings")
    delivery_fingerprint = canonical_sha256(
        timeline.delivery_profile.model_dump(mode="json")
    )
    if caption_policy.delivery_profile_fingerprint != delivery_fingerprint:
        raise ValueError("caption policy delivery profile is not current")

    records_by_track: dict[str, object] = {}
    for record in project.registry.assets:
        metadata = record.caption_metadata
        if metadata is not None:
            if metadata.caption_track_id in records_by_track:
                raise ValueError("active Registry contains duplicate caption track identity")
            records_by_track[metadata.caption_track_id] = record

    policy_by_track = {
        item.caption_track_id: item for item in caption_policy.track_policies
    }
    ordered_track_ids = tuple(item.caption_track_id for item in source.caption_bindings)
    if tuple(item.caption_track_id for item in caption_policy.track_policies) != ordered_track_ids:
        raise ValueError("caption policy does not exactly cover ordered active tracks")

    track_bindings: list[CaptionTrackReviewBinding] = []
    cue_subjects: list[CaptionCueSubject] = []
    for source_binding in source.caption_bindings:
        track_id = source_binding.caption_track_id
        record = records_by_track.get(track_id)
        if record is None:
            raise ValueError("active caption source is absent from Registry")
        metadata = record.caption_metadata
        assert metadata is not None
        track_policy = policy_by_track.get(track_id)
        if track_policy is None or track_policy.language_tag != metadata.language:
            raise ValueError("caption track language does not match selected policy")
        path = project.asset_paths.get(record.asset_id)
        if path is None:
            raise ValueError("active caption asset path is unavailable")
        snapshot = _read_regular_file_nofollow(path, contained_by=project.root)
        track = CaptionTrack.model_validate_json(snapshot.data)
        if (
            snapshot.file_sha256 != record.sha256
            or snapshot.data != _canonical_track_bytes(track)
            or not verify_artifact_hash(track)
            or track.caption_track_id != track_id
            or track.language != metadata.language
            or track.timing_fingerprint != metadata.timing_fingerprint
            or source_binding.caption_asset_sha256 != record.sha256
        ):
            raise ValueError("active caption track identity is not current")
        source_audio_track_ids = tuple(
            dict.fromkeys(
                item.track_id
                for item in timeline.audio_spans
                if item.asset_id == metadata.source_audio_asset_id
                and item.asset_sha256 == metadata.source_audio_sha256
            )
        )
        if len(source_audio_track_ids) != 1:
            raise ValueError("caption track does not bind one exact source audio track")
        track_bindings.append(
            CaptionTrackReviewBinding(
                caption_asset_id=record.asset_id,
                caption_asset_sha256=record.sha256,
                caption_track_id=track_id,
                language_tag=metadata.language,
                timing_fingerprint=metadata.timing_fingerprint,
                style_reference_id=source_binding.style_reference_id,
                style_content_hash=source_binding.style_content_hash,
                source_audio_track_id=source_audio_track_ids[0],
                source_audio_asset_id=metadata.source_audio_asset_id,
                source_audio_sha256=metadata.source_audio_sha256,
            )
        )
        cues = tuple(
            item for item in timeline.caption_cues if item.caption_track_id == track_id
        )
        if tuple(item.segment_id for item in cues) != source_binding.resolved_cue_ids:
            raise ValueError("renderer caption cue roster is not current")
        for cue in cues:
            cue_subjects.append(
                CaptionCueSubject(
                    subject_id=caption_cue_subject_id(cue=cue),
                    caption_track_id=cue.caption_track_id,
                    segment_id=cue.segment_id,
                    text_sha256=canonical_sha256({"text": cue.text}),
                    speaker_id=cue.speaker_id,
                    start_sample=cue.start_sample,
                    end_sample=cue.end_sample,
                    start_frame=cue.start_frame,
                    end_frame_exclusive=cue.end_frame_exclusive,
                    style_reference_id=cue.style_reference_id,
                    style_content_hash=cue.style_content_hash,
                )
            )

    cue_ids = tuple(item.subject_id for item in cue_subjects)
    whole_render_subject = canonical_sha256(
        {
            "schema": "caption-whole-render-domain/1",
            "start_frame": 0,
            "end_frame_exclusive": timeline.total_frames,
            "frame_width": timeline.delivery_profile.width,
            "frame_height": timeline.delivery_profile.height,
        }
    )
    domains = tuple(
        CaptionGroupCoverageDomain.create(
            requirement_group=group,
            subject_ids=(whole_render_subject,) if group is CaptionRequirementGroup.UNINTENDED_TEXT else cue_ids,
            start_frame=0,
            end_frame_exclusive=timeline.total_frames,
            frame_width=timeline.delivery_profile.width,
            frame_height=timeline.delivery_profile.height,
        )
        for group in CAPTION_REQUIREMENT_GROUPS
    )
    approved_text = tuple(
        ApprovedNonCaptionText(
            text_identity=canonical_sha256({"text": item.text}),
            start_frame=item.start_frame,
            end_frame_exclusive=item.end_frame_exclusive,
            region_identity=canonical_sha256(
                {
                    "graphic_id": item.graphic_id,
                    "x_milli": item.x_milli,
                    "y_milli": item.y_milli,
                    "width_milli": item.width_milli,
                    "font_size_px": item.font_size_px,
                }
            ),
        )
        for item in timeline.commercial_graphics
    )
    return CaptionReviewContext(
        caption_policy_hash=caption_policy.content_hash,
        measurement_contract_version=caption_policy.measurement_contract_version,
        caption_tracks=tuple(track_bindings),
        cue_subjects=tuple(cue_subjects),
        coverage_domains=domains,
        approved_non_caption_text=approved_text,
        timeline_fingerprint=state.timeline_fingerprint,
        render_output_sha256=state.output.file_sha256,
        dependency_graph_revision_id=graph.revision_id,
        expected_cue_coverage_manifest_hash=canonical_sha256(
            {"subject_ids": cue_ids}
        ),
    )


def _authority_for(
    *,
    authorities: tuple[CaptionEvidenceAuthority, ...],
    evidence: ReviewEvidence,
    group: CaptionRequirementGroup,
) -> CaptionEvidenceAuthority | None:
    strength = CaptionEvidenceStrength(evidence.strength.value)
    for authority in authorities:
        if (
            authority.tool_name == evidence.tool_identity.name
            and authority.tool_version == evidence.tool_identity.version
            and group in authority.requirement_groups
            and strength in authority.allowed_strengths
        ):
            return authority
    return None


def adjudicate_caption_review_evidence(
    *,
    policy: CaptionQualityPolicy,
    context: CaptionReviewContext,
    evidence: Sequence[ReviewEvidence],
) -> QaVerdict:
    """Aggregate exact-bound raw findings; analyzers never own the verdict."""
    try:
        validated_policy = CaptionQualityPolicy.model_validate(
            policy.model_dump(mode="json")
        )
        validated_context = CaptionReviewContext.model_validate(
            context.model_dump(mode="json")
        )
    except ValidationError:
        return QaVerdict.NOT_EVALUATED
    if (
        validated_context.caption_policy_hash != validated_policy.content_hash
        or validated_context.measurement_contract_version
        != validated_policy.measurement_contract_version
    ):
        return QaVerdict.NOT_EVALUATED
    context_digest = caption_context_hash(validated_context)
    expected_domains = {
        item.requirement_group: set(item.subject_ids)
        for item in validated_context.coverage_domains
    }
    findings_by_group: dict[CaptionRequirementGroup, list[object]] = {
        group: [] for group in CAPTION_REQUIREMENT_GROUPS
    }
    for item in evidence:
        try:
            validated = ReviewEvidence.model_validate(item.model_dump(mode="json"))
            if (
                validated.schema_version != "2.1"
                or validated.layer is not QaLayer.CAPTION
                or validated.render_output_sha256
                != validated_context.render_output_sha256
                or validated.timeline_fingerprint
                != validated_context.timeline_fingerprint
                or validated.dependency_graph_revision_id
                != validated_context.dependency_graph_revision_id
                or validated.measurement_contract_version
                != validated_context.measurement_contract_version
            ):
                return QaVerdict.NOT_EVALUATED
            payload = CaptionEvidencePayload.model_validate(
                dict(validated.measured_payload)
            )
        except (ValidationError, ValueError):
            return QaVerdict.NOT_EVALUATED
        if (
            payload.caption_policy_hash != validated_policy.content_hash
            or payload.caption_context_hash != context_digest
        ):
            return QaVerdict.NOT_EVALUATED
        for finding in payload.findings:
            if _authority_for(
                authorities=validated_policy.evidence_authorities,
                evidence=validated,
                group=finding.requirement_group,
            ) is not None:
                findings_by_group[finding.requirement_group].append(finding)

    group_verdicts: list[QaVerdict] = []
    for group in CAPTION_REQUIREMENT_GROUPS:
        findings = findings_by_group[group]
        if any(item.verdict == "fail" for item in findings):
            group_verdicts.append(QaVerdict.FAIL)
            continue
        if any(item.verdict == "not_evaluated" for item in findings):
            group_verdicts.append(QaVerdict.NOT_EVALUATED)
            continue
        passes = [item for item in findings if item.verdict == "pass"]
        covered = {
            subject_id for item in passes for subject_id in item.covered_subject_ids
        }
        if (
            not passes
            or any(
                item.coverage_status is not CaptionCoverageStatus.COMPLETE
                for item in passes
            )
            or covered != expected_domains[group]
            or len({item.observation_fingerprint for item in passes}) > 1
        ):
            group_verdicts.append(QaVerdict.NOT_EVALUATED)
            continue
        group_verdicts.append(QaVerdict.PASS)
    if QaVerdict.FAIL in group_verdicts:
        return QaVerdict.FAIL
    if any(item is not QaVerdict.PASS for item in group_verdicts):
        return QaVerdict.NOT_EVALUATED
    return QaVerdict.PASS


def adjudicate_caption_layer(
    *, policy: QaPolicy, context: CaptionReviewContext | None, evidence: Sequence[ReviewEvidence]
) -> QaVerdict:
    if policy.caption_policy is None or context is None:
        return QaVerdict.NOT_EVALUATED
    return adjudicate_caption_review_evidence(
        policy=policy.caption_policy,
        context=context,
        evidence=evidence,
    )


@dataclass(frozen=True)
class ReopenedCaptionReview:
    receipt: ReviewReceipt
    request: ReviewRequest
    evidence: tuple[ReviewEvidence, ...]
    verdict: QaVerdict


def reopen_caption_review_chain(
    *,
    project: LoadedProductionProject,
    receipt_pointer: ReviewReceiptPointer,
) -> ReopenedCaptionReview:
    """Strict-reopen and recompute one current durable CAPTION review chain."""
    from ai_video.production.project import (
        load_qa_policy,
        load_review_evidence,
        load_review_receipt,
        load_review_request,
    )

    manifest = project.manifest
    state = project.render_state
    graph = project.dependency_graph
    if (
        receipt_pointer.layer is not QaLayer.CAPTION
        or receipt_pointer not in manifest.active_review_receipts
        or state is None
        or graph is None
        or manifest.active_render_state is None
        or manifest.active_dependency_graph is None
        or manifest.active_qa_policy is None
        or not manifest_supports(
            manifest.schema_version, ManifestCapability.CAPTION_REVIEW
        )
    ):
        raise ValueError("CAPTION review pointer is not current")
    receipt = load_review_receipt(project.root, receipt_pointer)
    request = load_review_request(project.root, receipt.review_request)
    policy = load_qa_policy(project.root, receipt.qa_policy)
    evidence = tuple(
        load_review_evidence(project.root, pointer) for pointer in receipt.evidence
    )
    if (
        receipt.schema_version != "2.1"
        or request.schema_version != "2.1"
        or receipt.layer is not QaLayer.CAPTION
        or request.caption_context is None
        or request.qa_policy != manifest.active_qa_policy
        or receipt.qa_policy != manifest.active_qa_policy
        or request.dependency_graph != manifest.active_dependency_graph
        or receipt.dependency_graph_revision_id != graph.revision_id
        or request.render_state != manifest.active_render_state
        or receipt.render_state != manifest.active_render_state
        or request.render_output_sha256 != state.output.file_sha256
        or receipt.render_output_sha256 != state.output.file_sha256
        or request.timeline_fingerprint != state.timeline_fingerprint
        or receipt.timeline_fingerprint != state.timeline_fingerprint
        or QaLayer.CAPTION not in request.requested_layers
        or policy.caption_policy is None
        or request.caption_context
        != build_caption_review_context(
            project=project,
            caption_policy=policy.caption_policy,
        )
    ):
        raise ValueError("CAPTION review chain identity is stale or incomplete")
    dependency_states_hash = canonical_sha256(
        {
            "dependency_states": [
                item.model_dump(mode="json") for item in manifest.dependency_states
            ]
        }
    )
    if request.dependency_states_hash != dependency_states_hash:
        raise ValueError("CAPTION review dependency state is stale")
    verdict = adjudicate_caption_review_evidence(
        policy=policy.caption_policy,
        context=request.caption_context,
        evidence=evidence,
    )
    if receipt.verdict is not verdict:
        raise ValueError("CAPTION review stored verdict does not match durable evidence")
    return ReopenedCaptionReview(
        receipt=receipt,
        request=request,
        evidence=evidence,
        verdict=verdict,
    )
