"""Private P6 adapter for exact-target CAPTION review transactions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.caption_quality import (
    adjudicate_caption_review_evidence,
    build_caption_review_context,
    caption_context_hash,
    reopen_caption_review_chain,
)
from ai_video.production.caption_quality_contracts import (
    CaptionEvidencePayload,
    CaptionEvidenceStrength,
    CaptionQualityPolicy,
    CaptionReviewContext,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    QaPolicy,
    QaVerdict,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewReceipt,
    ReviewRequest,
    SourceReference,
    StateCommitStatus,
    ToolIdentity,
)
from ai_video.production.paths import canonical_review_evidence_path
from ai_video.production.project import load_production_project, load_review_request
from ai_video.production.quality_gate_coordinator import (
    ReviewLayerRunner,
    UniversalQaCheckOutcome,
    UniversalQaContext,
    UniversalQaProfile,
    validate_universal_qa_coverage,
)
from ai_video.production.review import build_technical_review_context
from ai_video.production.state_commit import ProductionStateCommitter


CaptionQualityEvaluator = Callable[
    [CaptionReviewContext, CaptionQualityPolicy], CaptionEvidencePayload
]


@dataclass(frozen=True)
class CaptionReviewExecution:
    evaluator: CaptionQualityEvaluator
    tool_identity: ToolIdentity
    evidence_strength: CaptionEvidenceStrength
    attempt_id: str
    request_id: str
    evidence_id: str
    review_id: str


def _canonical_json_bytes(value: object) -> bytes:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")  # type: ignore[union-attr]
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def _dependency_states_hash(manifest: object) -> str:
    states = getattr(manifest, "dependency_states")
    return canonical_sha256(
        {
            "dependency_states": [
                item.model_dump(mode="json") for item in states
            ]
        }
    )


def _tool_is_authorized(
    *, policy: CaptionQualityPolicy, execution: CaptionReviewExecution
) -> bool:
    return any(
        authority.tool_name == execution.tool_identity.name
        and authority.tool_version == execution.tool_identity.version
        and execution.evidence_strength in authority.allowed_strengths
        for authority in policy.evidence_authorities
    )


def _raise_if_caption_attempt_outcome_unknown(
    *, committer: ProductionStateCommitter, manifest: object
) -> None:
    for attempt in getattr(manifest, "attempts"):
        if (
            attempt.operation != "review"
            or attempt.status
            not in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
            or attempt.review_request is None
        ):
            continue
        request = load_review_request(committer.project_root, attempt.review_request)
        if QaLayer.CAPTION in request.requested_layers:
            raise AiVideoError(
                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
                "A CAPTION review attempt has an unknown outcome; blind retry is forbidden.",
                retryable=False,
            )


def reopen_current_caption_review_outcome(
    committer: ProductionStateCommitter,
) -> UniversalQaCheckOutcome:
    """Strict-reopen the sole current CAPTION receipt without writing state."""
    project = load_production_project(committer.project_root / "project.yaml")
    pointers = tuple(
        item
        for item in project.manifest.active_review_receipts
        if item.layer is QaLayer.CAPTION
    )
    if not pointers:
        return UniversalQaCheckOutcome(
            verdict=QaVerdict.NOT_EVALUATED,
            current=False,
        )
    if len(pointers) != 1:
        raise ValueError("Production Manifest must contain exactly one active CAPTION receipt")
    reopened = reopen_caption_review_chain(
        project=project,
        receipt_pointer=pointers[0],
    )
    return UniversalQaCheckOutcome(verdict=reopened.verdict, current=True)


def run_caption_review_transaction(
    *,
    committer: ProductionStateCommitter,
    execution: CaptionReviewExecution,
) -> UniversalQaCheckOutcome:
    """Run one durable CAPTION review, or zero-write reopen its exact replay."""
    project, timeline = committer.current_final_media_target()
    manifest = project.manifest
    _raise_if_caption_attempt_outcome_unknown(
        committer=committer,
        manifest=manifest,
    )
    if any(
        item.layer is QaLayer.CAPTION
        for item in manifest.active_review_receipts
    ):
        return reopen_current_caption_review_outcome(committer)
    policy = project.qa_policy
    render_state = project.render_state
    if (
        policy is None
        or policy.schema_version != "2.1"
        or policy.caption_policy is None
        or manifest.active_qa_policy is None
        or manifest.active_dependency_graph is None
        or manifest.active_render_state is None
        or render_state is None
        or not _tool_is_authorized(
            policy=policy.caption_policy,
            execution=execution,
        )
    ):
        return UniversalQaCheckOutcome(
            verdict=QaVerdict.NOT_EVALUATED,
            current=False,
        )
    caption_context = build_caption_review_context(
        project=project,
        caption_policy=policy.caption_policy,
    )
    technical_context = build_technical_review_context(
        project,
        timeline,
        render_output_sha256=render_state.output.file_sha256,
        measurement_contract_version=policy.caption_policy.measurement_contract_version,
    )
    request = seal_artifact(
        ReviewRequest(
            schema_version="2.1",
            artifact_id=execution.request_id,
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=execution.request_id,
            source_provenance=(
                SourceReference(
                    kind="derived",
                    reference=caption_context_hash(caption_context),
                ),
            ),
            request_id=execution.request_id,
            base_manifest_revision=manifest.manifest_revision,
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=_dependency_states_hash(manifest),
            render_state=manifest.active_render_state,
            render_output_sha256=render_state.output.file_sha256,
            timeline_fingerprint=render_state.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            requested_layers=(QaLayer.CAPTION,),
            evidence_tool_identities=(execution.tool_identity,),
            technical_context=technical_context,
            caption_context=caption_context,
        )
    )
    begun = committer.begin_review(request, attempt_id=execution.attempt_id)
    request_pointer = next(
        item.review_request
        for item in begun.attempts
        if item.attempt_id == execution.attempt_id and item.review_request is not None
    )

    def analyzer(durable_request: ReviewRequest, permit: object) -> ReviewEvidence:
        if durable_request.caption_context is None:
            raise ValueError("Durable CAPTION request lost its caption context")
        consumed = permit._consume_review_analysis_permit(  # type: ignore[attr-defined]
            request_content_hash=durable_request.content_hash,
            render_output_sha256=durable_request.render_output_sha256,
            technical_context_hash=canonical_sha256(
                durable_request.technical_context.model_dump(mode="json")
            ),
            caption_context_hash=caption_context_hash(
                durable_request.caption_context
            ),
        )
        if consumed is not True:
            raise ValueError("CAPTION review analysis permit is invalid or already consumed")
        payload = CaptionEvidencePayload.model_validate(
            execution.evaluator(
                durable_request.caption_context,
                policy.caption_policy,
            ).model_dump(mode="json")
        )
        return seal_artifact(
            ReviewEvidence(
                schema_version="2.1",
                artifact_id=execution.evidence_id,
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=execution.evidence_id,
                source_provenance=(
                    SourceReference(
                        kind="derived", reference=durable_request.content_hash
                    ),
                ),
                evidence_id=execution.evidence_id,
                layer=QaLayer.CAPTION,
                strength=EvidenceStrength(execution.evidence_strength.value),
                render_output_sha256=durable_request.render_output_sha256,
                timeline_fingerprint=durable_request.timeline_fingerprint,
                dependency_graph_revision_id=durable_request.dependency_graph.revision_id,
                tool_identity=execution.tool_identity,
                measurement_contract_version=(
                    durable_request.caption_context.measurement_contract_version
                ),
                subject_ids=tuple(
                    item.subject_id for item in durable_request.caption_context.cue_subjects
                ),
                measured_payload=payload.model_dump(mode="json"),
            )
        )

    evidence = committer.run_review_analysis(
        review_request=request_pointer,
        expected_manifest_revision=begun.manifest_revision,
        analyzer=analyzer,
    )
    if not isinstance(evidence, ReviewEvidence):
        raise ValueError("CAPTION evaluator did not return durable evidence")
    evidence_payload = _canonical_json_bytes(evidence)
    evidence_pointer = ReviewEvidencePointer(
        path=canonical_review_evidence_path(evidence.content_hash),
        evidence_id=evidence.evidence_id,
        layer=evidence.layer,
        strength=evidence.strength,
        content_hash=evidence.content_hash,
        file_sha256=hashlib.sha256(evidence_payload).hexdigest(),
    )
    verdict = adjudicate_caption_review_evidence(
        policy=policy.caption_policy,
        context=caption_context,
        evidence=(evidence,),
    )
    receipt = seal_artifact(
        ReviewReceipt(
            schema_version="2.1",
            artifact_id=execution.review_id,
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=execution.review_id,
            source_provenance=(
                SourceReference(kind="derived", reference=evidence.content_hash),
            ),
            review_id=execution.review_id,
            layer=QaLayer.CAPTION,
            review_request=request_pointer,
            render_state=request.render_state,
            render_output_sha256=request.render_output_sha256,
            timeline_fingerprint=request.timeline_fingerprint,
            dependency_graph_revision_id=request.dependency_graph.revision_id,
            qa_policy=request.qa_policy,
            evidence=(evidence_pointer,),
            evidence_ids=(evidence.evidence_id,),
            tool_identities=(execution.tool_identity,),
            verdict=verdict,
        )
    )
    current = load_production_project(
        committer.project_root / "project.yaml"
    ).manifest
    committer.record_review_receipt(
        receipt,
        (evidence,),
        expected_manifest_revision=current.manifest_revision,
        attempt_id=execution.attempt_id,
    )
    return reopen_current_caption_review_outcome(committer)


def caption_aware_review_layer_runner(
    *,
    committer: ProductionStateCommitter,
    profile: UniversalQaProfile,
    context: UniversalQaContext,
    policy: QaPolicy,
    execution: CaptionReviewExecution | None,
    fallback: ReviewLayerRunner,
) -> ReviewLayerRunner:
    """Bind Gate 1 CAPTION to the private P6 adapter, never to its caller."""
    coverage = validate_universal_qa_coverage(
        profile=profile,
        context=context,
        policy=policy,
    )
    caption_outcome = None
    if context.applicability.has_captions:
        caption_outcome = (
            run_caption_review_transaction(
                committer=committer,
                execution=execution,
            )
            if coverage.verdict is QaVerdict.PASS and execution is not None
            else UniversalQaCheckOutcome(
                verdict=QaVerdict.NOT_EVALUATED,
                current=False,
            )
        )
    elif execution is not None:
        raise ValueError("A no-caption timeline cannot run CAPTION review")

    def run(layer, gate_context, gate_profile):
        if layer is QaLayer.CAPTION:
            if caption_outcome is None:
                raise ValueError("CAPTION review is not applicable to this timeline")
            return caption_outcome
        return fallback(layer, gate_context, gate_profile)

    return run


__all__ = [
    "CaptionQualityEvaluator",
    "CaptionReviewExecution",
    "caption_aware_review_layer_runner",
    "reopen_current_caption_review_outcome",
    "run_caption_review_transaction",
]
